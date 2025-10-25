# Multi-Agent Workflow for Empathy Scale Construction

This project implements a comprehensive multi-agent workflow for constructing empathy measurement scales in human-robot collaboration scenarios. The system follows LangChain best practices and consists of two specialized agent groups that work together to gather requirements and conduct research.

## 🏗️ Architecture Overview

The system follows a **sequential workflow pattern** with **specialized agent groups**:

```
Interview Agent Group → Research Agent Group → Data Collection
```

### Agent Groups

1. **Interview Agent Group** (`agents/interview_agent_group.py`)
   - Conducts structured interviews about human-robot collaboration scenarios
   - Collects assessment context, robot platform details, collaboration patterns
   - Specialized sub-agents for different aspects of information gathering

2. **Research Agent Group** (`agents/research_agent_group.py`)
   - Analyzes interview summaries to generate research queries
   - Searches for relevant academic papers on empathy scale construction
   - Extracts methodology insights and generates design recommendations
   - Specialized sub-agents for different research aspects

## 🚀 Features

### LangChain Best Practices Implementation

- **Tool Calling Pattern**: Supervisor agents call specialized sub-agents as tools
- **Memory Management**: ConversationBufferMemory for context retention
- **Error Handling**: Comprehensive error handling and validation
- **Modular Design**: Each agent group is self-contained and extensible
- **State Management**: Structured data tracking and intermediate result storage

### Specialized Sub-Agents

**Interview Agent Group:**
- `TaskCollectorAgent`: Focuses on collaborative task analysis
- `EnvironmentAnalyzerAgent`: Analyzes environmental factors
- `PlatformSpecialistAgent`: Specializes in robot platform characteristics
- `CollaborationExpertAgent`: Expert in collaboration patterns

**Research Agent Group:**
- `PaperSearcherAgent`: Searches for academic papers
- `MethodologyAnalyzerAgent`: Analyzes research methodologies
- `ContextSpecialistAgent`: Extracts context-specific insights
- `ScaleDesignerAgent`: Generates scale design recommendations

## 📁 Data Structure

```
data/
├── intermediate_results/          # Agent group outputs
│   ├── interview_agent_group/    # Interview summaries and data
│   └── research_agent_group/     # Research findings and analysis
├── papers/                       # Collected research papers
├── summaries/                    # Generated summaries
└── README.md                     # Data structure documentation
```

## 🛠️ Usage

### Complete Workflow
```bash
python main.py
# Choose option 2: Complete workflow (Interview → Research)
```

### Interview Only
```bash
python main.py
# Choose option 1: Interview only
```

### Testing
```bash
python test_multi_agent_workflow.py
```

## 🔧 Configuration

### Environment Setup
```bash
conda activate EmpathyScale
```

### Configuration File (`config.json`)
```json
{
  "openai_api_key": "your-openai-api-key"
}
```

## 📋 Workflow Process

### Phase 1: Interview
1. **Opening**: Agent introduces empathy assessment focus
2. **Data Collection**: Structured questions about:
   - Assessment context (collaboration scenario)
   - Robot platform (appearance, capabilities)
   - Collaboration pattern (interaction mode)
   - Environmental setting (workplace context)
   - Assessment goals and expected empathy forms
   - Challenges and measurement requirements
3. **Progress Tracking**: Real-time data categorization and storage
4. **Completion Check**: Validates sufficient information gathered

### Phase 2: Research
1. **Summary Analysis**: Processes interview summary
2. **Query Generation**: Creates targeted research queries
3. **Paper Search**: Searches for relevant academic papers
4. **Methodology Analysis**: Analyzes research approaches
5. **Context Insights**: Extracts scenario-specific considerations
6. **Recommendations**: Generates scale design recommendations

## 🔍 Key Features

### Intelligent Data Categorization
The system automatically categorizes interview responses into structured fields:
- Assessment context
- Robot platform details
- Collaboration patterns
- Environmental settings
- Goals and requirements

### Comprehensive Research Process
- Multi-database paper search simulation
- Methodology analysis and validation
- Context-specific insight extraction
- Practical design recommendations

### Robust Error Handling
- Graceful error recovery
- Input validation
- Memory management
- State persistence

## 📊 Output Examples

### Interview Summary
```json
{
  "assessment_context": "Healthcare robot assisting nurses",
  "robot_platform": "Humanoid with facial expressions",
  "collaboration_pattern": "Supervised collaboration",
  "environmental_setting": "Hospital ward",
  "assessment_goals": ["Measure empathy effectiveness"],
  "expected_empathy_forms": ["Verbal empathy", "Facial expressions"],
  "assessment_challenges": ["High-stress environment"],
  "measurement_requirements": ["Real-time assessment"]
}
```

### Research Findings
```json
{
  "research_queries": ["empathy measurement healthcare robots"],
  "paper_search_results": ["Found 5 relevant papers..."],
  "methodology_analysis": ["Interpersonal Reactivity Index (IRI)..."],
  "context_insights": ["Task type influences empathy approach..."],
  "scale_design_recommendations": ["Multi-modal evaluation needed..."]
}
```

## 🧪 Testing

The system includes comprehensive tests:
- Data structure validation
- Prompt configuration loading
- Workflow integration verification
- Agent group functionality testing

Run tests: `python test_multi_agent_workflow.py`

## 🔮 Future Enhancements

- Integration with real academic databases (Semantic Scholar, arXiv)
- Advanced paper analysis with NLP
- Automated scale generation
- Multi-language support
- Web interface for easier interaction

## 📝 Dependencies

- `langchain>=0.3.0`
- `langchain-openai>=0.3.0`
- `openai>=2.0.0`
- `requests>=2.31.0`
- `pydantic>=2.7.0`

## 🤝 Contributing

This system is designed to be extensible. New agent groups can be added following the established patterns:

1. Create agent group class with specialized sub-agents
2. Define prompt configuration in `prompts/`
3. Implement required methods and tools
4. Integrate into main workflow
5. Add comprehensive tests

The modular architecture makes it easy to add new capabilities while maintaining system stability and performance.
