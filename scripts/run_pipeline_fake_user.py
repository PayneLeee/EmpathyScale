#!/usr/bin/env python3
"""
Run the full EmpathyScale pipeline without human input: an LLM plays the interviewee.

**Standalone entry** — not used by `python main.py`. Keeps core behavior unchanged.

Usage (from repository root):

  python scripts/run_pipeline_fake_user.py --scenario-file scripts/example_fake_scenario.txt
  python scripts/run_pipeline_fake_user.py --scenario-text "We use a mobile robot in ..."

Options:
  --max-turns   Safety cap for automated interview loop (default 80)
  --config      Path to config.json (default: project root config.json)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Repository root (parent of scripts/)
ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# So `import fake_interview_user` resolves to scripts/fake_interview_user.py
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Ensure imports match main.py (agents/, utils/)
sys.path.insert(0, str(ROOT / "agents"))
sys.path.insert(0, str(ROOT / "utils"))
os.chdir(ROOT)

from interview_agent_group import load_config  # noqa: E402
from main import MultiAgentWorkflow  # noqa: E402

from fake_interview_user import FakeInterviewUser, load_text_file  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Full pipeline with LLM fake interview user.")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument(
        "--scenario-file",
        type=str,
        help="UTF-8 text file describing the fake user's work / HRI scenario",
    )
    src.add_argument(
        "--scenario-text",
        type=str,
        help="Inline scenario description (quote for spaces)",
    )
    parser.add_argument("--config", type=str, default=None, help="config.json path")
    parser.add_argument("--max-turns", type=int, default=80, help="Max automated interview turns")
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o-mini",
        help="OpenAI model for the fake user (separate from agent models)",
    )
    args = parser.parse_args()

    if args.scenario_file:
        scenario = load_text_file(args.scenario_file)
    else:
        scenario = args.scenario_text

    config = load_config(args.config)
    api_key = config["openai_api_key"]

    fake = FakeInterviewUser(api_key=api_key, work_scenario=scenario, model_name=args.model)

    print("=" * 60)
    print("EmpathyScale — automated run (LLM fake interview user)")
    print("Core entry `main.py` is unchanged; this script is optional.")
    print("=" * 60)

    workflow = MultiAgentWorkflow(config_path=args.config)
    workflow.run_interview_session(
        user_input_factory=fake,
        max_automated_turns=args.max_turns,
    )


if __name__ == "__main__":
    main()
