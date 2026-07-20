//! Lock-free priority queue for intent scheduling.

use pyo3::prelude::*;
use std::cmp::Ordering;
use std::collections::BinaryHeap;
use std::sync::Arc;
use parking_lot::RwLock;

/// A queue item with priority and timestamp for ordering.
#[derive(Eq, PartialEq, Clone)]
struct QueueItem {
    priority: i64,
    timestamp: u64,
    intent_id: String,
}

impl Ord for QueueItem {
    fn cmp(&self, other: &Self) -> Ordering {
        self.priority
            .cmp(&other.priority)
            .then(self.timestamp.cmp(&other.timestamp).reverse())
    }
}

impl PartialOrd for QueueItem {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

/// Lock-free priority queue for EVOID intents.
///
/// Higher priority items are dequeued first.
/// Items with equal priority are dequeued by timestamp (FIFO).
#[pyclass]
pub struct PriorityQueue {
    heap: Arc<RwLock<BinaryHeap<QueueItem>>>,
}

#[pymethods]
impl PriorityQueue {
    #[new]
    fn new() -> Self {
        Self {
            heap: Arc::new(RwLock::new(BinaryHeap::new())),
        }
    }

    /// Add an intent to the queue with a given priority.
    fn push(&self, intent_id: String, priority: i64) {
        let item = QueueItem {
            priority,
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos() as u64,
            intent_id,
        };
        self.heap.write().push(item);
    }

    /// Remove and return the highest priority intent ID.
    /// Returns None if the queue is empty.
    fn pop(&self) -> Option<String> {
        self.heap.write().pop().map(|item| item.intent_id)
    }

    /// Return the number of items in the queue.
    fn len(&self) -> usize {
        self.heap.read().len()
    }

    /// Check if the queue is empty.
    fn is_empty(&self) -> bool {
        self.heap.read().is_empty()
    }

    /// Peek at the highest priority item without removing it.
    fn peek(&self) -> Option<(String, i64)> {
        self.heap.read().peek().map(|item| {
            (item.intent_id.clone(), item.priority)
        })
    }

    /// Clear all items from the queue.
    fn clear(&self) {
        self.heap.write().clear();
    }
}
