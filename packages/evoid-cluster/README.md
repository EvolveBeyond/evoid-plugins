<p align="center">
  <img src="https://img.shields.io/pypi/v/evoid-cluster?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/evoid-cluster?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/pypi/l/evoid-cluster?style=for-the-badge" alt="License">
</p>

<h1 align="center">evoid-cluster</h1>

<p align="center">
  <strong>Connect multiple evoid nodes into a unified system</strong>
</p>

---

## What is it?

evoid-cluster lets you connect multiple evoid servers into a cluster where each node has a specific role (user management, chat, database, game, marketplace). Nodes communicate through the message bus — no direct data access between them.

## How it works

```
Node A (users)  ←──WebSocket──→  Node B (chat)
       ↕                              ↕
Node C (database) ←──WebSocket──→  Node D (game)
```

Each node:
1. Announces its services via Intent through the message bus
2. ClusterBridge hooks into the local bus and forwards intents to remote nodes
3. Only Intent and Result flow between nodes — never raw data

## Quick Start

### 1. Install

```bash
pip install evoid-cluster
```

### 2. Config (cluster.toml)

```toml
[node]
id = "node-a"
name = "User Management"
host = "0.0.0.0"
port = 8001
roles = ["user"]

[cluster]
secret = "my-cluster-secret"
heartbeat_interval = 5

[cluster.peers]
"node-b" = { host = "192.168.1.11", port = 8002 }
"node-c" = { host = "192.168.1.12", port = 8003 }

[services]
"user:*" = "local"
"chat:*" = "node-b"
"database:*" = "node-c"
```

### 3. Node A (User Management)

```python
from evoid_cluster import ClusterBridge, ClusterConfig
from evoid import Intent, Level, execute

config = ClusterConfig.from_toml("cluster.toml")
bridge = ClusterBridge(config)

@bridge.service("user:*")
async def handle_user(ctx):
    if "get_profile" in ctx.intent.name:
        user = await ctx.deps["db"].read(f"user:{ctx.intent.metadata['user_id']}")
        return {"user": user}

await bridge.start()
```

### 4. Node B (Chat)

```python
config = ClusterConfig.from_toml("cluster.toml")  # roles = ["chat"]
bridge = ClusterBridge(config)

@bridge.service("chat:*")
async def handle_chat(ctx):
    if "send_message" in ctx.intent.name:
        # Get user info from Node A via cluster
        user = await execute(Intent(
            name="user:get_profile",
            level=Level.STANDARD,
            metadata={"user_id": ctx.intent.metadata["user_id"]}
        ))
        # user.value = {"user": {...}}
        return {"status": "sent"}

await bridge.start()
```

## Architecture

```
Application Layer (processors, game/chat/marketplace logic)
        │
ClusterBridge (intercept publish → routing → forwarding)
        │
evoid Message Bus (publish/subscribe — in-process)
        │
WebSocket Transport (inter-node connections)
        │
mTLS (auto-generated certificates)
```

## Key Concepts

### Service Registry
Each node announces its services. The registry maps Intent patterns to nodes:
- `user:get_profile` → Node A
- `chat:send_message` → Node B
- `database:*` → Node C

### Intent Routing
When a node publishes an Intent:
1. ClusterBridge checks if the service is local or remote
2. If remote: serialize → WebSocket → remote node → result → back
3. If local: execute normally

### No Direct Data Access
Nodes never access each other's data directly. Only Intent and Result flow between nodes. This ensures:
- Loose coupling
- Independent scaling
- Clean separation of concerns

## Admin API

```python
# List nodes
result = await execute(Intent(name="cluster:list_nodes"))

# Health check
result = await execute(Intent(name="cluster:health"))

# Register new node
await execute(Intent(name="cluster:register_node", metadata={
    "node_id": "node-e",
    "host": "192.168.1.14",
    "port": 8005,
    "roles": ["marketplace"],
}))
```

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)

## License

MIT
