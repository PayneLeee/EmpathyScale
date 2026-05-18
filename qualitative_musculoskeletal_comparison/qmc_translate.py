"""Chinese translations for qualitative report (cache + optional LLM fill)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

PKG_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PKG_ROOT.parent
ZH_PATH = PKG_ROOT / "data" / "zh_strings.json"


def load_zh_bundle() -> Dict[str, Any]:
    if ZH_PATH.exists():
        return json.loads(ZH_PATH.read_text(encoding="utf-8"))
    return {"dimensions": {}, "items": {}, "comparison_rows": {}, "similar_pairs": {}}


def save_zh_bundle(bundle: Dict[str, Any]) -> None:
    ZH_PATH.parent.mkdir(parents=True, exist_ok=True)
    ZH_PATH.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")


def _normalize_lookup_key(text: str) -> str:
    s = text.strip()
    for old, new in (
        ("\u2019", "'"),
        ("\u2018", "'"),
        ("\u201c", '"'),
        ("\u201d", '"'),
        ("\u2011", "-"),
        ("\u2013", "-"),
        ("\u2212", "-"),
        ("\u00a0", " "),
    ):
        s = s.replace(old, new)
    return " ".join(s.split())


def _lookup_item(bundle: Dict[str, Any], text: str) -> Optional[str]:
    items = bundle.get("items", {})
    raw = text.strip()
    if raw in items:
        return items[raw]
    norm = _normalize_lookup_key(raw)
    if norm in items:
        return items[norm]
    for key, val in items.items():
        if _normalize_lookup_key(key) == norm:
            return val
    return None


def translate_text(text: str, bundle: Dict[str, Any]) -> str:
    if not text or not text.strip():
        return text
    hit = _lookup_item(bundle, text)
    if hit:
        return hit
    for section in ("comparison_rows", "similar_pairs"):
        sub = bundle.get(section, {})
        if isinstance(sub, dict):
            for group in sub.values():
                if isinstance(group, dict) and text.strip() in group:
                    return group[text.strip()]
    return text


def _norm_dim_key(dim: str) -> str:
    return dim.replace("\u2011", "-").replace("\u2013", "-").replace("\u2212", "-")


def translate_dimension(dim: str, bundle: Dict[str, Any]) -> str:
    dims = bundle.get("dimensions", {})
    if dim in dims:
        return dims[dim]
    norm = _norm_dim_key(dim)
    if norm in dims:
        return dims[norm]
    return dim


def apply_zh_to_items(items: List[Dict[str, str]], bundle: Dict[str, Any]) -> List[Dict[str, str]]:
    out = []
    for it in items:
        text = it.get("item_text", "")
        dim = it.get("dimension", "—")
        out.append({
            **it,
            "item_text_en": text,
            "item_text": translate_text(text, bundle),
            "dimension_en": dim,
            "dimension": translate_dimension(dim, bundle),
        })
    return out


def fill_missing_via_llm(missing: List[str], bundle: Dict[str, Any]) -> Dict[str, Any]:
    if not missing:
        return bundle
    sys.path.insert(0, str(PROJECT_ROOT))
    sys.path.insert(0, str(PROJECT_ROOT / "agents"))
    from langchain_openai import ChatOpenAI
    from agents.interview_agent_group import load_config

    cfg = load_config(str(PROJECT_ROOT / "config.json"))
    llm = ChatOpenAI(
        api_key=cfg["openai_api_key"],
        model_name=cfg["model_name"],
        base_url=cfg.get("api_base") or None,
        temperature=0.2,
        timeout=120.0,
    )
    payload = json.dumps(missing, ensure_ascii=False, indent=2)
    prompt = (
        "将下列人机协作量表条目译为简体中文（工厂装配、共享料架场景）。\n"
        "要求：保留已有中文引号内容；语气适合李克特同意量表；每条一行对应。\n"
        "仅返回 JSON 数组，与输入顺序一致，不要其它文字。\n\n"
        f"{payload}"
    )
    resp = llm.invoke(prompt)
    raw = resp.content if hasattr(resp, "content") else str(resp)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    translations = json.loads(raw)
    if len(translations) != len(missing):
        raise ValueError(f"LLM returned {len(translations)} translations for {len(missing)} items")
    for src, zh in zip(missing, translations):
        bundle.setdefault("items", {})[src] = zh.strip()
    save_zh_bundle(bundle)
    return bundle


def ensure_bundle_for_texts(texts: List[str], use_llm: bool = True) -> Dict[str, Any]:
    bundle = load_zh_bundle()
    missing_items = sorted({
        t.strip() for t in texts
        if t.strip() and not _lookup_item(bundle, t.strip()) and not bundle.get("dimensions", {}).get(t.strip())
    })
    if missing_items and use_llm:
        print(f"Translating {len(missing_items)} missing strings via LLM...", flush=True)
        bundle = fill_missing_via_llm(missing_items, bundle)
    return bundle
