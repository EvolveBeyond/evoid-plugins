# evoid-maubot

EVOID adapter for [maubot](https://github.com/maubot/maubot) — generic framework for building Matrix bots with EVOID IOP.

## What It Does

Provides a base `EvoidMaubot` class that handles:
- Matrix event → EVOID Intent conversion
- Command routing and permission checking
- SQLite/Smart Storage initialization
- EVOID service lifecycle (start/stop)

**Jitsi-specific commands are NOT included** — they live in `matrix-jitsi-bot/services/matrixbot/`.

## Installation

```bash
pip install evoid-maubot
# With storage
pip install evoid-maubot[storage]
```

## Quick Start

```python
# mybot.py
from evoid_maubot import EvoidMaubot
from evoid_maubot.commands import CommandDef, COMMAND_REGISTRY, parse_required_one

# Define your commands
COMMAND_REGISTRY.update({
    "greet": CommandDef(
        description="Greet someone",
        usage="<name>",
        category="Social",
        arg_parser=parse_required_one,
    ),
})

class MyBot(EvoidMaubot):
    def _command_prefix(self) -> str:
        return "mybot"  # !mybot greet Alice

    def _intent_prefix(self) -> str:
        return "mybot"  # Intent: mybot:greet

    def _make_handler(self, cmd_name: str):
        async def handler(intent):
            name = intent.metadata.get("args", {}).get("value", "world")
            return {"status": "executed", "greeting": f"Hello, {name}!"}
        return handler

    def _make_intent(self, subcommand, cmd_def, args, event):
        intent = super()._make_intent(subcommand, cmd_def, args, event)
        intent.metadata["custom_field"] = "value"
        return intent

# Register as maubot plugin
def setup():
    return MyBot
```

## Configuration

```yaml
service_name: mybot
command_prefix: mybot

storage:
  db_path: mybot.db
  enable_smart_routing: true
  smart_mapping:
    mydata: storage.sqlite
  smart_schemas:
    mydata: ["id", "field1", "field2"]

admin_whitelist:
  - "@admin:example.com"
```

## Architecture

```
Matrix Event (!mybot greet Alice)
         ↓
EvoidMaubot.on_message() — Adapter
         ↓
Intent(name="mybot:greet", level=STANDARD, metadata={...})
         ↓
EVOID Pipeline: validate → authorize → handler
         ↓
Handler returns: {"greeting": "Hello, Alice!"}
         ↓
Matrix Reply
```

## Extending

Override these methods in your subclass:

| Method | Purpose |
|--------|---------|
| `_command_prefix()` | Matrix command prefix (default: "bot") |
| `_intent_prefix()` | EVOID intent namespace (default: "bot") |
| `_register_intents()` | Register custom intents |
| `_make_handler(cmd)` | Create EVOID handler for command |
| `_make_intent(...)` | Build Intent from command |
| `_on_command(event, args)` | Custom command dispatch |
| `_on_result(cmd, args, event, result)` | Post-result hook (persistence) |
| `_is_moderator(user_id)` | Moderator check |
| `_help_text()` | Custom help output |

## Storage

Optional persistence via `evoid-sqlite` and `evoid-smart-storage`:

```bash
pip install evoid-maubot[storage]
```

Configure `storage.smart_mapping` and `storage.smart_schemas` in config.

## Development

```bash
uv venv && uv pip install -e ".[dev]"
ruff check evoid_maubot/
ruff format evoid_maubot/
pytest tests/ -v
```

## License

Apache-2.0