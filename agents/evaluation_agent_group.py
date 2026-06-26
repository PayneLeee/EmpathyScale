"""
Evaluation Agent Group: LLM-simulated participant item testing (PETS-style).
Participants rate system empathy in scenarios using 0-100 scale (strongly disagree to strongly agree).
"""

import json
import re
import statistics
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

import numpy as np

from langchain_openai import ChatOpenAI
from openai import APIConnectionError

from utils.prompt_manager import PromptManager

try:
    from workflow_console import minor_separator, sub
except ImportError:
    def minor_separator(label=None):
        if label:
            print(f"      --- {label} ---", flush=True)

    def sub(msg, indent=6):
        print(f"{' ' * indent}▸ {msg}", flush=True)
from agents.scale_generation_agents import retry_llm_call
from agents.persona_generation_agent import PersonaGenerationAgent

PROJECT_ROOT = Path(__file__).parent.parent.resolve()


class EvaluationAgentGroup:
    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini", prompts_dir: str = None, 
                 max_workers: int = 5, items_batch_size: int = 100):
        """
        Initialize evaluation agent group.
        
        Args:
            api_key: OpenAI API key
            model_name: Model to use for evaluation
            prompts_dir: Directory containing prompt files
            max_workers: Maximum number of parallel workers for persona evaluation (default: 5)
            items_batch_size: Maximum number of items to process in one API call (default: 100)
                              If items exceed this, they will be processed in batches
        """
        # Set timeout to 300s (5 minutes) for large prompts with many items
        # This matches ContentAssessmentAgent timeout and prevents connection timeouts
        self.llm = ChatOpenAI(
            api_key=api_key, 
            model_name=model_name, 
            temperature=0.7,
            timeout=300.0  # 5 minutes timeout for large prompts (192 items + persona info)
        )
        self.prompt_manager = PromptManager(prompts_dir)
        self.api_key = api_key
        self.max_workers = max_workers
        self.items_batch_size = items_batch_size
        self._progress_lock = Lock()  # For thread-safe progress output

    # ---------- Public API ----------
    def evaluate_items(self, run_id: str, items: List[Dict[str, str]], scenario_context: Dict[str, Any],
                       n_participants: int = 25, scenario_id: str = None, 
                       personas: List[Dict[str, Any]] = None, phase: str = "selection", out_dir: Path = None) -> Dict[str, Any]:
        """
        Evaluate items using PETS Item Testing approach with personas.
        Each participant (with persona) rates ALL items for the scenario (0-100 scale).
        
        Args:
            run_id: Unique run identifier
            items: List of scale items to evaluate
            scenario_context: Scenario context dictionary
            n_participants: Number of participants to simulate
            scenario_id: Scenario identifier for persona storage/loading (e.g., "collab_robot_assembly")
            personas: Optional pre-generated personas. If None, will load or generate based on scenario_id
            phase: Phase identifier, "selection" (Phase 1) or "validation" (Phase 2). 
                   Phase 2 uses independent persona group to avoid overfitting (PETS methodology).
            out_dir: Optional output directory path
            
        Returns:
            Dictionary with evaluation results and summary
        """
        if out_dir is None:
            out_dir = PROJECT_ROOT / f"data/runs/{run_id}/evaluation_agent_group"
        out_dir.mkdir(parents=True, exist_ok=True)

        minor_separator(f"评估输出目录: {out_dir.name}")
        sub(f"Boateng Step 3–4：{n_participants} Personas × {len(items)} items（phase={phase}）", indent=6)

        # Load or generate personas
        if personas is None:
            if scenario_id:
                persona_agent = PersonaGenerationAgent(api_key=self.api_key, prompts_dir=self.prompt_manager.prompts_dir)
                personas = persona_agent.load_personas(scenario_id, phase=phase)
                if personas is None:
                    personas = persona_agent.generate_personas(scenario_context, n_participants)
                    persona_agent.save_personas(scenario_id, personas, phase=phase)
                elif len(personas) < n_participants:
                    personas = persona_agent.generate_personas(scenario_context, n_participants)
                    persona_agent.save_personas(scenario_id, personas, phase=phase)
                else:
                    personas = personas[:n_participants]
            else:
                persona_agent = PersonaGenerationAgent(api_key=self.api_key, prompts_dir=self.prompt_manager.prompts_dir)
                personas = persona_agent.generate_personas(scenario_context, n_participants)
        else:
            personas = personas[:n_participants] if len(personas) >= n_participants else personas

        # Determine if batching is needed
        use_batching = len(items) > self.items_batch_size

        participant_data = []
        start_time = time.time()
        completed_count = [0]

        def process_persona(persona_with_idx):
            """Process a single persona (with batching if needed)."""
            idx, persona = persona_with_idx
            try:
                if use_batching:
                    participant_result = self._simulate_participant_with_persona_batched(
                        items, scenario_context, persona
                    )
                else:
                    participant_result = self._simulate_participant_with_persona(
                        items, scenario_context, persona
                    )
                with self._progress_lock:
                    completed_count[0] += 1
                return participant_result
            except Exception as e:
                with self._progress_lock:
                    completed_count[0] += 1
                # Return error structure matching expected format
                persona_id = persona.get("persona_id", idx)
                complete_persona = persona.copy()
                if "interaction_experience" not in complete_persona:
                    complete_persona["interaction_experience"] = "No specific past experience"
                if "interaction_context" not in complete_persona:
                    complete_persona["interaction_context"] = "General interaction context"
                if "interaction_expectations" not in complete_persona:
                    complete_persona["interaction_expectations"] = "General expectations"
                
                # Note: In error case, we don't have item_offset, so use 0 (will be corrected in batching)
                return {
                    "participant_id": persona_id,
                    "persona_id": persona_id,
                    "persona": complete_persona,
                    "scenario": scenario_context,
                    "ratings": [{"item_id": i+1, "dimension": item.get("dimension", "Unknown"), 
                                "item_text": item.get("item_text", ""), "rating": None} 
                               for i, item in enumerate(items)],
                    "summary": f"Error: {e}",
                    "raw": f"Error during simulation: {e}",
                }
        
        # Parallel processing of personas
        persona_with_indices = [(idx, persona) for idx, persona in enumerate(personas, 1)]
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(process_persona, pwi): pwi[0] for pwi in persona_with_indices}
            
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    participant_data.append(result)
        
        # Sort by persona_id to maintain consistency
        participant_data.sort(key=lambda x: x.get("persona_id", 0))
        
        summary = self._summarize(participant_data, items)

        with open(out_dir / "participant_level_evaluations.json", "w", encoding="utf-8") as f:
            json.dump(participant_data, f, indent=2, ensure_ascii=False)
        with open(out_dir / "evaluation_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        return {
            "status": "completed",
            "n_items": len(items),
            "n_participants": n_participants,
            "summary": summary,
            "summary_path": str(out_dir / "evaluation_summary.json"),
        }

    def evaluate_baseline_txt(
        self,
        run_id: str,
        txt_path: Path,
        scenario_context: Dict[str, Any],
        n_participants: int = 25,
        scenario_id: str = None,
        label: str = "baseline",
        print_label: Optional[str] = None,
    ) -> Dict[str, Any]:
        pl = print_label if print_label is not None else label
        items = self._items_from_plain_text(txt_path)
        out_dir = PROJECT_ROOT / f"data/runs/{run_id}/evaluation_agent_group/baselines/{label}"
        return self.evaluate_items(run_id, items, scenario_context, n_participants, scenario_id=scenario_id, out_dir=out_dir)

    # ---------- Helpers ----------
    def _simulate_participant_with_persona_batched(self, items: List[Dict[str, str]], 
                                                   scenario_context: Dict[str, Any], 
                                                   persona: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate one participant rating all items, processing items in batches if needed.
        This method splits items into batches and processes each batch separately,
        then merges the results.
        
        Args:
            items: List of all scale items to rate
            scenario_context: Scenario context dictionary
            persona: Persona dictionary with persona characteristics
            
        Returns:
            Participant result dictionary with all ratings merged from batches
        """
        all_ratings = []
        num_batches = (len(items) + self.items_batch_size - 1) // self.items_batch_size
        persona_id = persona.get("persona_id", "unknown")
        
        for batch_idx in range(num_batches):
            start_idx = batch_idx * self.items_batch_size
            end_idx = min(start_idx + self.items_batch_size, len(items))
            batch_items = items[start_idx:end_idx]

            # Process this batch
            batch_result = self._simulate_participant_with_persona(
                batch_items, scenario_context, persona,
                item_offset=start_idx
            )

            # Collect ratings from this batch
            batch_ratings = batch_result.get("ratings", [])
            all_ratings.extend(batch_ratings)
        
        # Merge results - use the last batch result as template and update ratings
        merged_result = batch_result.copy()
        merged_result["ratings"] = all_ratings
        
        # Update summary to reflect batching
        if num_batches > 1:
            original_summary = merged_result.get("summary", "")
            merged_result["summary"] = f"[Processed in {num_batches} batches] {original_summary}"
        
        return merged_result
    
    def _simulate_participant_with_persona(self, items: List[Dict[str, str]], scenario_context: Dict[str, Any], 
                                           persona: Dict[str, Any], item_offset: int = 0) -> Dict[str, Any]:
        """
        Simulate one participant (with persona) rating all items for the scenario (PETS Item Testing).
        Returns participant-level data with ratings for all items (0-100 scale).
        
        Args:
            items: List of scale items to rate
            scenario_context: Scenario context dictionary
            persona: Persona dictionary with persona characteristics
            
        Returns:
            Participant result dictionary with persona_id, persona info, and ratings
        """
        # Build items list for prompt (use item_offset for correct numbering in batches)
        items_list = []
        for idx, item in enumerate(items, 1):
            dimension = item.get("dimension", "Unknown")
            item_text = item.get("item_text", "")
            # Use item_offset + idx for correct global item numbering
            global_item_num = item_offset + idx
            items_list.append(f"{global_item_num}. [{dimension}] {item_text}")
        items_list_str = "\n".join(items_list)
        
        # Extract persona information
        persona_id = persona.get("persona_id", 0)
        age = persona.get("age", "unknown")
        gender = persona.get("gender", "unknown")
        education = persona.get("education", "unknown")
        ati_score = persona.get("ati_score", "unknown")
        profession = persona.get("profession", "unknown")
        personality = persona.get("personality", "unknown")
        tech_experience = persona.get("tech_experience", "unknown")
        cultural_background = persona.get("cultural_background", "unknown")
        # Extract interaction background fields (with defaults for backward compatibility)
        interaction_experience = persona.get("interaction_experience", "No specific past experience")
        interaction_context = persona.get("interaction_context", "General interaction context")
        interaction_expectations = persona.get("interaction_expectations", "General expectations")
        # Extract concrete interaction experience (new field - critical for rating)
        concrete_interaction_experience = persona.get("concrete_interaction_experience", None)
        if not concrete_interaction_experience:
            # Fallback: generate a basic experience description if not provided
            concrete_interaction_experience = f"General interaction in {scenario_context.get('assessment_context', 'this scenario')}. The robot/system performed its tasks, but no specific empathic behaviors were particularly notable."
        
        prompt_template = self.prompt_manager.get_agent_group_prompt("evaluation_agent_group", "participant_evaluation_prompt")
        prompt = prompt_template.format(
            age=age,
            gender=gender,
            education=education,
            ati_score=ati_score,
            profession=profession,
            personality=personality,
            tech_experience=tech_experience,
            cultural_background=cultural_background,
            interaction_experience=interaction_experience,
            interaction_context=interaction_context,
            interaction_expectations=interaction_expectations,
            concrete_interaction_experience=concrete_interaction_experience,
            assessment_context=scenario_context.get("assessment_context", ""),
            robot_platform=scenario_context.get("robot_platform", ""),
            interaction_modalities=scenario_context.get("interaction_modalities", ""),
            collaboration_pattern=scenario_context.get("collaboration_pattern", ""),
            environmental_setting=scenario_context.get("environmental_setting", ""),
            items_list=items_list_str,
        )
        try:
            resp = retry_llm_call(lambda: self.llm.invoke(prompt).content.strip())
            data = self._parse_json_like(resp, len(items))
            
            # Build participant-level response with persona information
            # Ensure persona has all required fields (for backward compatibility)
            complete_persona = persona.copy()
            if "interaction_experience" not in complete_persona:
                complete_persona["interaction_experience"] = "No specific past experience"
            if "interaction_context" not in complete_persona:
                complete_persona["interaction_context"] = "General interaction context"
            if "interaction_expectations" not in complete_persona:
                complete_persona["interaction_expectations"] = "General expectations"
            if "concrete_interaction_experience" not in complete_persona:
                complete_persona["concrete_interaction_experience"] = concrete_interaction_experience
            # empathy_condition should already be in persona from add_interaction_experiences, but ensure it exists
            if "empathy_condition" not in complete_persona:
                # Infer from concrete_interaction_experience if not explicitly set
                if "empathic" in concrete_interaction_experience.lower():
                    complete_persona["empathy_condition"] = "empathic"
                elif "non-empathic" in concrete_interaction_experience.lower() or "non_empathic" in concrete_interaction_experience.lower():
                    complete_persona["empathy_condition"] = "non_empathic"
                else:
                    complete_persona["empathy_condition"] = None  # Unknown condition
            
            participant_result = {
                "participant_id": persona_id,  # Use persona_id as participant_id
                "persona_id": persona_id,
                "persona": complete_persona,  # Include full persona information with defaults
                "scenario": {
                    "assessment_context": scenario_context.get("assessment_context", ""),
                    "robot_platform": scenario_context.get("robot_platform", ""),
                    "interaction_modalities": scenario_context.get("interaction_modalities", ""),
                    "collaboration_pattern": scenario_context.get("collaboration_pattern", ""),
                    "environmental_setting": scenario_context.get("environmental_setting", ""),
                },
                "ratings": [],
                "summary": data.get("summary", ""),
                "raw": resp[:500],  # Keep more context for debugging
            }
            
            # Map ratings to items (use item_offset for correct item_id)
            ratings = data.get("ratings", [])
            for idx, item in enumerate(items):
                rating = ratings[idx] if idx < len(ratings) else None
                participant_result["ratings"].append({
                    "item_id": item_offset + idx + 1,  # Use item_offset for correct global item_id
                    "dimension": item.get("dimension", "Unknown"),
                    "item_text": item.get("item_text", ""),
                    "rating": rating,
                })
            
            return participant_result
        except Exception as e:
            # Return error structure matching expected format
            # Ensure persona has all required fields (for backward compatibility)
            complete_persona = persona.copy()
            if "interaction_experience" not in complete_persona:
                complete_persona["interaction_experience"] = "No specific past experience"
            if "interaction_context" not in complete_persona:
                complete_persona["interaction_context"] = "General interaction context"
            if "interaction_expectations" not in complete_persona:
                complete_persona["interaction_expectations"] = "General expectations"
            
            return {
                "participant_id": persona_id,
                "persona_id": persona_id,
                "persona": complete_persona,
                "scenario": scenario_context,
                "ratings": [{"item_id": item_offset + idx + 1, "dimension": item.get("dimension", "Unknown"), 
                            "item_text": item.get("item_text", ""), "rating": None} 
                           for idx, item in enumerate(items)],
                "summary": f"Error: {e}",
                "raw": f"Error during simulation: {e}",
            }

    def _parse_json_like(self, text: str, expected_n_ratings: int) -> Dict[str, Any]:
        """
        Parse LLM response to extract ratings (0-100 scale) and summary.
        Returns dict with 'ratings' list and 'summary' string.
        """
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group())
                ratings = parsed.get("ratings", [])
                # Ensure ratings are integers in 0-100 range
                if isinstance(ratings, list):
                    ratings = [int(r) if isinstance(r, (int, float)) and 0 <= r <= 100 else None for r in ratings]
                    # Pad or truncate to expected length
                    while len(ratings) < expected_n_ratings:
                        ratings.append(None)
                    ratings = ratings[:expected_n_ratings]
                return {
                    "ratings": ratings,
                    "summary": parsed.get("summary", ""),
                }
            except Exception:
                pass
        
        # Fallback heuristic: try to extract numbers that might be ratings
        numbers = re.findall(r'\b([0-9]{1,3})\b', text)
        ratings = []
        for num_str in numbers[:expected_n_ratings]:
            num = int(num_str)
            if 0 <= num <= 100:
                ratings.append(num)
            else:
                ratings.append(None)
        
        # Pad to expected length
        while len(ratings) < expected_n_ratings:
            ratings.append(None)
        
        return {
            "ratings": ratings[:expected_n_ratings],
            "summary": text[:200] if len(text) > 200 else text,
        }

    def _summarize(self, participant_data: List[Dict[str, Any]], items: List[Dict[str, str]], 
                   factor_structure: Optional[Dict[int, int]] = None) -> Dict[str, Any]:
        """
        Summarize participant-level data into item-level statistics.
        Computes mean, std, min, max for each item across all participants (0-100 scale).
        Also calculates PETS-style validation metrics if factor_structure is provided.
        
        Args:
            participant_data: List of participant evaluation data
            items: List of scale items
            factor_structure: Optional dictionary mapping item_id to factor_idx for validation metrics
        """
        def stats(vals):
            """Compute statistics for a list of values."""
            valid_vals = [v for v in vals if v is not None and isinstance(v, (int, float))]
            if not valid_vals:
                return {"mean": None, "std": None, "min": None, "max": None, "n": 0}
            return {
                "mean": round(statistics.mean(valid_vals), 2),
                "std": round(statistics.stdev(valid_vals), 2) if len(valid_vals) > 1 else 0.0,
                "min": min(valid_vals),
                "max": max(valid_vals),
                "n": len(valid_vals),
            }
        
        # Collect ratings for each item across all participants
        item_stats = []
        for item_idx, item in enumerate(items):
            item_ratings = []
            for participant in participant_data:
                ratings = participant.get("ratings", [])
                if item_idx < len(ratings):
                    rating = ratings[item_idx].get("rating")
                    if rating is not None:
                        item_ratings.append(float(rating))
            
            item_stat = stats(item_ratings)
            item_stats.append({
                "item_id": item_idx + 1,
                "dimension": item.get("dimension", "Unknown"),
                "item_text": item.get("item_text", ""),
                "rating_statistics": item_stat,
            })
        
        # Build ratings matrix for Cronbach's alpha (n_participants × n_items)
        ratings_matrix = np.full((len(participant_data), len(items)), np.nan)
        for p_idx, participant in enumerate(participant_data):
            ratings = participant.get("ratings", [])
            for item_idx in range(len(items)):
                if item_idx < len(ratings):
                    rating = ratings[item_idx].get("rating")
                    if rating is not None:
                        ratings_matrix[p_idx, item_idx] = float(rating)
        
        # Flag items with low mean ratings or high variance
        low_items = [
            it for it in item_stats
            if it["rating_statistics"]["mean"] is not None and it["rating_statistics"]["mean"] < 50
        ]
        
        high_variance_items = [
            it for it in item_stats
            if it["rating_statistics"]["std"] is not None and it["rating_statistics"]["std"] > 30
        ]
        
        # Overall statistics
        all_means = [it["rating_statistics"]["mean"] for it in item_stats 
                    if it["rating_statistics"]["mean"] is not None]
        overall_mean = round(statistics.mean(all_means), 2) if all_means else None
        
        # Persona diversity statistics
        persona_diversity = self._compute_persona_diversity(participant_data)
        
        # Calculate PETS-style validation metrics
        validation_metrics = {}
        
        # 1. Discriminant ability (t-test)
        discriminant_ability = self._calculate_discriminant_ability(participant_data, items)
        if discriminant_ability:
            validation_metrics["discriminant_ability"] = discriminant_ability
        
        # 2. Internal consistency (Cronbach's alpha)
        internal_consistency = self._calculate_cronbach_alpha(ratings_matrix)
        if internal_consistency:
            validation_metrics["internal_consistency"] = internal_consistency
        
        # 3. Factor scores (mean and std per factor)
        if factor_structure:
            factor_scores = self._calculate_factor_scores(item_stats, factor_structure)
            if factor_scores:
                validation_metrics["factor_scores"] = factor_scores
        
        result = {
            "n_items": len(item_stats),
            "n_participants": len(participant_data),
            "item_statistics": item_stats,
            "overall_mean_rating": overall_mean,
            "low_rating_items": low_items,  # Mean < 50 (below neutral)
            "high_variance_items": high_variance_items,  # Std > 30
            "scale_range": "0-100 (strongly disagree to strongly agree)",
            "persona_diversity": persona_diversity,
        }
        
        # Add validation_metrics if any were calculated
        if validation_metrics:
            result["validation_metrics"] = validation_metrics
        
        return result
    
    def _compute_persona_diversity(self, participant_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute persona diversity statistics from participant data."""
        ages = []
        genders = {}
        educations = {}
        ati_scores = []
        professions = {}
        
        for participant in participant_data:
            persona = participant.get("persona", {})
            if persona:
                # Age
                age = persona.get("age")
                if isinstance(age, (int, float)):
                    ages.append(float(age))
                
                # Gender
                gender = persona.get("gender", "unknown")
                genders[gender] = genders.get(gender, 0) + 1
                
                # Education
                education = persona.get("education", "unknown")
                educations[education] = educations.get(education, 0) + 1
                
                # ATI score
                ati = persona.get("ati_score")
                if isinstance(ati, (int, float)):
                    ati_scores.append(float(ati))
                
                # Profession
                profession = persona.get("profession", "unknown")
                professions[profession] = professions.get(profession, 0) + 1
        
        def stats(vals):
            if not vals:
                return {"mean": None, "std": None, "min": None, "max": None, "n": 0}
            return {
                "mean": round(statistics.mean(vals), 2),
                "std": round(statistics.stdev(vals), 2) if len(vals) > 1 else 0.0,
                "min": min(vals),
                "max": max(vals),
                "n": len(vals),
            }
        
        return {
            "age_distribution": stats(ages),
            "gender_distribution": genders,
            "education_distribution": educations,
            "ati_score_distribution": stats(ati_scores),
            "profession_distribution": professions,
        }

    def _calculate_discriminant_ability(self, participant_data: List[Dict[str, Any]], items: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """
        Calculate discriminant ability: t-test comparing empathic vs non-empathic scenarios (PETS Section 7.2).
        
        Args:
            participant_data: List of participant evaluation data (should contain persona with empathy_condition)
            items: List of scale items
            
        Returns:
            Dictionary with t-test results, or None if data insufficient
        """
        empathic_ratings = []
        non_empathic_ratings = []
        
        for participant in participant_data:
            persona = participant.get("persona", {})
            empathy_condition = persona.get("empathy_condition")
            
            if empathy_condition is None:
                continue
            
            # Collect all ratings for this participant
            ratings = participant.get("ratings", [])
            participant_ratings = []
            for rating_obj in ratings:
                rating = rating_obj.get("rating")
                if rating is not None:
                    participant_ratings.append(float(rating))
            
            if participant_ratings:
                if empathy_condition == "empathic":
                    empathic_ratings.extend(participant_ratings)
                elif empathy_condition == "non_empathic":
                    non_empathic_ratings.extend(participant_ratings)
        
        if not empathic_ratings or not non_empathic_ratings:
            return None
        
        try:
            from scipy import stats
            t_stat, p_value = stats.ttest_ind(empathic_ratings, non_empathic_ratings)
            
            # Calculate Cohen's d
            empathic_mean = np.mean(empathic_ratings)
            non_empathic_mean = np.mean(non_empathic_ratings)
            pooled_std = np.sqrt((np.var(empathic_ratings) + np.var(non_empathic_ratings)) / 2)
            cohens_d = (empathic_mean - non_empathic_mean) / pooled_std if pooled_std > 0 else 0.0
            
            return {
                "empathic_mean": round(float(empathic_mean), 2),
                "non_empathic_mean": round(float(non_empathic_mean), 2),
                "t_statistic": round(float(t_stat), 3),
                "p_value": round(float(p_value), 6),
                "cohens_d": round(float(cohens_d), 3),
                "significant": bool(p_value < 0.001),  # Convert numpy bool_ to Python bool for JSON serialization
                "n_empathic": len(empathic_ratings),
                "n_non_empathic": len(non_empathic_ratings)
            }
        except ImportError:
            # Fallback if scipy not available
            print("      [WARN] scipy not available, cannot calculate discriminant ability", flush=True)
            return None
        except Exception as e:
            print(f"      [WARN] Error calculating discriminant ability: {e}", flush=True)
            return None
    
    def _calculate_cronbach_alpha(self, ratings_matrix: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Calculate Cronbach's alpha for internal consistency (PETS Section 7.2).
        
        Args:
            ratings_matrix: 2D numpy array (n_participants × n_items) with ratings
            
        Returns:
            Dictionary with alpha and confidence interval, or None if calculation fails
        """
        if ratings_matrix.size == 0:
            return None
        
        try:
            # Remove rows/columns with all NaN
            valid_rows = ~np.isnan(ratings_matrix).all(axis=1)
            valid_cols = ~np.isnan(ratings_matrix).all(axis=0)
            
            if not np.any(valid_rows) or not np.any(valid_cols):
                return None
            
            ratings_clean = ratings_matrix[valid_rows][:, valid_cols]
            
            if ratings_clean.size == 0:
                return None
            
            n_items = ratings_clean.shape[1]
            if n_items < 2:
                return None
            
            # Calculate item variances
            item_variances = np.nanvar(ratings_clean, axis=0, ddof=1)
            total_variance = np.nanvar(np.nansum(ratings_clean, axis=1), ddof=1)
            
            # Cronbach's alpha formula
            sum_item_variances = np.nansum(item_variances)
            if total_variance == 0:
                return None
            
            alpha = (n_items / (n_items - 1)) * (1 - sum_item_variances / total_variance)
            
            # Simple confidence interval approximation (95% CI)
            # Using standard error approximation
            n_participants = ratings_clean.shape[0]
            se = np.sqrt(2 * n_items / ((n_items - 1) * n_participants))
            ci_lower = max(0.0, alpha - 1.96 * se)
            ci_upper = min(1.0, alpha + 1.96 * se)
            
            return {
                "alpha": round(float(alpha), 3),
                "ci_lower": round(float(ci_lower), 3),
                "ci_upper": round(float(ci_upper), 3),
                "n_items": n_items,
                "n_participants": n_participants
            }
        except Exception as e:
            print(f"      [WARN] Error calculating Cronbach's alpha: {e}", flush=True)
            return None
    
    def _calculate_factor_scores(self, item_statistics: List[Dict[str, Any]], 
                                 factor_structure: Optional[Dict[int, int]]) -> Dict[str, Dict[str, float]]:
        """
        Calculate mean and std for each factor (PETS Table 8).
        
        Args:
            item_statistics: List of item statistics from _summarize
            factor_structure: Dictionary mapping item_id to factor_idx, or None
            
        Returns:
            Dictionary mapping factor_name to {"mean": float, "std": float, "n_items": int}
        """
        if not factor_structure:
            return {}
        
        # Convert string keys to int if needed (JSON serialization)
        factor_structure_int = {}
        for k, v in factor_structure.items():
            try:
                item_id = int(k) if isinstance(k, str) else k
                factor_idx = int(v) if isinstance(v, str) else v
                factor_structure_int[item_id] = factor_idx
            except (ValueError, TypeError):
                continue
        
        # Group items by factor
        factor_items = {}  # {factor_idx: [item_stats]}
        for item_stat in item_statistics:
            item_id = item_stat.get("item_id")
            if item_id in factor_structure_int:
                factor_idx = factor_structure_int[item_id]
                if factor_idx not in factor_items:
                    factor_items[factor_idx] = []
                factor_items[factor_idx].append(item_stat)
        
        # Calculate mean and std for each factor
        factor_scores = {}
        for factor_idx, items in factor_items.items():
            factor_name = f"Factor{factor_idx+1}"
            means = []
            for item_stat in items:
                mean = item_stat.get("rating_statistics", {}).get("mean")
                if mean is not None:
                    means.append(float(mean))
            
            if means:
                factor_scores[factor_name] = {
                    "mean": round(float(np.mean(means)), 2),
                    "std": round(float(np.std(means)), 2) if len(means) > 1 else 0.0,
                    "n_items": len(means)
                }
        
        return factor_scores

    def _items_from_plain_text(self, txt_path: Path) -> List[Dict[str, str]]:
        if not txt_path.exists():
            return []
        text = txt_path.read_text(encoding="utf-8", errors="replace")
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        items = []
        for ln in lines:
            # naive: treat every non-empty line as potential item
            if len(ln) > 3:
                items.append({"dimension": "Baseline", "item_text": ln})
        return items

