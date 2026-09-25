"""Deterministic tests of the opt-in VNMD tool, not of literary quality."""
from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import random
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from vnmd import Contract, Program, Runner, VNError, expression, evaluate, sample, main, load_json  # noqa: E402


def contract(defaults=None, **extra):
    return {"format": "vnmd-0.1", "entry": "START", "defaults": defaults or {}, **extra}


def program(text, defaults=None, **extra):
    return Program.parse(text, contract(defaults, **extra))


class ParserTests(unittest.TestCase):
    def test_simple_path(self):
        p = program("author preamble\n::scene START\n正文\n::ending DONE\n不应显示")
        r = Runner(p).run()
        self.assertEqual(r.transcript(), "正文\n")
        self.assertEqual(r.ending, "DONE")

    def test_nested_if_and_elif(self):
        p = program('''::scene START
::if x == "a"
甲
::elif x == "b"
::if ready
乙
::else
丙
::endif
::else
丁
::endif
::ending DONE''', {"x": "b", "ready": True})
        self.assertEqual(Runner(p).run().transcript(), "乙\n")

    def test_only_chosen_branch_assigns(self):
        p = program('''::scene START
::choice C
::option a | 甲
::set value = "a"
::option b | 乙
::set value = "b"
::endchoice
::ending DONE''', {"value": "none"})
        r = Runner(p, {"C": "a"}).run()
        self.assertEqual(r.state["value"], "a")
        self.assertNotIn("【乙】", r.transcript())

    def test_nested_goto_escapes_both_blocks(self):
        p = program('''::scene START
::choice C
::option a | 走
::if true
::goto END
这句不能读
::endif
这句也不能读
::endchoice
末尾不能读
::ending BAD
::scene END
真正结尾
::ending GOOD''')
        r = Runner(p).run()
        self.assertEqual(r.ending, "GOOD")
        self.assertNotIn("不能读", r.transcript())

    def test_duplicate_scene(self):
        with self.assertRaisesRegex(VNError, "duplicate scene"):
            program("::scene START\n::ending D\n::scene START\n::ending E")

    def test_duplicate_choice(self):
        with self.assertRaisesRegex(VNError, "duplicate choice"):
            program("::scene START\n::choice C\n::option a | a\n::endchoice\n::choice C\n::option b | b\n::endchoice\n::ending E")

    def test_duplicate_option(self):
        with self.assertRaisesRegex(VNError, "duplicate option"):
            program("::scene START\n::choice C\n::option a | a\n::option a | a\n::endchoice\n::ending E")

    def test_missing_goto(self):
        with self.assertRaisesRegex(VNError, "missing goto"):
            program("::scene START\n::goto MISSING")

    def test_unclosed_if(self):
        with self.assertRaisesRegex(VNError, "endif"):
            program("::scene START\n::if true\n正文\n::ending D")

    def test_unclosed_choice(self):
        with self.assertRaisesRegex(VNError, "endchoice"):
            program("::scene START\n::choice C\n::option a | a\n::ending E")

    def test_stray_else(self):
        with self.assertRaises(VNError):
            program("::scene START\n::else\n::ending E")

    def test_unknown_directive(self):
        with self.assertRaisesRegex(VNError, "unsupported"):
            program("::scene START\n::execute destroy\n::ending E")

    def test_code_fence_rejected(self):
        with self.assertRaisesRegex(VNError, "code fences"):
            program("::scene START\n```python\n::ending E")

    def test_missing_entry(self):
        with self.assertRaisesRegex(VNError, "entry scene"):
            program("::scene ANOTHER\n::ending E")

    def test_static_unreachable_warning(self):
        p = program("::scene START\n::ending E\n::scene ORPHAN\n::ending F")
        self.assertTrue(any("unreachable" in w for w in p.warnings))

    def test_runtime_fallthrough(self):
        p = program("::scene START\n正文")
        self.assertTrue(p.warnings)
        with self.assertRaisesRegex(VNError, "fell through"):
            Runner(p).run()

    def test_prose_not_interpreted_as_a_fact(self):
        p = program("::scene START\n杯子依然完好。\n::ending E", {"cup": "broken"})
        r = Runner(p).run()
        self.assertEqual(r.state["cup"], "broken")  # Tool cannot find this prose contradiction.


