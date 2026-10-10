# SPDX-License-Identifier: GPL-3.0-or-later
"""Command boundary: no shell, no MIME writes, truthful launcher outcomes."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

SOURCE = Path(__file__).resolve().parents[1] / "plasma/applets/org.irixclassic.domainos.panel/contents/code/commands.py"
SPEC = importlib.util.spec_from_file_location("domainos_commands", SOURCE)
commands = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(commands)


class CommandsTest(unittest.TestCase):
    def test_terminal_keeps_metacharacters_as_arguments(self):
        with patch.object(commands.shutil, "which", return_value="/usr/bin/terminal"), \
                patch.object(commands.subprocess, "Popen", return_value=Mock(pid=123)) as start:
            result = commands.execute({"action": "terminal", "terminalCommand": 'terminal "$(touch /tmp/no)" "a;b"'})
        self.assertEqual(start.call_args.args[0], ["terminal", "$(touch /tmp/no)", "a;b"])
        self.assertNotIn("shell", start.call_args.kwargs)
        self.assertEqual(result["outcome"], "process-started")
        self.assertIn("not observed", result["detail"])

    def test_terminal_uses_session_preference_without_changing_it(self):
        with patch.object(commands, "read_setting", return_value="preferred-terminal --new-window") as setting, \
                patch.object(commands, "spawn", return_value={}) as start:
            commands.execute({"action": "terminal"})
        setting.assert_called_once_with("kdeglobals", "General", "TerminalApplication")
        start.assert_called_once_with(["preferred-terminal", "--new-window"])

    def test_mail_uses_default_without_compose_uri(self):
        with patch.object(commands, "default_mail_client", return_value="mail.desktop"), \
                patch.object(commands, "launch_desktop", return_value={}) as start:
            commands.execute({"action": "mail"})
        start.assert_called_once_with("mail.desktop")

    def test_mail_override_is_instance_only(self):
        with patch.object(commands, "default_mail_client") as default, \
                patch.object(commands, "launch_desktop", return_value={}) as start:
            commands.execute({"action": "mail", "mailClient": "thunderbird.desktop"})
        default.assert_not_called()
        start.assert_called_once_with("thunderbird.desktop")

    def test_application_id_rejects_paths_options_and_uri_injection(self):
        for identifier in ("/tmp/mail.desktop", "../mail.desktop", "--exec.desktop", "a.desktop?exec=bad", "a;bad.desktop", "applications:a.desktop"):
            with self.subTest(identifier=identifier), self.assertRaises(ValueError):
                commands.desktop_id(identifier)

    def test_launcher_failure_is_not_completion(self):
        def fail_launcher(*args,**kwargs):
            kwargs["stderr"].write(b"no service")
            return Mock(returncode=1)
        with patch.object(commands, "find_desktop_file", return_value=Path("/tmp/missing.desktop")), \
                patch.object(commands.shutil, "which", return_value="/usr/bin/kioclient"), \
                patch.object(commands.subprocess, "run", side_effect=fail_launcher):
            with self.assertRaisesRegex(RuntimeError, "no service"):
                commands.launch_desktop("missing.desktop")

    def test_launcher_exit_success_reports_request_only(self):
        with patch.object(commands, "find_desktop_file", return_value=Path("/tmp/application.desktop")), \
                patch.object(commands.shutil, "which", return_value="/usr/bin/kioclient"), \
                patch.object(commands.subprocess, "run", return_value=Mock(returncode=0)) as start:
            result = commands.launch_desktop("application.desktop")
        self.assertEqual(start.call_args.args[0], ["/usr/bin/kioclient", "--noninteractive", "exec", "/tmp/application.desktop"])
        self.assertEqual(start.call_args.kwargs["stdin"],commands.subprocess.DEVNULL)
        self.assertEqual(start.call_args.kwargs["stdout"],commands.subprocess.DEVNULL)
        self.assertNotEqual(start.call_args.kwargs["stderr"],commands.subprocess.PIPE)
        self.assertEqual(start.call_args.kwargs["timeout"],20)
        self.assertNotIn("capture_output",start.call_args.kwargs)
        self.assertEqual(result["outcome"], "request-accepted")
        self.assertIn("not observed", result["detail"])

    def test_desktop_ids_resolve_flat_and_nested_xdg_entries(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "applications"
            directory.mkdir()
            (directory / "flat.desktop").touch()
            (directory / "vendor").mkdir()
            (directory / "vendor" / "nested.desktop").touch()
            with patch.object(commands, "application_dirs", return_value=[directory]):
                self.assertEqual(commands.find_desktop_file("flat.desktop"), directory / "flat.desktop")
                self.assertEqual(commands.find_desktop_file("vendor-nested.desktop"), directory / "vendor/nested.desktop")

    def test_missing_valid_desktop_id_fails_before_launcher(self):
        with tempfile.TemporaryDirectory() as temporary, \
                patch.object(commands, "application_dirs", return_value=[Path(temporary)]), \
                patch.object(commands.subprocess, "run") as launcher:
            with self.assertRaisesRegex(RuntimeError, "Application is not installed"):
                commands.launch_desktop("missing-valid.desktop")
        launcher.assert_not_called()

    def test_xman_contrast_falls_back_for_matching_yellow_colors(self):
        argv = commands.xman_colors(dict(background="#dddd28", foreground="#dddd28",
                                        selection="#dddd28", selectionText="#dddd28"))
        self.assertEqual(argv[:4], ["-bg", "#dddd28", "-fg", "#000000"])
        self.assertIn("*Command.foreground: #000000", argv)

    def test_xman_rejects_resource_injection(self):
        with self.assertRaises(ValueError):
            commands.xman_colors(dict(background="#ffffff\n*anything:bad"))

    def test_unknown_command_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown"):
            commands.execute({"action": "arbitrary-shell-command"})


if __name__ == "__main__":
    unittest.main()
