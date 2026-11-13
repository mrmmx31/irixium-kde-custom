# SPDX-License-Identifier: GPL-3.0-or-later
"""A safe profile cannot turn a failed native startup into a passing result."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

PATH=Path(__file__).resolve().parents[1]/"tools/testar-domainos-iconbox-nativa.py"
SPEC=importlib.util.spec_from_file_location("domainos_iconbox_native_runner",PATH)
RUNNER=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class NativeReceiptTests(unittest.TestCase):
    def report(self,*,receipt=None,returncode=0):
        with tempfile.TemporaryDirectory(prefix="domainos-native-receipt-") as folder:
            output=Path(folder)
            (output/"runner.log").write_text("private worker startup failed\n")
            if receipt is not None:
                (output/"NATIVO.json").write_text(json.dumps(receipt))
            return RUNNER.finalize_report(output,returncode,{"kdeglobals":"unchanged"},{"kdeglobals":"unchanged"})

    def completed_receipt(self):
        return {"status":"passed","checks":{"native_host_exited":True},
                "state":{"checks":{"native_scenario_completed":True}}}

    def test_missing_native_receipt_fails_despite_unchanged_profile(self):
        report=self.report(returncode=1)
        self.assertEqual(report["status"],"failed")
        self.assertFalse(report["checks"]["native_worker_report_available"])
        self.assertTrue(report["checks"]["real_profiles_unchanged"])

    def test_nonzero_runner_exit_fails_despite_completed_receipt(self):
        report=self.report(receipt=self.completed_receipt(),returncode=2)
        self.assertEqual(report["status"],"failed")
        self.assertFalse(report["checks"]["native_runner_exited_zero"])

    def test_receipt_without_native_scenario_fails(self):
        self.assertEqual(self.report(receipt={"status":"failed","checks":{}})["status"],"failed")

    def test_failed_native_check_is_preserved(self):
        receipt=self.completed_receipt()
        receipt["checks"]["native_host_exited"]=False
        self.assertEqual(self.report(receipt=receipt)["status"],"failed")

    def test_completed_native_scenario_with_zero_exit_passes(self):
        self.assertEqual(self.report(receipt=self.completed_receipt())["status"],"passed")


if __name__=="__main__":unittest.main()
