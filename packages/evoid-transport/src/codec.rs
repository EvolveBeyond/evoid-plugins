//! Binary serialization for EVOID transport packets.
//!
//! Replaces JSON with bincode — ~60% smaller, ~3x faster decode.

#![allow(dead_code)]

use serde::{Deserialize, Serialize};

/// Magic bytes to identify EVOID packets: "EVOI"
pub const MAGIC: [u8; 4] = [0x45, 0x56, 0x4F, 0x49];

/// Protocol version — bump on breaking wire changes.
pub const PROTOCOL_VERSION: u8 = 1;

/// Packet types on the wire.
#[repr(u8)]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum PacketType {
    /// Client → Server: player action / intent
    Intent = 0x01,
    /// Server → Client: authoritative game state
    StateSync = 0x02,
    /// Client → Server: ACK for reliable delivery
    Ack = 0x03,
    /// Server → Client: connection accepted
    Connected = 0x04,
    /// Either direction: keepalive ping
    Ping = 0x05,
    /// Either direction: keepalive pong
    Pong = 0x06,
    /// Server → Client: player joined
    PlayerJoined = 0x07,
    /// Server → Client: player left
    PlayerLeft = 0x08,
}

/// Header prepended to every packet.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PacketHeader {
    pub magic: [u8; 4],
    pub version: u8,
    pub packet_type: PacketType,
    pub sequence: u32,
    pub ack: u32,
    pub ack_bitfield: u32,
}

impl PacketHeader {
    pub fn new(packet_type: PacketType, sequence: u32, ack: u32, ack_bitfield: u32) -> Self {
        Self {
            magic: MAGIC,
            version: PROTOCOL_VERSION,
            packet_type,
            sequence,
            ack,
            ack_bitfield,
        }
    }

    pub fn is_valid(&self) -> bool {
        self.magic == MAGIC && self.version == PROTOCOL_VERSION
    }
}

/// Intent packet — client action sent to server.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IntentPacket {
    pub header: PacketHeader,
    pub intent_name: String,
    pub metadata: Vec<u8>,
    pub priority: u8,
    pub timestamp: u64,
}

/// State sync packet — server sends authoritative state to clients.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StateSyncPacket {
    pub header: PacketHeader,
    pub game_id: String,
    pub state: Vec<u8>,
    pub tick: u64,
}

/// Connection accepted packet.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConnectedPacket {
    pub header: PacketHeader,
    pub client_id: u64,
    pub player_count: u32,
}

/// Player event packet (join/leave).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlayerEventPacket {
    pub header: PacketHeader,
    pub player_id: u64,
    pub player_name: String,
}

/// Ping/Pong packet for latency measurement.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PingPacket {
    pub header: PacketHeader,
    pub send_time: u64,
}

// ── Encode / Decode ────────────────────────────────────────────────────────

pub fn encode<T: Serialize>(packet: &T) -> Vec<u8> {
    bincode::serialize(packet).expect("evoid-transport: failed to encode packet")
}

pub fn decode_header(data: &[u8]) -> Result<PacketHeader, String> {
    bincode::deserialize(data).map_err(|e| format!("header decode: {e}"))
}

pub fn decode_intent(data: &[u8]) -> Result<IntentPacket, String> {
    bincode::deserialize(data).map_err(|e| format!("intent decode: {e}"))
}

pub fn decode_state_sync(data: &[u8]) -> Result<StateSyncPacket, String> {
    bincode::deserialize(data).map_err(|e| format!("state_sync decode: {e}"))
}

pub fn decode_ping(data: &[u8]) -> Result<PingPacket, String> {
    bincode::deserialize(data).map_err(|e| format!("ping decode: {e}"))
}
