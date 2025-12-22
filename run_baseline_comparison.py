"""
Baseline Comparison Experiment

Evaluates PETS and RoPE baseline scales using existing personas
for each scenario (collab_robot_assembly, home_service_robot, counseling_chatbot).

Usage:
    python run_baseline_comparison.py
"""

from pathlib import Path
import sys
import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any

# Force unbuffered output for real-time progress display
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

# Ensure local imports work when run as script
sys.path.append(os.path.join(os.path.dirname(__file__), "agents"))
sys.path.append(os.path.join(os.path.dirname(__file__), "utils"))

from agents.evaluation_agent_group import EvaluationAgentGroup
from utils.prompt_manager import PromptManager


def print_header(text: str, char: str = "="):
    """Print a formatted header."""
    width = 80
    print(f"\n{char * width}", flush=True)
    print(f"{text:^{width}}", flush=True)
    print(f"{char * width}\n", flush=True)


def print_step(step_num: int, total_steps: int, description: str):
    """Print a step indicator."""
    print(f"[{step_num}/{total_steps}] {description}...", flush=True)


def print_success(message: str):
    """Print a success message."""
    print(f"[OK] {message}", flush=True)


def print_info(message: str):
    """Print an info message."""
    print(f"[INFO] {message}", flush=True)


def print_warning(message: str):
    """Print a warning message."""
    print(f"[WARN] {message}", flush=True)


def print_error(message: str):
    """Print an error message."""
    print(f"[ERROR] {message}", flush=True)


SCENARIOS = [
    {
        "name": "collab_robot_assembly",
        "assessment_context": "factory assembly, human-robot teammate",
        "robot_platform": "collaborative arm",
        "interaction_modalities": "gesture + voice + visual display",
        "collaboration_pattern": "turn-taking assembly",
        "environmental_setting": "factory floor",
    },
    {
        "name": "home_service_robot",
        "assessment_context": "home assistant supporting daily tasks",
        "robot_platform": "mobile service robot",
        "interaction_modalities": "speech + navigation cues",
        "collaboration_pattern": "assistive",
        "environmental_setting": "home",
    },
    {
        "name": "counseling_chatbot",
        "assessment_context": "text-based counseling bot",
        "robot_platform": "chatbot",
        "interaction_modalities": "text chat",
        "collaboration_pattern": "supportive dialogue",
        "environmental_setting": "remote",
    },
]


