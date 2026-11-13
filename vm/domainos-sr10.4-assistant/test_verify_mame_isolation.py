import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from verify_mame_isolation import (VerificationError, _read_instance,
                                   discover_instances, validate_instances)


def row(pid, disk, namespace, channel):
    return {"pid": pid, "disk_identity": disk, "network_namespace": namespace,
            "control_directory": channel}


class IsolationTests(unittest.TestCase):
    def test_separate_disks_networks_and_channels_are_allowed(self):
        rows = [row(10, (1, 100), "net:[1000]", "/vm/a/control"),
                row(20, (1, 200), "net:[2000]", "/vm/b/control")]
        self.assertEqual(validate_instances(rows), rows)

    def test_shared_disk_blocks(self):
        with self.assertRaisesRegex(VerificationError, "disk_identity"):
            validate_instances([row(10, (1, 100), "net:[1000]", "/vm/a/control"),
                                row(20, (1, 100), "net:[2000]", "/vm/b/control")])

    def test_shared_network_namespace_blocks(self):
        with self.assertRaisesRegex(VerificationError, "network_namespace"):
            validate_instances([row(10, (1, 100), "net:[1000]", "/vm/a/control"),
                                row(20, (1, 200), "net:[1000]", "/vm/b/control")])

    def test_shared_control_channel_blocks(self):
        with self.assertRaisesRegex(VerificationError, "control_directory"):
            validate_instances([row(10, (1, 100), "net:[1000]", "/vm/a/control"),
                                row(20, (1, 200), "net:[2000]", "/vm/a/control")])

    def test_missing_identity_fails_closed(self):
        with self.assertRaisesRegex(VerificationError, "sem identidade"):
            validate_instances([row(10, (1, 100), "net:[1000]", "")])

    def _fake_proc(self, base, disk_arg=None, fd_target=None):
        pid = base / "123"
        (pid / "fd").mkdir(parents=True)
        (pid / "comm").write_text("mame\n")
        (pid / "stat").write_text("123 (mame) S " + " ".join(str(n) for n in range(4, 23)) + "\n")
        (pid / "status").write_text(f"Name:\tmame\nUid:\t{os.getuid()}\t{os.getuid()}\t{os.getuid()}\t{os.getuid()}\n")
        disk_arg = str(disk_arg)
        (pid / "cmdline").write_bytes(b"/usr/games/mame\0-disk1\0" + os.fsencode(disk_arg) + b"\0")
        (pid / "environ").write_bytes(b"MAME_CONTROL_DIR=" + os.fsencode(str(base / "control")) + b"\0")
        (pid / "ns").mkdir()
        (pid / "ns/net").symlink_to("net:[12345]")
        (base / "control").mkdir()
        if fd_target:
            (pid / "fd/17").symlink_to(fd_target)
        return 123, pid

    def test_live_mame_disk_inode_is_confirmed_through_open_fd(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            disk = base / "guest.awd"
            disk.write_bytes(b"disk")
            proc = base / "proc"
            pid, _ = self._fake_proc(proc, disk, disk)
            instance = _read_instance(pid, proc)
            self.assertEqual(instance["disk_identity"], (disk.stat().st_dev, disk.stat().st_ino))
            self.assertEqual(instance["open_disk_fds"], ("17",))

    def test_mismatched_open_disk_inode_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            disk = base / "guest.awd"
            other = base / "other.awd"
            disk.write_bytes(b"disk")
            other.write_bytes(b"other")
            proc = base / "proc"
            pid, _ = self._fake_proc(proc, disk, other)
            with self.assertRaisesRegex(VerificationError, "inode do caminho"):
                _read_instance(pid, proc)

    def test_mame_that_disappears_during_inventory_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            disk = base / "guest.awd"
            disk.write_bytes(b"disk")
            proc = base / "proc"
            self._fake_proc(proc, disk, disk)
            with mock.patch("verify_mame_isolation._read_instance",
                            side_effect=FileNotFoundError("vanished")):
                with self.assertRaisesRegex(VerificationError, "desapareceu"):
                    discover_instances(proc)

    def test_changed_pid_start_time_fails_closed(self):
        instance = row(123, (1, 100), "net:[1000]", "/vm/a/control")
        with mock.patch("verify_mame_isolation._mame_snapshot",
                        side_effect=({"123": "1"}, {"123": "2"})), \
                mock.patch("verify_mame_isolation._read_instance", return_value=instance), \
                mock.patch("verify_mame_isolation._start_time", return_value="2"):
            with self.assertRaisesRegex(VerificationError, "reutilizado"):
                discover_instances("/unused")


if __name__ == "__main__":
    unittest.main()
