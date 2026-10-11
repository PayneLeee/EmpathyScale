"""
psychometric_feedback.py — 心理测量诊断与奖励信号（自激励回路的核心）

把量表的心理测量质量变成可优化的标量奖励：
    reward = w_a * min(alpha / 0.8, 1)          # 信度门控（α≥0.8）
           + w_l * mean(max|loading| per item)  # 维度归属清晰度
           + w_d * min(d / 2.0, 1)              # 区分效度（empathic vs non-empathic）

并给出逐题诊断（题总相关、最大因子载荷、α-if-deleted），用于挑选"最弱题项"
交给 ItemRefinementAgent 重写。
"""
from __future__ import annotations

from typing import Dict, List, Sequence

import numpy as np
import pandas as pd

try:
    from sklearn.decomposition import FactorAnalysis
    SKLEARN_OK = True
except ImportError:  # pragma: no cover
    SKLEARN_OK = False


# --------------------------------------------------------------------------- #
# 基础统计
# --------------------------------------------------------------------------- #
def cronbach_alpha(df: pd.DataFrame) -> float:
    """Cronbach's α on items (columns) × respondents (rows). NaN → pairwise impute by item mean."""
    X = df.apply(lambda c: c.fillna(c.mean()))
    k = X.shape[1]
    if k < 2:
        return float("nan")
    item_var = X.var(ddof=1, axis=0).sum()
    total_var = X.sum(axis=1).var(ddof=1)
    if total_var <= 0:
        return float("nan")
    return float(k / (k - 1) * (1 - item_var / total_var))


def alpha_if_deleted(df: pd.DataFrame) -> Dict[str, float]:
    return {c: cronbach_alpha(df.drop(columns=[c])) for c in df.columns}


def item_total_correlations(df: pd.DataFrame) -> Dict[str, float]:
    """Corrected item-total correlation (item vs sum-of-others)."""
    out = {}
    for c in df.columns:
        rest = df.drop(columns=[c]).apply(lambda s: s.fillna(s.mean()), axis=1)
        total = rest.sum(axis=1)
        out[c] = float(df[c].corr(total))
    return out


def max_loadings(df: pd.DataFrame, n_factors: int = 2) -> Dict[str, float]:
    """Per-item maximum |factor loading| via sklearn FactorAnalysis."""
    if not SKLEARN_OK:
        return {c: float("nan") for c in df.columns}
    X = df.apply(lambda c: c.fillna(c.mean()))
    X = (X - X.mean()) / X.std().replace(0, 1)
    n_factors = max(1, min(n_factors, X.shape[1] - 1, X.shape[0] - 1))
    try:
        fa = FactorAnalysis(n_components=n_factors, random_state=0)
        fa.fit(X.values)
        load = np.abs(fa.components_.T)  # items × factors
        return {c: float(load[i].max()) for i, c in enumerate(df.columns)}
    except Exception:
        return {c: float("nan") for c in df.columns}


def discriminant_d(df: pd.DataFrame, group_flags: Sequence[bool]) -> float:
    """Cohen's d between empathic (True) and non-empathic (False) total scores."""
    total = df.apply(lambda s: s.fillna(s.mean()), axis=1).sum(axis=1).values  # 按位置取
    flag_arr = np.asarray(group_flags, dtype=bool)
    if len(total) != len(flag_arr):
        return float("nan")
    g1 = total[flag_arr]
    g0 = total[~flag_arr]
    if len(g1) < 2 or len(g0) < 2:
        return float("nan")
    n1, n0 = len(g1), len(g0)
    s_pooled = np.sqrt(((n1 - 1) * g1.var(ddof=1) + (n0 - 1) * g0.var(ddof=1)) / (n1 + n0 - 2))
    if s_pooled == 0:
        return float("nan")
    return float((g1.mean() - g0.mean()) / s_pooled)


# --------------------------------------------------------------------------- #
# 奖励信号与诊断
# --------------------------------------------------------------------------- #
DEFAULT_WEIGHTS = {"alpha": 0.4, "loading": 0.4, "discriminant": 0.2}


def scale_reward(df: pd.DataFrame,
                 group_flags: Sequence[bool],
                 n_factors: int = 2,
                 weights: Dict[str, float] = None) -> Dict[str, float]:
    """Composite reward ∈ [0, 1]（分量含义见模块 docstring）。"""
    w = dict(DEFAULT_WEIGHTS, **(weights or {}))
    a = cronbach_alpha(df)
    d = discriminant_d(df, group_flags)
    loads = max_loadings(df, n_factors=n_factors)
    mean_load = float(np.nanmean(list(loads.values()))) if loads else float("nan")

    def gate(x, target):
        return float("nan") if pd.isna(x) else float(min(max(x / target, 0.0), 1.0))

    parts = {
        "alpha_part": gate(a, 0.8) * w["alpha"],
        "loading_part": gate(mean_load, 0.5) * w["loading"],
        "discriminant_part": gate(d, 2.0) * w["discriminant"],
        "alpha": a,
        "mean_max_loading": mean_load,
        "discriminant_d": d,
    }
    parts["reward"] = float(np.nansum([parts["alpha_part"], parts["loading_part"],
                                       parts["discriminant_part"]]))
    return parts


def diagnose_items(df: pd.DataFrame, n_factors: int = 2) -> pd.DataFrame:
    """逐题诊断表：题总相关 / 最大载荷 / α-if-deleted / 均值 / 方差。"""
    itc = item_total_correlations(df)
    loads = max_loadings(df, n_factors=n_factors)
    aid = alpha_if_deleted(df)
    rows = []
    for c in df.columns:
        rows.append({
            "item_id": int(c) if str(c).lstrip("-").isdigit() else c,
            "item_total_r": round(itc[c], 3) if pd.notna(itc[c]) else np.nan,
            "max_loading": round(loads[c], 3) if pd.notna(loads[c]) else np.nan,
            "alpha_if_deleted": round(aid[c], 3) if pd.notna(aid[c]) else np.nan,
            "mean": round(float(df[c].mean()), 2),
            "std": round(float(df[c].std()), 2),
            "n_missing": int(df[c].isna().sum()),
        })
    out = pd.DataFrame(rows)
    # 弱题排序：低载荷优先，其次低题总相关
    out["weak_score"] = (out["max_loading"].fillna(0) + out["item_total_r"].fillna(0))
    return out.sort_values("weak_score").reset_index(drop=True)


def pick_weak_items(diag: pd.DataFrame, k: int,
                    min_loading: float = 0.40) -> List[int]:
    """挑 k 个最值得重写的题项 id：先取载荷不达标的，不够再取最弱的。"""
    weak = diag[diag["max_loading"].fillna(0) < min_loading]
    ids = weak["item_id"].astype(int).tolist() if len(weak) else []
    if len(ids) < k:
        extra = diag[~diag["item_id"].isin(ids)]["item_id"].astype(int).tolist()
        ids.extend(extra[: k - len(ids)])
    return ids[:k]
