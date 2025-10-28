# How to Add New Agent Groups

This guide walks you through adding a new agent group to the EmpathyScale system.

## Overview

Adding an agent group requires:
1. Creating the agent group class file
2. Creating the corresponding prompt file
3. Registering the agent in the main workflow
4. Testing the new agent

## Step 1: Create Agent Group Class

Create a new file: `agents/{name}_agent_group.py`

### Template

```python
"""
{Name} Agent Group for EmpathyScale
Brief description of what this agent group does.
"""

import os
import sys
from typing import Dict, List, Optional

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from langchain_openai import ChatOpenAI
from prompt_manager import PromptManager

class {Name}AgentGroup:
    """
    Agent group for [specific purpose].
    """
    
    def __init__(self, api_key: str, model_name: str = "gpt-4", prompts_dir: str = None):
        """
        Initialize the agent group.
        
        Args:
            api_key: OpenAI API key
            model_name: LLM model to use
            prompts_dir: Path to prompts directory (None = auto-detect)
        """
        # Initialize LLM
        self.llm = ChatOpenAI(api_key=api_key, model_name=model_name)
        
        # Initialize PromptManager
        self.prompt_manager = PromptManager(prompts_dir)
        
        # Initialize state
        self.data = {}
    
    def process(self, input_data: Dict) -> Dict:
        """
        Main processing method.
        
        Args:
            input_data: Input data dictionary
            
        Returns:
            Result dictionary
        """
        # Get system prompt
        system_prompt = self.prompt_manager.get_agent_group_prompt(
            "{name}_agent_group",  # Must match filename
            "system_prompt"
        )
        
        # Process using LLM and prompts
        # ...
        
        return result
```

### Example: Analysis Agent Group

```python
"""
Analysis Agent Group for EmpathyScale
Analyzes interview and literature data to generate insights.
"""

import os
import sys
from typing import Dict

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from langchain_openai import ChatOpenAI
from prompt_manager import PromptManager

class AnalysisAgentGroup:
    """Agent group for analyzing collected data."""
    
    def __init__(self, api_key: str, model_name: str = "gpt-4", prompts_dir: str = None):
        self.llm = ChatOpenAI(api_key=api_key, model_name=model_name)
        self.prompt_manager = PromptManager(prompts_dir)
        self.insights = []
    
    def analyze(self, interview_data: Dict, literature_data: Dict) -> Dict:
        """Analyze data and generate insights."""
        prompt_template = self.prompt_manager.get_agent_group_prompt(
            "analysis_agent_group",
            "analysis_prompt"
        )
        
        prompt = prompt_template.format(
            interview_summary=str(interview_data),
            literature_summary=str(literature_data)
        )
        
        response = self.llm.invoke(prompt)
        
        return {
            "insights": response.content,
            "summary": "Analysis completed"
        }
```

## Step 2: Create Prompt File

Create: `prompts/{name}_agent_group.json`

**Important**: Filename must match exactly: `{name}` in code must match `{name}` in filename.

### Template

```json
{
  "system_prompt": "You are an expert [domain] agent. Your role is to [primary responsibility]. IMPORTANT: [key instructions]...",
  "opening_message": "Initial message or action...",
  "completion_message": "Message when task completes...",
  "error_message": "Error occurred: {error}. Please try again.",
  "main_prompt": "Prompt for main processing task: {variable1} {variable2}",
  "sub_agent_prompt": "Prompt for sub-agent (if applicable)..."
}
```

### Example: Analysis Agent Group Prompts

```json
{
  "system_prompt": "You are an expert analyst specializing in human-robot collaboration and empathy assessment. Your role is to analyze interview data and literature findings to generate insights for scale design.",
  "analysis_prompt": "Analyze the following data:\n\nInterview Data:\n{interview_summary}\n\nLiterature Data:\n{literature_summary}\n\nGenerate insights about:\n1. Key patterns in the collaboration scenario\n2. Relevant empathy dimensions\n3. Recommended scale items\n4. Validation approaches",
  "completion_message": "Analysis completed successfully.",
  "error_message": "Analysis error: {error}"
}
```

**Key Points**:
- Use descriptive prompt keys (e.g., `analysis_prompt`, not `prompt1`)
- Include variables with `{variable_name}` for dynamic content
- Add clear instructions and constraints
- Use emphasis (ALL CAPS, **bold**) for critical instructions

## Step 3: Register in Main Workflow

Edit `main.py`:

### Add Import