def extract_pets_items(txt_path: Path) -> List[Dict[str, str]]:
    """
    Extract PETS items from text file.
    
    Extracts 10 items:
    - PETS-ER (Emotional Responsiveness): E1-E6
    - PETS-UT (Understanding and Trust): U1-U4
    
    Returns:
        List of item dictionaries with 'dimension' and 'item_text' keys
    """
    if not txt_path.exists():
        print_error(f"PETS text file not found: {txt_path}")
        return []
    
    text = txt_path.read_text(encoding="utf-8", errors="replace")
    items = []
    
    # Find Table 1 section - look for "Table 1:" or "PETS-ER Emotional Responsiveness"
    table1_start = text.find("Table 1:")
    if table1_start == -1:
        # Try alternative: look for PETS-ER header
        table1_start = text.find("PETS-ER Emotional Responsiveness")
        if table1_start == -1:
            print_error("Could not find Table 1 in PETS text file")
            return []
    
    # Extract section around Table 1 (next 2000 characters should contain the items)
    table_section = text[table1_start:table1_start+2000]
    
    # Pattern to match item lines: E1, E2, ..., E6, U1, U2, U3, U4
    # Format: "E1 The system considered my mental state."
    # Handle multi-line items (E6 spans two lines)
    # Match: E1-U4 followed by text, optionally continuing on next line if it doesn't start with E/U/PETS/CHI
    lines = table_section.split('\n')
    seen_ids = set()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Check if line starts with item ID
        item_match = re.match(r'^(E[1-6]|U[1-4])\s+(.+)$', line)
        if item_match:
            item_id = item_match.group(1)
            item_text = item_match.group(2).strip()
            
            # Check if next line continues the item (for E6)
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # If next line doesn't start with E/U/PETS/CHI and is short, it's likely continuation
                if (next_line and 
                    not re.match(r'^(E[1-6]|U[1-4]|PETS|CHI)', next_line, re.IGNORECASE) and
                    len(next_line) < 100):
                    item_text += " " + next_line
                    i += 1  # Skip next line
            
            # Skip if we've seen this ID (avoid duplicates)
            if item_id not in seen_ids:
                seen_ids.add(item_id)
                # Determine dimension
                if item_id.startswith('E'):
                    dimension = "PETS-ER"
                elif item_id.startswith('U'):
                    dimension = "PETS-UT"
                else:
                    dimension = "Unknown"
                
                items.append({
                    "dimension": dimension,
                    "item_text": item_text
                })
        i += 1
    
    # Sort items: E1-E6, then U1-U4
    def sort_key(item_dict):
        item_text = item_dict.get("item_text", "")
        # Extract item ID from text if it starts with E or U
        for prefix in ['E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'U1', 'U2', 'U3', 'U4']:
            if item_text.startswith(prefix):
                return (0 if prefix.startswith('E') else 1, int(prefix[1:]))
        return (99, 0)
    
    items.sort(key=sort_key)
    
    # Validate: should have exactly 10 items
    if len(items) != 10:
        print_warning(f"Expected 10 PETS items, found {len(items)}")
        # Show what we found
        for item in items:
            print_info(f"  Found: {item.get('dimension')} - {item.get('item_text')[:50]}...")
        print_error(f"Could not extract exactly 10 PETS items. Found {len(items)} items.")
        return []
    
    return items


def extract_rope_items(txt_path: Path) -> List[Dict[str, Any]]:
    """
    Extract RoPE items from text file.
    
    Extracts 18 items (14 main + 4 filler):
    - Empathic Understanding (EU): EU1-EU8
    - Empathic Response (ER): ER1-ER8
    - Filler items (FI): FI1-FI4 (optional, but included)
    
    Returns:
        List of item dictionaries with 'dimension', 'item_text', and 'is_negative' keys
    """
    if not txt_path.exists():
        print_error(f"RoPE text file not found: {txt_path}")
        return []
    
    text = txt_path.read_text(encoding="utf-8", errors="replace")
    items = []
    
    # Pattern to match item lines: EU1-EU8, ER1-ER8, FI1-FI4
    # Format: "EU1 The robot appreciates exactly how the things I experience feel to me."
    # Format with negative: "EU4 (−) The robot does not understand me."
    # Fix: escape the minus sign properly and handle both unicode and ASCII minus
    item_pattern = re.compile(r'^(EU[1-8]|ER[1-8]|FI[1-4])\s+(?:\([−-]\)\s*)?(.+)$', re.MULTILINE)
    
    # Pattern to match negative items (both unicode minus and ASCII hyphen)
    negative_pattern = re.compile(r'\([−-]\)', re.IGNORECASE)
    
    # Extract items
    for match in item_pattern.finditer(text):
        item_id = match.group(1)
        item_text = match.group(2).strip()
        
        # Check if item is negative
        is_negative = bool(negative_pattern.search(match.group(0)))
        
        # Determine dimension based on item ID
        if item_id.startswith('EU'):
            dimension = "Empathic Understanding"
        elif item_id.startswith('ER'):
            dimension = "Empathic Response"
        elif item_id.startswith('FI'):
            dimension = "Filler"
        else:
            dimension = "Unknown"
        
        # Handle multi-line items (e.g., ER1 spans two lines)
        end_pos = match.end()
        if end_pos < len(text):
            next_char = text[end_pos]
            if next_char == '\n':
                # Check next line
                next_line_start = text.find('\n', end_pos) + 1
                if next_line_start < len(text):
                    next_line = text[next_line_start:].split('\n')[0].strip()
                    # If next line doesn't start with EU/ER/FI pattern and is not empty, it might be continuation
                    if next_line and not re.match(r'^(EU[1-8]|ER[1-8]|FI[1-4]|id\s)', next_line, re.IGNORECASE):
                        # Check if it's part of the item
                        if len(next_line) < 100 and not next_line.startswith('Table'):
                            item_text += " " + next_line
        
        items.append({
            "dimension": dimension,
            "item_text": item_text,
            "is_negative": is_negative
        })
    
    # Validate: should have 18 items (14 main + 4 filler) or at least 14 main items
    main_items = [item for item in items if not item.get("dimension") == "Filler"]
    if len(main_items) < 14:
        print_warning(f"Expected at least 14 main RoPE items, found {len(main_items)}")
    
    if len(items) < 14:
        print_error(f"Could not extract sufficient RoPE items. Found {len(items)} items.")
    
    return items


def load_personas(scenario_id: str, phase: str = "selection") -> List[Dict[str, Any]]:
    """
    Load personas from data/personas/{scenario_id}/{phase}.json
    Falls back to personas.json for backward compatibility.
    
    Args:
        scenario_id: Scenario identifier
        phase: Phase identifier ("selection" or "validation"), default "selection"
    
    Returns:
        List of persona dictionaries
    """
    # Try new structure first: {phase}.json
    personas_path = Path(f"data/personas/{scenario_id}/{phase}.json")
    if not personas_path.exists():
        # Fallback to old structure: personas.json (for backward compatibility)
        personas_path = Path(f"data/personas/{scenario_id}/personas.json")
        if not personas_path.exists():
            print_warning(f"Personas file not found: {personas_path}")
            return []
    
    try:
        personas = json.loads(personas_path.read_text(encoding="utf-8"))
        print_success(f"Loaded {len(personas)} personas for scenario '{scenario_id}' from {personas_path.name}")
        return personas
    except Exception as e:
        print_error(f"Failed to load personas: {e}")
        return []


def generate_comparison_report(scenario_id: str, pets_result: Dict[str, Any], rope_result: Dict[str, Any], output_dir: Path):
    """
    Generate comparison report for baseline scales.
    
    Args:
        scenario_id: Scenario identifier
        pets_result: Evaluation result from PETS baseline
        rope_result: Evaluation result from RoPE baseline
        output_dir: Directory to save the report
    """
    report = {
        "scenario_id": scenario_id,
        "generated_at": datetime.now().isoformat(),
        "baselines": {}
    }
    
    # Extract PETS statistics
    if pets_result and "summary_path" in pets_result:
        pets_summary_path = Path(pets_result["summary_path"])
        if pets_summary_path.exists():
            try:
                pets_summary = json.loads(pets_summary_path.read_text(encoding="utf-8"))
                report["baselines"]["PETS"] = {
                    "n_items": pets_summary.get("n_items", 0),
                    "n_participants": pets_summary.get("n_participants", 0),
                    "overall_mean_rating": pets_summary.get("overall_mean_rating"),
                    "dimension_means": {}
                }
                
                # Calculate dimension means for PETS
                item_stats = pets_summary.get("item_statistics", [])
                er_ratings = []
                ut_ratings = []
                for item_stat in item_stats:
                    dimension = item_stat.get("dimension", "")
                    mean_rating = item_stat.get("rating_statistics", {}).get("mean")
                    if mean_rating is not None:
                        if "PETS-ER" in dimension:
                            er_ratings.append(mean_rating)
                        elif "PETS-UT" in dimension:
                            ut_ratings.append(mean_rating)
                
                if er_ratings:
                    report["baselines"]["PETS"]["dimension_means"]["PETS-ER"] = sum(er_ratings) / len(er_ratings)
                if ut_ratings:
                    report["baselines"]["PETS"]["dimension_means"]["PETS-UT"] = sum(ut_ratings) / len(ut_ratings)
            except Exception as e:
                print_warning(f"Failed to parse PETS summary: {e}")
    
    # Extract RoPE statistics
    if rope_result and "summary_path" in rope_result:
        rope_summary_path = Path(rope_result["summary_path"])
        if rope_summary_path.exists():
            try:
                rope_summary = json.loads(rope_summary_path.read_text(encoding="utf-8"))
                report["baselines"]["RoPE"] = {
                    "n_items": rope_summary.get("n_items", 0),
                    "n_participants": rope_summary.get("n_participants", 0),
                    "overall_mean_rating": rope_summary.get("overall_mean_rating"),
                    "dimension_means": {}
                }
                
                # Calculate dimension means for RoPE
                item_stats = rope_summary.get("item_statistics", [])
                eu_ratings = []
                er_ratings = []
                for item_stat in item_stats:
                    dimension = item_stat.get("dimension", "")
                    mean_rating = item_stat.get("rating_statistics", {}).get("mean")
                    if mean_rating is not None:
                        if "Empathic Understanding" in dimension:
                            eu_ratings.append(mean_rating)
                        elif "Empathic Response" in dimension and "Understanding" not in dimension:
                            er_ratings.append(mean_rating)
                
                if eu_ratings:
                    report["baselines"]["RoPE"]["dimension_means"]["Empathic Understanding"] = sum(eu_ratings) / len(eu_ratings)
                if er_ratings:
                    report["baselines"]["RoPE"]["dimension_means"]["Empathic Response"] = sum(er_ratings) / len(er_ratings)
            except Exception as e:
                print_warning(f"Failed to parse RoPE summary: {e}")
    
    # Save report
    report_path = output_dir / "comparison_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print_success(f"Comparison report saved: {report_path}")
    
    return report


def run_baseline_comparison():
    """Main function to run baseline comparison experiment."""
    print_header("BASELINE COMPARISON EXPERIMENT", "=")
    print_info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"Total scenarios: {len(SCENARIOS)}")
    print()
    
    # Load configuration
    config_path = Path("config.json")
    if not config_path.exists():
        print_error("config.json not found")
        return
    
    config = json.loads(config_path.read_text(encoding="utf-8"))
    api_key = config.get("openai_api_key")
    if not api_key:
        print_error("openai_api_key not found in config.json")
        return
    
    # Initialize evaluation agent
    prompt_manager = PromptManager()
    eval_agent = EvaluationAgentGroup(api_key=api_key, prompts_dir=prompt_manager.prompts_dir)
    
    # Baseline text file paths
    txt_dir = Path("agents/expert_pdfs/txt")
    pets_path = txt_dir / "Schmidmaier et al. - 2024 - Perceived Empathy of Technology Scale (PETS) Measuring Empathy of Systems Toward the User.txt"
    rope_path = txt_dir / "Charrier et al. - 2019 - The RoPE Scale a Measure of How Empathic a Robot is Perceived.txt"
    
    # Validate baseline files exist
    if not pets_path.exists():
        print_error(f"PETS text file not found: {pets_path}")
        return
    
    if not rope_path.exists():
        print_error(f"RoPE text file not found: {rope_path}")
        return
    
    # Process each scenario
    for idx, scenario in enumerate(SCENARIOS, 1):
        print_header(f"SCENARIO {idx}/{len(SCENARIOS)}: {scenario['name'].upper()}", "-")
        
        scenario_id = scenario['name']
        
        # Step 1: Load personas (use validation personas - base scenario name, 50 participants)
        print_step(1, 4, f"Loading validation personas for scenario '{scenario_id}'")
        print_info(f"  → Using base scenario name '{scenario_id}' (same as validation phase)")
        print_info(f"  → These personas are reusable for baseline comparison")
        personas = load_personas(scenario_id)
        if not personas:
            print_warning(f"No personas found for scenario '{scenario_id}'. Will generate 50 personas.")
            # Personas will be generated automatically by evaluate_items if not found
            n_participants = 50
        else:
            n_participants = len(personas)
            if n_participants < 50:
                print_warning(f"Only {n_participants} personas found, but 50 expected for validation phase.")
                print_info(f"  → Will use available {n_participants} personas")
            else:
                # Use first 50 if more are available
                personas = personas[:50]
                n_participants = 50
                print_info(f"  → Using {n_participants} personas (validation phase standard)")
        print()
        
        # Step 2: Extract and evaluate PETS
        print_step(2, 4, "Extracting and evaluating PETS baseline")
        print_info("  [2.1] Extracting PETS items from text file...")
        pets_items = extract_pets_items(pets_path)
        
        if len(pets_items) != 10:
            print_error(f"Failed to extract exactly 10 PETS items. Found {len(pets_items)}. Skipping PETS evaluation.")
            pets_result = None
        else:
            print_success(f"Extracted {len(pets_items)} PETS items")
            print_info("  [2.2] Evaluating PETS with personas...")
            
            # Create output directory
            output_dir = Path(f"data/baseline_comparison/{scenario_id}/PETS")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create a dummy run_id for baseline comparison
            run_id = f"baseline_comparison_{scenario_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            try:
                pets_result = eval_agent.evaluate_items(
                    run_id=run_id,
                    items=pets_items,
                    scenario_context=scenario,
                    n_participants=50,  # Use 50 participants (validation phase standard)
                    scenario_id=scenario_id,  # Use base scenario name (reusable personas)
                    personas=personas if personas else None,  # Pass personas if loaded, otherwise let it generate
                    out_dir=output_dir
                )
                print_success("PETS evaluation completed")
            except Exception as e:
                print_error(f"PETS evaluation failed: {e}")
                import traceback
                traceback.print_exc()
                pets_result = None
        print()
        
        # Step 3: Extract and evaluate RoPE
        print_step(3, 4, "Extracting and evaluating RoPE baseline")
        print_info("  [3.1] Extracting RoPE items from text file...")
        rope_items = extract_rope_items(rope_path)
        
        if len(rope_items) < 14:
            print_error(f"Failed to extract sufficient RoPE items. Found {len(rope_items)}. Skipping RoPE evaluation.")
            rope_result = None
        else:
            print_success(f"Extracted {len(rope_items)} RoPE items")
            print_info("  [3.2] Evaluating RoPE with personas...")
            
            # Create output directory
            output_dir = Path(f"data/baseline_comparison/{scenario_id}/RoPE")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Use same run_id structure
            run_id = f"baseline_comparison_{scenario_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            try:
                rope_result = eval_agent.evaluate_items(
                    run_id=run_id,
                    items=rope_items,
                    scenario_context=scenario,
                    n_participants=50,  # Use 50 participants (validation phase standard)
                    scenario_id=scenario_id,  # Use base scenario name (reusable personas)
                    personas=personas if personas else None,  # Pass personas if loaded, otherwise let it generate
                    out_dir=output_dir
                )
                print_success("RoPE evaluation completed")
            except Exception as e:
                print_error(f"RoPE evaluation failed: {e}")
                import traceback
                traceback.print_exc()
                rope_result = None
        print()
        
        # Step 4: Generate comparison report
        print_step(4, 4, "Generating comparison report")
        output_dir = Path(f"data/baseline_comparison/{scenario_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            report = generate_comparison_report(scenario_id, pets_result, rope_result, output_dir)
            print_success("Comparison report generated")
            
            # Print summary
            if "baselines" in report:
                print_info("  [Summary]:")
                if "PETS" in report["baselines"]:
                    pets_data = report["baselines"]["PETS"]
                    print_info(f"    → PETS: {pets_data.get('n_items', 0)} items, mean rating: {pets_data.get('overall_mean_rating', 'N/A')}")
                if "RoPE" in report["baselines"]:
                    rope_data = report["baselines"]["RoPE"]
                    print_info(f"    → RoPE: {rope_data.get('n_items', 0)} items, mean rating: {rope_data.get('overall_mean_rating', 'N/A')}")
        except Exception as e:
            print_error(f"Failed to generate comparison report: {e}")
            import traceback
            traceback.print_exc()
        print()
        
        # Scenario summary
        print_header(f"SCENARIO {idx} COMPLETED", "-")
        print_success(f"Scenario '{scenario_id}' baseline comparison completed")
        print_info(f"Data location: {output_dir}")
        print()
    
    # Final summary
    print_header("BASELINE COMPARISON COMPLETED", "=")
    print_info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_success(f"All {len(SCENARIOS)} scenarios processed")
    print()


if __name__ == "__main__":
    run_baseline_comparison()

