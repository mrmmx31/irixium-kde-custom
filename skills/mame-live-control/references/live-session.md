# Existing session controls

## Identify and observe

Discover the existing bridge first. Confirm the selected MAME process belongs to
the current user, its executable is MAME, and its current guest/launch arguments
match the task. `pgrep -a -x mame` is a bounded discovery aid, not authentication
of a remembered PID. Do not dump unrelated processes or environment variables.
When the sandbox hides the desktop process, use the environment's authorized
host execution mechanism for those bounded checks.

Run the read-only probe, inspect an up-to-date guest image, and record the live
profile rather than trusting launch arguments. In the source DomainOS SR10.4
session, the approved profile was main CPU 100%, Ethernet CPU 10%, frameskip 4,
throttle off. Preserve that profile when present; it is an observed session
preference, not a universal setting for every MAME guest. This skill does not
change any of these values.

The observed session used `manager.machine.video.frameskip`, `.throttled`,
`manager.machine.paused`, `manager.ui.ui_active`, `machine.ioport.ports`,
`port:read()`, `port:field(mask)`, `field:set_value(value)`, `field:clear_value()`,
`machine.time:as_double()`, `emu.add_machine_frame_notifier()` and notifier
`:unsubscribe()`. Verify availability in another MAME version. In this session,
`manager.machine.ui`, `is_menu_active()`, `get_slider_list()` and
`set_clock_scale()` were not supported. Do not recreate the failed assumptions.

## Serial commands and uncertain outcomes

Use only one controller. The sender stores a unique request ID and result-log
offset, publishes `command.lua` through a same-directory hard link, and waits for
that ID in `result.txt`. Publication never replaces an existing command. The
request remains on timeout, including when the command was already consumed.

```bash
python3 scripts/mame_control.py --channel-dir /path/to/channel status
```

If a correlated late reply appears and no command is still executing, record its
outcome and acknowledge it before proceeding:

```bash
python3 scripts/mame_control.py --channel-dir /path/to/channel status --acknowledge
```

Acknowledgement is a technical cleanup of a known reply, not authorization to
repeat the action. If there is no reply, do not remove the pending request or
reissue the mutation. Confirm process/channel liveness and diagnose the existing
session. An arbitrary Lua loop can still block MAME; submit only bounded code.
Timeout in the host sender cannot interrupt Lua already executing in MAME.

## Mouse and host focus

Read the running capture hook. In the observed Apollo adapter, AltGr releases
host capture and a left click recaptures after its release. F12 activates MAME's
UI mode; it is not the customized release key. Capture-off blocks the guest's
physical input sequences. Preserve original capture/wait state and port sequences.
Do not install a second hook, change SDL options or alter input mapping merely
to obtain control.

Use an authenticated MAME window for host focus. The reference implementation
saved X11 focus and revert mode, set focus only to a window verified against the
actual MAME PID, and restored both in `finally`. A KWin PID lookup worked better
than unverified `xdotool` focus in this KDE session. Keep focus intervention
separate from guest input; never deliver clicks/keys to the previous host window.
The portable helper does not choose a host window or change focus automatically.

`scripts/mame_mouse_control.lua` can be loaded by `dofile()` through the existing
bridge when graphical input is authorized. Loading it only creates functions.
Call `mame_live_mouse.hold()` after an image confirms the actual pointer target:

```lua
return mame_live_mouse.hold({port=button_port, mask=left_button_mask,
    seconds=0.8, confirm_target=true})
```

Tags and masks come from the probe and the device, not a remembered screen
coordinate. The observed Apollo fields were button port `:kbd:mouse1` (left mask
16, middle 64, right 32), and relative counters on `:kbd:mouse2`/`:kbd:mouse3`
(mask 255). These are adapter examples to verify before using, not defaults of
the portable mouse helper.

For a wrapped-counter device, `move_counters()` accepts explicit x/y ports,
masks, modulus, small delta, count and frame interval. Start with one measured
step. Counter values are not pixel coordinates: VUE acceleration and focus alter
the visible displacement. Clearing an override restores the physical accumulator
and can undo apparent displacement; inspect the image before another move.
Do not repeatedly chase a target using guessed absolute positions.

The helper clears its own button/counter overrides on completion, callback
error, explicit `release()` and emulator stop. Inspect
`mame_live_mouse.operation.done`, `.reason`, `.error`, `.cleanup_error` before
more input. Its deadline is **emulated time**, so a paused machine does not tick.
If pending, use the already loaded `release()` through the responsive bridge;
do not send a second input operation. It does not clear another controller's
fields, replace capture hooks or tune performance.

## Images and a bounded receipt

Use the verified screen's `screen:snapshot(output_path)` for native guest pixels.
Pass an explicit writable output path and select the actual screen tag. A legacy
bridge may already refresh `screen.png` periodically; compare mtime with the
command/operation completion to avoid reading a stale image. That guest snapshot
may omit MAME menu overlays. For emulator UI, capture the authenticated host
window instead and label the result as a host capture.

Record normal/held/released states separately. The source SR10.4 Trash Can proof
found an 11-pixel triangle with 2-pixel light/shadow bands, 53 pixels exchanging
light and shadow while held, and exact restoration on release. The empty window
did not prove content scrolling or thumb dragging. Native pixel measurements do
not automatically identify compiled Xt defaults or source-library revision.

At the end, record input released, own callback done, capture/focus restored,
live profile unchanged, emulator unpaused/menu closed as applicable, and channel
consumed. Record failures and unsupported queries; do not erase them on success.

## Guest network access

Prefer an already configured Telnet connection for shell reads and FTP for
configuration files. In the source DomainOS installation, FTP active mode
(`ftplib.FTP.set_pasv(False)`) without TLS was needed; passive mode failed.
This is a compatibility observation for that guest, not a rule for other servers.
Use current session-provided addresses/credentials. Do not store passwords in
this skill, command output or exported evidence. Do not enable access with
`xhost +`, change cookies, or modify a running guest's network to avoid a failed
GUI launch. Verify DISPLAY and X authorization separately.

## No existing bridge

Do not start or restart MAME to repair a missing channel during an attach task.
Report the missing capability and use available guest/network tools meanwhile.
If the user later authorizes a new launch, create a private control directory and
set `MAME_CONTROL_DIR` for that launch. `mame_bridge.lua` is the optional
`-autoboot_script` payload; it only polls `command.lua`, appends `result.txt` and
retains `command.running.lua` if it cannot record an outcome. Keep the user's
existing launch arguments, mouse initialization, storage and performance scripts.
Combine with an existing autoboot script only after inspecting that script;
do not replace it or promise that a restarted guest resumes its unsaved state.

## Validation scope of these portable resources

Run `python3 scripts/test_offline.py` for a temporary synthetic channel and Lua
5.4 interpreter. It exercises real Lua code with mocked MAME services: correlated
results, overlap rejection, unknown/late outcomes, input cleanup and the optional
bridge. It never locates the live channel or sends input to a VM. These tests
validate the portable logic, not mouse displacement, SDL focus, hardware timing
or compatibility with another emulator release. The originating native hold /
release capture and input-hook behavior were observed in MAME 0.276; new versions
and guests still require the bounded read-only observation described above.
