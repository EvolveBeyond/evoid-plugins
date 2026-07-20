//! UDP transport server — the core of evoid-transport.
//!
//! Manages client connections, packet sequencing, reliability, and
//! bridges to Python via PyO3.

#![allow(dead_code, unused_imports)]

use std::collections::HashMap;
use std::net::SocketAddr;
use std::time::{SystemTime, UNIX_EPOCH};

use parking_lot::RwLock;

use crate::codec::{
    self, ConnectedPacket, IntentPacket, PacketHeader, PacketType, PingPacket,
    PlayerEventPacket, StateSyncPacket,
};

// ── Connection State ────────────────────────────────────────────────────────

#[derive(Debug, Clone)]
struct ClientState {
    addr: SocketAddr,
    client_id: u64,
    player_name: String,
    sequence: u32,
    last_ack: u32,
    ack_bitfield: u32,
    last_packet_time: u64,
    connected: bool,
}

// ── UDP Server ──────────────────────────────────────────────────────────────

pub struct UdpServer {
    clients: RwLock<HashMap<SocketAddr, ClientState>>,
    addr_to_id: RwLock<HashMap<SocketAddr, u64>>,
    next_client_id: RwLock<u64>,
    listen_addr: SocketAddr,
    tick_rate: u32,
}

impl UdpServer {
    pub fn new(listen_addr: SocketAddr, tick_rate: u32) -> Self {
        Self {
            clients: RwLock::new(HashMap::new()),
            addr_to_id: RwLock::new(HashMap::new()),
            next_client_id: RwLock::new(2),
            listen_addr,
            tick_rate,
        }
    }

    pub fn addr(&self) -> SocketAddr {
        self.listen_addr
    }

    pub fn tick_rate(&self) -> u32 {
        self.tick_rate
    }

    pub fn register_client(&self, addr: SocketAddr, player_name: &str) -> u64 {
        let client_id = {
            let mut next = self.next_client_id.write();
            let id = *next;
            *next += 1;
            id
        };

        let now = Self::now_ms();
        let state = ClientState {
            addr,
            client_id,
            player_name: player_name.to_string(),
            sequence: 0,
            last_ack: 0,
            ack_bitfield: 0,
            last_packet_time: now,
            connected: true,
        };

        self.clients.write().insert(addr, state);
        self.addr_to_id.write().insert(addr, client_id);

        client_id
    }

    pub fn remove_client(&self, addr: &SocketAddr) -> Option<(u64, String)> {
        self.clients.write().remove(addr).map(|s| {
            self.addr_to_id.write().remove(addr);
            (s.client_id, s.player_name)
        })
    }

    pub fn get_client_id(&self, addr: &SocketAddr) -> Option<u64> {
        self.addr_to_id.read().get(addr).copied()
    }

    pub fn client_count(&self) -> usize {
        self.clients.read().len()
    }

    pub fn client_addrs(&self) -> Vec<(SocketAddr, u64)> {
        self.clients
            .read()
            .iter()
            .map(|(addr, state)| (*addr, state.client_id))
            .collect()
    }

    pub fn build_connected_packet(&self, client_id: u64) -> Vec<u8> {
        let seq = self.next_sequence(client_id);
        let (ack, ack_bits) = self.get_ack_state(client_id);

        codec::encode(&ConnectedPacket {
            header: PacketHeader::new(PacketType::Connected, seq, ack, ack_bits),
            client_id,
            player_count: self.client_count() as u32,
        })
    }

    pub fn build_state_sync_packet(
        &self,
        client_id: u64,
        game_id: &str,
        state: &[u8],
        tick: u64,
    ) -> Vec<u8> {
        let seq = self.next_sequence(client_id);
        let (ack, ack_bits) = self.get_ack_state(client_id);

        codec::encode(&StateSyncPacket {
            header: PacketHeader::new(PacketType::StateSync, seq, ack, ack_bits),
            game_id: game_id.to_string(),
            state: state.to_vec(),
            tick,
        })
    }

