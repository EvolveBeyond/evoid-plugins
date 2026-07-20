//! EVOID Scheduler — PyO3 Rust extensions.
//!
//! Provides lock-free priority queue and system metrics for EVOID scheduling.

mod metrics;
mod queue;

use pyo3::prelude::*;

/// EVOID Scheduler Rust extensions.
#[pymodule]
fn evoid_scheduler(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<queue::PriorityQueue>()?;
    m.add_class::<metrics::SystemMetrics>()?;
    Ok(())
}
