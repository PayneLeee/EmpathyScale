"""
Persona Generation Agent: Generate diverse participant personas based on scenario context.
参考PETS论文的参与者特征分布（Section 5.3）。
"""

import json
import re
import time
from pathlib import Path
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from langchain_openai import ChatOpenAI
from openai import APIConnectionError

from utils.prompt_manager import PromptManager
from agents.scale_generation_agents import retry_llm_call

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
PERSONAS_DIR = PROJECT_ROOT / "data" / "personas"


class PersonaGenerationAgent:
    """Generate diverse participant personas for evaluation studies."""
    
    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini", prompts_dir: str = None, 
                 batch_size: int = 12, max_workers: int = 3):
        """
        Initialize PersonaGenerationAgent.
        
        Args:
            api_key: OpenAI API key
            model_name: Model to use for persona generation
            prompts_dir: Directory containing prompt files
            batch_size: Number of personas to generate per batch (default: 12)
                       Smaller batches reduce prompt size and avoid timeout/connection errors
            max_workers: Maximum number of parallel workers for batch generation (default: 3)
                        Parallel processing speeds up generation while respecting API rate limits
        """
        # Increased temperature to 1.0 to promote more diverse persona generation
        # Set timeout to 300s (5 minutes) for large persona generation requests
        # Reduced batch_size from 25 to 12 to reduce prompt size and avoid timeout/connection errors
        # Set timeout to 300s (5 minutes) for large persona generation requests
        # Reduced batch_size from 25 to 12 to reduce prompt size and avoid timeout/connection errors
        self.llm = ChatOpenAI(
            api_key=api_key, 
            model_name=model_name, 
            temperature=1.0,
            timeout=300.0  # 5 minutes timeout for large prompts
        )
        self.prompt_manager = PromptManager(prompts_dir)
        self.api_key = api_key
        self.batch_size = batch_size  # Number of personas to generate per batch
        self.max_workers = max_workers  # Number of parallel workers for batch generation
        self._progress_lock = Lock()  # For thread-safe progress output
    
    def generate_personas(self, scenario_context: Dict[str, Any], n_personas: int = 25) -> List[Dict[str, Any]]:
        """
        根据场景上下文生成多样化的被试人设。
        参考PETS论文的参与者特征分布。
        如果personas数量较大，将分批并行生成以避免API超时并提高速度。
        
        Args:
            scenario_context: 场景上下文字典
            n_personas: 要生成的人设数量
            
        Returns:
            List of persona dictionaries with required fields
        """
        # Use batch processing if n_personas exceeds batch_size
        if n_personas <= self.batch_size:
            return self._generate_personas_batch(scenario_context, n_personas, batch_start_id=1)
        
        # Generate in batches with parallel processing
        num_batches = (n_personas + self.batch_size - 1) // self.batch_size
        print(f"      [Persona] Generating {n_personas} personas in {num_batches} batches (batch size: {self.batch_size})...", flush=True)
        print(f"      [Persona] Using {self.max_workers} parallel workers for batch generation", flush=True)
        
        # Prepare batch tasks
        batch_tasks = []
        persona_id_counter = 1
        for batch_idx in range(num_batches):
            batch_start = batch_idx * self.batch_size
            batch_end = min(batch_start + self.batch_size, n_personas)
            batch_size_actual = batch_end - batch_start
            batch_tasks.append({
                "batch_idx": batch_idx + 1,
                "batch_size": batch_size_actual,
                "batch_start_id": persona_id_counter,
                "total_batches": num_batches
            })
            persona_id_counter += batch_size_actual
        
        # Parallel batch generation
        all_personas = []
        start_time = time.time()
        completed_count = [0]  # Use list for closure modification
        
        def process_batch(batch_task):
            """Process a single batch of persona generation."""
            batch_idx = batch_task["batch_idx"]
            batch_size_actual = batch_task["batch_size"]
            batch_start_id = batch_task["batch_start_id"]
            total_batches = batch_task["total_batches"]
            
            try:
                with self._progress_lock:
                    print(f"      [Persona] Batch {batch_idx}/{total_batches}: generating {batch_size_actual} personas...", flush=True)
                
                batch_personas = self._generate_personas_batch(
                    scenario_context, 
                    batch_size_actual, 
                    batch_start_id=batch_start_id
                )
                
                with self._progress_lock:
                    completed_count[0] += 1
                    elapsed = time.time() - start_time
                    avg_time = elapsed / completed_count[0] if completed_count[0] > 0 else 0
                    remaining = avg_time * (total_batches - completed_count[0])
                    if completed_count[0] % max(1, total_batches // 5) == 0 or completed_count[0] == total_batches:
                        print(f"      [Persona] Batch {completed_count[0]}/{total_batches} completed ({elapsed:.1f}s total, ETA: {remaining:.0f}s)", flush=True)
                
                return batch_personas
            except Exception as e:
                with self._progress_lock:
                    print(f"      [ERROR] Batch {batch_idx} failed: {e}", flush=True)
                # Fill with default personas for this batch
                return self._generate_default_personas(batch_size_actual, start_id=batch_start_id)
        
        # Execute batches in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all batch tasks
            future_to_task = {executor.submit(process_batch, task): task for task in batch_tasks}
            
            # Collect results as they complete
            batch_results = {}
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    batch_personas = future.result()
                    batch_results[task["batch_idx"]] = batch_personas
                except Exception as e:
                    batch_idx = task["batch_idx"]
                    batch_size_actual = task["batch_size"]
                    batch_start_id = task["batch_start_id"]
                    with self._progress_lock:
                        print(f"      [ERROR] Batch {batch_idx} execution failed: {e}", flush=True)
                    # Use default personas as fallback
                    batch_results[batch_idx] = self._generate_default_personas(batch_size_actual, start_id=batch_start_id)
        
        # Combine results in batch order
        for batch_idx in range(1, num_batches + 1):
            if batch_idx in batch_results:
                all_personas.extend(batch_results[batch_idx])
        
        print(f"      [Persona] Successfully generated {len(all_personas)} personas", flush=True)
        return all_personas[:n_personas]  # Ensure we return exactly n_personas
    
    def _generate_personas_batch(
        self, 
        scenario_context: Dict[str, Any], 
        n_personas: int, 
        batch_start_id: int = 1
    ) -> List[Dict[str, Any]]:
        """
        生成一批personas（内部方法，处理单个批次）。
        
        Args:
            scenario_context: 场景上下文字典
            n_personas: 本批次要生成的人设数量
            batch_start_id: 本批次persona_id的起始值
            
        Returns:
            List of persona dictionaries with required fields
        """
        prompt_template = self.prompt_manager.get_agent_group_prompt(
            "persona_generation_agent", "persona_generation_prompt"
        )
        
        prompt = prompt_template.format(
            assessment_context=scenario_context.get("assessment_context", ""),
            robot_platform=scenario_context.get("robot_platform", ""),
            interaction_modalities=scenario_context.get("interaction_modalities", ""),
            collaboration_pattern=scenario_context.get("collaboration_pattern", ""),
            environmental_setting=scenario_context.get("environmental_setting", ""),
            n_personas=n_personas,
        )
        
        try:
            resp = retry_llm_call(lambda: self.llm.invoke(prompt).content.strip())
            personas = self._parse_personas(resp, n_personas)
            
            # Ensure all personas have persona_id (assign sequentially from batch_start_id)
            for idx, persona in enumerate(personas):
                if "persona_id" not in persona:
                    persona["persona_id"] = batch_start_id + idx
                else:
                    # Adjust persona_id to be sequential across batches
                    persona["persona_id"] = batch_start_id + idx
            
            return personas
        except Exception as e:
            print(f"      [ERROR] Persona generation batch failed: {e}", flush=True)
            # Return default personas as fallback
            return self._generate_default_personas(n_personas, start_id=batch_start_id)
    
    def _parse_personas(self, text: str, expected_n: int) -> List[Dict[str, Any]]:
        """Parse LLM response to extract personas."""
        # Try to find JSON in response
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group())
                if "personas" in parsed:
                    personas = parsed["personas"]
                    # Ensure we have the right number
                if len(personas) < expected_n:
                    # Pad with default personas
                    default_start_id = len(personas) + 1
                    default = self._generate_default_personas(expected_n - len(personas), start_id=default_start_id)
                    personas.extend(default)
                    return personas[:expected_n]
                elif isinstance(parsed, list):
                    return parsed[:expected_n]
            except Exception:
                pass
        
        # Fallback: generate default personas
        return self._generate_default_personas(expected_n, start_id=1)
    
    def _generate_default_personas(self, n: int, start_id: int = 1) -> List[Dict[str, Any]]:
        """Generate default personas as fallback."""
        import random
        genders = ["male", "female", "non-binary"]
        educations = ["university degree", "high school", "vocational training", "doctoral"]
        professions = ["worker", "engineer", "manager", "technician", "operator"]
        tech_levels = ["low", "moderate", "high"]
        cultures = ["European", "North American", "Asian", "South American", "African"]
        
        personas = []
        for i in range(n):
            personas.append({
                "persona_id": start_id + i,
                "age": random.randint(25, 45),
                "gender": random.choice(genders),
                "education": random.choice(educations),
                "ati_score": round(random.uniform(3.0, 5.0), 1),
                "profession": random.choice(professions),
                "personality": "balanced",
                "tech_experience": random.choice(tech_levels),
                "cultural_background": random.choice(cultures),
                # Add default interaction background fields
                "interaction_experience": "General experience with technology",
                "interaction_context": "Regular interaction in typical setting",
                "interaction_expectations": "Expects system to be helpful and responsive",
            })
        return personas
    
    def save_personas(self, scenario_id: str, personas: List[Dict[str, Any]], phase: str = "selection"):
        """
        保存人设到文件，按场景ID和阶段组织。
        
        Args:
            scenario_id: 场景标识符（如 "collab_robot"）
            personas: 人设列表（应包含empathy_condition字段区分empathic/non_empathic）
            phase: 阶段标识符，"selection"（Phase 1）或 "validation"（Phase 2）
        """
        scenario_dir = PERSONAS_DIR / scenario_id
        scenario_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存到 {phase}.json（如 selection.json 或 validation.json）
        persona_file = scenario_dir / f"{phase}.json"
        with open(persona_file, "w", encoding="utf-8") as f:
            json.dump(personas, f, indent=2, ensure_ascii=False)
        
        # 统计empathic和non_empathic数量
        empathic_count = sum(1 for p in personas if p.get("empathy_condition") == "empathic")
        non_empathic_count = sum(1 for p in personas if p.get("empathy_condition") == "non_empathic")
        print(f"      [Persona] Saved {len(personas)} personas to {persona_file} (empathic: {empathic_count}, non_empathic: {non_empathic_count})", flush=True)
    
    def load_personas(self, scenario_id: str, phase: str = "selection") -> List[Dict[str, Any]]:
        """
        从文件加载人设。
        
        Args:
            scenario_id: 场景标识符
            phase: 阶段标识符，"selection"（Phase 1）或 "validation"（Phase 2）
            
        Returns:
            人设列表，如果文件不存在则返回None
        """
        persona_file = PERSONAS_DIR / scenario_id / f"{phase}.json"
        if persona_file.exists():
            try:
                personas = json.loads(persona_file.read_text(encoding="utf-8"))
                empathic_count = sum(1 for p in personas if p.get("empathy_condition") == "empathic")
                non_empathic_count = sum(1 for p in personas if p.get("empathy_condition") == "non_empathic")
                print(f"      [Persona] Loaded {len(personas)} personas from {persona_file} (empathic: {empathic_count}, non_empathic: {non_empathic_count})", flush=True)
                return personas
            except Exception as e:
                print(f"      [WARN] Failed to load personas: {e}", flush=True)
                return None
        return None
    
    def add_interaction_experiences(
        self, 
        personas: List[Dict[str, Any]], 
        scenario_context: Dict[str, Any],
        interaction_type: str = "empathic"
    ) -> List[Dict[str, Any]]:
        """
        为persona列表添加concrete_interaction_experience字段和empathy_condition字段。
        根据interaction_type生成empathic或non-empathic的交互经历。
        
        Args:
            personas: Persona列表
            scenario_context: 场景上下文字典
            interaction_type: "empathic" 或 "non_empathic"
            
        Returns:
            添加了concrete_interaction_experience和empathy_condition的persona列表
        """
        result_personas = []
        
        for persona in personas:
            persona_copy = persona.copy()
            
            # 生成empathic或non-empathic的交互经历
            if interaction_type == "empathic":
                experience = self._generate_empathic_experience(persona, scenario_context)
                empathy_condition = "empathic"  # 与有共情能力的系统交互
            else:
                experience = self._generate_non_empathic_experience(persona, scenario_context)
                empathy_condition = "non_empathic"  # 与无共情能力的系统交互
            
            persona_copy["concrete_interaction_experience"] = experience
            persona_copy["empathy_condition"] = empathy_condition  # 记录交互条件
            result_personas.append(persona_copy)
        
        return result_personas
    
    def _generate_empathic_experience(
        self, 
        persona: Dict[str, Any], 
        scenario_context: Dict[str, Any]
    ) -> str:
        """
        生成empathic交互经历：描述与有共情能力的系统交互的实际体验。
        系统表现出理解、情感响应、支持行为，但persona不知道这是"empathic"系统，
        只是描述实际感受到的积极交互体验。
        """
        # 提取关键场景信息（简化）
        platform = scenario_context.get("robot_platform", "system")
        # 截断过长的平台描述
        if len(platform) > 30:
            platform = platform[:27] + "..."
        
        # 描述实际的积极交互体验，不明确提及"empathic"
        # Persona只知道自己感受到的理解、支持和适应
        experiences = [
            f"The {platform} noticed when I seemed stressed and adjusted its pace to match mine. It expressed understanding and provided encouraging feedback, making me feel genuinely supported.",
            
            f"When I hesitated, the {platform} paused and asked if I needed help. It acknowledged my concerns and adapted its behavior accordingly, showing it understood my needs.",
            
            f"The {platform} recognized my frustration and responded with supportive actions. It adjusted its approach based on my emotional cues, making me feel listened to and valued.",
            
            f"The {platform} showed interest in my well-being and proactively offered assistance when I seemed overwhelmed. Its responses felt warm and understanding, making me feel comfortable.",
            
            f"The {platform} communicated understanding and provided emotional support when needed, adapting its behavior to my emotional state. I felt it truly cared about my experience."
        ]
        
        # 根据persona_id选择，保证相同persona总是得到相同的经历
        idx = (persona.get("persona_id", 0) - 1) % len(experiences)
        return experiences[idx]
    
    def _generate_non_empathic_experience(
        self, 
        persona: Dict[str, Any], 
        scenario_context: Dict[str, Any]
    ) -> str:
        """
        生成non-empathic交互经历：描述与无共情能力的系统交互的实际体验。
        系统只完成任务，缺乏情感理解，但persona不知道这是"non-empathic"系统，
        只是描述实际感受到的功能性但缺乏理解的交互体验。
        """
        # 提取关键场景信息（简化）
        platform = scenario_context.get("robot_platform", "system")
        # 截断过长的平台描述
        if len(platform) > 30:
            platform = platform[:27] + "..."
        
        # 描述实际的功能性但缺乏理解的交互体验，不明确提及"non-empathic"
        # Persona只知道系统很有效率但没有注意到自己的情感状态
        experiences = [
            f"The {platform} was purely functional. Even when I was clearly stressed, it maintained a fixed pace. It performed tasks efficiently but showed no awareness of my emotional state, making me feel like it was just executing commands.",
            
            f"The {platform} operated in a task-oriented manner. It completed objectives but failed to recognize my hesitation or frustration. It provided only functional feedback without any emotional awareness.",
            
            f"Working with the {platform} was purely transactional. It focused solely on task completion, ignoring my emotional cues. When I struggled, it didn't adjust its behavior or offer any emotional support.",
            
            f"The {platform} was strictly functional. It used communication only for task-related purposes, showing no interest in my emotional state. Even when I needed support, it continued with its predefined routines without acknowledging how I felt.",
            
            f"The {platform} processed tasks efficiently but didn't respond to my emotional expressions. It was reliable and functional, but completely lacked awareness of my feelings or needs."
        ]
        
        # 根据persona_id选择，保证相同persona总是得到相同的经历
        idx = (persona.get("persona_id", 0) - 1) % len(experiences)
        return experiences[idx]

