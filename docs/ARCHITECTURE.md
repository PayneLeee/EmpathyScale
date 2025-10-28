# Agent Group and Prompt Architecture

This document describes the design and structure of the agent group system and prompt management in the EmpathyScale project.

## Table of Contents

1. [Overview](#overview)
2. [Agent Group Architecture](#agent-group-architecture)
3. [Prompt Management System](#prompt-management-system)
4. [File Organization](#file-organization)
5. [Agent Group Structure](#agent-group-structure)
6. [Sub-Agent Pattern](#sub-agent-pattern)
7. [Prompt Usage Patterns](#prompt-usage-patterns)
8. [Adding New Agent Groups](#adding-new-agent-groups)
9. [Best Practices](#best-practices)

---

## Overview

The EmpathyScale project uses a **multi-agent group architecture** where:

- **Agent Groups** are high-level agents that handle major workflow tasks (e.g., conducting interviews, searching literature)
- **Sub-Agents** are specialized agents within a group that focus on specific aspects of the task
- **Prompts** are externalized in JSON files, making them easy to modify, version control, and debug
- **PromptManager** centralizes all prompt loading, formatting, and management

This design enables:
- ✅ **Modularity**: Each agent group is self-contained
- ✅ **Flexibility**: Prompts can be modified without code changes
- ✅ **Debuggability**: Prompts are visible and version-controlled
- ✅ **Extensibility**: New agent groups can be added easily
- ✅ **Specialization**: Sub-agents handle domain-specific tasks

---

## Agent Group Architecture

### Hierarchical Structure

```
MultiAgentWorkflow (main.py)
├── InterviewAgentGroup
│   ├── Main Agent (uses LangChain AgentExecutor)
│   ├── Tools (save_interview_data, get_interview_progress, delegate_to_sub_agent)
│   └── Sub-Agents
│       ├── TaskCollectorAgent
│       ├── EnvironmentAnalyzerAgent
│       ├── PlatformSpecialistAgent
│       └── CollaborationExpertAgent
│
└── LiteratureSearchAgentGroup
    ├── Main Agent (uses LLM directly)
    └── Methods (generate_queries, search_and_screen, extract_findings, etc.)
```

### Agent Group Components

Each agent group typically includes:

1. **Main Agent Class** - The primary agent that orchestrates the workflow
2. **PromptManager Integration** - Uses PromptManager to load prompts from JSON
3. **LLM Instance** - ChatOpenAI instance for language model interactions
4. **State Management** - Internal data structures to track progress
5. **Tools (optional)** - LangChain tools for complex agent groups
6. **Sub-Agents (optional)** - Specialized sub-agents for specific tasks

---

## Prompt Management System

### PromptManager Class

The `PromptManager` (`utils/prompt_manager.py`) is the central system for managing all prompts:

**Key Features:**
- Auto-detects project root and prompts directory
- Loads all prompts from JSON files on initialization
- Provides methods to get, format, and reload prompts
- Supports variable formatting in prompts using Python `.format()`

**Key Methods:**

```python
# Get a specific prompt
prompt_manager.get_agent_group_prompt("interview_agent_group", "system_prompt")

# Format a prompt with variables
prompt_manager.format_agent_group_prompt(
    "literature_search_agent_group", 
    "query_generation_prompt",
    context="...",
    platform="...",
    interaction_modalities="..."
)

# Reload prompts for an agent group (hot-reload during development)
prompt_manager.reload_agent_group_prompts("interview_agent_group")
```

### Prompt Directory Structure

```
prompts/
├── interview_agent_group.json
└── literature_search_agent_group.json
```

**Naming Convention:**
- Each agent group has a corresponding JSON file: `{agent_group_name}.json`
- The file name MUST match the agent group name exactly
- File is loaded automatically when PromptManager initializes

---

## File Organization

### Agent Group Files

```
agents/
├── interview_agent_group.py          # InterviewAgentGroup class
└── literature_search_agent_group.py  # LiteratureSearchAgentGroup class
```

**Naming Convention:**
- Agent group file: `{agent_group_name}.py`
- Class name: `{AgentGroupName}` (PascalCase, underscores removed)

### Prompt Files

```
prompts/
├── interview_agent_group.json         # All prompts for InterviewAgentGroup
└── literature_search_agent_group.json # All prompts for LiteratureSearchAgentGroup
```

**Structure of Prompt JSON:**

```json
{
  "system_prompt": "Main system prompt for the agent...",
  "opening_message": "Initial message to user...",
  "error_message": "Error message template: {error}",
  "completion_message": "Completion message...",
  "sub_agent_name_prompt": "Prompt for specific sub-agent...",
  "template_prompt": "Prompt with {variables} for formatting"
}
```

---

## Agent Group Structure

### Base Structure

Every agent group follows this pattern:

```python
class ExampleAgentGroup:
    def __init__(self, api_key: str, model_name: str = "gpt-4", prompts_dir: str = None):
        # 1. Initialize LLM
        self.llm = ChatOpenAI(api_key=api_key, model_name=model_name)
        
        # 2. Initialize PromptManager
        self.prompt_manager = PromptManager(prompts_dir)
        
        # 3. Initialize agent-specific components
        # (memory, tools, sub-agents, state, etc.)
        
        # 4. Load prompts and configure agent
        self._initialize_from_prompts()
    
    def _initialize_from_prompts(self):
        """Load prompts and configure agent."""
        system_prompt = self.prompt_manager.get_agent_group_prompt(
            "example_agent_group", 
            "system_prompt"
        )
        # Configure agent with prompts...
```

### Example: InterviewAgentGroup

```python
class InterviewAgentGroup:
    def __init__(self, api_key: str, ...):
        # LLM and PromptManager
        self.llm = ChatOpenAI(...)
        self.prompt_manager = PromptManager(prompts_dir)
        
        # State tracking
        self.interview_data = {
            "assessment_context": None,
            "robot_platform": None,
            "interaction_modalities": None,
            # ...
        }
        
        # Sub-agents
        self.sub_agents = self._initialize_sub_agents()
        
        # LangChain components
        self.prompt = ChatPromptTemplate.from_messages([...])
        self.tools = self._create_tools()
        self.agent_executor = AgentExecutor(...)
    
    def _get_system_prompt(self) -> str:
        """Load system prompt from JSON."""
        return self.prompt_manager.get_agent_group_prompt(
            "interview_agent_group", 
            "system_prompt"
        )
```

### Example: LiteratureSearchAgentGroup

```python
class LiteratureSearchAgentGroup:
    def __init__(self, api_key: str, ...):
        # LLM and PromptManager
        self.llm = ChatOpenAI(api_key=api_key, model_name=model_name)
        self.prompt_manager = PromptManager(prompts_dir)
        
        # State tracking
        self.papers = []
        self.screened_papers = []
        self.extracted_findings = []
    
    def generate_queries(self, interview_summary: Dict) -> List[str]:
        """Use prompt to generate search queries."""
        template = self.prompt_manager.get_agent_group_prompt(
            "literature_search_agent_group",
            "query_generation_prompt"
        )
        prompt = template.format(
            context=interview_summary.get('assessment_context', 'N/A'),
            platform=interview_summary.get('robot_platform', 'N/A'),
            interaction_modalities=interview_summary.get('interaction_modalities', 'N/A'),
            goals=", ".join(interview_summary.get('assessment_goals', []))
        )
        response = self.llm.invoke(prompt)
        # Parse and return queries...
```

---

## Sub-Agent Pattern

### Purpose

Sub-agents allow an agent group to delegate specific tasks to specialized components. They provide:
- **Focus**: Each sub-agent has a narrow, well-defined responsibility
- **Reusability**: Sub-agents can be called multiple times with different inputs
- **Modularity**: Sub-agent logic is isolated and easier to test/modify

### Implementation Pattern

```python
class MainAgentGroup:
    def _initialize_sub_agents(self) -> Dict[str, any]:
        """Initialize sub-agents."""
        return {
            "task_collector": TaskCollectorAgent(self.prompt_manager),
            "environment_analyzer": EnvironmentAnalyzerAgent(self.prompt_manager),
            # ...
        }
    
    def _create_tools(self) -> List[Tool]:
        """Create tools including delegation to sub-agents."""
        def delegate_to_sub_agent(sub_agent_name: str, task: str) -> str:
            if sub_agent_name in self.sub_agents:
                return self.sub_agents[sub_agent_name].process_task(task)
            return f"Sub-agent {sub_agent_name} not found."
        
        return [
            Tool(
                name="delegate_to_sub_agent",
                description="Delegate specific tasks to specialized sub-agents",
                func=delegate_to_sub_agent
            ),
            # ... other tools
        ]
```

### Sub-Agent Structure

```python
class TaskCollectorAgent:
    """Sub-agent specialized in collecting task-related information."""
    
    def __init__(self, prompt_manager: PromptManager):
        self.prompt_manager = prompt_manager
    
    def process_task(self, task_description: str) -> str:
        """Process task-related information."""
        prompt = self.prompt_manager.get_agent_group_prompt(
            "interview_agent_group",  # Parent agent group name
            "task_collector_prompt"    # Sub-agent prompt key
        )
        return f"Task analysis: {prompt} - Processing: {task_description}"
```

**Key Points:**
- Sub-agents are simple classes with a `process_task()` method
- They receive the `PromptManager` to access prompts
- Prompts are stored in the parent agent group's JSON file
- Sub-agent prompts use keys like `{sub_agent_name}_prompt`

---

## Prompt Usage Patterns

### Pattern 1: System Prompt

Used to define the agent's role, behavior, and capabilities:

```python
# In agent group initialization
system_prompt = self.prompt_manager.get_agent_group_prompt(
    "interview_agent_group",
    "system_prompt"
)

# Used in LangChain prompt template
self.prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
])
```

**In JSON:**
```json
{
  "system_prompt": "You are an expert interviewer... Your goal is... IMPORTANT: You MUST..."
}
```

### Pattern 2: Template Prompts with Variables

Used when prompts need dynamic content:

```python
# Format prompt with variables
prompt_template = self.prompt_manager.get_agent_group_prompt(
    "literature_search_agent_group",
    "query_generation_prompt"
)
formatted_prompt = prompt_template.format(
    context=interview_summary.get('assessment_context', 'N/A'),
    platform=interview_summary.get('robot_platform', 'N/A'),
    interaction_modalities=interview_summary.get('interaction_modalities', 'N/A'),
    goals=", ".join(interview_summary.get('assessment_goals', []))
)
```

**In JSON:**
```json
{
  "query_generation_prompt": "Based on this interview summary...\n\nContext: {context}\nPlatform: {platform}\nModalities: {interaction_modalities}\nGoals: {goals}\n\nGenerate queries..."
}
```

### Pattern 3: Error Messages

Used for user-facing error messages:

```python
error_msg = self.prompt_manager.format_agent_group_prompt(
    "interview_agent_group",
    "error_message",
    error=str(e)
)
```

**In JSON:**
```json
{
  "error_message": "I apologize, but I encountered an error: {error}. Could you please rephrase?"
}
```

### Pattern 4: Sub-Agent Prompts

Used by sub-agents for specialized tasks:

```python
# In sub-agent
prompt = self.prompt_manager.get_agent_group_prompt(
    "interview_agent_group",      # Parent agent group
    "task_collector_prompt"        # Sub-agent specific prompt
)
```

**In JSON:**
```json
{
  "task_collector_prompt": "Focus on understanding the specific collaborative tasks...",
  "environment_analyzer_prompt": "Analyze the environmental setting...",
  "platform_specialist_prompt": "Focus on the robot platform characteristics..."
}
```

---

## Adding New Agent Groups

### Step 1: Create Agent Group Class

Create `agents/{agent_group_name}_agent_group.py`:

```python
from langchain_openai import ChatOpenAI
from utils.prompt_manager import PromptManager

class NewAgentGroup:
    def __init__(self, api_key: str, model_name: str = "gpt-4", prompts_dir: str = None):
        self.llm = ChatOpenAI(api_key=api_key, model_name=model_name)
        self.prompt_manager = PromptManager(prompts_dir)
        # Initialize your agent...
    
    def _get_system_prompt(self) -> str:
        return self.prompt_manager.get_agent_group_prompt(
            "new_agent_group",  # Must match filename
            "system_prompt"
        )
```

### Step 2: Create Prompt File

Create `prompts/{agent_group_name}_agent_group.json`:

```json
{
  "system_prompt": "You are a specialized agent for...",
  "task_prompt": "Your task is to...",
  "completion_message": "Task completed successfully."
}
```

### Step 3: Register in Main Workflow

Add to `main.py`:

```python
def _initialize_agents(self):
    # Existing agents
    self.agents['interview'] = InterviewAgentGroup(...)
    self.agents['literature'] = LiteratureSearchAgentGroup(...)
    
    # New agent
    self.agents['new_agent'] = NewAgentGroup(
        api_key=self.config["openai_api_key"]
    )
```

**Important:** The agent group name used in code must match the JSON filename (without `.json` extension).

---

## Best Practices

### 1. Prompt Design

- **Be Explicit**: Clearly state the agent's role, goals, and constraints
- **Use Emphasis**: Use `**bold**` or ALL CAPS for critical instructions
- **Include Examples**: Show desired behavior through examples in prompts
- **Variable Names**: Use clear, descriptive variable names in templates (e.g., `{context}`, `{platform}`)

### 2. Prompt Organization

- **Group by Function**: Organize prompts logically in JSON (system, tools, sub-agents, etc.)
- **Use Descriptive Keys**: Use clear prompt keys like `query_generation_prompt`, not `prompt1`
- **Document Prompts**: Add comments in code explaining what each prompt does

### 3. Agent Group Design

- **Single Responsibility**: Each agent group should have one clear purpose
- **State Management**: Use clear data structures to track agent state
- **Error Handling**: Always handle errors gracefully with user-friendly messages
- **Prompt Reloading**: Support prompt reloading for development/debugging

### 4. Sub-Agent Design

- **Narrow Focus**: Each sub-agent should handle a specific domain (tasks, environment, platform)
- **Simple Interface**: Sub-agents should have a simple `process_task()` method
- **Prompt Integration**: Sub-agents should use prompts from the parent agent group's JSON file

### 5. File Organization

- **Naming Consistency**: Follow `{name}_agent_group.py` and `{name}_agent_group.json` pattern
- **Project Structure**: Keep prompts external (in `prompts/`) and code in `agents/`
- **Version Control**: Commit prompt changes so they're tracked in git history

---

## Key Design Principles

### 1. Separation of Concerns

- **Prompts** (what the agent says/thinks) are separate from **Code** (how the agent works)
- Prompts can be modified without changing code
- Code can be refactored without changing prompts

### 2. Externalization

- All prompts are in JSON files, not hardcoded in Python
- This enables:
  - Easy prompt iteration and A/B testing
  - Version control of prompt changes
  - Non-developers to modify prompts
  - Prompt debugging and inspection

### 3. Hierarchical Organization

- **Agent Groups** → Main workflow tasks
- **Sub-Agents** → Specialized subtasks
- **Prompts** → Organized by agent group and purpose

### 4. Consistency

- All agent groups follow the same initialization pattern
- All prompts follow the same JSON structure
- All sub-agents follow the same interface pattern

---

## Example: Complete Agent Group Lifecycle

```python
# 1. Initialize
agent = InterviewAgentGroup(api_key="...")

# 2. Agent uses prompts from JSON automatically
# System prompt loaded during initialization
# Tools use prompts when invoked

# 3. Process input
response = agent.process_response("We want to evaluate robot empathy in healthcare")

# 4. Agent uses save_interview_data tool
# Tool uses prompts to categorize data

# 5. Get results
summary = agent.get_interview_summary()
# Returns structured data based on prompts and tool usage

# 6. Hot-reload prompts (during development)
agent.reload_prompts()
# System prompt and tools are updated with new prompts
```

---

## Troubleshooting

### Prompt Not Found

**Error:** `KeyError: Prompt not found: interview_agent_group.system_prompt`

**Solution:**
- Check that `prompts/interview_agent_group.json` exists
- Verify the JSON key exists: `"system_prompt"`
- Ensure JSON is valid (use a JSON validator)

### Variable Format Error

**Error:** `ValueError: Missing required variable for prompt formatting`

**Solution:**
- Check that all `{variable}` placeholders in the prompt have corresponding values
- Verify variable names match exactly (case-sensitive)
- Use `.get(key, 'default')` for optional variables

### Agent Group Not Found

**Error:** `KeyError: Agent group 'new_agent_group' not found`

**Solution:**
- Verify the prompt file exists: `prompts/new_agent_group.json`
- Check the agent group name matches the filename (without `.json`)
- Ensure PromptManager loaded the file (check initialization)

---

## Summary

The EmpathyScale project uses a well-structured, modular agent group architecture:

- **Agent Groups** handle major workflow tasks
- **Sub-Agents** provide specialized capabilities
- **PromptManager** centralizes prompt management
- **JSON Files** externalize all prompts
- **Consistent Patterns** ensure maintainability and extensibility

This design enables rapid development, easy debugging, and seamless integration of new agent groups while maintaining code quality and prompt version control.