class ExpressionTests(unittest.TestCase):
    def test_boolean_logic(self):
        tree = expression('not x or (n >= 2 and tag == "ok")', {"x", "n", "tag"})
        self.assertTrue(evaluate(tree, {"x": True, "n": 2, "tag": "ok"}))

    def test_function_call_rejected(self):
        with self.assertRaisesRegex(VNError, "unsupported"):
            expression('__import__("os").system("echo unsafe")', set())

    def test_attribute_index_arithmetic_rejected(self):
        for value in ("x.real", "x[0]", "x + 1"):
            with self.subTest(value=value), self.assertRaises(VNError):
                expression(value, {"x"})

    def test_undefined_even_in_dead_branch(self):
        with self.assertRaisesRegex(VNError, "undeclared"):
            program("::scene START\n::if false\n::set x = hidden\n::endif\n::ending E", {"x": False})

    def test_undeclared_assignment(self):
        with self.assertRaisesRegex(VNError, "undeclared"):
            program("::scene START\n::set hidden = true\n::ending E")

    def test_non_boolean_guard_rejected_at_execution(self):
        p = program('::scene START\n::if "yes"\n正文\n::endif\n::ending E')
        with self.assertRaisesRegex(VNError, "must be boolean"):
            Runner(p).run()

    def test_bool_not_equal_to_int(self):
        self.assertFalse(evaluate(expression("true == 1", set()), {}))

    def test_nonfinite_default_rejected(self):
        with self.assertRaisesRegex(VNError, "finite"):
            Contract.parse(contract({"x": float("inf")}))

    def test_constant_domain_error(self):
        with self.assertRaisesRegex(VNError, "outside domain"):
            program('::scene START\n::set cup = "repaired"\n::ending E',
                    {"cup": "intact"}, domains={"cup": ["intact", "broken"]})

    def test_type_change_rejected(self):
        with self.assertRaisesRegex(VNError, "type changed"):
            program('::scene START\n::set x = "yes"\n::ending E', {"x": False})

    def test_nullable_domain(self):
        p = program('::scene START\n::set answer = "yes"\n::ending E',
                    {"answer": None}, domains={"answer": [None, "yes", "no"]})
        self.assertEqual(Runner(p).run().state["answer"], "yes")

    def test_invariant_fails_at_assignment(self):
        p = program("::scene START\n::set delivered = true\n::ending E",
                    {"authorized": False, "delivered": False},
                    invariants=[{"id": "arrival", "expr": "not delivered or authorized"}])
        with self.assertRaisesRegex(VNError, "invariant failed"):
            Runner(p).run()

    def test_initial_invariant_fails(self):
        with self.assertRaisesRegex(VNError, "invariant failed"):
            Contract.parse(contract({"x": True}, invariants=[{"id": "bad", "expr": "not x"}]))

    def test_ordered_boolean_comparison_rejected(self):
        p = program("::scene START\n::if true < 2\n正文\n::endif\n::ending E")
        with self.assertRaisesRegex(VNError, "comparison"):
            Runner(p).run()


