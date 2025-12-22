"""
Lightweight agents for construct definition, item generation, and content assessment.
They wrap LLM calls using PromptManager prompts defined in prompts/scale_generation_support.json.
"""

import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from openai import APIConnectionError

from utils.prompt_manager import PromptManager


def retry_llm_call(func, max_retries=3, base_delay=3):
    """
    Retry LLM call on connection errors with exponential backoff.
    
    Args:
        func: Function to call (should be a lambda that makes the API call)
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Base delay in seconds for exponential backoff (default: 3)
                    Delays will be: base_delay, base_delay*2, base_delay*4
    """
    import random
    
    for attempt in range(max_retries):
        try:
            return func()
        except (APIConnectionError, Exception) as e:
            if attempt < max_retries - 1:
                # Exponential backoff with jitter: base_delay * 2^attempt + random(0, 1)
                wait_time = base_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"    [RETRY] Attempt {attempt + 1}/{max_retries} failed: {type(e).__name__}. Retrying in {wait_time:.1f}s...", flush=True)
                time.sleep(wait_time)
            else:
                print(f"    [ERROR] All {max_retries} attempts failed: {type(e).__name__}: {str(e)[:100]}", flush=True)
                raise


class ConstructDefinitionAgent:
    """Derive scenario-tailored empathy dimensions."""

    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini", prompts_dir: str = None):
        self.llm = ChatOpenAI(api_key=api_key, model_name=model_name, temperature=0.2)
        self.prompt_manager = PromptManager(prompts_dir)
        self._expert_knowledge = None  # Cache expert knowledge

    def _load_expert_knowledge(self) -> str:
        """Load expert knowledge summary from JSON file.
        
        Returns:
            Expert knowledge summary string, or empty string if file not found or error occurs.
        """
        if self._expert_knowledge is not None:
            return self._expert_knowledge
        
        try:
            # Use prompts_dir from PromptManager to find expert_knowledge.json
            prompts_base = Path(self.prompt_manager.prompts_dir)
            knowledge_path = prompts_base / "expert_knowledge.json"
            
            if knowledge_path.exists():
                with open(knowledge_path, 'r', encoding='utf-8') as f:
                    knowledge = json.load(f)
                    summary = knowledge.get("summary", "")
                    self._expert_knowledge = summary
                    return summary
            else:
                # File doesn't exist, cache empty string to avoid repeated file system checks
                self._expert_knowledge = ""
                return ""
        except Exception as e:
            # On any error, return empty string and cache it to avoid repeated failures
            print(f"    [WARN] Failed to load expert knowledge: {e}", flush=True)
            self._expert_knowledge = ""
            return ""

    def define_constructs(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        prompt_template = self.prompt_manager.get_agent_group_prompt("scale_generation_support", "construct_system_prompt")
        
        # Load expert knowledge and inject into prompt if placeholder exists
        # Use replace() instead of format() to avoid conflicts with JSON examples in the prompt
        expert_knowledge = self._load_expert_knowledge()
        if "{expert_knowledge_summary}" in prompt_template:
            prompt = prompt_template.replace("{expert_knowledge_summary}", expert_knowledge)
        else:
            # If no placeholder, use template as-is (backward compatibility)
            prompt = prompt_template
        
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
        # Increase timeout for long prompts (item generation prompt is now very detailed with 10 semantic aspects)
        self.llm = ChatOpenAI(
            api_key=api_key, 
            model_name=model_name, 
            temperature=0.7,  # Increased from 0.6 to 0.7 for more diversity
            timeout=180.0  # 3 minutes timeout for long prompts (10 semantic aspects + scenario + dimensions)
        )
        self.prompt_manager = PromptManager(prompts_dir)
        self._expert_knowledge = None  # Cache expert knowledge

    def _load_expert_knowledge(self) -> str:
        """Load expert knowledge summary from JSON file.
        
        Returns:
            Expert knowledge summary string, or empty string if file not found or error occurs.
        """
        if self._expert_knowledge is not None:
            return self._expert_knowledge
        
        try:
            # Use prompts_dir from PromptManager to find expert_knowledge.json
            prompts_base = Path(self.prompt_manager.prompts_dir)
            knowledge_path = prompts_base / "expert_knowledge.json"
            
            if knowledge_path.exists():
                with open(knowledge_path, 'r', encoding='utf-8') as f:
                    knowledge = json.load(f)
                    summary = knowledge.get("summary", "")
                    self._expert_knowledge = summary
                    return summary
            else:
                # File doesn't exist, cache empty string to avoid repeated file system checks
                self._expert_knowledge = ""
                return ""
        except Exception as e:
            # On any error, return empty string and cache it to avoid repeated failures
            print(f"    [WARN] Failed to load expert knowledge: {e}", flush=True)
            self._expert_knowledge = ""
            return ""

    def generate_items(self, dimensions: List[Dict[str, str]], scenario: Dict[str, Any]) -> Dict[str, Any]:
        prompt_template = self.prompt_manager.get_agent_group_prompt("scale_generation_support", "item_generation_prompt")
        
        # Load expert knowledge and inject into prompt if placeholder exists
        # Use replace() instead of format() to avoid conflicts with JSON examples in the prompt
        expert_knowledge = self._load_expert_knowledge()
        if "{expert_knowledge_summary}" in prompt_template:
            prompt = prompt_template.replace("{expert_knowledge_summary}", expert_knowledge)
        else:
            # If no placeholder, use template as-is (backward compatibility)
            prompt = prompt_template
        
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
        # Increase timeout for large prompts (default is 60s, increase to 300s for 300+ items)
        self.llm = ChatOpenAI(
            api_key=api_key, 
            model_name=model_name, 
            temperature=0.3,
            timeout=300.0  # 5 minutes timeout for large batches
        )
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
        
        # Calculate total items
        total_items = sum(len(block.get("items", [])) for block in candidates)
        
        # If we have too many items (>100), process in batches to avoid timeout
        # Note: 100 items ≈ 2000 tokens input, safe for API calls
        MAX_ITEMS_PER_BATCH = 100
        if total_items > MAX_ITEMS_PER_BATCH:
            print(f"    [INFO] Processing {total_items} items in batches (max {MAX_ITEMS_PER_BATCH} per batch)...", flush=True)
            
            # Collect all items with their dimensions
            all_items_with_dim = []
            for block in candidates:
                dim = block.get("dimension") or block.get("name") or "Unknown"
                for item in block.get("items", []):
                    all_items_with_dim.append((dim, item))
            
            # Process in batches
            all_refined_items = {}  # {dimension: [items]}
            for batch_start in range(0, len(all_items_with_dim), MAX_ITEMS_PER_BATCH):
                batch_end = min(batch_start + MAX_ITEMS_PER_BATCH, len(all_items_with_dim))
                batch = all_items_with_dim[batch_start:batch_end]
                
                # Group batch items by dimension
                batch_by_dim = {}
                for dim, item in batch:
                    if dim not in batch_by_dim:
                        batch_by_dim[dim] = []
                    batch_by_dim[dim].append(item)
                
                # Build prompt for this batch
                candidate_lines = []
                for dim, items in batch_by_dim.items():
                    candidate_lines.append(f"Dimension: {dim}")
                    for it in items:
                        candidate_lines.append(f"- {it}")
                
                full_prompt = f"{prompt}\n\nScenario:\n{scenario_text}\n\nCandidates:\n" + "\n".join(candidate_lines)
                
                print(f"    [INFO] Processing batch {batch_start//MAX_ITEMS_PER_BATCH + 1}/{(len(all_items_with_dim)-1)//MAX_ITEMS_PER_BATCH + 1} ({len(batch)} items)...", flush=True)
                resp = retry_llm_call(lambda: self.llm.invoke(full_prompt).content.strip())
                
                # Parse this batch's response and merge
                # Use simple JSON parsing
                import json
                import re
                try:
                    # Try to extract JSON from response
                    json_match = re.search(r'\[.*\]', resp, re.DOTALL)
                    if json_match:
                        batch_result = json.loads(json_match.group())
                        for block in batch_result:
                            dim = block.get("dimension", "Unknown")
                            items = block.get("items", [])
                            if dim not in all_refined_items:
                                all_refined_items[dim] = []
                            all_refined_items[dim].extend(items)
                except Exception as e:
                    print(f"    [WARN] Failed to parse batch response, using raw response: {e}", flush=True)
                    # Fallback: return raw response and let caller handle it
                    return {"raw": resp}
            
            # Combine all refined items into final JSON format
            final_blocks = [{"dimension": dim, "items": items} for dim, items in all_refined_items.items()]
            import json
            return {"raw": json.dumps(final_blocks, ensure_ascii=False)}
        else:
            # Original single-batch processing for smaller item sets
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

