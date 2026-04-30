import pytest
from backend.models.schemas import ProblemTestCase
from backend.services.sandbox import run_code


def _tc(inp, out, label=""):
    return ProblemTestCase(input=inp, expected_output=out, is_hidden=False, edge_case_label=label)


def test_correct_solution():
    code = "def two_sum(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n        if target - n in seen:\n            return [seen[target - n], i]\n        seen[n] = i\n"
    result = run_code(code, "two_sum", [
        _tc({"nums": [2, 7, 11, 15], "target": 9}, [0, 1]),
        _tc({"nums": [3, 2, 4], "target": 6}, [1, 2]),
    ])
    assert result.all_passed
    assert result.test_cases_passed == 2
    assert result.exit_code == 0


def test_wrong_answer():
    code = "def two_sum(nums, target):\n    return [0, 0]\n"
    result = run_code(code, "two_sum", [
        _tc({"nums": [2, 7, 11, 15], "target": 9}, [0, 1]),
    ])
    assert not result.all_passed
    assert result.test_cases_passed == 0


def test_syntax_error():
    code = "def two_sum(nums, target)\n    return [0, 1]\n"
    result = run_code(code, "two_sum", [_tc({"nums": [2, 7], "target": 9}, [0, 1])])
    assert not result.all_passed
    assert "SyntaxError" in result.test_case_results[0].error


def test_runtime_exception():
    code = "def two_sum(nums, target):\n    return nums[999]\n"
    result = run_code(code, "two_sum", [_tc({"nums": [1, 2], "target": 3}, [0, 1])])
    assert not result.all_passed
    assert "IndexError" in result.test_case_results[0].error


def test_infinite_loop_timeout():
    code = "def two_sum(nums, target):\n    while True: pass\n"
    result = run_code(code, "two_sum", [_tc({"nums": [1, 2], "target": 3}, [0, 1])])
    assert result.exit_code == -1
    assert "Time limit exceeded" in result.stderr


def test_blocked_import_os():
    code = "import os\ndef two_sum(nums, target):\n    return [0, 1]\n"
    result = run_code(code, "two_sum", [_tc({"nums": [1, 2], "target": 3}, [0, 1])])
    assert result.exit_code == 2
    assert "not allowed" in result.stderr


def test_blocked_open():
    code = "def two_sum(nums, target):\n    f = open('/etc/passwd')\n    return [0, 1]\n"
    result = run_code(code, "two_sum", [_tc({"nums": [1, 2], "target": 3}, [0, 1])])
    assert result.exit_code == 2


def test_empty_test_cases():
    code = "def two_sum(nums, target):\n    return []\n"
    result = run_code(code, "two_sum", [])
    assert result.test_cases_total == 0
    assert result.all_passed
