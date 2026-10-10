#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Event-driven Thunderbird native host; only bounded aggregate counts enter.

One persistent user-session D-Bus connection publishes Unity updates. A private
Desktop ID prevents unrelated badge providers from becoming our data source.
No account, mail database, content, settings, subprocess, polling or restart.
"""
import json
import os
import signal
import struct
import sys

sys.dont_write_bytecode = True
SERVICE = "org.irixclassic.DomainOS.Thunderbird"
DESKTOP_ID = "org.irixclassic.domainos.thunderbird.counts.desktop"
MAX_FRAME = 512
MAX_COUNT = 2147483646


def validate(message):
    if not isinstance(message, dict) or set(message) != {"schema", "type", "available", "unreadCount"} \
            or message.get("schema") != 1 or isinstance(message.get("schema"), bool) \
            or message.get("type") != "counts" or type(message.get("available")) is not bool:
        raise ValueError("Invalid aggregate schema")
    count = message["unreadCount"]
    if message["available"]:
        if type(count) is not int or not 0 <= count <= MAX_COUNT:
            raise ValueError("Invalid aggregate count")
    elif count is not None:
        raise ValueError("Unavailable aggregate requires null")
    return message["available"], count


class Framing:
    def __init__(self):
        self.buffer = bytearray()

    def feed(self, chunk):
        self.buffer.extend(chunk)
        messages = []
        while len(self.buffer) >= 4:
            length, = struct.unpack("<I", self.buffer[:4])
            if not 0 < length <= MAX_FRAME:
                raise ValueError("Invalid native frame size")
            if len(self.buffer) < length + 4:
                break
            raw = bytes(self.buffer[4:4 + length])
            del self.buffer[:4 + length]
            messages.append(validate(json.loads(raw.decode("utf-8"))))
        if len(self.buffer) > MAX_FRAME + 4:
            raise ValueError("Oversized partial native frame")
        return messages


def respond(message):
    raw = json.dumps(message, separators=(",", ":")).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("<I", len(raw)) + raw)
    sys.stdout.buffer.flush()


def main():
    from PyQt6.QtCore import QCoreApplication, QSocketNotifier
    from PyQt6.QtDBus import QDBusConnection, QDBusMessage
    app = QCoreApplication(sys.argv)
    bus = QDBusConnection.sessionBus()
    if not bus.isConnected():
        respond({"ok": False, "code": "session-bus-unavailable"}); return 1
    if bus.interface().isServiceRegistered(SERVICE).value():
        # A second profile must not clear the first profile's live source.
        respond({"ok": False, "code": "source-already-connected"}); return 1

    def publish(available, count):
        message = QDBusMessage.createSignal("/org/irixclassic/DomainOS/Thunderbird",
            "com.canonical.Unity.LauncherEntry", "Update")
        message.setArguments(["application://" + DESKTOP_ID,
            {"count": count if available else 0, "count-visible": available}])
        return bus.send(message)

    # KDE 6.3.6 does not wire its Unity sender-loss watcher. Clear any old entry
    # before announcing this new source; our QML also watches SERVICE itself.
    if not publish(False, None) or not bus.registerService(SERVICE):
        respond({"ok": False, "code": "source-registration-failed"}); return 1
    parser = Framing()
    os.set_blocking(sys.stdin.fileno(), False)
    notifier = QSocketNotifier(sys.stdin.fileno(), QSocketNotifier.Type.Read)
    exit_code = [0]

    def stop(code=0):
        notifier.setEnabled(False)
        exit_code[0] = code
        app.quit()

    def read_available(*_):
        try:
            chunk = os.read(sys.stdin.fileno(), 4096)
            if not chunk:
                if parser.buffer:
                    raise ValueError("Truncated native frame")
                stop(); return
            for available, count in parser.feed(chunk):
                if not publish(available, count):
                    raise RuntimeError("Could not publish aggregate")
                respond({"ok": True, "available": available,
                    "unreadCount": count if available else None})
        except BlockingIOError:
            pass
        except (ValueError, UnicodeError, OSError, RuntimeError):
            # Never print payloads or exception details to stderr/protocol.
            try: respond({"ok": False, "code": "aggregate-unavailable"})
            except (OSError, BrokenPipeError): pass
            stop(1)

    notifier.activated.connect(read_available)
    signal.signal(signal.SIGTERM, lambda *_: stop())
    signal.signal(signal.SIGINT, lambda *_: stop())
    try:
        app.exec()
    finally:
        publish(False, None)
        # Synchronous name release also sends queued messages before the owner
        # disappears. The panel still marks source unavailable after SIGKILL.
        bus.unregisterService(SERVICE)
    return exit_code[0]


if __name__ == "__main__":
    sys.exit(main())