class ExecutionTests(unittest.TestCase):
    STORY = '''::scene START
::choice C
::option a | A
::set x = true
::option b if x | B
::set x = false
::endchoice
::ending E'''

    def test_one_eligible_auto_selected(self):
        r = Runner(program(self.STORY, {"x": False})).run()
        self.assertEqual(r.selected[0]["option"], "a")

    def test_disabled_option_rejected(self):
        with self.assertRaisesRegex(VNError, "unavailable"):
            Runner(program(self.STORY, {"x": False}), {"C": "b"}).run()

    def test_missing_selection_rejected(self):
        with self.assertRaisesRegex(VNError, "missing selection"):
            Runner(program(self.STORY, {"x": True})).run()

    def test_no_eligible_option(self):
        p = program("::scene START\n::choice C\n::option a if false | a\n::ending E\n::endchoice")
        with self.assertRaisesRegex(VNError, "no eligible"):
            Runner(p).run()

    def test_state_does_not_leak_between_runs(self):
        p = program(self.STORY, {"x": False})
        first = Runner(p).run()
        second = Runner(p)
        self.assertTrue(first.state["x"])
        self.assertFalse(second.state["x"])

    def test_unknown_plan_id(self):
        with self.assertRaisesRegex(VNError, "unknown choice"):
            Runner(program(self.STORY, {"x": False}), {"typo": "a"})

    def test_unused_plan_selection(self):
        with self.assertRaisesRegex(VNError, "unused"):
            Runner(program(self.STORY, {"x": False}), {"C": ["a", "a"]}).run()

    def test_loop_limit(self):
        p = program("::scene START\n::goto START")
        with self.assertRaisesRegex(VNError, "step limit"):
            Runner(p, max_steps=8).run()

    def test_repeated_choice_sequence(self):
        p = program('''::scene START
::choice C
::option again | 再来
::goto START
::option end | 结束
::ending DONE
::endchoice''')
        r = Runner(p, {"C": ["again", "end"]}).run()
        self.assertEqual(r.record()["choices"], {"C": ["again", "end"]})
        self.assertEqual(r.ending, "DONE")

    def test_cues_comments_removed(self):
        p = program("::scene START\n[CUE: no audio]\n<!-- note -->\n正文\n::ending E")
        self.assertEqual(Runner(p).run().transcript(), "正文\n")

    def test_seed_reproducible_and_coverage(self):
        p = program(self.STORY, {"x": True})
        a, b = sample(p, 40, 7, 100), sample(p, 40, 7, 100)
        self.assertEqual(a, b)
        self.assertEqual(a["coverage"]["options"]["visited"], 2)
        self.assertEqual(a["failed_runs"], 0)

    def test_sample_reports_failure(self):
        p = program("::scene START\n::choice C\n::option a if false | a\n::ending E\n::endchoice")
        report = sample(p, 3, 7, 100)
        self.assertEqual(report["failed_runs"], 3)
        self.assertTrue(report["coverage"]["options"]["unvisited"])

    def test_example_full_path(self):
        p = Program.parse((ROOT / "examples/umbrella.vnm.md").read_text(),
                          load_json(ROOT / "examples/umbrella.state.json"))
        r = Runner(p, load_json(ROOT / "examples/umbrella.path.json")).run()
        self.assertEqual(r.ending, "TOGETHER")
        self.assertTrue(r.state["knows_book"])
        self.assertNotIn("::", r.transcript())
        self.assertNotIn("CUE:", r.transcript())
        self.assertNotIn("明天还你", r.transcript())
        self.assertIn("周五拿书", r.transcript())

    def test_example_low_information_path(self):
        p = Program.parse((ROOT / "examples/umbrella.vnm.md").read_text(),
                          load_json(ROOT / "examples/umbrella.state.json"))
        r = Runner(p, {"OFFER": "lend", "WALK": "ahead"}).run()
        self.assertEqual(r.ending, "AHEAD")
        self.assertNotIn("园艺", r.transcript())
        self.assertNotIn("拿书", r.transcript())


class CLITests(unittest.TestCase):
    def test_source_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            story, state = folder / "draft.md", folder / "state.json"
            content = "::scene START\n正文\n::ending E"
            story.write_text(content)
            state.write_text(json.dumps(contract()))
            with contextlib.redirect_stderr(io.StringIO()):
                code = main(["lint", str(story), "--state", str(state), "--out", str(story), "--force"])
            self.assertEqual(code, 1)
            self.assertEqual(story.read_text(), content)

    def test_existing_output_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            story, state, out = folder / "draft.md", folder / "state.json", folder / "out.md"
            story.write_text("::scene START\n正文\n::ending E")
            state.write_text(json.dumps(contract()))
            out.write_text("keep")
            with contextlib.redirect_stderr(io.StringIO()):
                code = main(["trace", str(story), "--state", str(state), "--out", str(out)])
            self.assertEqual(code, 1)
            self.assertEqual(out.read_text(), "keep")

    def test_hardlink_to_source_not_overwritten(self):
        import os
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            story, state, alias = folder / "draft.md", folder / "state.json", folder / "alias.md"
            content = "::scene START\n正文\n::ending E"
            story.write_text(content)
            state.write_text(json.dumps(contract()))
            try:
                os.link(story, alias)
            except OSError:
                self.skipTest("hard links unavailable on this filesystem")
            with contextlib.redirect_stderr(io.StringIO()):
                code = main(["lint", str(story), "--state", str(state), "--out", str(alias), "--force"])
            self.assertEqual(code, 1)
            self.assertEqual(story.read_text(), content)

    def test_trace_outputs_cannot_share_path(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            story, state, out = folder / "draft.md", folder / "state.json", folder / "out.md"
            story.write_text("::scene START\n正文\n::ending E")
            state.write_text(json.dumps(contract()))
            with contextlib.redirect_stderr(io.StringIO()):
                code = main(["trace", str(story), "--state", str(state),
                             "--out", str(out), "--record", str(out), "--force"])
            self.assertEqual(code, 1)
            self.assertFalse(out.exists())

    def test_duplicate_json_key_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "input.json"
            p.write_text('{"x": 1, "x": 2}')
            with self.assertRaisesRegex(VNError, "duplicate JSON"):
                load_json(p)

    def test_lint_output_is_json(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main(["lint", str(ROOT / "examples/umbrella.vnm.md"),
                         "--state", str(ROOT / "examples/umbrella.state.json")])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(buf.getvalue())["status"], "static_checks_passed")


if __name__ == "__main__":
    unittest.main()
