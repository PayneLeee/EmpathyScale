---
name: Update Run Files with Phase 1/2 Persona Requirements
overview: "Update all run files to match test_single_scenario_quick.py Phase 1 structure (dual groups: empathic + non-empathic, 100*2=200) and implement Phase 2 with 100*2=200 personas for run_predefined_scenarios.py. Other run files should follow FINALproposal.txt requirements and reuse phase 2 personas for the same scenarios."
todos: []
---

# Update Run Files with Phase 1/2 Persona Requirements

## Overview

Modify all run files to align with `test_single_scenario_quick.py` Phase 1 structure and implement proper Phase 2 persona management according to requirements.

## Key Changes Required

### 1. `run_predefined_scenarios.py`

**Phase 1 Changes:**

- Match `test_single_scenario_quick.py` Phase 1 implementation exactly
- Use dual persona groups: empathic + non-empathic (100*2 = 200 total)
- Generate base personas, then split into empathic/non-empathic groups using `add_interaction_experiences()`
- Save merged personas to `{scenario_id}/selection.json`
- Evaluate separately for each group, then merge results for EFA+CFA
- Use `combined` directory structure for merged evaluation data

**Phase 2 Changes:**

- Generate 100*2 = 200 personas (not 50) for complete evaluation
- Use base scenario name (not `{scenario_id}_selection`) for reusability
- Generate dual groups (empathic + non-empathic) similar to Phase 1
- Save to `{scenario_id}/validation.json`

### 2. `run_baseline_comparison.py`

- Follow FINALproposal.txt requirements
- Use validation personas (phase="validation") from base scenario name
- Reuse same personas for PETS and RoPE evaluation (same scenario)
- Load from `{scenario_id}/validation.json` (not selection.json)

### 3. `run_statistical_item_selection.py`

- Follow FINALproposal.txt requirements
- Phase 1: Use selection personas (`{scenario_id}_selection`)
- Phase 2: Use validation personas (`{scenario_id}_validation`) - independent group
- Ensure proper persona loading and reuse

### 4. `run_ablation_minimal.py`

- Currently empty, may need implementation or removal

### 5. `tools/run_single_variant.py`

- Follow FINALproposal.txt requirements
- Use appropriate phase personas based on evaluation type
- Reuse personas for same scenarios

## Implementation Details

### Phase 1 Dual Groups Pattern (from test_single_scenario_quick.py)

```python
# Load or generate personas for Phase 1
scenario_id = scenario['name']
selection_personas = persona_agent.load_personas(scenario_id, phase="selection")
n_per_group = 100  # 100*2 = 200 total

if selection_personas is None or len(selection_personas) < n_per_group * 2:
    # Generate base personas
    base_personas = persona_agent.generate_personas(scenario, n_personas=n_per_group)
    
    # Create dual groups
    personas_empathic = persona_agent.add_interaction_experiences(
        base_personas.copy(), scenario, interaction_type="empathic"
    )
    personas_non_empathic = persona_agent.add_interaction_experiences(
        base_personas.copy(), scenario, interaction_type="non_empathic"
    )
    
    # Merge and save
    selection_personas = personas_empathic + personas_non_empathic
    persona_agent.save_personas(scenario_id, selection_personas, phase="selection")
    
    # Evaluate separately
    eval_agent.evaluate_items(..., personas=personas_empathic, out_dir=.../empathic)
    eval_agent.evaluate_items(..., personas=personas_non_empathic, out_dir=.../non_empathic)
    
    # Merge results for EFA+CFA
    # Save to .../combined/ directory
```



### Phase 2 Pattern (200 personas)

```python
# Load or generate personas for Phase 2
validation_personas = persona_agent.load_personas(scenario_id, phase="validation")
n_per_group = 100  # 100*2 = 200 total

if validation_personas is None or len(validation_personas) < n_per_group * 2:
    # Generate base personas
    base_personas = persona_agent.generate_personas(scenario, n_personas=n_per_group)
    
    # Create dual groups
    personas_empathic = persona_agent.add_interaction_experiences(
        base_personas.copy(), scenario, interaction_type="empathic"
    )
    personas_non_empathic = persona_agent.add_interaction_experiences(
        base_personas.copy(), scenario, interaction_type="non_empathic"
    )
    
    # Merge and save
    validation_personas = personas_empathic + personas_non_empathic
    persona_agent.save_personas(scenario_id, validation_personas, phase="validation")
    
    # Evaluate with all personas (or separately if needed)
    eval_agent.evaluate_items(..., personas=validation_personas, ...)
```



## Files to Modify

1. `run_predefined_scenarios.py` - Major changes for Phase 1 dual groups and Phase 2 (200 personas)
2. `run_baseline_comparison.py` - Update to use validation personas
3. `run_statistical_item_selection.py` - Ensure proper phase persona usage
4. `tools/run_single_variant.py` - Update persona usage if needed

## Testing Considerations

- Verify Phase 1 uses dual groups (empathic + non-empathic) correctly
- Verify Phase 2 generates/loads 200 personas correctly