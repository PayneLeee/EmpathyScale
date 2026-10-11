"""
incentive_loop.py — 以量表得分为奖励，迭代被评模型的 system prompt

这是"以评估为激励迭代模型"的免训练实现（prompt 层爬山法）：
  1. 当前最优 system prompt → 被评模型回应 → GLM 按量表打分 → reward
  2. 用 GLM 对最优 prompt 做变异（生成 K 个候选，强调不同共情侧面）
  3. 每个候选走 1 的流程，reward 最高者若超过当前最优则替换
  4. 重复 iters 轮；全程落盘轨迹

被评模型若要真正"更新权重"，可把 (system_prompt, 情境, 回应, reward) 轨迹
作为偏好数据做 DPO/LoRA —— CPU 上 0.5B 模型可承受极小规模，见 README。
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from judge import GLMJudge, SUBJECT_PROMPT_DEFAULT, aggregate, _glm_chat

MUTATION_ASPECTS = [
    "更强调情绪识别：先命名用户的情绪再回应",
    "更强调倾听与陪伴：少给建议，多表达在场与耐心",
    "更强调记忆与关切：回应用户之前提到的个人情况",
    "更强调语气温和：使用更柔软、更慢节奏的表达",
]


class PromptIncentiveLoop:
    def __init__(self, judge: GLMJudge, scale: list[dict], scenarios: list[str],
                 subject, out_dir: Path, iters: int = 2, k_mutants: int = 2):
        self.judge = judge
        self.scale = scale
        self.scenarios = scenarios
        self.subject = subject
        self.out_dir = out_dir
        self.iters = iters
        self.k = k_mutants
        self.trace = []

    # ---- 评估一个 prompt：所有情境 × 全量表 ----
    def evaluate_prompt(self, prompt: str, tag: str) -> dict:
        per_scenario = []
        for sc in self.scenarios:
            reply = self.subject.respond(prompt, sc)
            scores = self.judge.score_response(reply, sc, self.scale)
            per_scenario.append({"scenario": sc, "reply": reply, "scores": scores})
        agg = aggregate(per_scenario, scale=self.scale)
        rec = {"tag": tag, "prompt": prompt, "reward": agg["total"],
               "detail": agg, "per_scenario": per_scenario}
        self.trace.append(rec)
        return rec

    # ---- 用 GLM 生成 prompt 变异体 ----
    def mutate(self, best_prompt: str, aspect: str) -> str:
        text = _glm_chat(self.judge.model, [{"role": "user", "content":
            f"请把下面这个家庭陪伴机器人的 system prompt 改写得更能体现：{aspect}。\n"
            f"保持中文，长度不超过 120 字，只输出改写后的 prompt 本身。\n\n"
            f"{best_prompt}"}], temperature=0.8)
        return (text or best_prompt).strip()

    def run(self) -> dict:
        t0 = time.time()
        best = self.evaluate_prompt(SUBJECT_PROMPT_DEFAULT, tag="baseline")
        print(f"[loop] baseline reward = {best['reward']}")
        for it in range(1, self.iters + 1):
            aspect = MUTATION_ASPECTS[(it - 1) % len(MUTATION_ASPECTS)]
            cands = []
            for k in range(self.k):
                mp = self.mutate(best["prompt"], aspect)
                rec = self.evaluate_prompt(mp, tag=f"iter{it}-mut{k}")
                cands.append(rec)
                print(f"[loop] iter{it}-mut{k} reward = {rec['reward']}  "
                      f"(aspect: {aspect[:18]}…)")
            top = max(cands, key=lambda r: r["reward"])
            if top["reward"] > best["reward"]:
                print(f"[loop] iter{it}: {best['reward']} -> {top['reward']}  KEEP ✓")
                best = top
            else:
                print(f"[loop] iter{it}: 无提升，保留当前最优")
        best["elapsed_sec"] = round(time.time() - t0, 1)
        self._save(best)
        return best

    def _save(self, best: dict):
        self.out_dir.mkdir(parents=True, exist_ok=True)
        payload = {"best": {k: best[k] for k in ("tag", "prompt", "reward", "detail")},
                   "iters": self.iters, "trace": self.trace}
        json.dump(payload, open(self.out_dir / "incentive_trace.json", "w",
                                encoding="utf-8"), ensure_ascii=False, indent=2)
        md = ["# LLM 共情评估 — 激励迭代轨迹", "",
              f"- 被评模型: `{type(self.subject).__name__}`",
              f"- 评审: GLM 按 {len(self.scale)} 题量表",
              f"- 最优 reward: **{best['reward']}**（{best['tag']}）", "",
              "## 最优 system prompt", "", "```", best["prompt"], "```", "",
              "## 全部轨迹", "", "| tag | reward |", "|---|---|"]
        for t in self.trace:
            md.append(f"| {t['tag']} | {t['reward']} |")
        (self.out_dir / "incentive_trace.md").write_text("\n".join(md), encoding="utf-8")
