"""
LLM-based simulated interviewee for end-to-end pipeline testing.

This module is NOT imported by main.py or any agent code. Use only from
scripts/run_pipeline_fake_user.py (or your own driver outside the core package).

Requires: langchain-openai (same as the rest of EmpathyScale).
"""

from __future__ import annotations

from typing import List

from langchain_openai import ChatOpenAI


class FakeInterviewUser:
    """
    Callable: (last_agent_message: str) -> str

    ``work_scenario`` is the **ground truth** for consistency, but the persona does
    not "hand in the full form" on turn one: they answer like someone who does not
    know what will be asked next.

    Keeps an internal transcript of what the fake user already said so later turns
    stay consistent without repeating everything.
    """

    _SYSTEM = """You are **not** filling out a questionnaire. You are an ordinary practitioner (e.g. shop-floor lead, engineer, lab researcher) in a **live** chat with an interviewer. You have **no idea** what they will ask after this message.

## Your real situation (private memory — use for facts only; **never dump this whole block in a single reply**)
---
{work_scenario}
---

## How to answer
- Use the **same language** as the interviewer (Chinese or English).
- Reply **only** to what they are asking **right now**. One question → one slice of information.
- **Do not** preempt topics they have not asked about yet: full robot specs, exact environment layout, **how** human and robot communicate (voice, screen, gestures, haptics, lights, etc.), or teamwork structure—**wait** until a question clearly targets that.
- **Opening / broad “what scenario?”**: In **2–3 short sentences**, say **only** the main human–robot task and who does roughly what. You may say “we use a robot” in passing; **do not** list modalities, sensors, room details, or empathy-measurement goals unless they ask.
- **Later turns**: Add **new** facts from private memory when the question calls for them. If you already touched a topic, add **one** level of detail or a short confirmation—no essay.
- **Length**: usually **1–4 short sentences** unless they explicitly ask for a list.
- Do **not** say you are an AI or a language model.
- Output **only** what you would say aloud (no “User:”, no markdown fences)."""

    def __init__(
        self,
        api_key: str,
        work_scenario: str,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.55,
    ):
        if not (work_scenario or "").strip():
            raise ValueError("work_scenario must be non-empty")
        self._llm = ChatOpenAI(
            api_key=api_key,
            model_name=model_name,
            temperature=temperature,
        )
        self._system = self._SYSTEM.format(work_scenario=work_scenario.strip())
        self._reply_history: List[str] = []

    def __call__(self, last_agent_message: str) -> str:
        text = (last_agent_message or "").strip()
        prior_block = ""
        if self._reply_history:
            lines = []
            for i, r in enumerate(self._reply_history[-6:], start=1):
                snippet = r if len(r) <= 320 else r[:317] + "…"
                lines.append(f"{i}. {snippet}")
            prior_block = (
                "Earlier in this interview **you** (the interviewee) already said:\n"
                + "\n".join(lines)
                + "\n\nDo **not** repeat all of that. Only add what this **latest** interviewer message asks for, "
                "or briefly clarify if they ask about something you already mentioned.\n\n"
            )

        prompt = (
            f"{prior_block}"
            "The interviewer just said:\n---\n"
            f"{text}\n---\n\n"
            "Your reply (plain text only, as the interviewee):"
        )
        msg = self._llm.invoke(
            [
                ("system", self._system),
                ("human", prompt),
            ]
        )
        out = (getattr(msg, "content", None) or "").strip()
        if out:
            self._reply_history.append(out)
        return out


def load_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
