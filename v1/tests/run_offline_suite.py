"""
Unified offline verification suite for the EmpathyScale pipeline.

Runs each offline test in an ISOLATED subprocess (each patches create_llm /
search APIs in its own process, so module-patch state never leaks), then reports
a single PASS/FAIL summary. This is the one command that proves "all agent code
paths are sound" without any API key or network access.

    venv/Scripts/python.exe tests/run_offline_suite.py

Coverage (each test drives the REAL agent code, only the LLM / search backend is
mocked):
  - offline_smoke_test.py              -> main orchestration (Phase B) 13/13
  - offline_generation_agent_test.py   -> real EmpathyScaleGenerationAgentGroup 5/5
  - offline_literature_agent_test.py   -> real LiteratureSearchAgentGroup 5/5
  (Interview agent uses a langchain AgentExecutor that needs a real/compatible LLM
   to build; it is excluded here and covered by `python main.py` with a real key.)
"""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TESTS = [
    "offline_smoke_test.py",
    "offline_generation_agent_test.py",
    "offline_literature_agent_test.py",
]


def run_one(test_file: str) -> tuple:
    path = Path(__file__).resolve().parent / test_file
    proc = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    out = proc.stdout + proc.stderr
    # Pull the most informative single line for the summary.
    marker = None
    for line in out.splitlines():
        if "RESULT:" in line or "SUMMARY:" in line or "ARTIFACT CHECK" in line:
            marker = line.strip()
    return proc.returncode == 0, marker, out


def main():
    print("=" * 64)
    print("EMPATHYSCALE OFFLINE VERIFICATION SUITE")
    print("=" * 64)
    results = []
    for t in TESTS:
        ok, marker, _ = run_one(t)
        results.append((t, ok, marker))
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {t}" + (f"  -> {marker}" if marker else ""))

    n_fail = sum(1 for _, ok, _ in results if not ok)
    print("-" * 64)
    print("OVERALL:", "ALL PASS" if n_fail == 0 else f"{n_fail} FAILED")
    print("=" * 64)
    return n_fail == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
