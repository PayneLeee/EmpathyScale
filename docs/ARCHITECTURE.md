# System Architecture

This document describes the core architecture, design patterns, and technical structure of the EmpathyScale project.

## Overview

EmpathyScale uses a **modular multi-agent architecture** with:
- **Agent Groups**: High-level agents handling major workflow tasks
- **Sub-Agents**: Specialized components within groups for focused tasks
- **Externalized Prompts**: All prompts stored in JSON files for flexibility
- **PromptManager**: Centralized prompt loading and management
- **DataManager**: Timestamp-isolated data storage

## Architecture Principles

### 1. Separation of Concerns
- **Prompts** (what agents say/think) are separate from **Code** (how agents work)
- Prompts can be modified without code changes
- Code can be refactored without changing prompts

### 2. Externalization
- All prompts in JSON files, not hardcoded
- Enables easy iteration, version control, and non-developer modification

### 3. Modularity
- Each agent group is self-contained
- Clear interfaces between components
- Independent development and testing

### 4. Consistency
- Standardized initialization patterns
- Consistent naming conventions
- Uniform prompt structures

## Agent Group Structure

### Hierarchical Organization

```
MultiAgentWorkflow (main.py)
├── InterviewAgentGroup
│   ├── Main Agent (LangChain AgentExecutor)
│   ├── Tools (save_interview_data, get_interview_progress, delegate_to_sub_agent)
│   └── Sub-Agents
│       ├── TaskCollectorAgent
│       ├── EnvironmentAnalyzerAgent
│       ├── PlatformSpecialistAgent
│       └── CollaborationExpertAgent
│
└── LiteratureSearchAgentGroup
    ├── LLM Integration (direct ChatOpenAI calls)
    └── Methods (generate_queries, search_and_screen, extract_findings, etc.)
```

### Base Agent Group Pattern

All agent groups follow this structure:

```python
class AgentGroup:
    def __init__(self, api_key: str, model_name: str = "gpt-4", prompts_dir: str = None):
        # 1. Initialize LLM
        self.llm = ChatOpenAI(api_key=api_key, model_name=model_name)
        
        # 2. Initialize PromptManager
        self.prompt_manager = PromptManager(prompts_dir)
        
        # 3. Initialize agent-specific components
        # (memory, tools, sub-agents, state, etc.)
        
        # 4. Load prompts and configure
        self._initialize_from_prompts()
    
    def _initialize_from_prompts(self):
        """Load prompts and configure agent."""
        system_prompt = self.prompt_manager.get_agent_group_prompt(
            "agent_group_name", 
            "system_prompt"
        )
        # Configure agent...
```

## File Organization

### Naming Conventions

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
```

## Prompt Management

### PromptManager Class

**Location**: `utils/prompt_manager.py`

**Key Features**:
- Auto-detects project root and prompts directory
- Loads all prompts from JSON files on initialization
- Provides get, format, and reload methods
- Supports variable formatting using Python `.format()`

**Usage**:
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

### Prompt File Structure

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

## Sub-Agent Pattern

### Purpose
Sub-agents provide focused specialization within an agent group:
- **Focus**: Each handles a narrow, well-defined domain
- **Reusability**: Can be called multiple times
- **Modularity**: Isolated logic, easier to test/modify

### Implementation

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

## Data Management

### DataManager Class

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

**Storage Structure**:
```
data/runs/YYYY-MM-DD_HHMMSS/
├── metadata.json
├── interview_agent_group/
│   ├── summary.json
│   └── conversation.json
└── literature_search_agent_group/
    ├── summary.json
    └── pdfs/...
