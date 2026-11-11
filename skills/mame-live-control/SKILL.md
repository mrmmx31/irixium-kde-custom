---
name: mame-live-control
description: Inspect and control an already running MAME session through its Lua file bridge, with correlated replies and bounded input cleanup. Use for guest interface observations and native design comparisons; preserve the existing emulator and guest state.
---

Attach to the existing session. Identify its process, control directory and guest
before sending input. This skill does not authorize restarting MAME, creating a
second instance, changing its performance profile or editing guest files.

For this repository's historical DomainOS work, the only authorized reference
is the project-owned Domain/OS SR10.4 + HP VUE 2.01 assistant clone. Read
[`references/domainos-sr104.md`](references/domainos-sr104.md) and
[`../../docs/DOMAINOS-REGRAS-VM.md`](../../docs/DOMAINOS-REGRAS-VM.md) before
using it. Never substitute the user's original VM, another project's VM, or a
different DomainOS release. A request to use this VM is not by itself permission
to alter its guest, network, saved profile, or disk.

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
target before ordinary graphical input. Exception: if the verified guest is
Domain/OS and its screen is black from idle, first verify MAME process, canonical
disk, VM identity and control channel, then send one guest keypress to wake it;
the black image is the wake condition, not a reason to ask the user or stop.
Verify the returned image before any further input. Keep only one owner of
graphical input. A queued input callback has its own completion state; a command
reply only proves it was queued.

For mouse capture controls, preserve the running hook instead of replacing it.
`scripts/mame_mouse_capture.lua` is a parameterized copy of the observed AltGr
release/left-click recapture mechanism for a session that lacks it. Loading it
changes input routing, so first verify that this is within the requested task.
Do not load it over an existing hook.

## Temporary handoff to the user

Keep MAME headless or on a private display by default. If no viable headless
path remains and the user can help by inspecting or operating the guest, tell
them before temporarily exposing the current VM window because it takes desktop
focus. Preserve and verify the session's existing AltGr mouse-capture release
hook. It does not change keyboard focus; the user returns keyboard focus to the
host with the desktop's normal window-switch shortcut. Do not send keyboard or
mouse events while the user owns input; explain how to return control and wait for their explicit
handback before resuming. If the user reports being stuck, stop VM input and
help restore host control, then use this conditional handoff if the headless
problem still has no viable solution. Do not create/restart a VM or risk guest
state merely to show a window without first explaining that requirement. This
does not authorize changing another VM or replacing the project's launcher,
disk, namespace, or coordination rules.

Record the reference system/version, configured resources, measured pixels and
observed states separately. Compare normal, held and released controls at native
scale. Save a short receipt with remaining limits; a successful input or integrity
test does not prove visual fidelity or content scrolling in an empty window.

If no Lua bridge exists, read the last section of the reference. The bundled
`scripts/mame_bridge.lua` is an optional bridge for a future authorized launch;
do not restart the current session to install it. Prefer an existing Telnet/FTP
connection for shell commands and file reads when available. Receive credentials
from the actual session; never copy them into this skill or public artifacts.
