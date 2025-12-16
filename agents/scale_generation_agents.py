"""
Lightweight agents for construct definition, item generation, and content assessment.
They wrap LLM calls using PromptManager prompts defined in prompts/scale_generation_support.json.
"""

import time
from typing import Dict, List, Any
from langchain_openai import ChatOpenAI
from openai import APIConnectionError

from utils.prompt_manager import PromptManager


def retry_llm_call(func, max_retries=3, delay=2):
    """Retry LLM call on connection errors."""
    for attempt in range(max_retries):
        try:
            return func()
        except (APIConnectionError, Exception) as e:
            if attempt < max_retries - 1:
                wait_time = delay * (attempt + 1)
                print(f"    [RETRY] Attempt {attempt + 1}/{max_retries} failed: {type(e).__name__}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"    [ERROR] All {max_retries} attempts failed: {type(e).__name__}: {str(e)[:100]}")
                raise


class ConstructDefinitionAgent:
    """Derive scenario-tailored empathy dimensions."""

    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini", prompts_dir: str = None):
        self.llm = ChatOpenAI(api_key=api_key, model_name=model_name, temperature=0.2)
        self.prompt_manager = PromptManager(prompts_dir)

    def define_constructs(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self.prompt_manager.get_agent_group_prompt("scale_generation_support", "construct_system_prompt")
        # Compose a compact context block
        context_lines = [
            f"assessment_context: {scenario.get('assessment_context', '')}",
            f"robot_platform: {scenario.get('robot_platform', '')}",
            f"interaction_modalities: {scenario.get('interaction_modalities', '')}",
            f"collaboration_pattern: {scenario.get('collaboration_pattern', '')}",
            f"environmental_setting: {scenario.get('environmental_setting', '')}",
            f"assessment_goals: {', '.join(scenario.get('assessment_goals', []))}",
            f"expected_empathy_forms: {', '.join(scenario.get('expected_empathy_forms', []))}",
        ]
        full_prompt = f"{prompt}\n\nScenario:\n" + "\n".join(context_lines)
        resp = retry_llm_call(lambda: self.llm.invoke(full_prompt).content.strip())
        return {"raw": resp}


class ItemGenerationAgent:
    """Generate candidate items given dimensions."""

    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini", prompts_dir: str = None):
        self.llm = ChatOpenAI(api_key=api_key, model_name=model_name, temperature=0.6)
        self.prompt_manager = PromptManager(prompts_dir)

    def generate_items(self, dimensions: List[Dict[str, str]], scenario: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self.prompt_manager.get_agent_group_prompt("scale_generation_support", "item_generation_prompt")
        scenario_text = "\n".join([
            f"assessment_context: {scenario.get('assessment_context', '')}",
            f"robot_platform: {scenario.get('robot_platform', '')}",
            f"interaction_modalities: {scenario.get('interaction_modalities', '')}",
            f"collaboration_pattern: {scenario.get('collaboration_pattern', '')}",
            f"environmental_setting: {scenario.get('environmental_setting', '')}",
        ])
        dim_lines = [f"- {d.get('name','')}: {d.get('description','')}" for d in dimensions]
        full_prompt = f"{prompt}\n\nScenario:\n{scenario_text}\n\nDimensions:\n" + "\n".join(dim_lines)
        resp = retry_llm_call(lambda: self.llm.invoke(full_prompt).content.strip())
        return {"raw": resp}


class ContentAssessmentAgent:
    """Refine and de-duplicate items."""

    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini", prompts_dir: str = None):
        self.llm = ChatOpenAI(api_key=api_key, model_name=model_name, temperature=0.3)
        self.prompt_manager = PromptManager(prompts_dir)

    def refine(self, candidates: List[Dict[str, Any]], scenario: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self.prompt_manager.get_agent_group_prompt("scale_generation_support", "content_assessment_prompt")
        scenario_text = "\n".join([
            f"assessment_context: {scenario.get('assessment_context', '')}",
            f"robot_platform: {scenario.get('robot_platform', '')}",
            f"interaction_modalities: {scenario.get('interaction_modalities', '')}",
            f"collaboration_pattern: {scenario.get('collaboration_pattern', '')}",
            f"environmental_setting: {scenario.get('environmental_setting', '')}",
        ])
        # Flatten candidate text for the prompt
        candidate_lines = []
        for block in candidates:
            dim = block.get("dimension") or block.get("name") or "Unknown"
            items = block.get("items") or []
            candidate_lines.append(f"Dimension: {dim}")
            for it in items:
                candidate_lines.append(f"- {it}")
        full_prompt = f"{prompt}\n\nScenario:\n{scenario_text}\n\nCandidates:\n" + "\n".join(candidate_lines)
        resp = retry_llm_call(lambda: self.llm.invoke(full_prompt).content.strip())
        return {"raw": resp}

