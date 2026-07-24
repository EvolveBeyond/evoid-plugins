# evoid-maubot

EVOID adapter for [maubot](https://github.com/maubot/maubot) — bridges Matrix events to Jitsi iframe commands via EVOID pipeline.

## What It Does

Converts Matrix `!jitsi` commands into EVOID Intents, which map to Jitsi's 50+ iframe API commands. Full reference: https://jitsi.github.io/handbook/docs/dev-guide/dev-guide-iframe-commands/

## Installation

```bash
# As EVOID plugin
evo plug install evoid-maubot

# As maubot plugin
cd packages/evoid-maubot
zip -9r evoid-maubot.mbp *
# Upload .mbp to maubot management interface
```

## Commands

### Room Management
| Command | Description | Mod |
|---------|-------------|-----|
| `!jitsi create [name]` | Create a new meeting | |
| `!jitsi join <room>` | Get join link | |
| `!jitsi hangup` | End the call | |
| `!jitsi end` | End conference for everyone | Yes |

### Watch Party
| Command | Description | Mod |
|---------|-------------|-----|
| `!jitsi watch <url> [name]` | Create watch party (YouTube/video/audio) | |
| `!jitsi stopwatch` | Stop shared video | |

### Display
| Command | Description | Mod |
|---------|-------------|-----|
| `!jitsi name <name>` | Set display name | |
| `!jitsi email <email>` | Set email address | |
| `!jitsi subject <text>` | Set conference subject | Yes |
| `!jitsi localsubject <text>` | Set local subject | |

### Media Control
| Command | Description | Mod |
|---------|-------------|-----|
| `!jitsi mute` | Toggle audio mute | |
| `!jitsi video` | Toggle video mute | |
| `!jitsi screen` | Toggle screen sharing | |
| `!jitsi muteall [audio\|video]` | Mute all participants | Yes |
| `!jitsi muteremote <id> [audio\|video]` | Mute specific participant | Yes |
| `!jitsi noise [true\|false]` | Toggle noise suppression | |
| `!jitsi quality <720\|480\|360\|240>` | Set video quality | |
| `!jitsi audioonly [true\|false]` | Audio only mode | |
| `!jitsi camera [user\|environment]` | Toggle camera facing | |
| `!jitsi mirror` | Toggle camera mirror | |
| `!jitsi vbg` | Toggle virtual background dialog | |
| `!jitsi blur [slight-blur\|blur\|none]` | Set blurred background | |
| `!jitsi virtualbg [true\|false] [img]` | Set virtual background | |

### Layout
| Command | Description | Mod |
|---------|-------------|-----|
| `!jitsi tile` | Toggle tile view | |
| `!jitsi settile [true\|false]` | Set tile view | |
| `!jitsi filmstrip` | Toggle filmstrip | |
| `!jitsi chat` | Toggle chat panel | |
| `!jitsi hand` | Toggle raise hand | |
| `!jitsi subtitles` | Toggle subtitles | |
| `!jitsi setsubtitles [true\|false] [lang]` | Set subtitles | |
| `!jitsi participants [true\|false]` | Toggle participants pane | |
| `!jitsi whiteboard` | Toggle whiteboard | |
| `!jitsi lobby [true\|false]` | Toggle lobby mode | Yes |

### Participants
| Command | Description | Mod |
|---------|-------------|-----|
| `!jitsi kick <id>` | Kick participant | Yes |
| `!jitsi mod <id>` | Grant moderator | Yes |
| `!jitsi pin [id]` | Pin participant | |
| `!jitsi volume <id> <0-1>` | Set volume | |
| `!jitsi largevideo [id] [camera\|desktop]` | Set large video | |
| `!jitsi names <id:name> [id:name ...]` | Overwrite names locally | |
| `!jitsi sendto <id> <roomId>` | Send to breakout room | Yes |

### Moderation
| Command | Description | Mod |
|---------|-------------|-----|
| `!jitsi approveknock <id> <true\|false>` | Approve/reject lobby | Yes |
| `!jitsi moderation <true\|false> <audio\|video>` | Toggle moderation | Yes |
| `!jitsi askunmute <id>` | Ask to unmute | Yes |
| `!jitsi approvevideo <id>` | Approve video | Yes |
| `!jitsi reject <id> <audio\|video>` | Reject participant | Yes |

### Chat
| Command | Description | Mod |
|---------|-------------|-----|
| `!jitsi send <message> [id]` | Send chat message | |
| `!jitsi pm <id>` | Start private chat | |
| `!jitsi cancelpm` | Cancel private chat | |
| `!jitsi notify <title> [desc]` | Show notification | |
| `!jitsi hidenotify <uid>` | Hide notification | |
| `!jitsi tone <tones> [dur] [pause]` | Play touch tones | |

### Recording
| Command | Description | Mod |
|---------|-------------|-----|
| `!jitsi record <local\|file\|stream> [key]` | Start recording | Yes |
| `!jitsi stoprecord <local\|file\|stream>` | Stop recording | Yes |

### Breakout Rooms
| Command | Description | Mod |
|---------|-------------|-----|
| `!jitsi breakout [name]` | Create breakout room | Yes |
| `!jitsi autobreakout` | Auto-assign participants | Yes |
| `!jitsi closebreakout <roomId>` | Close breakout room | Yes |
| `!jitsi joinbreakout [roomId]` | Join breakout room | |
| `!jitsi removebreakout <jid>` | Remove breakout room | Yes |

### Misc
| Command | Description | Mod |
|---------|-------------|-----|
| `!jitsi followme [true\|false]` | Toggle follow me | Yes |
| `!jitsi config <key=value> ...` | Overwrite config | Yes |
| `!jitsi bandwidth <bps>` | Set assumed bandwidth | |
| `!jitsi timer [duration] [elapsed]` | Set meeting timer | |
| `!jitsi resizefilm <width>` | Resize filmstrip | |
| `!jitsi resizelarge <w> <h>` | Resize large video | |
| `!jitsi sendcamera <id> [user\|env]` | Request camera change | |
| `!jitsi sendtext <id> <text>` | Send private text | |

## Configuration

```yaml
service_name: maubot-bot
command_prefix: jitsi

jitsi:
  server_url: https://meet.example.com
  muc_domain: conference.meet.example.com
  admin_username: admin
  admin_password: secret

admin_whitelist:
  - "@admin:example.com"

# Storage (optional)
storage:
  db_path: jitsi-bot.db
  enable_smart_routing: true
```

## Storage

Optional persistence via `evoid-sqlite` and `evoid-smart-storage`:

```bash
pip install evoid-maubot[storage]
```

Data stored:
| Type | Namespace | Content |
|------|-----------|---------|
| `meeting:*` | meetings | Room ID, name, creator, URL |
| `watch:*` | watch_parties | Video URL, content type, creator |
| `mod:*` | moderators | Moderator grants |

Storage is optional — bot works without it but won't persist data across restarts.

## EVOID Integration

Each command maps to a Jitsi iframe API command. The flow:

```
!jitsi watch https://youtube.com/watch?v=abc
    ↓
Matrix Event → Adapter → Intent(name="jitsi:watch", level=STANDARD)
    ↓
Pipeline: validate → authorize
    ↓
Handler returns: {iframe_command: "startShareVideo", args: {url: "..."}}
    ↓
Jitsi executes command in user's browser
```

Moderator commands use `level=CRITICAL` for full pipeline validation.

## Development

```bash
uv venv && uv pip install -e ".[dev]"
ruff check evoid_maubot/
ruff format evoid_maubot/
pytest tests/ -v
```

## License

Apache-2.0
