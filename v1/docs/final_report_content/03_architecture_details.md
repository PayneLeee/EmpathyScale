# Technical Approach - Architecture Details

## 1. System Architecture

### 1.1 Modular Multi-Agent Architecture

EmpathyScale uses a **modular multi-agent architecture** with:

- **Agent Groups**: High-level agents handling major workflow tasks
- **Sub-Agents**: Specialized components within groups for focused tasks
- **Externalized Prompts**: All prompts stored in JSON files for flexibility
- **PromptManager**: Centralized prompt loading and management
- **DataManager**: Timestamp-isolated data storage

### 1.2 Architecture Principles

#### Separation of Concerns
- **Prompts** (what agents say/think) are separate from **Code** (how agents work)
- Prompts can be modified without code changes
- Code can be refactored without changing prompts

#### Externalization
- All prompts in JSON files, not hardcoded
- Enables easy iteration, version control, and non-developer modification

#### Modularity
- Each agent group is self-contained
- Clear interfaces between components
- Independent development and testing

#### Consistency
- Standardized initialization patterns
- Consistent naming conventions
- Uniform prompt structures

## 2. File Organization

### 2.1 Naming Conventions

**Agent Group Files**:
- File: `agents/{name}_agent_group.py`
- Class: `{Name}AgentGroup` (PascalCase)
- Example: `interview_agent_group.py` → `InterviewAgentGroup`

**Prompt Files**:
- File: `prompts/{name}_agent_group.json`
- Must match agent group name exactly
- Example: `prompts/interview_agent_group.json`

**1:1 Mapping**:
```
agents/interview_agent_group.py ↔ prompts/interview_agent_group.json
agents/literature_search_agent_group.py ↔ prompts/literature_search_agent_group.json
agents/empathy_scale_generation_agent_group.py ↔ prompts/empathy_scale_generation_agent_group.json
agents/evaluation_agent_group.py ↔ prompts/evaluation_agent_group.json
agents/persona_generation_agent.py ↔ prompts/persona_generation_agent.json
```

### 2.2 Project Structure

```
EmpathyScale/
├── agents/                    # Agent group implementations
│   ├── interview_agent_group.py
│   ├── literature_search_agent_group.py
│   ├── empathy_scale_generation_agent_group.py
│   ├── evaluation_agent_group.py
│   ├── item_selection_agent.py
│   ├── persona_generation_agent.py
│   ├── scale_generation_agents.py
│   └── expert_pdfs/          # Reference PDFs for agents
│
├── prompts/                   # Agent prompts (JSON files)
│   ├── interview_agent_group.json
│   ├── literature_search_agent_group.json
│   ├── empathy_scale_generation_agent_group.json
│   ├── evaluation_agent_group.json
│   ├── persona_generation_agent.json
│   └── scale_generation_support.json
│
├── utils/                     # Core utilities
│   ├── prompt_manager.py      # Prompt loading & management
│   ├── data_manager.py        # Data storage & run management
│   ├── research_api.py        # Academic database APIs
│   ├── semantic_deduplication.py  # Semantic deduplication
│   ├── statistical_item_selection.py  # EFA/CFA item selection
│   └── factor_analysis.py     # Factor analysis utilities
│
├── data/                      # Runtime data storage
│   ├── runs/                  # Timestamped run directories
│   ├── ablation_studies/      # Ablation study results
│   ├── baseline_comparison/   # Baseline comparison results
│   └── personas/              # Generated personas
│
└── main.py                    # Main workflow orchestrator
```

## 3. Prompt Management System

### 3.1 PromptManager Class

**Location**: `utils/prompt_manager.py`

**Key Features**:
- Auto-detects project root and prompts directory
- Loads all prompts from JSON files on initialization
- Provides get, format, and reload methods
- Supports variable formatting using Python `.format()`

**Usage Example**:
```python
# Get a specific prompt
prompt = prompt_manager.get_agent_group_prompt(
    "interview_agent_group", 
    "system_prompt"
)

# Format prompt with variables
formatted = prompt_manager.format_agent_group_prompt(
    "literature_search_agent_group",
    "query_generation_prompt",
    context="...",
    platform="...",
    interaction_modalities="..."
)

# Reload prompts (hot-reload during development)
prompt_manager.reload_agent_group_prompts("interview_agent_group")
```

### 3.2 Prompt File Structure

```json
{
  "system_prompt": "Main system prompt defining agent role...",
  "opening_message": "Initial message to user...",
  "error_message": "Error message template: {error}",
  "completion_message": "Completion message...",
  "sub_agent_name_prompt": "Prompt for specific sub-agent...",
  "template_prompt": "Prompt with {variables} for formatting"
}
```

**Organization**:
- Prompts grouped by purpose (system, messages, tools, sub-agents)
- Descriptive keys (e.g., `query_generation_prompt`, not `prompt1`)
- Variables clearly named (e.g., `{context}`, `{platform}`)

## 4. Data Management System

### 4.1 DataManager Class

**Location**: `utils/data_manager.py`

**Purpose**: Handles timestamp-isolated data storage with agent group separation

