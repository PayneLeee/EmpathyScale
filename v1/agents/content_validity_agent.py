"""
Content Validity Agent (CVI)
基于 Boateng 量表开发流程 Step 2：内容效度评估

让多个 LLM 扮演专家，对生成的题项进行内容效度评分，计算：
- I-CVI (Item-level Content Validity Index)：每个题项被评为"相关"的专家比例
- S-CVI (Scale-level Content Validity Index)：所有题项的平均 I-CVI
- 剔除 I-CVI < 0.78 的题项（标准参考：Polit & Beck, 2006）
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from utils.llm_client import create_llm
from utils.prompt_manager import PromptManager


@dataclass
class CVIResult:
    """单个题项的内容效度评估结果"""
    item_id: int
    item_text: str
    dimension: str
    expert_scores: List[int]
    i_cvi: float
    is_relevant: bool
    expert_comments: List[str] = field(default_factory=list)


@dataclass
class CVISummary:
    """整体内容效度评估汇总"""
    item_results: List[CVIResult]
    scale_cvi: float
    items_removed: List[int]
    items_kept: List[int]
    all_expert_comments: Dict[int, List[str]] = field(default_factory=dict)


class ContentValidityAgent:
    """
    内容效度评估 Agent
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        n_experts: int = 5,
        cvi_threshold: float = 0.78,
        max_workers: int = 3,
        prompts_dir: Optional[str] = None,
    ):
        self.llm = create_llm(api_key=api_key, model_name=model_name)
        self.n_experts = n_experts
        self.cvi_threshold = cvi_threshold
        self.max_workers = max_workers
        self.prompt_manager = PromptManager(prompts_dir)

    def evaluate_items(
        self,
        items: List[Dict[str, Any]],
        dimensions: List[Dict[str, str]],
        scenario: Dict[str, Any],
    ) -> CVISummary:
        if not items:
            return CVISummary(
                item_results=[],
                scale_cvi=0.0,
                items_removed=[],
                items_kept=[],
            )

        for idx, item in enumerate(items, 1):
            item.setdefault("item_id", idx)

        print(f"[CVI] 开始评估 {len(items)} 个题项，{self.n_experts} 位专家...")

        item_results: List[CVIResult] = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self._evaluate_single_item,
                    item,
                    dimensions,
                    scenario,
                ): item
                for item in items
            }
            for future in as_completed(futures):
                result = future.result()
                item_results.append(result)
                status = "✅ 保留" if result.is_relevant else "❌ 剔除"
                print(f"[CVI] Item {result.item_id}: I-CVI={result.i_cvi:.2f} {status}")

        # S-CVI (universal agreement) = 平均 I-CVI 覆盖全部题项，而非仅保留项
        scale_cvi = sum(r.i_cvi for r in item_results) / len(item_results) if item_results else 0.0
        items_removed = [r.item_id for r in item_results if not r.is_relevant]
        items_kept = [r.item_id for r in item_results if r.is_relevant]

        print(f"[CVI] 评估完成: S-CVI={scale_cvi:.3f}, 保留 {len(items_kept)}/{len(items)} 个题项")

        return CVISummary(
            item_results=item_results,
            scale_cvi=scale_cvi,
            items_removed=items_removed,
            items_kept=items_kept,
        )

    def _evaluate_single_item(
        self,
        item: Dict[str, Any],
        dimensions: List[Dict[str, str]],
        scenario: Dict[str, Any],
    ) -> CVIResult:
        item_id = item.get("item_id", 0)
        item_text = item.get("item_text", "")
        item_dimension = item.get("dimension", "")

        dimension_desc = ""
        for d in dimensions:
            if d.get("name") == item_dimension:
                dimension_desc = d.get("description", "")
                break

        prompt = self._build_expert_prompt(item_text, item_dimension, dimension_desc, scenario)

        scores: List[int] = []
        comments: List[str] = []
        for expert_idx in range(self.n_experts):
            score, comment = self._get_expert_rating(prompt, expert_idx)
            scores.append(score)
            comments.append(comment)

        relevant_count = sum(1 for s in scores if s >= 3)
        i_cvi = relevant_count / self.n_experts
        is_relevant = i_cvi >= self.cvi_threshold

        return CVIResult(
            item_id=item_id,
            item_text=item_text,
            dimension=item_dimension,
            expert_scores=scores,
            i_cvi=i_cvi,
            is_relevant=is_relevant,
            expert_comments=comments,
        )

    def _build_expert_prompt(
        self,
        item_text: str,
        dimension: str,
        dimension_desc: str,
        scenario: Dict[str, Any],
    ) -> str:
        template = None
        try:
            template = self.prompt_manager.prompts.get("content_validity", {}).get("template")
        except Exception:
            template = None

        if template:
            return self.prompt_manager.get_agent_prompt(
                "content_validity", "template",
                item_text=item_text,
                dimension=dimension,
                dimension_desc=dimension_desc,
                scenario=json.dumps(scenario, ensure_ascii=False, indent=2),
            )

        return f"""
你是一位量表开发领域的专家。请评估以下题项是否适合测量「{dimension}」这个维度。

## 场景背景
{json.dumps(scenario, ensure_ascii=False, indent=2)}

## 维度定义
{dimension_desc}

## 待评估题项
"{item_text}"

## 评分标准
请给出 1-4 分的评分：
- 1 = 不相关：题项与维度完全无关
- 2 = 需大改：题项与维度有一定关联，但需要大幅修改
- 3 = 需小改：题项与维度高度相关，但需要小幅修改措辞
- 4 = 高度相关：题项准确反映了维度内容，无需修改

## 输出格式（仅输出 JSON）
{{"score": 3, "comment": "简洁的修改建议或理由"}}
"""

    def _get_expert_rating(self, prompt: str, expert_idx: int) -> Tuple[int, str]:
        try:
            response = self.llm.invoke(prompt)
            content = getattr(response, "content", str(response)).strip()

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            data = json.loads(content)
            score = int(data.get("score", 0))
            comment = data.get("comment", "")

            if score < 1 or score > 4:
                score = 0

            return score, comment
        except Exception as e:
            print(f"[CVI] 专家 {expert_idx + 1} 评分失败: {e}")
            return 0, f"评分失败: {e}"

    def generate_report(self, summary: CVISummary) -> str:
        lines: List[str] = []
        lines.append("=" * 60)
        lines.append("内容效度评估报告 (Content Validity Index)")
        lines.append("=" * 60)
        lines.append(f"\nS-CVI (量表水平内容效度指数): {summary.scale_cvi:.3f}")
        lines.append(f"评估标准: I-CVI >= {self.cvi_threshold} 为保留")
        lines.append(f"专家数量: {self.n_experts}")
        lines.append(f"\n题项统计:")
        lines.append(f"  - 总题项: {len(summary.item_results)}")
        lines.append(f"  - 保留题项: {len(summary.items_kept)}")
        lines.append(f"  - 剔除题项: {len(summary.items_removed)}")

        if summary.items_removed:
            lines.append(f"\n剔除题项 (I-CVI < {self.cvi_threshold}):")
            for r in summary.item_results:
                if not r.is_relevant:
                    lines.append(f"  - Item {r.item_id}: {r.item_text[:50]}... (I-CVI={r.i_cvi:.2f})")

        lines.append("\n" + "=" * 60)
        lines.append("详细结果:")
        for r in summary.item_results:
            status = "✅" if r.is_relevant else "❌"
            lines.append(f"  {status} Item {r.item_id}: I-CVI={r.i_cvi:.2f}, 专家评分={r.expert_scores}")

        return "\n".join(lines)
