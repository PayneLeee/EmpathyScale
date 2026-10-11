# Optional automation scripts

These files are **not** imported by `main.py` or the agent packages. They exist for **testing / demos** only.

## Full pipeline with LLM fake interviewee

Uses the same `MultiAgentWorkflow` as interactive mode, but supplies an LLM-generated user instead of `input()`.

```bash
# From repository root
python scripts/run_pipeline_fake_user.py --scenario-file scripts/example_fake_scenario.txt
```

Requires `config.json` with `openai_api_key` (same as normal runs).

## Core project

- Normal human run: `python main.py` (unchanged).
- The only core change is an **optional** `user_input_factory` argument on `MultiAgentWorkflow.run_interview_session()`; default remains stdin.

## `fake_interview_user.py`

Self-contained helper: `FakeInterviewUser(api_key, work_scenario)` callable as `factory(last_agent_message) -> str`.

You can copy this file **outside the repo** into your own driver; pass a factory with the same signature into `run_interview_session` if you keep a checkout of `main.py` with that hook.
