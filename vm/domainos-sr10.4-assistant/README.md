# Domain/OS SR10.4 assistant VM

This is the project's primary historical reference machine. Read
[`../../docs/DOMAINOS-REGRAS-VM.md`](../../docs/DOMAINOS-REGRAS-VM.md) before
using it. Its live runtime is in `runtime/`; disk and mutable session data are
intentionally excluded from Git. `private/` holds a second hard-link name for
the disk, not a backup. The versioned manifest records ownership, settings,
network isolation and recovery boundaries.

The former Tempia path remains as a symlink for compatibility. A fresh Git clone
does not contain the VM disk or session data; preserve this machine's local
`runtime/` directory independently of Git operations.

Run `./verify.sh` before starting work after a host reboot. It checks that the
runtime and repository hard-link paths identify the same disk, then inventories
all MAME processes. Coexistence is allowed only when each process has one
explicit `-disk1` whose device/inode is confirmed by an open descriptor, a
distinct network namespace, and a distinct existing `MAME_CONTROL_DIR`. Missing
or changing identity data fails closed. This preflight is not an atomic lock;
announce each instance and recheck PID/disk/channel immediately before input.
