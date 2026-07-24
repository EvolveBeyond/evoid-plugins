"""Jitsi iframe command definitions.

Reference: https://jitsi.github.io/handbook/docs/dev-guide/dev-guide-iframe-commands/

Each command maps a Matrix !jitsi subcommand to a Jitsi iframe API command.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class CommandDef:
    """Definition of a Jitsi command exposed via Matrix."""

    iframe_command: str
    description: str
    usage: str
    category: str
    requires_moderator: bool = False
    arg_parser: Callable[[list[str]], dict[str, Any] | None] | None = None
    response_formatter: Callable[[dict, dict], str] | None = None

    def parse_args(self, args: list[str]) -> dict[str, Any] | None:
        """Parse raw args into structured dict. Returns None if invalid."""
        if self.arg_parser:
            return self.arg_parser(args)
        return {}

    def format_response(self, result: dict, args: dict) -> str:
        """Format EVOID result into human-readable response."""
        if self.response_formatter:
            return self.response_formatter(result, args)
        return f"{self.iframe_command}: {result.get('status', 'done')}"


# ── Argument Parsers ────────────────────────────────────────────────────────

def _parse_required_one(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 1:
        return None
    return {"value": args[0]}


def _parse_optional_one(args: list[str]) -> dict[str, Any]:
    return {"value": args[0] if args else ""}


def _parse_no_args(args: list[str]) -> dict[str, Any]:
    return {}


def _parse_display_name(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 1:
        return None
    return {"displayName": " ".join(args)}


def _parse_password(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 1:
        return None
    return {"password": args[0]}


def _parse_email(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 1:
        return None
    return {"email": args[0]}


def _parse_subject(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 1:
        return None
    return {"subject": " ".join(args)}


def _parse_watch(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 1:
        return None
    return {"url": args[0], "name": args[1] if len(args) > 1 else ""}


def _parse_video_quality(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 1:
        return None
    try:
        return {"height": int(args[0])}
    except ValueError:
        return None


def _parse_mute_everyone(args: list[str]) -> dict[str, Any]:
    media_type = args[0] if args else "audio"
    if media_type not in ("audio", "video"):
        media_type = "audio"
    return {"mediaType": media_type}


def _parse_mute_remote(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 1:
        return None
    media_type = args[1] if len(args) > 1 else "audio"
    return {"participantId": args[0], "mediaType": media_type}


def _parse_kick(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 1:
        return None
    return {"participantId": args[0]}


def _parse_grant_moderator(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 1:
        return None
    return {"participantId": args[0]}


def _parse_send_message(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 1:
        return None
    to = args[1] if len(args) > 1 else ""
    return {"message": args[0], "to": to}


def _parse_pin(args: list[str]) -> dict[str, Any]:
    return {"participantId": args[0] if args else ""}


def _parse_volume(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 2:
        return None
    try:
        vol = float(args[1])
        vol = max(0.0, min(1.0, vol))
        return {"participantId": args[0], "volume": vol}
    except ValueError:
        return None


def _parse_tones(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 1:
        return None
    duration = int(args[1]) if len(args) > 1 else 200
    pause = int(args[2]) if len(args) > 2 else 200
    return {"tones": args[0], "duration": duration, "pause": pause}


def _parse_recording(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 1:
        return None
    mode = args[0]
    if mode not in ("local", "file", "stream"):
        return None
    result: dict[str, Any] = {"mode": mode}
    if mode == "stream" and len(args) > 1:
        result["rtmpStreamKey"] = args[1]
    if mode == "file" and len(args) > 1:
        result["dropboxToken"] = args[1]
    return result


def _parse_stop_recording(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 1:
        return None
    mode = args[0]
    if mode not in ("local", "file", "stream"):
        return None
    return {"mode": mode}


def _parse_breakout_room(args: list[str]) -> dict[str, Any]:
    return {"name": " ".join(args) if args else ""}


def _parse_close_breakout(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 1:
        return None
    return {"roomId": args[0]}


def _parse_join_breakout(args: list[str]) -> dict[str, Any]:
    return {"roomId": args[0] if args else ""}


def _parse_remove_breakout(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 1:
        return None
    return {"breakoutRoomJid": args[0]}


def _parse_send_to_room(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 2:
        return None
    return {"participantId": args[0], "roomId": args[1]}


def _parse_notification(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 1:
        return None
    return {"title": args[0], "description": args[1] if len(args) > 1 else ""}


def _parse_hide_notification(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 1:
        return None
    return {"uid": args[0]}


def _parse_large_video(args: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if args:
        result["participantId"] = args[0]
    if len(args) > 1:
        result["videoType"] = args[1]
    return result


def _parse_overwrite_names(args: list[str]) -> dict[str, Any] | None:
    # Format: id:name [id:name ...]
    if len(args) < 1:
        return None
    names = []
    for pair in args:
        if ":" in pair:
            pid, name = pair.split(":", 1)
            names.append({"id": pid, "name": name})
    return {"names": names}


def _parse_set_follow_me(args: list[str]) -> dict[str, Any]:
    enabled = args[0].lower() in ("true", "1", "on", "yes") if args else True
    recorder_only = args[1].lower() in ("true", "1", "on", "yes") if len(args) > 1 else False
    return {"value": enabled, "recorderOnly": recorder_only}


def _parse_set_subtitles(args: list[str]) -> dict[str, Any]:
    enabled = args[0].lower() in ("true", "1", "on", "yes") if args else True
    language = args[1] if len(args) > 1 else "en"
    return {"enabled": enabled, "language": language}


def _parse_set_tile_view(args: list[str]) -> dict[str, Any]:
    enabled = args[0].lower() in ("true", "1", "on", "yes") if args else True
    return {"enabled": enabled}


def _parse_lobby(args: list[str]) -> dict[str, Any]:
    enabled = args[0].lower() in ("true", "1", "on", "yes") if args else True
    return {"enabled": enabled}


def _parse_answer_knock(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 2:
        return None
    approved = args[1].lower() in ("true", "1", "on", "yes")
    return {"id": args[0], "approved": approved}


def _parse_moderation(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 2:
        return None
    enable = args[0].lower() in ("true", "1", "on", "yes")
    media_type = args[1]
    if media_type not in ("audio", "video"):
        return None
    return {"enable": enable, "mediaType": media_type}


def _parse_ask_unmute(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 1:
        return None
    return {"participantId": args[0]}


def _parse_approve_video(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 1:
        return None
    return {"participantId": args[0]}


def _parse_reject_participant(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 2:
        return None
    media_type = args[1]
    if media_type not in ("audio", "video"):
        media_type = "audio"
    return {"participantId": args[0], "mediaType": media_type}


def _parse_overwrite_config(args: list[str]) -> dict[str, Any] | None:
    # Simple key=value pairs
    if len(args) < 1:
        return None
    config = {}
    for pair in args:
        if "=" in pair:
            k, v = pair.split("=", 1)
            config[k] = v
    return {"config": config}


def _parse_show_notification(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 1:
        return None
    result: dict[str, Any] = {"title": args[0]}
    if len(args) > 1:
        result["description"] = args[1]
    return result


def _parse_bandwidth(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 1:
        return None
    try:
        return {"assumedBandwidthBps": int(args[0])}
    except ValueError:
        return None


def _parse_blur(args: list[str]) -> dict[str, Any]:
    blur_type = args[0] if args else "blur"
    if blur_type not in ("slight-blur", "blur", "none"):
        blur_type = "blur"
    return {"blurType": blur_type}


def _parse_audio_only(args: list[str]) -> dict[str, Any]:
    enabled = args[0].lower() in ("true", "1", "on", "yes") if args else True
    return {"enabled": enabled}


def _parse_virtual_bg(args: list[str]) -> dict[str, Any]:
    enabled = args[0].lower() in ("true", "1", "on", "yes") if args else True
    image = args[1] if len(args) > 1 else ""
    return {"enabled": enabled, "backgroundImage": image}


def _parse_meeting_timer(args: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if args:
        try:
            result["duration"] = int(args[0])
        except ValueError:
            result["duration"] = 0
    if len(args) > 1:
        try:
            result["elapsed"] = int(args[1])
        except ValueError:
            pass
    return result


def _parse_resize_filmstrip(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 1:
        return None
    try:
        return {"width": int(args[0])}
    except ValueError:
        return None


def _parse_resize_large_video(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 2:
        return None
    try:
        return {"width": int(args[0]), "height": int(args[1])}
    except ValueError:
        return None


# ── Response Formatters ─────────────────────────────────────────────────────

def _fmt_created(result: dict, args: dict) -> str:
    url = result.get("meeting_url", "")
    return f"Room created: {url}" if url else "Room created"


def _fmt_watch(result: dict, args: dict) -> str:
    url = result.get("meeting_url", "")
    video = args.get("url", "")
    ctype = result.get("content_type", "video")
    return f"Watch party ({ctype}): {video}\nRoom: {url}"


def _fmt_generic(result: dict, args: dict) -> str:
    cmd = result.get("command", result.get("status", "done"))
    return f"{cmd}: {result.get('status', 'executed')}"


# ── Command Registry ────────────────────────────────────────────────────────

COMMAND_REGISTRY: dict[str, CommandDef] = {
    # ── Room Management ────────────────────────────────────────────────────
    "create": CommandDef(
        iframe_command="",
        description="Create a new meeting room",
        usage="[name]",
        category="Room",
        arg_parser=_parse_optional_one,
        response_formatter=_fmt_created,
    ),
    "join": CommandDef(
        iframe_command="",
        description="Get join link for a room",
        usage="<room_name>",
        category="Room",
        arg_parser=_parse_required_one,
        response_formatter=lambda r, a: f"Join: {r.get('meeting_url', '')}",
    ),
    "watch": CommandDef(
        iframe_command="startShareVideo",
        description="Create watch party with shared video",
        usage="<url> [name]",
        category="Watch Party",
        arg_parser=_parse_watch,
        response_formatter=_fmt_watch,
    ),
    "stopwatch": CommandDef(
        iframe_command="stopShareVideo",
        description="Stop shared video playback",
        usage="",
        category="Watch Party",
        arg_parser=_parse_no_args,
    ),
    "hangup": CommandDef(
        iframe_command="hangup",
        description="End the call",
        usage="",
        category="Room",
        arg_parser=_parse_no_args,
    ),
    "end": CommandDef(
        iframe_command="endConference",
        description="End conference for everyone (mod only)",
        usage="",
        category="Room",
        requires_moderator=True,
        arg_parser=_parse_no_args,
    ),

    # ── Display / Identity ─────────────────────────────────────────────────
    "name": CommandDef(
        iframe_command="displayName",
        description="Set your display name",
        usage="<name>",
        category="Display",
        arg_parser=_parse_display_name,
    ),
    "email": CommandDef(
        iframe_command="email",
        description="Set your email address",
        usage="<email>",
        category="Display",
        arg_parser=_parse_email,
    ),
    "subject": CommandDef(
        iframe_command="subject",
        description="Set conference subject (mod only)",
        usage="<subject>",
        category="Display",
        requires_moderator=True,
        arg_parser=_parse_subject,
    ),
    "localsubject": CommandDef(
        iframe_command="localSubject",
        description="Set local subject",
        usage="<subject>",
        category="Display",
        arg_parser=_parse_subject,
    ),

    # ── Audio / Video ──────────────────────────────────────────────────────
    "mute": CommandDef(
        iframe_command="toggleAudio",
        description="Mute/unmute your audio",
        usage="",
        category="Media",
        arg_parser=_parse_no_args,
    ),
    "video": CommandDef(
        iframe_command="toggleVideo",
        description="Mute/unmute your video",
        usage="",
        category="Media",
        arg_parser=_parse_no_args,
    ),
    "screen": CommandDef(
        iframe_command="toggleShareScreen",
        description="Toggle screen sharing",
        usage="",
        category="Media",
        arg_parser=_parse_no_args,
    ),
    "muteall": CommandDef(
        iframe_command="muteEveryone",
        description="Mute all participants (mod only)",
        usage="[audio|video]",
        category="Media",
        requires_moderator=True,
        arg_parser=_parse_mute_everyone,
    ),
    "muteremote": CommandDef(
        iframe_command="muteRemoteParticipant",
        description="Mute a specific participant (mod only)",
        usage="<participantId> [audio|video]",
        category="Media",
        requires_moderator=True,
        arg_parser=_parse_mute_remote,
    ),
    "noise": CommandDef(
        iframe_command="setNoiseSuppressionEnabled",
        description="Toggle noise suppression",
        usage="[true|false]",
        category="Media",
        arg_parser=lambda a: {"enabled": a[0].lower() in ("true", "1", "on", "yes")} if a else {"enabled": True},
    ),
    "quality": CommandDef(
        iframe_command="setVideoQuality",
        description="Set video quality (height in px)",
        usage="<720|480|360|240>",
        category="Media",
        arg_parser=_parse_video_quality,
    ),
    "audioonly": CommandDef(
        iframe_command="setAudioOnly",
        description="Enable/disable audio only mode",
        usage="[true|false]",
        category="Media",
        arg_parser=_parse_audio_only,
    ),
    "camera": CommandDef(
        iframe_command="toggleCamera",
        description="Toggle camera facing mode",
        usage="[user|environment]",
        category="Media",
        arg_parser=lambda a: {"facingMode": a[0] if a else ""},
    ),
    "mirror": CommandDef(
        iframe_command="toggleCameraMirror",
        description="Toggle camera mirror",
        usage="",
        category="Media",
        arg_parser=_parse_no_args,
    ),
    "vbg": CommandDef(
        iframe_command="toggleVirtualBackgroundDialog",
        description="Toggle virtual background dialog",
        usage="",
        category="Media",
        arg_parser=_parse_no_args,
    ),
    "blur": CommandDef(
        iframe_command="setBlurredBackground",
        description="Set blurred background",
        usage="[slight-blur|blur|none]",
        category="Media",
        arg_parser=_parse_blur,
    ),
    "virtualbg": CommandDef(
        iframe_command="setVirtualBackground",
        description="Set virtual background with image",
        usage="[true|false] [base64_image]",
        category="Media",
        arg_parser=_parse_virtual_bg,
    ),

    # ── Layout / UI ────────────────────────────────────────────────────────
    "tile": CommandDef(
        iframe_command="toggleTileView",
        description="Toggle tile view layout",
        usage="",
        category="Layout",
        arg_parser=_parse_no_args,
    ),
    "settile": CommandDef(
        iframe_command="setTileView",
        description="Enable/disable tile view",
        usage="[true|false]",
        category="Layout",
        arg_parser=_parse_set_tile_view,
    ),
    "filmstrip": CommandDef(
        iframe_command="toggleFilmStrip",
        description="Toggle filmstrip visibility",
        usage="",
        category="Layout",
        arg_parser=_parse_no_args,
    ),
    "chat": CommandDef(
        iframe_command="toggleChat",
        description="Toggle chat panel",
        usage="",
        category="Layout",
        arg_parser=_parse_no_args,
    ),
    "hand": CommandDef(
        iframe_command="toggleRaiseHand",
        description="Toggle raise hand",
        usage="",
        category="Layout",
        arg_parser=_parse_no_args,
    ),
    "subtitles": CommandDef(
        iframe_command="toggleSubtitles",
        description="Toggle subtitles",
        usage="",
        category="Layout",
        arg_parser=_parse_no_args,
    ),
    "setsubtitles": CommandDef(
        iframe_command="setSubtitles",
        description="Enable/disable subtitles with language",
        usage="[true|false] [language]",
        category="Layout",
        arg_parser=_parse_set_subtitles,
    ),
    "participants": CommandDef(
        iframe_command="toggleParticipantsPane",
        description="Toggle participants pane",
        usage="[true|false]",
        category="Layout",
        arg_parser=lambda a: {"enabled": a[0].lower() in ("true", "1", "on", "yes")} if a else {"enabled": True},
    ),
    "whiteboard": CommandDef(
        iframe_command="toggleWhiteboard",
        description="Toggle whiteboard",
        usage="",
        category="Layout",
        arg_parser=_parse_no_args,
    ),
    "lobby": CommandDef(
        iframe_command="toggleLobby",
        description="Toggle lobby mode (mod only)",
        usage="[true|false]",
        category="Layout",
        requires_moderator=True,
        arg_parser=_parse_lobby,
    ),

    # ── Participant Management ──────────────────────────────────────────────
    "kick": CommandDef(
        iframe_command="kickParticipant",
        description="Kick a participant (mod only)",
        usage="<participantId>",
        category="Participants",
        requires_moderator=True,
        arg_parser=_parse_kick,
    ),
    "mod": CommandDef(
        iframe_command="grantModerator",
        description="Grant moderator rights (mod only)",
        usage="<participantId>",
        category="Participants",
        requires_moderator=True,
        arg_parser=_parse_grant_moderator,
    ),
    "pin": CommandDef(
        iframe_command="pinParticipant",
        description="Pin a participant to large video",
        usage="[participantId]",
        category="Participants",
        arg_parser=_parse_pin,
    ),
    "volume": CommandDef(
        iframe_command="setParticipantVolume",
        description="Set participant volume (0-1)",
        usage="<participantId> <0.0-1.0>",
        category="Participants",
        arg_parser=_parse_volume,
    ),
    "largevideo": CommandDef(
        iframe_command="setLargeVideoParticipant",
        description="Set large video participant",
        usage="[participantId] [camera|desktop]",
        category="Participants",
        arg_parser=_parse_large_video,
    ),
    "names": CommandDef(
        iframe_command="overwriteNames",
        description="Overwrite participant names locally",
        usage="<id:name> [id:name ...]",
        category="Participants",
        arg_parser=_parse_overwrite_names,
    ),
    "sendto": CommandDef(
        iframe_command="sendParticipantToRoom",
        description="Send participant to a room (mod only)",
        usage="<participantId> <roomId>",
        category="Participants",
        requires_moderator=True,
        arg_parser=_parse_send_to_room,
    ),

    # ── Moderation ──────────────────────────────────────────────────────────
    "approveknock": CommandDef(
        iframe_command="answerKnockingParticipant",
        description="Approve/reject lobby participant (mod only)",
        usage="<participantId> <true|false>",
        category="Moderation",
        requires_moderator=True,
        arg_parser=_parse_answer_knock,
    ),
    "moderation": CommandDef(
        iframe_command="toggleModeration",
        description="Toggle audio/video moderation (mod only)",
        usage="<true|false> <audio|video>",
        category="Moderation",
        requires_moderator=True,
        arg_parser=_parse_moderation,
    ),
    "askunmute": CommandDef(
        iframe_command="askToUnmute",
        description="Ask participant to unmute (mod only)",
        usage="<participantId>",
        category="Moderation",
        requires_moderator=True,
        arg_parser=_parse_ask_unmute,
    ),
    "approvevideo": CommandDef(
        iframe_command="approveVideo",
        description="Approve participant for video (mod only)",
        usage="<participantId>",
        category="Moderation",
        requires_moderator=True,
        arg_parser=_parse_approve_video,
    ),
    "reject": CommandDef(
        iframe_command="rejectParticipant",
        description="Reject participant from moderation (mod only)",
        usage="<participantId> <audio|video>",
        category="Moderation",
        requires_moderator=True,
        arg_parser=_parse_reject_participant,
    ),

    # ── Chat / Messaging ───────────────────────────────────────────────────
    "send": CommandDef(
        iframe_command="sendChatMessage",
        description="Send chat message",
        usage="<message> [participantId]",
        category="Chat",
        arg_parser=_parse_send_message,
    ),
    "pm": CommandDef(
        iframe_command="initiatePrivateChat",
        description="Start private chat with participant",
        usage="<participantId>",
        category="Chat",
        arg_parser=_parse_required_one,
    ),
    "cancelpm": CommandDef(
        iframe_command="cancelPrivateChat",
        description="Cancel private chat",
        usage="",
        category="Chat",
        arg_parser=_parse_no_args,
    ),
    "notify": CommandDef(
        iframe_command="showNotification",
        description="Show a notification",
        usage="<title> [description]",
        category="Chat",
        arg_parser=_parse_show_notification,
    ),
    "hidenotify": CommandDef(
        iframe_command="hideNotification",
        description="Hide a notification by uid",
        usage="<uid>",
        category="Chat",
        arg_parser=_parse_hide_notification,
    ),
    "tone": CommandDef(
        iframe_command="sendTones",
        description="Play touch tones",
        usage="<tones> [duration] [pause]",
        category="Chat",
        arg_parser=_parse_tones,
    ),

    # ── Recording ──────────────────────────────────────────────────────────
    "record": CommandDef(
        iframe_command="startRecording",
        description="Start recording (local/file/stream)",
        usage="<local|file|stream> [key]",
        category="Recording",
        requires_moderator=True,
        arg_parser=_parse_recording,
    ),
    "stoprecord": CommandDef(
        iframe_command="stopRecording",
        description="Stop recording",
        usage="<local|file|stream>",
        category="Recording",
        requires_moderator=True,
        arg_parser=_parse_stop_recording,
    ),

    # ── Breakout Rooms ─────────────────────────────────────────────────────
    "breakout": CommandDef(
        iframe_command="addBreakoutRoom",
        description="Create breakout room (mod only)",
        usage="[name]",
        category="Breakout",
        requires_moderator=True,
        arg_parser=_parse_breakout_room,
    ),
    "autobreakout": CommandDef(
        iframe_command="autoAssignToBreakoutRooms",
        description="Auto-assign participants to breakout rooms (mod only)",
        usage="",
        category="Breakout",
        requires_moderator=True,
        arg_parser=_parse_no_args,
    ),
    "closebreakout": CommandDef(
        iframe_command="closeBreakoutRoom",
        description="Close breakout room (mod only)",
        usage="<roomId>",
        category="Breakout",
        requires_moderator=True,
        arg_parser=_parse_close_breakout,
    ),
    "joinbreakout": CommandDef(
        iframe_command="joinBreakoutRoom",
        description="Join a breakout room",
        usage="[roomId]",
        category="Breakout",
        arg_parser=_parse_join_breakout,
    ),
    "removebreakout": CommandDef(
        iframe_command="removeBreakoutRoom",
        description="Remove breakout room (mod only)",
        usage="<breakoutRoomJid>",
        category="Breakout",
        requires_moderator=True,
        arg_parser=_parse_remove_breakout,
    ),

    # ── Misc ───────────────────────────────────────────────────────────────
    "followme": CommandDef(
        iframe_command="setFollowMe",
        description="Toggle follow me mode (mod only)",
        usage="[true|false] [recorderOnly]",
        category="Misc",
        requires_moderator=True,
        arg_parser=_parse_set_follow_me,
    ),
    "config": CommandDef(
        iframe_command="overwriteConfig",
        description="Overwrite Jitsi config",
        usage="<key=value> [key=value ...]",
        category="Misc",
        requires_moderator=True,
        arg_parser=_parse_overwrite_config,
    ),
    "bandwidth": CommandDef(
        iframe_command="setAssumedBandwidthBps",
        description="Set assumed bandwidth (bps)",
        usage="<bps>",
        category="Misc",
        arg_parser=_parse_bandwidth,
    ),
    "timer": CommandDef(
        iframe_command="setMeetingTimer",
        description="Set meeting timer",
        usage="[duration_sec] [elapsed_sec]",
        category="Misc",
        arg_parser=_parse_meeting_timer,
    ),
    "resizefilm": CommandDef(
        iframe_command="resizeFilmStrip",
        description="Resize filmstrip width",
        usage="<width>",
        category="Misc",
        arg_parser=_parse_resize_filmstrip,
    ),
    "resizelarge": CommandDef(
        iframe_command="resizeLargeVideo",
        description="Resize large video",
        usage="<width> <height>",
        category="Misc",
        arg_parser=_parse_resize_large_video,
    ),
    "sendcamera": CommandDef(
        iframe_command="sendCameraFacingMode",
        description="Request participant to change camera",
        usage="<participantId> [user|environment]",
        category="Misc",
        arg_parser=lambda a: {"participantId": a[0], "facingMode": a[1] if len(a) > 1 else ""} if len(a) >= 1 else None,
    ),
    "sendtext": CommandDef(
        iframe_command="sendEndpointTextMessage",
        description="Send private text to participant",
        usage="<participantId> <text>",
        category="Misc",
        arg_parser=lambda a: {"participantId": a[0], "text": " ".join(a[1:])} if len(a) >= 2 else None,
    ),
}
