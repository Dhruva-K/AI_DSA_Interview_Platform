"""
Sandboxed code execution service.

User code is never eval()'d or exec()'d in the main process.
It is written to a temp file and run in an isolated subprocess via a harness.
"""
import json
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path

from backend.models.schemas import SandboxResult, ProblemTestCase, TestCaseResult

TIMEOUT_SECONDS = 10
MEMORY_LIMIT_MB = 256

# Imports blocked before subprocess is even started
BLOCKED_IMPORTS = [
    "import os",
    "import subprocess",
    "import socket",
    "import sys",
    "import shutil",
    "import pathlib",
    "__import__",
    "importlib",
]
BLOCKED_BUILTINS = ["open(", "exec(", "eval(", "compile(", "__builtins__"]

RUNNER_TEMPLATE = textwrap.dedent("""\
    import sys
    import json
    import importlib.util
    import traceback
    import io
    import inspect
    import re

    def load_solution(path):
        spec = importlib.util.spec_from_file_location("solution", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def _to_snake_case(name):
        s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\\1_\\2", name)
        return re.sub(r"([a-z0-9])([A-Z])", r"\\1_\\2", s1).lower()

    def _to_camel_case(name):
        parts = [p for p in name.split("_") if p]
        if not parts:
            return name
        return parts[0] + "".join(p[:1].upper() + p[1:] for p in parts[1:])

    def _normalized_name(name):
        return name.replace("_", "").lower()

    def _resolve_function(mod, function_name, test_cases):
        # 1) Exact match first.
        fn = getattr(mod, function_name, None)
        if callable(fn):
            return fn, function_name

        callable_items = [
            (name, value)
            for name, value in vars(mod).items()
            if callable(value) and not name.startswith("_")
        ]

        # 2) Common naming transformations (snake_case <-> camelCase).
        aliases = {
            function_name,
            _to_snake_case(function_name),
            _to_camel_case(function_name),
        }
        for alias in aliases:
            candidate = getattr(mod, alias, None)
            if callable(candidate):
                return candidate, alias

        # 3) Relaxed comparison by normalized name.
        target = _normalized_name(function_name)
        normalized_matches = [
            (name, value)
            for name, value in callable_items
            if _normalized_name(name) == target
        ]
        if len(normalized_matches) == 1:
            return normalized_matches[0][1], normalized_matches[0][0]

        # 4) Last resort: pick a function compatible with test input keys.
        if test_cases:
            sample_input = test_cases[0].get("input", {})
            compatible = []
            for name, value in callable_items:
                try:
                    inspect.signature(value).bind(**sample_input)
                    compatible.append((name, value))
                except Exception:
                    continue
            if len(compatible) == 1:
                return compatible[0][1], compatible[0][0]

        available = [name for name, _ in callable_items]
        raise AttributeError(
            f"Function '{function_name}' not found. Available callables: {available}"
        )

    def run():
        data = json.loads(sys.stdin.read())
        solution_path = data["solution_path"]
        function_name = data["function_name"]
        test_cases = data["test_cases"]

        results = []
        try:
            mod = load_solution(solution_path)
            fn, resolved_name = _resolve_function(mod, function_name, test_cases)
        except Exception:
            error_msg = traceback.format_exc()
            for i, tc in enumerate(test_cases):
                results.append({
                    "index": i,
                    "passed": False,
                    "edge_case_label": tc.get("edge_case_label", ""),
                    "error": error_msg,
                })
            print(json.dumps({"results": results}))
            return

        for i, tc in enumerate(test_cases):
            stdout_buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = stdout_buf
            try:
                actual = fn(**tc["input"])
                passed = actual == tc["expected_output"]
                error = "" if passed else f"Expected {tc['expected_output']!r}, got {actual!r}"
            except Exception:
                passed = False
                error = traceback.format_exc()
            finally:
                sys.stdout = old_stdout
            results.append({
                "index": i,
                "passed": passed,
                "edge_case_label": tc.get("edge_case_label", ""),
                "error": error,
            })

        print(json.dumps({"results": results}))

    run()
""")


