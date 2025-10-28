# Multi-Agent LLM Workflow for Human-Robot Collaboration Analysis

A sophisticated multi-agent system built with LangChain for conducting interviews and analyzing human-robot collaboration scenarios.

## 🚀 Features

- **Interview Agent**: Specialized agent for gathering information about human-robot collaboration scenarios
- **Modular Architecture**: Designed for easy expansion with additional specialized agents
- **Secure Configuration**: API keys stored in separate JSON configuration file
- **Conversation Memory**: Maintains context throughout the interview process
- **Interactive Interface**: User-friendly command-line interface
- **External Prompt Management**: Prompts stored in separate JSON files for easy debugging and modification
- **Prompt Debugging Tools**: Built-in utilities for testing and modifying prompts

## 📋 Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Internet connection for API calls

## 🛠️ Installation

1. **Clone or download the project files**

2. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your OpenAI API key:**
   - The `config.json` file is already set up with your API key
   - For security, consider moving this to a more secure location in production

## 🎯 Usage

### Running the Interview Agent

```bash
python main.py
```

This will start an interactive interview session where the agent will ask questions about:
- Task descriptions and activities
- Working environment
- Robot platform details
- Collaboration types
- Current challenges
- Specific requirements

### Direct Agent Usage

You can also run the interview agent group directly:

```bash
python agents/interview_agent_group.py
```

### Prompt Debugging Tool

Use the built-in prompt debugging tool to test and modify prompts:

```bash
python debug_prompts.py
```

This tool allows you to:
- View all available agents and their prompts
- Test prompt formatting with different parameters
- Reload all prompts or specific agent prompts
- View prompt file paths for easy editing
- Each agent's prompts are organized in separate files

## 🏗️ Architecture

For detailed architecture documentation, see **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.

### Why This Design?

1. **Modularity**: Each agent is a separate class that can be developed and tested independently
2. **Scalability**: Easy to add new specialized agents (analysis, reporting, decision-making)
3. **Security**: Sensitive configuration separated from code
4. **Maintainability**: Clear separation of concerns and well-documented code
5. **Extensibility**: Built on LangChain's flexible agent framework

### Documentation

- **[Architecture Guide](docs/ARCHITECTURE.md)**: Complete guide to agent groups, prompts, and system design
- **[Adding Agents Guide](docs/HOW_TO_ADD_AGENTS.md)**: Step-by-step instructions for extending the system
- **[Literature Search](docs/LITERATURE_SEARCH_IMPROVEMENTS.md)**: Details on literature search capabilities

### Project Structure

```
EmpathyScale/
├── agents/                   # Agent group implementation files
│   ├── __init__.py
│   └── interview_agent_group.py    # Interview agent group (information gathering)
├── utils/
│   ├── __init__.py
│   └── prompt_manager.py     # Prompt management utilities
├── prompts/                  # Agent group-specific prompt files (1:1 mapping)
│   └── interview_agent_group.json  # Interview agent group prompts
├── main.py                   # Main application entry point
├── debug_prompts.py         # Prompt debugging tool
├── config.json              # Configuration file with API keys
├── requirements.txt         # Python dependencies
├── README.md               # This file
└── docs/                    # Documentation directory
    ├── README.md           # Documentation index
    ├── ARCHITECTURE.md     # Agent group and prompt architecture guide
    ├── HOW_TO_ADD_AGENTS.md # Guide for adding new agent groups
    └── LITERATURE_SEARCH_IMPROVEMENTS.md # Literature search improvements
```

**命名约定**: 每个agent group的Python文件与对应的prompt文件名称完全一致
- `agents/interview_agent_group.py` ↔ `prompts/interview_agent_group.json`

**未来扩展**: 当添加新的agent group时，遵循相同的命名约定：
- `agents/analysis_agent_group.py` ↔ `prompts/analysis_agent_group.json`
- `agents/report_agent_group.py` ↔ `prompts/report_agent_group.json`
- `agents/validation_agent_group.py` ↔ `prompts/validation_agent_group.json`

**Agent Group架构**: 每个agent group包含多个子agent，专门处理特定功能领域

### Key Components

- **InterviewAgentGroup**: Conducts structured interviews about human-robot collaboration
  - Contains sub-agents: TaskCollectorAgent, EnvironmentAnalyzerAgent, PlatformSpecialistAgent, CollaborationExpertAgent
- **MultiAgentWorkflow**: Orchestrates multiple agent groups
- **PromptManager**: Manages prompts from external JSON configuration files organized by agent group
- **Configuration Management**: Secure handling of API keys and settings
- **Memory Management**: Conversation context preservation
- **Debug Tools**: Utilities for testing and modifying prompts

## 🔧 Configuration

### API Configuration
The `config.json` file contains:
```json
{
  "openai_api_key": "your-openai-api-key-here"
}
```

### Prompt Configuration
The `prompts/` directory contains agent group-specific prompt files:
- `interview_agent_group.json`: Interview agent group prompts (information gathering)

Each file contains prompts specific to that agent group and its sub-agents:
```json
{
  "system_prompt": "You are an expert interviewer...",
  "opening_message": "Hello! I'm here to learn...",
  "error_message": "I apologize, but I encountered an error...",
  "task_collector_prompt": "Focus on gathering task information...",
  "environment_analyzer_prompt": "Analyze the working environment..."
}
```

### Modifying Prompts
1. Edit the specific agent group's JSON file in the `prompts/` directory
2. Use the debug tool: `python debug_prompts.py`
3. Reload prompts in the running application using the debug tool
4. Each agent group's prompts are stored in separate files for better organization
5. Sub-agent prompts are included within the agent group's prompt file

## 🚀 Future Extensions

This architecture is designed to easily accommodate additional agents:

- **Analysis Agent**: Process collected data and generate insights
- **Report Agent**: Create structured reports from interview data
- **Recommendation Agent**: Suggest improvements based on analysis
- **Validation Agent**: Verify data quality and completeness

## 🐛 Troubleshooting

### Common Issues

1. **API Key Error**: Ensure your OpenAI API key is valid and has sufficient credits
2. **Import Errors**: Make sure all dependencies are installed with `pip install -r requirements.txt`
3. **Configuration Error**: Verify `config.json` exists and contains valid JSON

### Getting Help

If you encounter issues:
1. Check that all dependencies are installed
2. Verify your OpenAI API key is correct
3. Ensure you have an active internet connection

## 📝 License

This project is designed for research and educational purposes in human-robot collaboration analysis.
