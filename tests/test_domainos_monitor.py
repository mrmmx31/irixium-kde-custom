# SPDX-License-Identifier: GPL-3.0-or-later
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("domainos_monitor", Path(__file__).resolve().parents[1] / "tools/monitor_domainos.py")
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)


class MonitorTests(unittest.TestCase):
    def setUp(self):
        self.observer = monitor.Responsiveness()
        self.service = {"ok": True}
        self.sample = {"pid": 71, "start": 200, "cpu": 1, "monotonic": 10}
        self.fail = {"ok": False, "timeout": True, "output": ""}
        self.ok = {"ok": True, "timeout": False, "output": monitor.MARKER + "\n"}

    def test_three_timeouts_and_recovery(self):
        statuses = [self.observer.observe(self.service, self.sample, self.fail)["status"] for _ in range(3)]
        self.assertEqual(statuses, ["resposta_inconclusiva", "resposta_inconclusiva", "sem_resposta"])
        recovered = self.observer.observe(self.service, self.sample, self.ok)
        self.assertEqual(recovered["status"], "respondendo")
        self.assertEqual(recovered["consecutive_failures"], 0)

    def test_cpu_saturation_is_not_a_freeze(self):
        self.observer.observe(self.service, self.sample, self.ok)
        result = self.observer.observe(self.service, dict(self.sample, cpu=2, monotonic=11), self.ok)
        self.assertEqual(result["cpu_percent_one_core"], 100)
        self.assertEqual(result["status"], "respondendo")

    def test_pid_reuse_resets_failure_counter(self):
        self.observer.observe(self.service, self.sample, self.fail)
        self.observer.observe(self.service, self.sample, self.fail)
        result = self.observer.observe(self.service, dict(self.sample, start=201), self.fail)
        self.assertEqual(result["consecutive_failures"], 1)

    def test_missing_service_or_probe_is_not_reported_as_freeze(self):
        result = self.observer.observe({"ok": False}, None, {})
        self.assertEqual(result["status"], "monitor_indisponivel")
        result = self.observer.observe(self.service, self.sample, {"unavailable": True})
        self.assertEqual(result["status"], "sonda_indisponivel")

    def test_suspension_and_scheduling_gap_reset_old_failures(self):
        for sample in (dict(self.sample, monotonic=11, boottime=1000),
                       dict(self.sample, monotonic=1000, boottime=1000)):
            observer = monitor.Responsiveness()
            initial = dict(self.sample, boottime=10)
            observer.observe(self.service, initial, self.fail)
            observer.observe(self.service, initial, self.fail)
            result = observer.observe(self.service, sample, self.fail)
            self.assertTrue(result["observation_reset_after_gap"])
            self.assertEqual(result["consecutive_failures"], 1)
            self.assertEqual(result["status"], "resposta_inconclusiva")

    def test_immediate_dbus_error_is_not_called_a_freeze(self):
        error = {"ok": False, "timeout": False, "output": ""}
        for _ in range(5):
            result = self.observer.observe(self.service, self.sample, error)
            self.assertEqual(result["status"], "sonda_indisponivel")
            self.assertEqual(result["consecutive_failures"], 0)

    def test_command_timeout_is_bounded_and_missing_command_is_distinct(self):
        result = monitor.bounded_command(["/usr/bin/python3", "-c", "import time;time.sleep(1)"], 0.03)
        self.assertTrue(result["timeout"])
        self.assertFalse(result["ok"])
        result = monitor.bounded_command(["/no/such/domainos-command"], 0.1)
        self.assertTrue(result["unavailable"])

    def test_report_is_atomic_and_rejects_symlink(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as folder:
            path = Path(folder) / "state.json"
            monitor.write_report(path, {"latest": "respondendo"})
            self.assertEqual(json.loads(path.read_text())["latest"], "respondendo")
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            link = Path(folder) / "link.json"
            link.symlink_to(path)
            with self.assertRaises(ValueError):
                monitor.write_report(link, {})
            self.assertEqual(json.loads(path.read_text())["latest"], "respondendo")


if __name__ == "__main__": unittest.main()
