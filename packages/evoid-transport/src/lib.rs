//! EVOID Transport — low-latency UDP transport for EVOID.
//!
//! PyO3 module exposing UDP server/client to Python.

mod codec;
mod server;

use std::net::SocketAddr;
use std::sync::Arc;

use pyo3::prelude::*;

use server::UdpServer;

/// Python-facing UDP transport server.
#[pyclass]
pub struct EvoidTransport {
    inner: Arc<UdpServer>,
}

#[pymethods]
impl EvoidTransport {
    #[new]
    #[pyo3(signature = (host, port, tick_rate=60))]
    fn new(host: &str, port: u16, tick_rate: u32) -> Self {
        let addr: SocketAddr = format!("{host}:{port}").parse()
            .expect("evoid-transport: invalid listen address");
        Self {
            inner: Arc::new(UdpServer::new(addr, tick_rate)),
        }
    }

    #[getter]
    fn address(&self) -> String {
        self.inner.addr().to_string()
    }

    #[getter]
    fn tick_rate(&self) -> u32 {
        self.inner.tick_rate()
    }

    #[getter]
    fn client_count(&self) -> usize {
        self.inner.client_count()
    }

    fn register_client(&self, address: &str, player_name: &str) -> u64 {
        let addr: SocketAddr = address.parse()
            .expect("evoid-transport: invalid client address");
        self.inner.register_client(addr, player_name)
    }

    fn remove_client(&self, address: &str) -> Option<(u64, String)> {
        let addr: SocketAddr = address.parse()
            .expect("evoid-transport: invalid client address");
        self.inner.remove_client(&addr)
    }

    fn get_client_id(&self, address: &str) -> Option<u64> {
        let addr: SocketAddr = address.parse()
            .expect("evoid-transport: invalid client address");
        self.inner.get_client_id(&addr)
    }

    fn list_clients(&self) -> Vec<(String, u64)> {
        self.inner
            .client_addrs()
            .into_iter()
            .map(|(addr, id)| (addr.to_string(), id))
            .collect()
    }

    fn build_connected(&self, client_id: u64) -> Vec<u8> {
        self.inner.build_connected_packet(client_id)
    }

    fn build_state_sync(&self, client_id: u64, game_id: &str, state: &[u8], tick: u64) -> Vec<u8> {
        self.inner.build_state_sync_packet(client_id, game_id, state, tick)
    }

    fn build_player_joined(&self, client_id: u64, player_id: u64, player_name: &str) -> Vec<u8> {
        self.inner.build_player_joined_packet(client_id, player_id, player_name)
    }

    fn build_player_left(&self, client_id: u64, player_id: u64, player_name: &str) -> Vec<u8> {
        self.inner.build_player_left_packet(client_id, player_id, player_name)
    }

    fn build_ping(&self, client_id: u64) -> Vec<u8> {
        self.inner.build_ping_packet(client_id)
    }

    fn cleanup_stale(&self, timeout_ms: u64) -> Vec<(u64, String)> {
        self.inner.cleanup_stale(timeout_ms)
    }
}

// ── Codec Functions ─────────────────────────────────────────────────────────

#[pyfunction]
fn validate_packet(data: &[u8]) -> bool {
    match codec::decode_header(data) {
        Ok(header) => header.is_valid(),
        Err(_) => false,
    }
}

#[pyfunction]
fn protocol_version() -> u8 {
    codec::PROTOCOL_VERSION
}

#[pyfunction]
fn magic_bytes() -> Vec<u8> {
    codec::MAGIC.to_vec()
}

// ── Module Registration ─────────────────────────────────────────────────────

#[pymodule]
fn evoid_transport_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<EvoidTransport>()?;
    m.add_function(wrap_pyfunction!(validate_packet, m)?)?;
    m.add_function(wrap_pyfunction!(protocol_version, m)?)?;
    m.add_function(wrap_pyfunction!(magic_bytes, m)?)?;
    Ok(())
}
