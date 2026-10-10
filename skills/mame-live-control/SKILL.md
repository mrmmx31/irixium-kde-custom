---
name: mame-live-control
description: Inspect and control an already running MAME session through its Lua file bridge, with correlated replies and bounded input cleanup. Use for guest interface observations and native design comparisons; preserve the existing emulator and guest state.
---

Attach to the existing session. Identify its process, control directory and guest
before sending input. This skill does not authorize restarting MAME, creating a
second instance, changing its performance profile or editing guest files.

Use `scripts/mame_control.py`: it publishes one complete command atomically,
waits for a unique reply and retains an unresolved request after timeout. Never
overwrite a pending command, reuse an old result or retry an uncertain mutation.
Use `status` to inspect late replies. Legacy `command.lua`/`result.txt` bridges
are supported; all controllers must respect the shared pending file. The lock
serializes this helper, but cannot stop an unrelated script that ignores it.

```bash
python3 scripts/mame_control.py --channel-dir /path/to/existing-channel probe
python3 scripts/mame_control.py --pointer-file /path/to/channel-pointer status
python3 scripts/mame_control.py --channel-dir /path/to/existing-channel lua --file /path/to/read-only-query.lua
```

Paths above are examples to replace, not installed locations. With no explicit
path, discovery checks `MAME_CONTROL_DIR`, `MAME_CONTROL_PATH_FILE`, then the
generic and legacy pointers in `/tmp`; conflicting pointers require an explicit
choice. A probe reads the video profile, capture state, available screens and
input ports. It does not move the mouse or adjust performance.

Before graphical input, read [references/live-session.md](references/live-session.md).
It describes authenticated host focus, the observed Apollo mouse counters,
hold/release cleanup, native captures and boundaries between guest and host.
Require a current native image that confirms the pointer is over the intended
target before pressing. Keep only one owner of graphical input. A queued input
callback has its own completion state; a command reply only proves it was queued.

For mouse capture controls, preserve the running hook instead of replacing it.
`scripts/mame_mouse_capture.lua` is a parameterized copy of the observed AltGr
release/left-click recapture mechanism for a session that lacks it. Loading it
changes input routing, so first verify that this is within the requested task.
Do not load it over an existing hook.

Record the reference system/version, configured resources, measured pixels and
observed states separately. Compare normal, held and released controls at native
scale. Save a short receipt with remaining limits; a successful input or integrity
test does not prove visual fidelity or content scrolling in an empty window.

If no Lua bridge exists, read the last section of the reference. The bundled
`scripts/mame_bridge.lua` is an optional bridge for a future authorized launch;
do not restart the current session to install it. Prefer an existing Telnet/FTP
connection for shell commands and file reads when available. Receive credentials
from the actual session; never copy them into this skill or public artifacts.