def _check_blocked_patterns(code: str) -> str | None:
    """Return an error message if the code contains blocked patterns, else None."""
    for pattern in BLOCKED_IMPORTS + BLOCKED_BUILTINS:
        if pattern in code:
            return f"Use of '{pattern}' is not allowed in submissions."
    return None


def run_code(
    code: str,
    function_name: str,
    test_cases: list[ProblemTestCase],
) -> SandboxResult:
    block_error = _check_blocked_patterns(code)
    if block_error:
        results = [
            TestCaseResult(
                index=i,
                passed=False,
                edge_case_label=tc.edge_case_label,
                error=block_error,
            )
            for i, tc in enumerate(test_cases)
        ]
        return SandboxResult(
            stdout="",
            stderr=block_error,
            exit_code=2,
            runtime_ms=0,
            test_cases_passed=0,
            test_cases_total=len(test_cases),
            all_passed=False,
            test_case_results=results,
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        solution_file = tmppath / "solution.py"
        solution_file.write_text(code, encoding="utf-8")

        runner_file = tmppath / "runner.py"
        runner_file.write_text(RUNNER_TEMPLATE, encoding="utf-8")

        stdin_payload = json.dumps({
            "solution_path": str(solution_file),
            "function_name": function_name,
            "test_cases": [tc.model_dump() for tc in test_cases],
        })

        start = time.monotonic()
        try:
            proc = subprocess.run(
                [sys.executable, str(runner_file)],
                input=stdin_payload,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                cwd=tmpdir,
            )
        except subprocess.TimeoutExpired:
            elapsed = int((time.monotonic() - start) * 1000)
            results = [
                TestCaseResult(
                    index=i,
                    passed=False,
                    edge_case_label=tc.edge_case_label,
                    error="Time limit exceeded (10s)",
                )
                for i, tc in enumerate(test_cases)
            ]
            return SandboxResult(
                stdout="",
                stderr="Time limit exceeded (10s)",
                exit_code=-1,
                runtime_ms=elapsed,
                test_cases_passed=0,
                test_cases_total=len(test_cases),
                all_passed=False,
                test_case_results=results,
            )

        elapsed = int((time.monotonic() - start) * 1000)

        if proc.returncode != 0 or not proc.stdout.strip():
            results = [
                TestCaseResult(
                    index=i,
                    passed=False,
                    edge_case_label=tc.edge_case_label,
                    error=proc.stderr or "Unknown error",
                )
                for i, tc in enumerate(test_cases)
            ]
            return SandboxResult(
                stdout=proc.stdout,
                stderr=proc.stderr,
                exit_code=proc.returncode,
                runtime_ms=elapsed,
                test_cases_passed=0,
                test_cases_total=len(test_cases),
                all_passed=False,
                test_case_results=results,
            )

        try:
            output = json.loads(proc.stdout)
            raw_results = output["results"]
        except (json.JSONDecodeError, KeyError):
            results = [
                TestCaseResult(
                    index=i,
                    passed=False,
                    edge_case_label=tc.edge_case_label,
                    error="Runner produced malformed output",
                )
                for i, tc in enumerate(test_cases)
            ]
            return SandboxResult(
                stdout=proc.stdout,
                stderr=proc.stderr,
                exit_code=1,
                runtime_ms=elapsed,
                test_cases_passed=0,
                test_cases_total=len(test_cases),
                all_passed=False,
                test_case_results=results,
            )

        tc_results = [
            TestCaseResult(
                index=r["index"],
                passed=r["passed"],
                edge_case_label=r.get("edge_case_label", ""),
                error=r.get("error", ""),
            )
            for r in raw_results
        ]
        passed_count = sum(1 for r in tc_results if r.passed)
        first_failure = next(
            (
                {"index": r.index, "error": r.error}
                for r in tc_results
                if not r.passed
            ),
            None,
        )

        return SandboxResult(
            stdout=proc.stdout,
            stderr=proc.stderr,
            exit_code=proc.returncode,
            runtime_ms=elapsed,
            test_cases_passed=passed_count,
            test_cases_total=len(tc_results),
            all_passed=passed_count == len(tc_results),
            test_case_results=tc_results,
            failed_test_case=first_failure,
        )