```

See [DATA_STORAGE.md](./DATA_STORAGE.md) for detailed structure.

## Agent Group Implementations

### InterviewAgentGroup

**Type**: LangChain-based agent with tools

**Components**:
- `ChatOpenAI`: LLM integration
- `AgentExecutor`: Manages agent execution
- `ConversationBufferMemory`: Maintains conversation context
- `Tools`: `save_interview_data`, `get_interview_progress`, `delegate_to_sub_agent`
- `Sub-agents`: 4 specialized sub-agents

**State Management**:
- `interview_data`: Dictionary tracking collected information
- `conversation_history`: List of message objects
- Completion tracking

**Key Methods**:
- `start_interview()`: Returns opening message
- `process_response(user_input)`: Processes user input, returns agent response
- `is_interview_complete()`: Checks if sufficient data collected
- `get_interview_summary()`: Returns structured summary

### LiteratureSearchAgentGroup

**Type**: Direct LLM integration (no LangChain tools)

**Components**:
- `ChatOpenAI`: LLM for query generation, screening, extraction
- `ResearchAPIClient`: Interface to arXiv and Semantic Scholar
- `PromptManager`: Prompt loading

**State Management**:
- `papers`: Raw search results
- `screened_papers`: Relevance-filtered papers
- `extracted_findings`: Processed findings
- `downloaded`: PDF download status

**Key Methods**:
- `generate_queries(interview_summary)`: Generate search queries
- `search_and_screen(queries)`: Search and filter papers
- `extract_findings(papers)`: Extract structured findings
- `download_pdfs(papers, run_id)`: Download and organize PDFs
- `run_complete_search(interview_summary, run_id)`: Execute full workflow

## Prompt Usage Patterns

### 1. System Prompt
Defines agent role and behavior:
```python
system_prompt = prompt_manager.get_agent_group_prompt(
    "interview_agent_group",
    "system_prompt"
)
```

### 2. Template Prompts with Variables
Dynamic content from context:
```python
prompt = template.format(
    context=interview_summary.get('assessment_context'),
    platform=interview_summary.get('robot_platform'),
    interaction_modalities=interview_summary.get('interaction_modalities')
)
```

### 3. Error Messages
User-facing error handling:
```python
error_msg = prompt_manager.format_agent_group_prompt(
    "interview_agent_group",
    "error_message",
    error=str(e)
)
```

### 4. Sub-Agent Prompts
Specialized task prompts:
```python
prompt = prompt_manager.get_agent_group_prompt(
    "interview_agent_group",
    "task_collector_prompt"
)
```

## Adding New Agent Groups

See [HOW_TO_ADD_AGENTS.md](./HOW_TO_ADD_AGENTS.md) for step-by-step guide.

**Quick Checklist**:
1. Create `agents/{name}_agent_group.py` with class following base pattern
2. Create `prompts/{name}_agent_group.json` with all prompts
3. Register in `main.py` `_initialize_agents()`
4. Add to workflow execution if needed

## Best Practices

### Prompt Design
- **Be explicit**: Clearly state role, goals, constraints
- **Use emphasis**: Use `**bold**` or ALL CAPS for critical instructions
- **Include examples**: Show desired behavior
- **Clear variables**: Descriptive names like `{context}`, not `{x}`

### Agent Group Design
- **Single responsibility**: One clear purpose per group
- **Clear state**: Use well-defined data structures
- **Error handling**: Graceful failures with user-friendly messages
- **Prompt reloading**: Support hot-reload for development

### File Organization
- **Naming consistency**: Follow `{name}_agent_group.{py,json}` pattern
- **Project structure**: Keep prompts external, code in `agents/`
- **Version control**: Commit prompt changes for history

## Troubleshooting

### Prompt Not Found
- Verify JSON file exists: `prompts/{name}_agent_group.json`
- Check JSON key exists and is valid
- Validate JSON syntax

### Variable Format Error
- Ensure all `{variables}` have corresponding values
- Verify variable names match exactly (case-sensitive)
- Use `.get(key, 'default')` for optional variables

### Agent Group Not Found
- Verify prompt file exists and name matches
- Check PromptManager loaded file during initialization
- Ensure agent group registered in `main.py`

## Summary

The EmpathyScale architecture prioritizes:
- **Modularity**: Independent, testable components
- **Flexibility**: Externalized prompts enable rapid iteration
- **Consistency**: Standardized patterns across all agent groups
- **Maintainability**: Clear separation of concerns
- **Extensibility**: Easy to add new agent groups following established patterns

This design enables rapid development, easy debugging, and seamless integration of new capabilities while maintaining code quality and prompt version control.
