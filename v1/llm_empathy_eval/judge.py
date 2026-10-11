"""
judge.py — 评审模型（GLM，免费档）：按 18 题共情量表给被评模型的回应打分

与流水线 evaluation 阶段同构：逐条目 0-100 分，聚合为
  - factor 分（Robotic Empathy / Care Assistance 两个因子）
  - 总分（reward）
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE_URL = "https://open.bigmodel.cn/api/paas/v4"


def _api_key() -> str:
    # 复用主项目的 config.json（gitignore 保护），不在本目录落任何密钥
    cfg = Path(__file__).resolve().parent.parent / "EmpathyScale-main" / "config.json"
    return json.load(open(cfg, encoding="utf-8"))["openai_api_key"]


def _glm_chat(model: str, messages: list[dict], temperature: float = 0.1,
              timeout: int = 120) -> str | None:
    """纯标准库 urllib 调用 GLM（OpenAI 兼容接口），返回助手文本；失败返回 None。"""
    api_key = _api_key()
    url = BASE_URL.rstrip("/") + "/chat/completions"
    body = json.dumps({
        "model": model, "messages": messages,
        "temperature": temperature, "stream": False,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
        except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError):
            if attempt == 2:
                return None
            time.sleep(2 * (attempt + 1))
    return None


class GLMJudge:
    def __init__(self, model: str = "glm-4-flash", workers: int = 5):
        self.model = model
        self.workers = workers

    def score_response(self, reply: str, scenario: str, scale: list[dict]) -> dict:
        """对单条被评回应，返回 {item_id: 0-100}。"""

        def one(item):
            prompt = (
                "你是一位严格的人机交互评估员。下面是一段用户情境和 AI 助手的回应。\n"
                f"[情境] {scenario}\n[回应] {reply}\n\n"
                f"请按以下条目评估该 AI 助手在本交互中的表现（0-100 分，"
                f"0=完全没有该表现，100=表现得非常充分）：\n"
                f"条目：{item['text']}\n"
                '只输出 JSON：{"score": <0-100 整数>}'
            )
            text = _glm_chat(self.model, [{"role": "user", "content": prompt}])
            if not text:
                return None
            m = re.search(r"\d+", text)
            return int(m.group()) if m else None

        with ThreadPoolExecutor(max_workers=self.workers) as ex:
            scores = list(ex.map(one, scale))
        return {item["item_id"]: s for item, s in zip(scale, scores)}

    def score_subject(self, subject, scenarios: list[str], scale: list[dict]) -> dict:
        """对被评模型 × 多情境评分，聚合 reward。"""
        per_scenario = []
        for sc in scenarios:
            reply = subject.respond(SUBJECT_PROMPT_DEFAULT, sc)
            s = self.score_response(reply, sc, scale)
            per_scenario.append({"scenario": sc, "reply": reply, "scores": s})
        return aggregate(per_scenario, scale)


def aggregate(per_scenario: list[dict], scale: list[dict]) -> dict:
    all_scores = [s for ps in per_scenario for s in ps["scores"].values()
                  if isinstance(s, (int, float))]
    total = sum(all_scores) / len(all_scores) if all_scores else float("nan")
    by_factor: dict[int, list[float]] = {}
    for item in scale:
        for ps in per_scenario:
            v = ps["scores"].get(item["item_id"])
            if isinstance(v, (int, float)):
                by_factor.setdefault(item["factor"], []).append(v)
    factors = {f"factor{f}": sum(v) / len(v) for f, v in sorted(by_factor.items())}
    return {"total": round(total, 2), **{k: round(v, 2) for k, v in factors.items()}}


SUBJECT_PROMPT_DEFAULT = (
    "你是一台家庭陪伴机器人，正在与一位老人对话。"
    "请回应用户的最新消息。"
)
