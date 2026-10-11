import json
import sys
sys.path.append('.')
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.llm_client import create_llm
from utils.prompt_manager import PromptManager

class PretestAgent:
    """
    预测试 Agent
    模拟真实用户试填题项，检测题项是否存在歧义。
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None, max_workers: int = 3):
        self.llm = create_llm(api_key=api_key, model_name=model_name)
        self.max_workers = max_workers
        self.prompt_manager = PromptManager()

    def detect_ambiguities(
        self,
        items: List[Dict[str, Any]],
        dimensions: List[Dict[str, str]],
        scenario: Dict[str, Any]
    ):
        """
        检测题项歧义
        返回：歧义报告，包含每个题项的疑似歧义、建议修改等
        """
        if not items:
            return {"ambiguities": [], "summary": "没有题项可检测"}

        print(f"[Pretest] 开始预测试，共 {len(items)} 个题项...")
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._pretest_one, item, dimensions, scenario): item
                for item in items
            }
            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        ambiguity_items = [r for r in results if r.get("has_ambiguity")]
        print(f"[Pretest] 完成，发现 {len(ambiguity_items)} 个存在歧义的题项")

        return {
            "results": results,
            "ambiguity_items": ambiguity_items,
            "total_items": len(items),
            "ambiguity_count": len(ambiguity_items)
        }

    def _pretest_one(self, item, dimensions, scenario):
        item_text = item.get("item_text", "")
        item_dimension = item.get("dimension", "")

        dimension_names = [d.get("name") for d in dimensions]

        prompt = self.prompt_manager.get_agent_prompt(
    "pretest",  # agent_name
    "template",  # prompt_key (prompts/pretest.json 的键是 "template")
    item_text=item_text,
    item_dimension=item_dimension,
    dimension_names=json.dumps(dimension_names, ensure_ascii=False),
    scenario=json.dumps(scenario, ensure_ascii=False)
)

        try:
            resp = self.llm.invoke(prompt)
            content = resp.content.strip()

            if "`json" in content:
                content = content.split("`json")[1].split("`")[0]
            elif "`" in content:
                content = content.split("`")[1].split("`")[0]

            data = json.loads(content)
            return {
                "item_id": item.get("item_id", 0),
                "item_text": item_text,
                "dimension": item_dimension,
                "has_ambiguity": data.get("has_ambiguity", False),
                "reason": data.get("reason", ""),
                "suggested_revision": data.get("suggested_revision", ""),
                "simulated_understanding": data.get("simulated_understanding", "")
            }
        except Exception as e:
            return {
                "item_id": item.get("item_id", 0),
                "item_text": item_text,
                "dimension": item_dimension,
                "has_ambiguity": True,
                "reason": f"预测试评估异常: {str(e)}",
                "suggested_revision": "待人工复核",
                "simulated_understanding": ""
            }

    def generate_pretest_report(self, pretest_result):
        """
        生成预测试报告
        """
        if not pretest_result or not pretest_result.get("results"):
            return "没有可用数据生成报告。"

        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("预测试歧义检测报告")
        report_lines.append("=" * 60)
        report_lines.append(f"总题项数: {pretest_result.get('total_items', 0)}")
        report_lines.append(f"存在歧义题项数: {pretest_result.get('ambiguity_count', 0)}")

        if pretest_result.get("ambiguity_items"):
            report_lines.append("\n存在歧义的题项：")
            for a in pretest_result["ambiguity_items"]:
                report_lines.append(f"\n--- Item {a.get('item_id')} ---")
                report_lines.append(f"题项: {a.get('item_text')}")
                report_lines.append(f"维度: {a.get('dimension')}")
                report_lines.append(f"模拟理解: {a.get('simulated_understanding')}")
                report_lines.append(f"歧义原因: {a.get('reason')}")
                report_lines.append(f"修改建议: {a.get('suggested_revision')}")
        else:
            report_lines.append("\n所有题项均未检测到明显歧义！")

        return "\n".join(report_lines)
