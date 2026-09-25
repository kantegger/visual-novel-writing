#!/usr/bin/env python3
"""VNMD-0.1: opt-in structural checker and reading-path renderer.

Python 3.10+, standard library only. No eval, shell calls, network or source writes.
This does not infer facts, chronology, emotions or literary quality from prose.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import math
from pathlib import Path
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Any

VERSION = "0.1.0"
IDENT = r"[A-Za-z_][A-Za-z0-9_]*"
RESERVED = {"true": True, "false": False, "null": None}
SCENE_RE = re.compile(rf"::scene\s+({IDENT})$")
OPTION_RE = re.compile(rf"::option\s+({IDENT})(?:\s+if\s+(.+?))?\s*\|\s*(.+)$")
SET_RE = re.compile(rf"::set\s+({IDENT})\s*=\s*(.+)$")


class VNError(ValueError):
    def __init__(self, message: str, line: int | None = None):
        self.line = line
        super().__init__(f"line {line}: {message}" if line else message)


def scalar(value: Any) -> bool:
    return type(value) in (str, bool, int, float, type(None)) and (
        type(value) is not float or math.isfinite(value)
    )


def same(a: Any, b: Any) -> bool:
    return type(a) is type(b) and a == b


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise VNError(f"duplicate JSON key: {key}")
        out[key] = value
    return out


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_object)


def expression(text: str, names: set[str], line: int | None = None) -> ast.expr:
    if len(text) > 4096:
        raise VNError("expression exceeds 4096 characters", line)
    try:
        tree = ast.parse(text.strip(), mode="eval").body
    except (SyntaxError, RecursionError) as exc:
        raise VNError(f"invalid expression: {text}", line) from exc
    nodes = list(ast.walk(tree))
    if len(nodes) > 256:
        raise VNError("expression exceeds 256 AST nodes", line)
    allowed = (
        ast.Constant, ast.Name, ast.Load, ast.BoolOp, ast.And, ast.Or,
        ast.UnaryOp, ast.Not, ast.USub, ast.UAdd, ast.Compare,
        ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    )
    for node in nodes:
        if not isinstance(node, allowed):
            raise VNError(f"unsupported expression element: {type(node).__name__}", line)
        if isinstance(node, ast.Name) and node.id not in names and node.id not in RESERVED:
            raise VNError(f"undeclared variable: {node.id}", line)
        if isinstance(node, ast.Constant) and not scalar(node.value):
            raise VNError("only finite scalar constants are supported", line)
    return tree


def boolean(value: Any, line: int | None = None) -> bool:
    if type(value) is not bool:
        raise VNError(f"condition must be boolean, got {type(value).__name__}", line)
    return value


def evaluate(node: ast.expr, state: dict[str, Any], line: int | None = None) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return RESERVED[node.id] if node.id in RESERVED else state[node.id]
    if isinstance(node, ast.UnaryOp):
        value = evaluate(node.operand, state, line)
        if isinstance(node.op, ast.Not):
            return not boolean(value, line)
        if type(value) not in (int, float):
            raise VNError("unary +/- requires a number", line)
        return -value if isinstance(node.op, ast.USub) else value
    if isinstance(node, ast.BoolOp):
        # Short-circuit, but never treat a non-boolean as a condition.
        for child in node.values:
            value = boolean(evaluate(child, state, line), line)
            if isinstance(node.op, ast.And) and not value:
                return False
            if isinstance(node.op, ast.Or) and value:
                return True
        return isinstance(node.op, ast.And)
    if isinstance(node, ast.Compare):
        left = evaluate(node.left, state, line)
        for op, right_node in zip(node.ops, node.comparators):
            right = evaluate(right_node, state, line)
            if isinstance(op, ast.Eq):
                passed = same(left, right)
            elif isinstance(op, ast.NotEq):
                passed = not same(left, right)
            else:
                numeric = type(left) in (int, float) and type(right) in (int, float)
                strings = type(left) is str and type(right) is str
                if not (numeric or strings):
                    raise VNError("ordered comparison needs two numbers or two strings", line)
                if isinstance(op, ast.Lt):
                    passed = left < right
                elif isinstance(op, ast.LtE):
                    passed = left <= right
                elif isinstance(op, ast.Gt):
                    passed = left > right
                else:
                    passed = left >= right
            if not passed:
                return False
            left = right
        return True
    raise VNError("unexpected expression node", line)


@dataclass
class Contract:
    entry: str
    defaults: dict[str, Any]
    domains: dict[str, list[Any]]
    invariants: list[tuple[str, ast.expr]]

    @classmethod
    def parse(cls, data: Any) -> "Contract":
        if not isinstance(data, dict) or data.get("format") != "vnmd-0.1":
            raise VNError('state file must be an object with "format": "vnmd-0.1"')
        if set(data) - {"format", "entry", "defaults", "domains", "invariants"}:
            raise VNError("unknown top-level field in state file")
        entry, defaults = data.get("entry"), data.get("defaults")
        if not isinstance(entry, str) or not re.fullmatch(IDENT, entry):
            raise VNError("state entry must be a scene identifier")
        if not isinstance(defaults, dict):
            raise VNError("defaults must be an object (empty is allowed)")
        for name, value in defaults.items():
            if not re.fullmatch(IDENT, name) or name in RESERVED or name in {"True", "False", "None"}:
                raise VNError(f"invalid state variable name: {name}")
            if not scalar(value):
                raise VNError(f"default for {name} is not a finite scalar")
        domains = data.get("domains", {})
        if not isinstance(domains, dict) or set(domains) - set(defaults):
            raise VNError("domains must refer only to declared variables")
        for name, values in domains.items():
            if not isinstance(values, list) or not values or not all(scalar(v) for v in values):
                raise VNError(f"domain for {name} must be a nonempty list of finite scalars")
        raw_inv = data.get("invariants", [])
        if not isinstance(raw_inv, list):
            raise VNError("invariants must be a list")
        invariants: list[tuple[str, ast.expr]] = []
        ids: set[str] = set()
        for item in raw_inv:
            if not isinstance(item, dict) or set(item) != {"id", "expr"}:
                raise VNError("each invariant requires only id and expr")
            if not isinstance(item["id"], str) or not re.fullmatch(IDENT, item["id"]) or item["id"] in ids:
                raise VNError("invariant IDs must be unique identifiers")
            if not isinstance(item["expr"], str):
                raise VNError("invariant expression must be text")
            ids.add(item["id"])
            invariants.append((item["id"], expression(item["expr"], set(defaults))))
        obj = cls(entry, copy.deepcopy(defaults), domains, invariants)
        for name, value in defaults.items():
            obj.check_value(name, value)
        obj.check_invariants(defaults)
        return obj

    def check_value(self, name: str, value: Any, line: int | None = None) -> None:
        if name not in self.defaults:
            raise VNError(f"assignment to undeclared variable: {name}", line)
        if not scalar(value):
            raise VNError(f"non-scalar or non-finite assignment: {name}", line)
        if name in self.domains:
            if not any(same(value, x) for x in self.domains[name]):
                raise VNError(f"value {value!r} outside domain of {name}", line)
        elif type(value) is not type(self.defaults[name]):
            raise VNError(f"type changed for {name}; define an explicit domain if intentional", line)

    def check_invariants(self, state: dict[str, Any], line: int | None = None) -> None:
        for name, tree in self.invariants:
            if not boolean(evaluate(tree, state, line), line):
                raise VNError(f"invariant failed: {name}", line)


@dataclass
class Option:
    name: str
    label: str
    guard: str | None
    line: int
    body: list["Node"]


@dataclass
class Node:
    kind: str
    line: int
    value: str = ""
    name: str = ""
    arms: list[tuple[str | None, list["Node"]]] = field(default_factory=list)
    options: list[Option] = field(default_factory=list)


class Parser:
    def __init__(self, lines: list[tuple[int, str]]):
        self.lines, self.i = lines, 0

    def current(self) -> tuple[int, str, str]:
        line, raw = self.lines[self.i]
        text = raw.strip()
        return line, text, text.split(maxsplit=1)[0] if text else ""

    def consume_exact(self, expected: str) -> None:
        if self.i >= len(self.lines):
            raise VNError(f"missing {expected}")
        line, text, _ = self.current()
        if text != expected:
            raise VNError(f"expected {expected}, got {text}", line)
        self.i += 1

    def block(self, stops: set[str] | None = None) -> list[Node]:
        out: list[Node] = []
        stops = stops or set()
        while self.i < len(self.lines):
            line, text, tag = self.current()
            if tag in stops:
                return out
            if tag == "::if":
                cond = text[len(tag):].strip()
                if not cond:
                    raise VNError("empty if condition", line)
                self.i += 1
                arms = [(cond, self.block({"::elif", "::else", "::endif"}))]
                while self.i < len(self.lines) and self.current()[2] == "::elif":
                    ln, value, _ = self.current()
                    cond = value[len("::elif"):].strip()
                    if not cond:
                        raise VNError("empty elif condition", ln)
                    self.i += 1
                    arms.append((cond, self.block({"::elif", "::else", "::endif"})))
                if self.i < len(self.lines) and self.current()[2] == "::else":
                    self.consume_exact("::else")
                    arms.append((None, self.block({"::endif"})))
                self.consume_exact("::endif")
                out.append(Node("if", line, arms=arms))
            elif tag == "::choice":
                name = text[len(tag):].strip()
                if not re.fullmatch(IDENT, name):
                    raise VNError("invalid choice ID", line)
                self.i += 1
                options: list[Option] = []
                while self.i < len(self.lines):
                    ln, value, next_tag = self.current()
                    if not value:
                        self.i += 1
                        continue
                    if next_tag == "::endchoice":
                        break
                    match = OPTION_RE.fullmatch(value)
                    if not match:
                        raise VNError("expected ::option ID [if expression] | label", ln)
                    self.i += 1
                    body = self.block({"::option", "::endchoice"})
                    options.append(Option(match[1], match[3], match[2], ln, body))
                self.consume_exact("::endchoice")
                if not options:
                    raise VNError("choice must contain at least one option", line)
                if len({o.name for o in options}) != len(options):
                    raise VNError(f"duplicate option ID in {name}", line)
                out.append(Node("choice", line, name=name, options=options))
            elif tag == "::set":
                match = SET_RE.fullmatch(text)
                if not match:
                    raise VNError("expected ::set variable = expression", line)
                out.append(Node("set", line, value=match[2], name=match[1]))
                self.i += 1
            elif tag in {"::goto", "::ending"}:
                target = text[len(tag):].strip()
                if not re.fullmatch(IDENT, target):
                    raise VNError(f"invalid identifier after {tag}", line)
                out.append(Node(tag[2:], line, value=target))
                self.i += 1
            elif text.startswith("::"):
                raise VNError(f"unexpected or unsupported directive: {tag}", line)
            else:
                if text.startswith("```") or text.startswith("~~~"):
                    raise VNError("code fences inside scenes are unsupported; keep author data outside scenes", line)
                out.append(Node("text", line, value=self.lines[self.i][1]))
                self.i += 1
        return out


@dataclass
class Program:
    scenes: dict[str, list[Node]]
    contract: Contract
    choices: dict[str, Node]
    endings: set[str]
    warnings: list[str]
    expressions: dict[str, ast.expr]
    sources: dict[str, str] = field(default_factory=dict)

    @classmethod
    def parse(cls, text: str, data: dict[str, Any]) -> "Program":
        contract = Contract.parse(data)
        sections: dict[str, list[tuple[int, str]]] = {}
        name: str | None = None
        for line, raw in enumerate(text.splitlines(), 1):
            stripped = raw.strip()
            if stripped.startswith("::scene"):
                match = SCENE_RE.fullmatch(stripped)
                if not match:
                    raise VNError("expected ::scene IDENTIFIER", line)
                name = match[1]
                if name in sections:
                    raise VNError(f"duplicate scene: {name}", line)
                sections[name] = []
            elif name is not None:
                sections[name].append((line, raw))
            elif stripped.startswith("::"):
                raise VNError("directive outside a scene", line)
        if contract.entry not in sections:
            raise VNError(f"entry scene not found: {contract.entry}")
        scenes = {key: Parser(lines).block() for key, lines in sections.items()}
        result = cls(scenes, contract, {}, set(), [], {})
        edges: dict[str, set[str]] = {key: set() for key in scenes}

        def add_expr(value: str, line: int) -> None:
            if value not in result.expressions:
                result.expressions[value] = expression(value, set(contract.defaults), line)

        def walk(nodes: list[Node], scene: str) -> None:
            for node in nodes:
                if node.kind == "set":
                    if node.name not in contract.defaults:
                        raise VNError(f"assignment to undeclared variable: {node.name}", node.line)
                    add_expr(node.value, node.line)
                    tree = result.expressions[node.value]
                    dynamic = any(isinstance(x, ast.Name) and x.id not in RESERVED for x in ast.walk(tree))
                    if not dynamic:
                        contract.check_value(node.name, evaluate(tree, contract.defaults, node.line), node.line)
                elif node.kind == "if":
                    for cond, body in node.arms:
                        if cond is not None:
                            add_expr(cond, node.line)
                        walk(body, scene)
                elif node.kind == "choice":
                    if node.name in result.choices:
                        raise VNError(f"duplicate choice ID: {node.name}", node.line)
                    result.choices[node.name] = node
                    for option in node.options:
                        if option.guard is not None:
                            add_expr(option.guard, option.line)
                        walk(option.body, scene)
                elif node.kind == "goto":
                    if node.value not in scenes:
                        raise VNError(f"missing goto scene: {node.value}", node.line)
                    edges[scene].add(node.value)
                elif node.kind == "ending":
                    result.endings.add(node.value)

        def terminates(nodes: list[Node]) -> bool:
            for node in nodes:
                if node.kind in {"goto", "ending"}:
                    return True
                if node.kind == "if" and any(c is None for c, _ in node.arms):
                    if all(terminates(b) for _, b in node.arms):
                        return True
                if node.kind == "choice" and all(terminates(o.body) for o in node.options):
                    return True
            return False

        for key, nodes in scenes.items():
            walk(nodes, key)
            if not terminates(nodes):
                result.warnings.append(f"scene {key}: possible fallthrough; explicit goto/ending required at runtime")
        reached, pending = set(), [contract.entry]
        while pending:
            key = pending.pop()
            if key not in reached:
                reached.add(key)
                pending.extend(edges[key] - reached)
        for key in sorted(set(scenes) - reached):
            result.warnings.append(f"scene {key}: structurally unreachable from entry (guards ignored)")
        if not result.endings:
            result.warnings.append("no ending directives found")
        return result

    def eval(self, text: str, state: dict[str, Any], line: int) -> Any:
        return evaluate(self.expressions[text], state, line)

    def inventory(self) -> dict[str, Any]:
        return {
            "scenes": sorted(self.scenes),
            "choices": sorted(self.choices),
            "options": sorted(f"{key}/{o.name}" for key, node in self.choices.items() for o in node.options),
            "endings": sorted(self.endings),
            "variables": sorted(self.contract.defaults),
        }


class Runner:
    def __init__(self, program: Program, plan: dict[str, Any] | None = None,
                 rng: random.Random | None = None, max_steps: int = 10000):
        self.program, self.rng, self.max_steps = program, rng, max_steps
        self.state = copy.deepcopy(program.contract.defaults)
        self.plan: dict[str, list[str]] = {}
        if plan is not None:
            if not isinstance(plan, dict):
                raise VNError("choice plan must be a JSON object")
            for key, value in plan.items():
                if key not in program.choices:
                    raise VNError(f"choice plan has unknown choice: {key}")
                sequence = [value] if isinstance(value, str) else value
                if not isinstance(sequence, list) or not sequence or not all(isinstance(v, str) for v in sequence):
                    raise VNError(f"plan value for {key} must be an option ID or nonempty list of IDs")
                self.plan[key] = list(sequence)
        if max_steps < 1:
            raise VNError("max_steps must be positive")
        self.used: dict[str, int] = {}
        self.steps = 0
        self.visited: list[str] = []
        self.selected: list[dict[str, Any]] = []
        self.output: list[str] = []
        self.ending: str | None = None

    def tick(self, line: int | None = None) -> None:
        self.steps += 1
        if self.steps > self.max_steps:
            raise VNError(f"step limit {self.max_steps} exceeded; possible loop", line)

    def choose(self, node: Node) -> Option:
        eligible = [o for o in node.options if o.guard is None or boolean(
            self.program.eval(o.guard, self.state, o.line), o.line)]
        if not eligible:
            raise VNError(f"choice {node.name} has no eligible options", node.line)
        index = self.used.get(node.name, 0)
        specified = self.plan.get(node.name, [])
        if index < len(specified):
            wanted = specified[index]
            matches = [o for o in eligible if o.name == wanted]
            if not matches:
                raise VNError(f"option {wanted!r} unavailable in {node.name}; available: " +
                              ", ".join(o.name for o in eligible), node.line)
            option = matches[0]
            self.used[node.name] = index + 1
        elif self.rng is not None:
            option = self.rng.choice(eligible)
        elif len(eligible) == 1:
            option = eligible[0]
        else:
            raise VNError(f"missing selection for {node.name}; available: " +
                          ", ".join(o.name for o in eligible), node.line)
        self.selected.append({"choice": node.name, "option": option.name, "line": node.line})
        label = option.label
        self.output.append(label if label.startswith("【") and label.endswith("】") else f"【{label}】")
        return option

    def execute(self, nodes: list[Node]) -> tuple[str, str] | None:
        for node in nodes:
            self.tick(node.line)
            if node.kind == "text":
                text = node.value.strip()
                if text.startswith("[CUE:") and text.endswith("]"):
                    continue
                if text.startswith("<!--") and text.endswith("-->"):
                    continue
                self.output.append(node.value)
            elif node.kind == "set":
                value = self.program.eval(node.value, self.state, node.line)
                self.program.contract.check_value(node.name, value, node.line)
                self.state[node.name] = value
                self.program.contract.check_invariants(self.state, node.line)
            elif node.kind == "if":
                for cond, body in node.arms:
                    if cond is None or boolean(self.program.eval(cond, self.state, node.line), node.line):
                        transfer = self.execute(body)
                        if transfer:
                            return transfer
                        break
            elif node.kind == "choice":
                option = self.choose(node)
                transfer = self.execute(option.body)
                if transfer:
                    return transfer
            elif node.kind in {"goto", "ending"}:
                return node.kind, node.value
        return None

    def run(self) -> "Runner":
        self.program.contract.check_invariants(self.state)
        current = self.program.contract.entry
        while True:
            self.tick()
            self.visited.append(current)
            result = self.execute(self.program.scenes[current])
            if result is None:
                raise VNError(f"scene {current} fell through without goto or ending")
            kind, target = result
            if kind == "ending":
                self.ending = target
                break
            current = target
        leftovers = {key: values[self.used.get(key, 0):] for key, values in self.plan.items()
                     if self.used.get(key, 0) < len(values)}
        if leftovers:
            raise VNError(f"choice plan contains unused selections: {leftovers}")
        return self

    def transcript(self) -> str:
        # No unselected options, state assignments, cue lines or author preamble.
        return re.sub(r"\n{3,}", "\n\n", "\n".join(self.output)).strip() + "\n"

    def record(self) -> dict[str, Any]:
        replay: dict[str, list[str]] = {}
        for item in self.selected:
            replay.setdefault(item["choice"], []).append(item["option"])
        return {"ending": self.ending, "scenes": self.visited, "decisions": self.selected,
                "choices": replay, "state": self.state, "steps": self.steps}


def sample(program: Program, runs: int, seed: int, max_steps: int) -> dict[str, Any]:
    if not 1 <= runs <= 100000:
        raise VNError("runs must be between 1 and 100000")
    rng = random.Random(seed)
    inventory = program.inventory()
    seen: dict[str, set[str]] = {k: set() for k in ("scenes", "choices", "options", "endings")}
    failures: list[dict[str, Any]] = []
    representatives: dict[str, Any] = {}
    successful = 0
    failure_count = 0
    for i in range(runs):
        runner = Runner(program, rng=rng, max_steps=max_steps)
        try:
            runner.run()
            successful += 1
            assert runner.ending is not None
            seen["endings"].add(runner.ending)
            representatives.setdefault(runner.ending, runner.record())
        except VNError as exc:
            failure_count += 1
            # Keep a bounded set of concrete reproductions; retain the full count.
            if len(failures) < 20:
                failures.append({"run": i + 1, "error": str(exc), "trace": runner.record()})
        seen["scenes"].update(runner.visited)
        seen["choices"].update(d["choice"] for d in runner.selected)
        seen["options"].update(f"{d['choice']}/{d['option']}" for d in runner.selected)
    coverage = {key: {"visited": len(seen[key]), "declared": len(inventory[key]),
                      "unvisited": sorted(set(inventory[key]) - seen[key])} for key in seen}
    return {
        "tool": f"vnmd {VERSION}", "mode": "sample", "seed": seed,
        "runs": runs, "successful_runs": successful, "failed_runs": failure_count,
        "max_steps_per_run": max_steps, "input_sha256": program.sources,
        "warnings": program.warnings, "coverage": coverage,
        "failures_first_20": failures, "representative_paths": representatives,
        "limits": ["Not exhaustive state-space exploration.",
                   "Scene/option/ending coverage is not condition-combination coverage.",
                   "Checks declared transitions and invariants only, not facts inferred from prose.",
                   "No engine, audiovisual, accessibility or reader-quality test was performed."],
    }


def is_protected(path: Path, protected: set[Path]) -> bool:
    if path.resolve() in protected:
        return True
    if path.exists():
        for source in protected:
            try:
                if path.samefile(source):
                    return True
            except OSError:
                continue
    return False


def write_output(path: Path | None, text: str, force: bool, protected: set[Path]) -> None:
    if path is None:
        sys.stdout.write(text)
        return
    if is_protected(path, protected):
        raise VNError("refusing to overwrite a source input, even with --force")
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents accidental overwrite, including a newly appeared file.
    # Explicit --force opts into replacement of generated output, never source inputs.
    with path.open("w" if force else "x", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    sub = cli.add_subparsers(dest="command", required=True)
    for name in ("lint", "trace", "sample"):
        cmd = sub.add_parser(name)
        cmd.add_argument("story", type=Path)
        cmd.add_argument("--state", type=Path, required=True)
        cmd.add_argument("--out", type=Path, help="default: stdout; existing files require --force")
        cmd.add_argument("--force", action="store_true", help="overwrite generated output, never an input")
        if name != "lint":
            cmd.add_argument("--max-steps", type=int, default=10000)
        if name == "trace":
            cmd.add_argument("--choices", type=Path, help="explicit per-choice option IDs; no hidden defaults")
            cmd.add_argument("--record", type=Path, help="optional JSON execution record")
        if name == "sample":
            cmd.add_argument("--runs", type=int, default=200)
            cmd.add_argument("--seed", type=int, default=17)
    args = cli.parse_args(argv)
    try:
        program = Program.parse(args.story.read_text(encoding="utf-8-sig"), load_json(args.state))
        program.sources = {"story": hashlib.sha256(args.story.read_bytes()).hexdigest(),
                           "state": hashlib.sha256(args.state.read_bytes()).hexdigest()}
        protected = {args.story.resolve(), args.state.resolve()}
        if args.command == "lint":
            report = {"tool": f"vnmd {VERSION}", "mode": "lint", "status": "static_checks_passed",
                      "inventory": program.inventory(), "warnings": program.warnings,
                      "input_sha256": program.sources,
                      "limits": "Static references and syntax only; no prose semantics or path execution."}
            write_output(args.out, json.dumps(report, ensure_ascii=False, indent=2) + "\n", args.force, protected)
        elif args.command == "trace":
            plan = load_json(args.choices) if args.choices else None
            if args.choices:
                protected.add(args.choices.resolve())
            if args.out and args.record and args.out.resolve() == args.record.resolve():
                raise VNError("transcript and record output must be different files")
            # Preflight both destinations before writing either of them.
            for destination in (args.out, args.record):
                if destination and is_protected(destination, protected):
                    raise VNError("output destination is a protected input")
                if destination and destination.exists() and not args.force:
                    raise VNError(f"output exists: {destination}; use a new path or --force")
            runner = Runner(program, plan=plan, max_steps=args.max_steps).run()
            write_output(args.out, runner.transcript(), args.force, protected)
            if args.record:
                report = {"tool": f"vnmd {VERSION}", "mode": "trace",
                          "input_sha256": program.sources, **runner.record()}
                write_output(args.record, json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                             args.force, protected)
        else:
            report = sample(program, args.runs, args.seed, args.max_steps)
            write_output(args.out, json.dumps(report, ensure_ascii=False, indent=2) + "\n", args.force, protected)
            if report["failed_runs"]:
                return 1
        return 0
    except (VNError, OSError, UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        print(f"vnmd: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
