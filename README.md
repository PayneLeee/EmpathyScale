# Multi-Agent LLM Workflow for Human-Robot Collaboration Analysis

A sophisticated multi-agent system built with LangChain for conducting interviews, researching empathy scales, and analyzing human-robot collaboration scenarios.

## 🚀 Features

- **Interview Agent Group**: Specialized agents for gathering information about human-robot collaboration scenarios
- **Research Agent Group**: Advanced agents for academic paper research and empathy scale construction
- **PDF Download System**: Automated paper collection for RAG (Retrieval-Augmented Generation) tasks
- **Time-Stamped Data Storage**: Organized data storage with complete run history tracking
- **Modular Architecture**: Designed for easy expansion with additional specialized agents
- **Secure Configuration**: API keys stored in separate JSON configuration file
- **Conversation Memory**: Maintains context throughout the workflow process
- **Interactive Interface**: User-friendly command-line interface with multiple workflow modes
- **External Prompt Management**: Prompts stored in separate JSON files for easy debugging and modification
- **Comprehensive Testing**: Built-in test scripts for functionality verification

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

### Running the Complete Workflow

```bash
python main.py
```

This will present you with three workflow options:

1. **Interview only**: Conduct interviews to gather assessment scenario information
2. **Complete workflow**: Run both interview and research phases sequentially
3. **Research only**: Run research phase using existing interview data

### Workflow Modes

#### Complete Workflow (Recommended)
The complete workflow runs both phases:
- **Phase 1: Interview**: Gathers information about human-robot collaboration scenarios
- **Phase 2: Research**: Searches for academic papers and constructs empathy scales

#### Interview Phase
The interview agent will ask questions about:
- Assessment context and scenarios
- Robot platform characteristics
- Collaboration patterns
- Environmental settings
- Assessment goals and requirements
- Expected empathy forms
- Measurement challenges

#### Research Phase
The research agent will:
- Search for relevant academic papers
- Analyze methodologies for empathy scale construction
- Extract context-specific insights
- Generate design recommendations
- Download PDF papers for RAG tasks

### Testing and Verification

Use the comprehensive test scripts to verify functionality:

```bash
# Quick functionality check
python checkscripts/quick_agent_check.py

# Complete functionality test
python checkscripts/test_agent_functionality.py

# Test PDF download functionality
python checkscripts/test_pdf_download.py

# Test new data storage structure
python checkscripts/test_new_data_storage.py
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

## 🏗️ Architecture

### Why This Design?

1. **Modularity**: Each agent is a separate class that can be developed and tested independently
2. **Scalability**: Easy to add new specialized agents (analysis, reporting, decision-making)
3. **Security**: Sensitive configuration separated from code
4. **Maintainability**: Clear separation of concerns and well-documented code
5. **Extensibility**: Built on LangChain's flexible agent framework

### Project Structure

```
EmpathyScale/
├── agents/                   # Agent group implementation files
│   ├── __init__.py
│   ├── interview_agent_group.py    # Interview agent group (information gathering)
│   └── research_agent_group.py    # Research agent group (academic research)
├── utils/                    # Utility modules
│   ├── __init__.py
│   ├── prompt_manager.py     # Prompt management utilities
│   └── run_manager.py        # Data storage and run management
├── prompts/                  # Agent group-specific prompt files (1:1 mapping)
│   ├── interview_agent_group.json  # Interview agent group prompts
│   └── research_agent_group.json  # Research agent group prompts
├── checkscripts/             # Testing and verification scripts
│   ├── check_openai_key.py
│   ├── quick_agent_check.py
│   ├── test_agent_functionality.py
│   ├── test_pdf_download.py
│   └── test_new_data_storage.py
├── data/                     # Data storage directory
│   ├── runs/                 # Time-stamped run records
│   ├── templates/            # Template files
│   └── README.md             # Data structure documentation
├── main.py                   # Main application entry point
├── debug_prompts.py         # Prompt debugging tool
├── config.json              # Configuration file with API keys
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── RAG_PREPARATION_GUIDE.md # RAG integration guide
└── HOW_TO_ADD_AGENTS.md    # Guide for adding new agent groups
```

**命名约定**: 每个agent group的Python文件与对应的prompt文件名称完全一致
- `agents/interview_agent_group.py` ↔ `prompts/interview_agent_group.json`
- `agents/research_agent_group.py` ↔ `prompts/research_agent_group.json`

**未来扩展**: 当添加新的agent group时，遵循相同的命名约定：
- `agents/analysis_agent_group.py` ↔ `prompts/analysis_agent_group.json`
- `agents/report_agent_group.py` ↔ `prompts/report_agent_group.json`
- `agents/validation_agent_group.py` ↔ `prompts/validation_agent_group.json`

**Agent Group架构**: 每个agent group包含多个子agent，专门处理特定功能领域

### Key Components

- **InterviewAgentGroup**: Conducts structured interviews about human-robot collaboration
  - Contains sub-agents: TaskCollectorAgent, EnvironmentAnalyzerAgent, PlatformSpecialistAgent, CollaborationExpertAgent
- **ResearchAgentGroup**: Conducts academic research and empathy scale construction
  - Contains sub-agents: PaperSearcherAgent, MethodologyAnalyzerAgent, ContextSpecialistAgent, ScaleDesignerAgent
- **MultiAgentWorkflow**: Orchestrates multiple agent groups with complete workflow management
- **RunManager**: Manages time-stamped data storage and run history tracking
- **DataSaver**: Handles automatic data saving to organized directory structures
- **PromptManager**: Manages prompts from external JSON configuration files organized by agent group
- **Configuration Management**: Secure handling of API keys and settings
- **Memory Management**: Conversation context preservation across workflow phases
- **Testing Framework**: Comprehensive test scripts for functionality verification

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
- `research_agent_group.json`: Research agent group prompts (academic research)

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

- **Analysis Agent Group**: Process collected data and generate insights
- **Report Agent Group**: Create structured reports from interview and research data
- **Recommendation Agent Group**: Suggest improvements based on analysis
- **Validation Agent Group**: Verify data quality and completeness
- **RAG Agent Group**: Implement retrieval-augmented generation for enhanced research

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