**Key Methods**:
```python
# Create new run
run_id = data_manager.new_run()

# Save agent group data
data_manager.save_agent_group_data(
    run_id, 
    "interview_agent_group",
    summary, 
    conversation
)

# Complete run
data_manager.complete_run(run_id, ["interview_agent_group", ...])

# Load data
data = data_manager.load_agent_group_data(run_id, "interview_agent_group")

# Get latest run
latest = data_manager.get_latest_run_id()
```

### 4.2 Storage Structure

```
data/runs/YYYY-MM-DD_HHMMSS/
├── metadata.json
├── interview_agent_group/
│   ├── summary.json
│   └── conversation.json
├── literature_search_agent_group/
│   ├── summary.json
│   ├── queries.json
│   ├── screened_papers.json
│   ├── extracted_findings.json
│   └── pdfs/
│       ├── definitions/
│       ├── behaviors/
│       └── measurement/
├── empathy_scale_generation_agent_group/
│   ├── scale_draft.md
│   ├── filtered_scale_draft.md
│   └── generation_summary.json
├── evaluation_agent_group/
│   ├── phase1_evaluation/
│   │   ├── evaluation_summary.json
│   │   └── participant_data.json
│   └── phase2_validation/
│       ├── evaluation_summary.json
│       └── participant_data.json
└── statistical_selection/
    ├── selected_items.json
    ├── efa_results.json
    └── cfa_results.json
```

## 5. Sub-Agent Pattern

### 5.1 Purpose

Sub-agents provide focused specialization within an agent group:
- **Focus**: Each handles a narrow, well-defined domain
- **Reusability**: Can be called multiple times
- **Modularity**: Isolated logic, easier to test/modify

### 5.2 Implementation

```python
class MainAgentGroup:
    def _initialize_sub_agents(self) -> Dict[str, any]:
        return {
            "task_collector": TaskCollectorAgent(self.prompt_manager),
            "environment_analyzer": EnvironmentAnalyzerAgent(self.prompt_manager),
        }
    
    def _create_tools(self) -> List[Tool]:
        def delegate_to_sub_agent(sub_agent_name: str, task: str) -> str:
            if sub_agent_name in self.sub_agents:
                return self.sub_agents[sub_agent_name].process_task(task)
            return f"Sub-agent {sub_agent_name} not found."
        
        return [Tool(name="delegate_to_sub_agent", ...), ...]

class TaskCollectorAgent:
    def __init__(self, prompt_manager: PromptManager):
        self.prompt_manager = prompt_manager
    
    def process_task(self, task_description: str) -> str:
        prompt = self.prompt_manager.get_agent_group_prompt(
            "interview_agent_group",  # Parent agent group
            "task_collector_prompt"    # Sub-agent prompt key
        )
        # Process using prompt...
```

**Key Points**:
- Sub-agents are simple classes with `process_task()` method
- Receive `PromptManager` to access prompts
- Prompts stored in parent agent group's JSON file
- Prompt keys: `{sub_agent_name}_prompt`

## 6. Agent Group Communication

### 6.1 Sequential Workflow

Agent groups communicate through data files:

```
InterviewAgentGroup
    ↓ (saves summary.json)
DataManager
    ↓ (loads summary.json)
LiteratureSearchAgentGroup
    ↓ (saves findings.json)
DataManager
    ↓ (loads findings.json)
EmpathyScaleGenerationAgentGroup
    ...
```

### 6.2 Data Flow

Each agent group:
1. Loads input data from previous agent groups
2. Processes data using LLM calls
3. Saves output data for next agent groups
4. Maintains state in memory during execution

### 6.3 Error Handling

- **Graceful Failures**: Each agent group handles errors independently
- **Partial Results**: System continues even if some steps fail
- **Error Logging**: Errors logged to files for debugging
- **User Feedback**: User-friendly error messages displayed

## 7. Extensibility

### 7.1 Adding New Agent Groups

To add a new agent group:

1. Create `agents/{name}_agent_group.py` with class following base pattern
2. Create `prompts/{name}_agent_group.json` with all prompts
3. Register in `main.py` `_initialize_agents()`
4. Add to workflow execution if needed

### 7.2 Modifying Existing Agents

- **Prompts**: Modify JSON files (no code changes needed)
- **Behavior**: Modify Python code (prompts remain unchanged)
- **Hot-Reload**: Prompts can be reloaded during development

## 8. Best Practices

### 8.1 Prompt Design
- **Be explicit**: Clearly state role, goals, constraints
- **Use emphasis**: Use `**bold**` or ALL CAPS for critical instructions
- **Include examples**: Show desired behavior
- **Clear variables**: Descriptive names like `{context}`, not `{x}`

### 8.2 Agent Group Design
- **Single responsibility**: One clear purpose per group
- **Clear state**: Use well-defined data structures
- **Error handling**: Graceful failures with user-friendly messages
- **Prompt reloading**: Support hot-reload for development

### 8.3 File Organization
- **Naming consistency**: Follow `{name}_agent_group.{py,json}` pattern
- **Project structure**: Keep prompts external, code in `agents/`
- **Version control**: Commit prompt changes for history
