//! System metrics collection using sysinfo.

use pyo3::prelude::*;

/// System metrics snapshot for scheduler decisions.
#[pyclass]
#[derive(Clone)]
pub struct SystemMetrics {
    #[pyo3(get)]
    cpu_cores: usize,
    #[pyo3(get)]
    cpu_count_logical: usize,
    #[pyo3(get)]
    load_avg_1m: f64,
    #[pyo3(get)]
    load_avg_5m: f64,
    #[pyo3(get)]
    load_avg_15m: f64,
    #[pyo3(get)]
    memory_total_mb: f64,
    #[pyo3(get)]
    memory_available_mb: f64,
}

#[pymethods]
impl SystemMetrics {
    #[new]
    fn new() -> Self {
        let mut sys = sysinfo::System::new_all();
        sys.refresh_all();

        let load = sysinfo::System::load_average();
        let cpu_cores = sysinfo::System::physical_core_count().unwrap_or(4);
        let cpu_logical = sysinfo::System::available_parallelism()
            .map(|n| n.get())
            .unwrap_or(cpu_cores);

        let total_mem = sys.total_memory();
        let avail_mem = sys.available_memory();

        Self {
            cpu_cores,
            cpu_count_logical: cpu_logical,
            load_avg_1m: load.one,
            load_avg_5m: load.five,
            load_avg_15m: load.fifteen,
            memory_total_mb: total_mem as f64 / 1024.0 / 1024.0,
            memory_available_mb: avail_mem as f64 / 1024.0 / 1024.0,
        }
    }

    /// Check if system is overloaded (load > logical cores).
    fn is_overloaded(&self) -> bool {
        self.load_avg_1m > self.cpu_count_logical as f64
    }

    /// Get recommended concurrency based on current load.
    fn recommended_concurrency(&self) -> usize {
        if self.is_overloaded() {
            (self.cpu_count_logical / 2).max(1)
        } else {
            self.cpu_count_logical
        }
    }

    /// Get memory usage percentage.
    fn memory_usage_percent(&self) -> f64 {
        if self.memory_total_mb > 0.0 {
            (1.0 - self.memory_available_mb / self.memory_total_mb) * 100.0
        } else {
            0.0
        }
    }

    /// Refresh metrics (creates new snapshot).
    fn refresh(&self) -> SystemMetrics {
        SystemMetrics::new()
    }
}
