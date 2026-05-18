"""
Run 5 single-prompt direct LLM scale generations (same model as main pipeline).
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PKG_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "agents"))

from langchain_openai import ChatOpenAI  # noqa: E402

from agents.interview_agent_group import load_config  # noqa: E402

sys.path.insert(0, str(PKG_ROOT))
from direct_llm_prompt import build_direct_prompt_payload  # noqa: E402
from qmc_utils import (  # noqa: E402
    PKG_ROOT,
    parse_scale_markdown,
    save_json,
    load_json,
    scenario_text_from_interview,
)

N_RUNS = 5
SEEDS = [42, 43, 44, 45, 46]


def main() -> None:
    cfg = load_config(str(PROJECT_ROOT / "config.json"))
    scenario_path = PKG_ROOT / "data" / "scenario_input.json"
    if not scenario_path.exists():
        raise FileNotFoundError(f"Missing {scenario_path}; run build_report.py --init-data first")

    scenario = load_json(scenario_path)
    scenario_text = scenario.get("scenario_text") or scenario_text_from_interview(scenario)

    llm = ChatOpenAI(
        api_key=cfg["openai_api_key"],
        model_name=cfg["model_name"],
        base_url=cfg.get("api_base") or None,
        temperature=0.85,
        timeout=180.0,
    )

    runs_dir = PKG_ROOT / "direct_llm_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    prompt_payload = build_direct_prompt_payload(scenario_text)
    (runs_dir / "prompt_used.txt").write_text(prompt_payload["filled"], encoding="utf-8")
    save_json(
        runs_dir / "prompt_meta.json",
        {
            "model": cfg["model_name"],
            "temperature": prompt_payload["temperature"],
            "seeds": SEEDS[:N_RUNS],
            "scenario_source": str(scenario_path),
        },
    )
    manifest = []

    for i, seed in enumerate(SEEDS[:N_RUNS], start=1):
        run_id = f"run_{i:02d}"
        run_dir = runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        print(f"[{i}/{N_RUNS}] Generating {run_id} (seed={seed})...", flush=True)

        llm_seed = llm.bind(seed=seed) if hasattr(llm, "bind") else llm
        prompt = prompt_payload["filled"]
        try:
            resp = llm_seed.invoke(prompt)
            md = resp.content if hasattr(resp, "content") else str(resp)
        except Exception as e:
            md = f"# Error\n\nGeneration failed: {e}"
            print(f"  WARN: {e}", flush=True)

        (run_dir / "scale_draft.md").write_text(md, encoding="utf-8")
        items = parse_scale_markdown(md)
        meta = {
            "run_id": run_id,
            "seed": seed,
            "model": cfg["model_name"],
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "n_items_parsed": len(items),
            "n_dimensions": len({i["dimension"] for i in items}),
        }
        save_json(run_dir / "meta.json", meta)
        manifest.append(meta)
        print(f"  -> {len(items)} items, {meta['n_dimensions']} dimensions", flush=True)

    save_json(runs_dir / "manifest.json", {"runs": manifest, "n_runs": N_RUNS})
    print("Done. Run: python qualitative_musculoskeletal_comparison/build_report.py", flush=True)


if __name__ == "__main__":
    main()
