<p align="center">
  <img src="https://img.shields.io/pypi/v/evoid-cluster?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/evoid-cluster?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/pypi/l/evoid-cluster?style=for-the-badge" alt="License">
</p>

<h1 align="center">evoid-cluster</h1>

<p align="center">
  <strong>Multi-node clustering — Intent Handler system</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#intent-handler">Intent Handler</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#api">API</a>
</p>

---

## Quick Start

```bash
pip install evoid-cluster
```

### Method 1: Intent Handler (Recommended)

```python
from evoid_cluster import register_handlers

# Register cluster as Intent handlers
register_handlers(config={
    "node": {"id": "node-1", "host": "0.0.0.0", "port": 9100},
    "cluster": {"secret": "my-secret"},
})
```

### Method 2: Direct API

```python
from evoid_cluster import ClusterBridge, ClusterConfig

config = ClusterConfig.from_toml("cluster.toml")
bridge = ClusterBridge(config)
```

---

## Intent Handler

evoid-cluster registers inter-node communication as Intent handlers.

---

## Architecture

```
Node A (users)  ←──WebSocket──→  Node B (chat)
       ↕                              ↕
Node C (database) ←──WebSocket──→  Node D (game)
```

Each node:
1. Announces its services via Intent through the message bus
2. ClusterBridge forwards intents to remote nodes
3. Only Intent and Result flow between nodes — never raw data

---

## Configuration

### TOML (separate file)

```toml
[node]
id = "node-1"
host = "0.0.0.0"
port = 9100

[cluster]
secret = "my-cluster-secret"

[cluster.peers]
"node-b" = { host = "192.168.1.11", port = 9100 }
```

---

## API

### `register_handlers(config: dict)`

Register cluster as Intent handlers.

### ClusterBridge Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `start` | `async start()` | Start cluster node |
| `stop` | `async stop()` | Stop cluster node |
| `broadcast` | `async broadcast(intent)` | Send intent to all peers |

---

## Dependencies

- `evoid>=0.4.0`
- `websockets>=12.0`

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)
- [Plugin Collection](https://evolvebeyond.github.io/EVOID/learn/plugin-collection/)

## License

MIT
