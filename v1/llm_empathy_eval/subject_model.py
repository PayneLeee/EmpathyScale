"""
subject_model.py — 被评模型（"被试"换成被评估的 LLM）

后端：
  - StubSubject    : 离线桩，规则化回应（打通管道用，无下载）
  - QwenSubject    : Qwen2.5-0.5B-Instruct（CPU，~1GB，transformers + torch）
  - LlamaCppSubject: Qwen2.5-0.5B-Instruct 的 GGUF 量化版（CPU，llama-cpp-python，
                     无需 torch；本机沙箱拦截 torch 头文件安装时用此后端）

被评模型只做一件事：给定共情情境 + 自己的 system prompt（即"人格参数"），
生成一段陪伴式回应。回应质量随后由评审模型按共情量表打分。
"""
from __future__ import annotations

import json
import time
import urllib.request


class StubSubject:
    """离线桩：按 system prompt 中是否包含共情关键词给出"有共情/无共情"两种回应。"""

    EMPATHIC_MARKERS = ("共情", "情绪", "感受", "倾听", "理解", "陪伴", "安慰", "耐心")

    def __init__(self, seed: int = 0):
        import random
        self.rng = random.Random(seed)

    def respond(self, system_prompt: str, scenario: str) -> str:
        hits = sum(1 for m in self.EMPATHIC_MARKERS if m in system_prompt)
        if hits >= 2:
            return ("我能感受到您现在的难过，这确实不容易。"
                    "您愿意多说一点吗？我会一直在这里陪着您。")
        if hits == 1:
            return "请告诉我发生了什么，我可以提供一些建议。"
        return ("根据您提供的信息，建议如下：1. 保持规律作息；"
                "2. 适当运动；3. 如有需要请联系专业人士。")


class QwenSubject:
    """Qwen2.5-0.5B-Instruct，纯 CPU 推理（首次运行自动下载 ~1GB）。"""

    MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"

    def __init__(self, max_new_tokens: int = 120):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch  # noqa: F401  (确保 CPU torch 已安装)
        self.tok = AutoTokenizer.from_pretrained(self.MODEL_ID)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.MODEL_ID, torch_dtype="auto")
        self.model.eval()
        self.max_new_tokens = max_new_tokens

    def respond(self, system_prompt: str, scenario: str) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": scenario},
        ]
        text = self.tok.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tok([text], return_tensors="pt")
        import torch
        with torch.no_grad():
            out = self.model.generate(
                **inputs, max_new_tokens=self.max_new_tokens, do_sample=True,
                temperature=0.7, top_p=0.9)
        reply = self.tok.decode(out[0][inputs["input_ids"].shape[1]:],
                                skip_special_tokens=True)
        return reply.strip()


class LlamaCppSubject:
    """Qwen2.5-0.5B-Instruct 的 GGUF 量化版，纯 CPU 推理（llama-cpp-python，无需 torch）。

    首次运行自动从 HuggingFace 镜像下载 ~0.4GB 的 q4_k_m GGUF。
    选用 llama-cpp 的原因：本机沙箱拦截 torch 官方 wheel 的 C++ 头文件写入，
    导致 transformers+torch 路线装不上；而 GGUF 路线只依赖一个预编译的 llama_cpp
    扩展，无头文件、无 CUDA，正好能在无 GPU 的电脑上跑超小免费模型。
    """

    REPO_ID = "Qwen/Qwen2.5-0.5B-Instruct-GGUF"
    GGUF_FILE = "qwen2.5-0.5b-instruct-q4_k_m.gguf"

    def __init__(self, max_new_tokens: int = 120, n_threads: int | None = None):
        import os
        from llama_cpp import Llama
        from huggingface_hub import hf_hub_download

        os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
        model_path = hf_hub_download(repo_id=self.REPO_ID, filename=self.GGUF_FILE)
        self.llm = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=n_threads or max(1, (os.cpu_count() or 4) // 2),
            verbose=False,
        )
        self.max_new_tokens = max_new_tokens

    def respond(self, system_prompt: str, scenario: str) -> str:
        out = self.llm.create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": scenario},
            ],
            temperature=0.7,
            top_p=0.9,
            max_tokens=self.max_new_tokens,
        )
        return out["choices"][0]["message"]["content"].strip()


class GLMSubject:
    """被评模型 = GLM-4-Flash（API，免费、无需 GPU）。

    直接演示"LLM 当被试"：用 chat API 生成陪伴式回应，由 GLMJudge 按量表打分，
    再以分数为激励迭代其 system prompt。

    说明：本机沙箱拦截 torch 官方 wheel 的头文件写入、且 llama-cpp-python 在
    cp313 无预编译 wheel（需 CMake/C++ 编译链，本机缺失），故本地 Qwen/GGUF 路线
    装不上。GLMSubject 用同一个免费 API 充当"被评 LLM"，概念完全等价——
    subject 与 judge 都是 LLM，恰好最贴合 EmpathyScale 的"LLM 当被试 + LLM 当评委"
    主张。若日后环境允许本地推理，只需把 make_subject 换成 qwen/llamacpp 即可。
    """

    BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

    def __init__(self, model: str = "glm-4-flash", max_new_tokens: int = 120):
        from pathlib import Path
        cfg = Path(__file__).resolve().parent.parent / "EmpathyScale-main" / "config.json"
        self.api_key = json.load(open(cfg, encoding="utf-8"))["openai_api_key"]
        self.model = model
        self.max_new_tokens = max_new_tokens

    def respond(self, system_prompt: str, scenario: str) -> str:
        payload = {
            "model": self.model,
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": self.max_new_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": scenario},
            ],
        }
        req = urllib.request.Request(
            self.BASE_URL + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}",
                     "Content-Type": "application/json"},
            method="POST",
        )
        last_err = None
        for _ in range(3):
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    data = json.loads(r.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"].strip()
            except Exception as e:  # noqa: BLE001
                last_err = e
                time.sleep(2)
        return f"（被评模型调用失败：{last_err}）"


def make_subject(kind: str, **kw):
    if kind == "stub":
        return StubSubject(**kw)
    if kind == "qwen":
        return QwenSubject(**kw)
    if kind == "llamacpp":
        return LlamaCppSubject(**kw)
    if kind == "glm":
        return GLMSubject(**kw)
    raise ValueError(f"unknown subject kind: {kind}")
