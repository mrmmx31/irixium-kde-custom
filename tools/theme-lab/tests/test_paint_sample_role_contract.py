#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Static contract for independent manual-paint target/reference jobs.

The native helpers are asynchronous.  This test deliberately checks the
controller/view routing seams that keep a late target result out of the
reference panel (and vice versa) without starting a display or a toolkit.
"""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTROLLER = (ROOT / "src/controller.c").read_text(encoding="utf-8")
VIEW = (ROOT / "src/view.c").read_text(encoding="utf-8")


def function_body(source: str, signature: str) -> str:
    """Return one C function body using balanced braces."""
    start = source.index(signature)
    opening = source.index("{", start)
    depth = 0
    for offset in range(opening, len(source)):
        if source[offset] == "{":
            depth += 1
        elif source[offset] == "}":
            depth -= 1
            if depth == 0:
                return source[opening + 1:offset]
    raise AssertionError(f"unterminated function: {signature}")


class PaintSampleRoleContract(unittest.TestCase):
    def test_controller_owns_distinct_job_and_request_per_role(self):
        enum = re.search(r"typedef enum\s*\{(?P<body>.*?)\}\s*JobKind;",
                         CONTROLLER, re.S)
        self.assertIsNotNone(enum)
        kinds = enum.group("body")
        self.assertIn("JOB_PAINT_SAMPLE", kinds)
        self.assertIn("JOB_PAINT_REFERENCE_SAMPLE", kinds)

        controller = re.search(r"typedef struct\s*\{(?P<body>.*?)\}\s*Controller;",
                               CONTROLLER, re.S)
        self.assertIsNotNone(controller)
        fields = controller.group("body")
        self.assertIn("paint_sample_request", fields)
        self.assertIn("paint_reference_request", fields)

        selector = function_body(CONTROLLER, "paint_request_for(")
        self.assertIn("JOB_PAINT_REFERENCE_SAMPLE", selector)
        self.assertIn("&c->paint_reference_request", selector)
        self.assertIn("&c->paint_sample_request", selector)

    def test_dispatch_cancels_and_updates_only_requested_role(self):
        dispatch = function_body(CONTROLLER, "static void dispatch(")
        case_start = dispatch.index("case TL_PAINT_SAMPLE:")
        case_end = dispatch.index("case TL_SELECT_FAMILY:", case_start)
        paint_case = dispatch[case_start:case_end]

        self.assertIn("TL_PAINT_REFERENCE_SAMPLE", paint_case)
        self.assertIn("JOB_PAINT_REFERENCE_SAMPLE:JOB_PAINT_SAMPLE", paint_case)
        self.assertIn("stop_kind(c,kind)", paint_case)
        self.assertNotIn("stop_kind(c,JOB_PAINT_SAMPLE)", paint_case)
        self.assertNotIn("stop_kind(c,JOB_PAINT_REFERENCE_SAMPLE)", paint_case)
        self.assertIn("c->paint_reference_request=request", paint_case)
        self.assertIn("c->paint_sample_request=request", paint_case)
        self.assertIn("start_job(c,kind", paint_case)

    def test_job_keeps_request_snapshot_and_finish_checks_same_role(self):
        start = function_body(CONTROLLER, "static int start_job(")
        self.assertIn("sample_request=*paint_request_for(c,kind)",
                      re.sub(r"\s+", "", start))

        finish = function_body(CONTROLLER, "static void finish_job(")
        normalized = re.sub(r"\s+", "", finish)
        self.assertIn("current=paint_request_for(c,j->kind)", normalized)
        self.assertIn("memcmp(&j->sample_request,current,sizeof(j->sample_request))",
                      normalized)
        self.assertIn("j->kind==JOB_PAINT_REFERENCE_SAMPLE?"
                      "tl_view_manual_paint_reference_png", normalized)
        self.assertIn(":tl_view_manual_paint_native_png", normalized)

    def test_view_exposes_independent_current_requests_and_sinks(self):
        target_current = function_body(
            VIEW, "int tl_view_manual_paint_sample_current(")
        reference_current = function_body(
            VIEW, "int tl_view_manual_paint_reference_current(")
        self.assertIn("paint_request", target_current)
        self.assertNotIn("paint_reference_request", target_current)
        self.assertIn("paint_reference_request", reference_current)

        target_sink = function_body(
            VIEW, "int tl_view_manual_paint_native_png(")
        reference_sink = function_body(
            VIEW, "int tl_view_manual_paint_reference_png(")
        self.assertIn("paint_context_valid", target_sink)
        self.assertIn("paint_native_samples", target_sink)
        self.assertNotIn("paint_reference_sample", target_sink)
        self.assertIn("paint_reference_request_valid", reference_sink)
        self.assertIn("paint_reference_sample", reference_sink)
        self.assertNotIn("paint_native_samples", reference_sink)


if __name__ == "__main__":
    unittest.main()
