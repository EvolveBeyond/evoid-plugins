<p align="center">
  <img src="https://img.shields.io/pypi/v/evoid-auth?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/evoid-auth?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/pypi/l/evoid-auth?style=for-the-badge" alt="License">
</p>

<h1 align="center">evoid-auth</h1>

<p align="center">
  <strong>Bring-your-own-provider authentication — Intent Handler system</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#intent-handler">Intent Handler</a> •
  <a href="#configuration">Config</a> •
  <a href="#api">API</a>
</p>

---

## Quick Start

```bash
pip install evoid-auth
```

### Method 1: Intent Handler (Recommended)

```python
from evoid_auth import register_provider, register_handlers
from evoid.core.extend import before

# Register your auth logic
async def my_auth(token: str) -> dict:
    user = await db.find_by_token(token)
    if not user:
        raise ValueError("Invalid token")
    return {"user": user.name, "role": user.role}

register_provider("my_auth", my_auth)

# Register auth as Intent handlers
register_handlers()

# Wire to pipeline
before("GET:/users", "authenticate")
before("POST:/admin", "authenticate")
```

### Method 2: Direct API

```python
from evoid_auth import authenticate, authorize, register_provider

register_provider("jwt", jwt_auth_fn)
# authenticate and authorize are pipeline processors
```

---

## Intent Handler

evoid-auth registers these Intent handlers:

| Intent | Handler | Description |
|--------|---------|-------------|
| `auth.authenticate` | `authenticate` | Extract token, call provider, set user in ctx |
| `auth.authorize` | `authorize` | Check role against requirement |

### How it works

1. `register_handlers()` registers auth Intents as pipeline processors
2. `authenticate` extracts token from request headers/metadata
3. Calls your registered provider function
4. Writes `user`, `role`, `auth_method` to `ctx.state`
5. `authorize` checks `ctx.state["role"]` against required roles

---

## Token Sources

The `authenticate` processor checks these in order:

1. `metadata["token"]` — direct field
2. `Authorization: Bearer <token>` header
3. `Authorization: Token <token>` header
4. `X-API-Key` header
5. Query parameter fallback

## Role Hierarchy

```
admin (4) > editor (3) > viewer (2) > guest (1)
```

A higher role satisfies any lower requirement.

```python
from evoid.core.extend import before

# Requires admin role
before("DELETE:/users", "authenticate", required_role="admin")

# Requires viewer or higher
before("GET:/reports", "authenticate", required_roles=["viewer", "editor", "admin"])
```

---

## Configuration

### TOML

```toml
[engines]
auth = "auth"
```

### Python

```python
from evoid_auth import register_provider

# Register multiple providers
register_provider("jwt", jwt_auth_fn)
register_provider("api_key", api_key_auth_fn)

# Use specific provider in pipeline
before("GET:/users", "authenticate", provider="jwt")
```

---

## API

### `register_handlers()`

Register auth as Intent handlers. No parameters needed.

### Provider Registration

| Function | Signature | Description |
|----------|-----------|-------------|
| `register_provider` | `register_provider(name, fn)` | Register an auth provider |
| `resolve_provider` | `resolve_provider(name)` | Get provider by name |
| `list_providers` | `list_providers()` | List all registered names |

### Processors

| Processor | Description |
|-----------|-------------|
| `authenticate` | Extracts token, calls provider, sets `ctx.state` |
| `authorize` | Checks role against requirement |

### Provider Signature

```python
async def my_provider(token: str) -> dict:
    """Must return dict with at least 'role' key."""
    return {"user": "alice", "role": "admin"}
```

---

## Dependencies

- `evoid>=0.4.0`

## Optional Dependencies

- `pyjwt>=2.8.0` — for JWT decoding in your provider

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)
- [Plugin Collection](https://evolvebeyond.github.io/EVOID/learn/plugin-collection/)

## License

MIT