```python
from analysis_agent_group import AnalysisAgentGroup
```

### Initialize in _initialize_agents()

```python
def _initialize_agents(self):
    # Existing agents
    self.agents['interview'] = InterviewAgentGroup(
        api_key=self.config["openai_api_key"]
    )
    
    self.agents['literature'] = LiteratureSearchAgentGroup(
        api_key=self.config["openai_api_key"]
    )
    
    # New agent
    self.agents['analysis'] = AnalysisAgentGroup(
        api_key=self.config["openai_api_key"]
    )
```

### Add to Workflow (if needed)

```python
def run_analysis(self, interview_data: Dict, literature_data: Dict):
    """Run analysis on collected data."""
    analysis_agent = self.agents['analysis']
    results = analysis_agent.analyze(interview_data, literature_data)
    
    # Save results
    if self.run_id:
        self.data_manager.save_agent_group_data(
            self.run_id,
            "analysis_agent_group",
            results,
            []  # Conversation history (if applicable)
        )
    
    return results
```

## Step 4: Testing

### Test Prompt Loading

Use the debug tool:
```bash
python debug_prompts.py
```

Select your new agent group and verify prompts load correctly.

### Unit Test

Create `tests/test_{name}_agent_group.py`:

```python
"""Test for {Name} Agent Group."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agents.{name}_agent_group import {Name}AgentGroup
from utils.prompt_manager import load_config

def test_{name}_agent():
    """Test basic functionality."""
    config = load_config()
    
    agent = {Name}AgentGroup(api_key=config["openai_api_key"])
    
    # Test initialization
    assert agent is not None
    assert agent.prompt_manager is not None
    
    # Test prompt loading
    prompt = agent.prompt_manager.get_agent_group_prompt(
        "{name}_agent_group",
        "system_prompt"
    )
    assert prompt is not None
    
    print("✓ All tests passed!")

if __name__ == "__main__":
    test_{name}_agent()
```

## Naming Convention Checklist

- [ ] Class name: `{Name}AgentGroup` (PascalCase, no underscores)
- [ ] File name: `{name}_agent_group.py` (snake_case)
- [ ] Prompt file: `{name}_agent_group.json` (snake_case, matches exactly)
- [ ] Agent group name in code: `"{name}_agent_group"` (matches filename)
- [ ] Registration key: `self.agents['{name}']` (simple identifier)

## Example: Complete Flow

### 1. File Structure
```
agents/
└── analysis_agent_group.py

prompts/
└── analysis_agent_group.json
```

### 2. Code (`agents/analysis_agent_group.py`)
```python
class AnalysisAgentGroup:
    def __init__(self, api_key: str, ...):
        self.prompt_manager = PromptManager(prompts_dir)
    
    def analyze(self, ...):
        prompt = self.prompt_manager.get_agent_group_prompt(
            "analysis_agent_group",  # Matches filename
            "analysis_prompt"
        )
```

### 3. Prompts (`prompts/analysis_agent_group.json`)
```json
{
  "system_prompt": "...",
  "analysis_prompt": "..."
}
```

### 4. Registration (`main.py`)
```python
from analysis_agent_group import AnalysisAgentGroup

self.agents['analysis'] = AnalysisAgentGroup(...)
```

## Common Issues

### Prompt Not Found
- **Issue**: `KeyError: Prompt not found`
- **Fix**: Verify JSON filename matches exactly, check JSON key exists

### Import Error
- **Issue**: `ModuleNotFoundError: No module named '{name}_agent_group'`
- **Fix**: Check file exists, verify import path in `main.py`

### Agent Group Not Registered
- **Issue**: Agent not appearing in workflow
- **Fix**: Verify `_initialize_agents()` includes new agent

## Best Practices

1. **Follow naming convention strictly**: Consistency prevents errors
2. **Test prompts early**: Use `debug_prompts.py` to verify loading
3. **Include error handling**: Graceful failures improve UX
4. **Document the agent**: Clear docstrings and comments
5. **Save data consistently**: Use `DataManager` for all storage
6. **Version control prompts**: Commit prompt changes for history

## Next Steps

After adding your agent group:
1. Test thoroughly with sample data
2. Integrate into workflow if needed
3. Update documentation (this file, ARCHITECTURE.md)
4. Add to integration tests
5. Commit changes with clear messages

For architecture details, see [ARCHITECTURE.md](./ARCHITECTURE.md).  
For workflow integration, see [WORKFLOW.md](./WORKFLOW.md).
