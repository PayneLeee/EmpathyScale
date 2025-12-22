# EmpathyScale: Robot Empathy Assessment Framework

A multi-agent AI system for designing and evaluating scales that quantify perceived empathy in robots during human-robot collaboration scenarios.

## 🎯 Project Objectives

This system enables researchers and developers to:
- **Conduct structured interviews** about human-robot collaboration scenarios
- **Identify key factors** influencing perceived robot empathy (interaction modalities, collaboration patterns, context)
- **Search and synthesize literature** on robot empathy, scale construction, and measurement methods
- **Generate comprehensive background** for creating validated empathy assessment scales

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key
- Internet connection for literature search

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd EmpathyScale

# Install dependencies
pip install -r requirements.txt

# Configure API key in config.json
```

### Run the Workflow

```bash
python main.py
```

The system will:
1. **Interview Agent**: Conduct an interactive interview about your robot collaboration scenario
2. **Literature Search Agent**: Automatically search academic literature based on interview findings
3. **Save Results**: Store all data in timestamped run directories

## 📁 Project Structure

```
EmpathyScale/
├── agents/                    # Agent group implementations
│   ├── interview_agent_group.py          # Information gathering
│   └── literature_search_agent_group.py  # Literature search & synthesis
├── prompts/                   # Agent prompts (JSON files)
│   ├── interview_agent_group.json
│   └── literature_search_agent_group.json
├── utils/                     # Core utilities
│   ├── prompt_manager.py      # Prompt loading & management
│   ├── data_manager.py        # Data storage & run management
│   └── research_api.py        # Academic database APIs
├── docs/                      # Documentation
│   ├── ARCHITECTURE.md        # System architecture
│   ├── WORKFLOW.md            # Agent workflows & responsibilities
│   ├── DATA_STORAGE.md        # Data storage structure
│   └── HOW_TO_ADD_AGENTS.md   # Extension guide
├── data/                      # Runtime data storage
│   └── runs/                  # Timestamped run directories
├── main.py                    # Main workflow orchestrator
├── config.json                # API configuration
└── requirements.txt           # Python dependencies
```

## 🔄 Workflow Overview

### 1. Interview Phase
The **Interview Agent Group** conducts a structured conversation to gather:
- **Assessment Context**: What scenario are you evaluating?
- **Robot Platform**: What type of robot and capabilities?
- **Interaction Modalities**: Speech, touch, visual cues, etc.
- **Collaboration Patterns**: How do humans and robots interact?
- **Assessment Goals**: What empathy aspects to measure?

### 2. Literature Search Phase
The **Literature Search Agent Group** automatically:
- Generates targeted search queries from interview findings
- Searches arXiv and Semantic Scholar databases
- Screens papers for relevance to robot empathy and scale construction
- Downloads relevant PDFs organized by category
- Extracts key findings on definitions, behaviors, and measurement methods
- Organizes findings for scale design reference

### 3. Data Storage
All data is saved in timestamped directories:
- Interview summaries and conversations
- Literature search queries and results
- Downloaded PDFs organized by category
- Extracted findings and organized insights

See [docs/DATA_STORAGE.md](docs/DATA_STORAGE.md) for detailed structure.

## 📚 Documentation

- **[Architecture Guide](docs/ARCHITECTURE.md)**: Agent groups, prompt management, design patterns
- **[Workflow Guide](docs/WORKFLOW.md)**: Agent responsibilities, data flow, execution steps
- **[Data Storage](docs/DATA_STORAGE.md)**: Run structure, file organization, data access
- **[Adding Agents](docs/HOW_TO_ADD_AGENTS.md)**: Step-by-step extension guide

## 🧪 Run Scripts

The project includes several run scripts that implement the experiments described in the proposal:

### Core Experiments

#### 1. `run_predefined_scenarios.py` - Main Scale Generation
**Purpose**: Generate scenario-specific empathy scales for 2-3 predefined scenarios

**Features**:
- Runs complete pipeline: generation → Phase 1 evaluation → statistical selection → Phase 2 validation
- Scenarios: collab_robot_assembly, home_service_robot, counseling_chatbot
- Two-phase evaluation with independent persona sets
- Statistical item selection based on evaluation data

**Usage**:
```bash
python run_predefined_scenarios.py
```

#### 2. `run_ablation_minimal.py` - Ablation Study
**Purpose**: Compare different generation configurations (2x2 design)

**Features**:
- Single vs multi-agent generation
- With vs without content assessment
- Runs on collab_robot_assembly scenario
- Generates ablation summary report

**Usage**:
```bash
python run_ablation_minimal.py
```

#### 3. `run_baseline_comparison.py` - Baseline Comparison
**Purpose**: Evaluate baseline scales (PETS and RoPE) using the same personas

**Features**:
- Evaluates PETS and RoPE baseline scales
- Uses same personas as generated scales for fair comparison
- Generates comparison reports for each scenario

**Usage**:
```bash
python run_baseline_comparison.py
```

### Optional Tools

#### 4. `run_statistical_item_selection.py` - Independent Selection Tool
**Purpose**: Apply statistical selection to existing run results

**Features**:
- Can be used to apply statistical selection to previously generated scales
- Supports multiple selection strategies (rating_threshold, percentile, dimension_balanced)

**Usage**:
```bash
python run_statistical_item_selection.py --run-id <run_id> --strategy rating_threshold
```

### Development Tools

Development tools are located in the `tools/` directory:
- `tools/run_single_variant.py` - Re-run individual ablation variants (for debugging)

For details on the evaluation process and persona configuration, see [docs/EVALUATION_PROCESS_UNIFICATION.md](docs/EVALUATION_PROCESS_UNIFICATION.md).

## 🛠️ Additional Tools

### Prompt Debugging
```bash
python debug_prompts.py
```
View, test, and reload agent prompts without code changes.

### Testing
```bash
# Fast integration test (mocked operations)
python tests/test_integration_fast.py

# Full integration test (real API calls)
python tests/test_integration.py
```

## 🏗️ Key Design Principles

- **Modularity**: Each agent group is self-contained and independently testable
- **Prompt Externalization**: All prompts in JSON files for easy iteration
- **Timestamp Isolation**: Each run gets unique directory, no data conflicts
- **Extensibility**: Clear patterns for adding new agent groups
- **Robustness**: Comprehensive error handling and data validation

## 🔧 Configuration

### API Keys
Store in `config.json`:
```json
{
  "openai_api_key": "your-api-key-here"
}
```

### Model Selection
Modify agent initialization in `main.py`:
```python
InterviewAgentGroup(api_key=..., model_name="gpt-4")  # or "gpt-3.5-turbo"
```

## 📝 License

This project is designed for research and educational purposes in human-robot collaboration analysis.

## 🤝 Contributing

See [docs/HOW_TO_ADD_AGENTS.md](docs/HOW_TO_ADD_AGENTS.md) for guidelines on extending the system with new agent groups.