    pub fn build_player_joined_packet(
        &self,
        client_id: u64,
        player_id: u64,
        player_name: &str,
    ) -> Vec<u8> {
        let seq = self.next_sequence(client_id);
        let (ack, ack_bits) = self.get_ack_state(client_id);

        codec::encode(&PlayerEventPacket {
            header: PacketHeader::new(PacketType::PlayerJoined, seq, ack, ack_bits),
            player_id,
            player_name: player_name.to_string(),
        })
    }

    pub fn build_player_left_packet(
        &self,
        client_id: u64,
        player_id: u64,
        player_name: &str,
    ) -> Vec<u8> {
        let seq = self.next_sequence(client_id);
        let (ack, ack_bits) = self.get_ack_state(client_id);

        codec::encode(&PlayerEventPacket {
            header: PacketHeader::new(PacketType::PlayerLeft, seq, ack, ack_bits),
            player_id,
            player_name: player_name.to_string(),
        })
    }

    pub fn build_ping_packet(&self, client_id: u64) -> Vec<u8> {
        let seq = self.next_sequence(client_id);
        let (ack, ack_bits) = self.get_ack_state(client_id);

        codec::encode(&PingPacket {
            header: PacketHeader::new(PacketType::Ping, seq, ack, ack_bits),
            send_time: Self::now_ms(),
        })
    }

    pub fn process_incoming(&self, data: &[u8], from: SocketAddr) -> Option<ProcessedPacket> {
        let header = codec::decode_header(data).ok()?;
        if !header.is_valid() {
            return None;
        }

        if let Some(client_id) = self.get_client_id(&from) {
            self.update_ack_state(client_id, header.ack, header.ack_bitfield);
        }

        match header.packet_type {
            PacketType::Intent => {
                let packet = codec::decode_intent(data).ok()?;
                Some(ProcessedPacket::Intent {
                    client_id: self.get_client_id(&from).unwrap_or(0),
                    intent_name: packet.intent_name,
                    metadata: packet.metadata,
                    priority: packet.priority,
                    timestamp: packet.timestamp,
                })
            }
            PacketType::Ping => {
                let packet = codec::decode_ping(data).ok()?;
                Some(ProcessedPacket::Ping {
                    client_id: self.get_client_id(&from).unwrap_or(0),
                    send_time: packet.send_time,
                })
            }
            PacketType::Ack => None,
            _ => None,
        }
    }

    pub fn cleanup_stale(&self, timeout_ms: u64) -> Vec<(u64, String)> {
        let now = Self::now_ms();
        let mut stale = Vec::new();
        let mut clients = self.clients.write();
        let mut to_remove = Vec::new();

        for (addr, state) in clients.iter() {
            if now.saturating_sub(state.last_packet_time) > timeout_ms {
                stale.push((state.client_id, state.player_name.clone()));
                to_remove.push(*addr);
            }
        }

        for addr in to_remove {
            clients.remove(&addr);
            self.addr_to_id.write().remove(&addr);
        }

        stale
    }

    fn next_sequence(&self, client_id: u64) -> u32 {
        let mut clients = self.clients.write();
        for state in clients.values_mut() {
            if state.client_id == client_id {
                let seq = state.sequence;
                state.sequence = seq.wrapping_add(1);
                return seq;
            }
        }
        0
    }

    fn get_ack_state(&self, client_id: u64) -> (u32, u32) {
        let clients = self.clients.read();
        for state in clients.values() {
            if state.client_id == client_id {
                return (state.last_ack, state.ack_bitfield);
            }
        }
        (0, 0)
    }

    fn update_ack_state(&self, client_id: u64, ack: u32, ack_bitfield: u32) {
        let mut clients = self.clients.write();
        for state in clients.values_mut() {
            if state.client_id == client_id {
                state.last_ack = ack;
                state.ack_bitfield = ack_bitfield;
                state.last_packet_time = Self::now_ms();
                break;
            }
        }
    }

    fn now_ms() -> u64 {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_millis() as u64
    }
}

// ── Processed Packet ────────────────────────────────────────────────────────

#[derive(Debug, Clone)]
pub enum ProcessedPacket {
    Intent {
        client_id: u64,
        intent_name: String,
        metadata: Vec<u8>,
        priority: u8,
        timestamp: u64,
    },
    Ping {
        client_id: u64,
        send_time: u64,
    },
}
