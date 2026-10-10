#!/usr/bin/env python3
"""Serialize commands to an existing MAME command.lua/result.txt bridge."""
from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import time
import uuid

MARKER = "MAME_LIVE_REPLY:"
MAX_COMMAND = 1024 * 1024
MAX_RESULT = 8 * 1024 * 1024
PENDING = ".mame-live-pending.json"


class ChannelError(RuntimeError):
    pass


class RequestTimeout(ChannelError):
    pass


def lua_string(value: str) -> str:
    # Lua decimal byte escapes preserve UTF-8, quotes and literal newlines.
    return '"' + "".join(f"\\{byte:03d}" for byte in value.encode("utf-8")) + '"'


def packet(code: str, request_id: str) -> str:
    return f'''local request_id={lua_string(request_id)}
local function hex(value)
 return (tostring(value):gsub('.',function(c)return string.format('%02x',string.byte(c))end))
end
local fn,load_error=load({lua_string(code)},'mame-live-control','t',_G)
local ok,value=false,load_error
if fn then ok,value=pcall(fn) end
return '{MARKER}'..request_id..':'..(ok and 'OK' or 'ERR')..':'..hex(value)
'''


def secure_file(path: Path, flags: int) -> int:
    fd = os.open(path, flags | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
        os.close(fd)
        raise ChannelError(f"Not an owned regular file: {path}")
    return fd


def read_owned(path: Path, maximum: int) -> bytes:
    fd = secure_file(path, os.O_RDONLY)
    try:
        if os.fstat(fd).st_size > maximum:
            raise ChannelError(f"File exceeds the read limit: {path}")
        with os.fdopen(fd, "rb", closefd=False) as handle:
            return handle.read(maximum + 1)
    finally:
        os.close(fd)


def publish_exclusive(path: Path, data: bytes) -> None:
    fd, temporary = tempfile.mkstemp(prefix=".mame-live-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        # Same-directory hard link publishes the complete inode without replacing
        # a command that an older, noncooperating controller just created.
        os.link(temporary, path, follow_symlinks=False)
    finally:
        os.unlink(temporary)


def discover(explicit: str | None, pointer: str | None) -> Path:
    if explicit:
        base = Path(explicit).expanduser()
    elif pointer:
        base = Path(read_owned(Path(pointer).expanduser(), 4096).decode().strip())
    elif os.environ.get("MAME_CONTROL_DIR"):
        base = Path(os.environ["MAME_CONTROL_DIR"]).expanduser()
    else:
        configured = os.environ.get("MAME_CONTROL_PATH_FILE")
        pointers = [Path(configured)] if configured else [
            Path("/tmp/mame-control-path"), Path("/tmp/domainos-control-path")]
        choices = {Path(read_owned(p, 4096).decode().strip()).resolve()
                   for p in pointers if p.exists()}
        if len(choices) != 1:
            raise ChannelError("No unique existing channel; use --channel-dir or --pointer-file")
        base = choices.pop()
    if not base.is_absolute():
        raise ChannelError("The control directory must be absolute")
    base = base.resolve(strict=True)
    info = base.stat()
    if not base.is_dir() or info.st_uid != os.getuid() or info.st_mode & 0o022:
        raise ChannelError("The channel must be an owned directory, not writable by others")
    return base


class Channel:
    def __init__(self, base: Path):
        self.base = base
        self.lock_fd = None

    def __enter__(self):
        self.lock_fd = secure_file(self.base / ".mame-live.lock", os.O_RDWR | os.O_CREAT)
        try:
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(self.lock_fd)
            self.lock_fd = None
            raise ChannelError("Another controller owns this channel") from None
        return self

    def __exit__(self, *args):
        fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
        os.close(self.lock_fd)

    def pending(self):
        path = self.base / PENDING
        if not path.exists():
            return None
        record = json.loads(read_owned(path, 16384))
        if not re.fullmatch(r"[a-f0-9]{32}", record.get("request_id", "")):
            raise ChannelError("Invalid pending request; inspect it without deleting it")
        if not isinstance(record.get("result_offset"), int) or record["result_offset"] < 0:
            raise ChannelError("Invalid pending result offset")
        return record

    def reply(self, record):
        path = self.base / "result.txt"
        if not path.exists():
            return None
        fd = secure_file(path, os.O_RDONLY)
        try:
            size = os.fstat(fd).st_size
            if size < record["result_offset"]:
                raise ChannelError("Result log was truncated; outcome remains unknown")
            if size - record["result_offset"] > MAX_RESULT:
                raise ChannelError("Result read limit exceeded; inspect the channel")
            with os.fdopen(fd, "rb", closefd=False) as handle:
                handle.seek(record["result_offset"])
                data = handle.read(MAX_RESULT + 1).decode("utf-8", "replace")
        finally:
            os.close(fd)
        match = re.search(re.escape(MARKER + record["request_id"])
                          + r":(OK|ERR):([0-9a-f]*)\r?\n", data)
        if not match:
            return None
        try:
            value = bytes.fromhex(match[2]).decode("utf-8", "replace")
        except ValueError:
            raise ChannelError("Malformed correlated reply") from None
        return {"request_id": record["request_id"], "status": match[1], "value": value}

    def status(self, acknowledge=False):
        record = self.pending()
        reply = self.reply(record) if record else None
        files = [name for name in ("command.lua", "command.running.lua")
                 if (self.base / name).exists()]
        if acknowledge:
            if not record or reply is None or files:
                raise ChannelError("Cannot acknowledge an unknown outcome or pending execution")
            (self.base / PENDING).unlink()
        return {"channel": str(self.base), "pending": record, "reply": reply,
                "pending_files": files, "acknowledged": bool(acknowledge)}

    def call(self, code: str, timeout=15.0):
        if not 0.05 <= timeout <= 60:
            raise ChannelError("Timeout must be between 0.05 and 60 seconds")
        if len(code.encode()) > MAX_COMMAND:
            raise ChannelError("Command exceeds 1 MiB")
        if self.pending():
            raise ChannelError("An earlier outcome needs inspection: run status; do not resend")
        if any((self.base / name).exists() for name in ("command.lua", "command.running.lua")):
            raise ChannelError("Previous command still pending; nothing was written")
        result = self.base / "result.txt"
        offset = 0
        if result.exists():
            fd = secure_file(result, os.O_RDONLY)
            offset = os.fstat(fd).st_size
            os.close(fd)
        record = {"request_id": uuid.uuid4().hex, "result_offset": offset,
                  "submitted_at_unix": time.time()}
        wire = packet(code, record["request_id"]).encode()
        if len(wire) > MAX_COMMAND:
            raise ChannelError("Encoded command exceeds the bridge's 1 MiB limit")
        publish_exclusive(self.base / PENDING, json.dumps(record).encode())
        try:
            publish_exclusive(self.base / "command.lua", wire)
        except Exception:
            (self.base / PENDING).unlink()
            raise
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            response = self.reply(record)
            if response is not None:
                (self.base / PENDING).unlink()
                return response
            time.sleep(min(0.05, max(0, deadline - time.monotonic())))
        raise RequestTimeout("No correlated reply: request retained; inspect status, do not retry")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    route = parser.add_mutually_exclusive_group()
    route.add_argument("--channel-dir")
    route.add_argument("--pointer-file")
    parser.add_argument("--timeout", type=float, default=15)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("probe", help="Read live profile and available controls without input")
    status = commands.add_parser("status", help="Inspect a pending request without sending Lua")
    status.add_argument("--acknowledge", action="store_true", help="Clear only a correlated completed request")
    execute = commands.add_parser("lua")
    source = execute.add_mutually_exclusive_group(required=True)
    source.add_argument("--code")
    source.add_argument("--file", type=Path)
    args = parser.parse_args(argv)
    try:
        base = discover(args.channel_dir, args.pointer_file)
        with Channel(base) as channel:
            if args.command == "status":
                response = channel.status(args.acknowledge)
            else:
                if args.command == "probe":
                    code = Path(__file__).with_name("readonly_probe.lua").read_text()
                else:
                    code = args.file.read_text() if args.file else args.code
                response = channel.call(code, args.timeout)
        print(json.dumps(response, ensure_ascii=False, indent=2))
        return 1 if response.get("status") == "ERR" else 0
    except (ChannelError, OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 3 if isinstance(error, RequestTimeout) else 2


if __name__ == "__main__":
    raise SystemExit(main())
