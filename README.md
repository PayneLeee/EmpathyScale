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

### Run Experiments

The project includes three main experiment scripts:

**1. Main Scale Generation (Predefined Scenarios)**
```bash
python run_predefined_scenarios.py
```
Generates scenario-specific empathy scales for 2-3 predefined scenarios with complete pipeline: generation → Phase 1 evaluation → statistical selection → Phase 2 validation.

**2. Ablation Study**
```bash
python run_ablation_minimal.py
```
Compares different generation configurations against baseline (fewer generators, no content assessment, combined variants).

**3. Baseline Comparison**
```bash
python run_baseline_comparison.py
```
Evaluates baseline scales (PETS and RoPE) using the same personas for fair comparison.

**4. Interactive Workflow (Alternative)**
```bash
python main.py
```
Runs an interactive interview session followed by literature search and scale generation.

## 📁 Project Structure

```
EmpathyScale/
├── agents/                    # Agent group implementations
│   ├── interview_agent_group.py              # Information gathering
│   ├── literature_search_agent_group.py      # Literature search & synthesis
│   ├── empathy_scale_generation_agent_group.py  # Scale item generation
│   ├── evaluation_agent_group.py             # LLM-based evaluation
│   ├── item_selection_agent.py               # Item selection logic
│   ├── persona_generation_agent.py           # Persona generation
│   ├── scale_generation_agents.py            # Scale generation sub-agents
│   └── expert_pdfs/                          # Reference PDFs for agents
├── prompts/                   # Agent prompts (JSON files)
│   ├── interview_agent_group.json
│   ├── literature_search_agent_group.json
│   ├── empathy_scale_generation_agent_group.json
│   ├── evaluation_agent_group.json
│   ├── persona_generation_agent.json
│   ├── scale_generation_support.json
│   └── expert_knowledge.json
├── utils/                     # Core utilities
│   ├── prompt_manager.py      # Prompt loading & management
│   ├── data_manager.py        # Data storage & run management
│   ├── research_api.py        # Academic database APIs
│   ├── semantic_deduplication.py  # Semantic deduplication
│   ├── statistical_item_selection.py  # EFA/CFA item selection
│   ├── factor_analysis.py     # Factor analysis utilities
│   ├── pdf_reader.py           # PDF reading utilities
│   └── [other utility modules]
├── tools/                     # Development and analysis tools
│   ├── run_all_experiments.py # Run all experiments in sequence
│   ├── analyze_all_results.py # Analysis scripts
│   ├── debug_prompts.py       # Prompt debugging tool
│   ├── check_openai_key.py    # API key validation
│   └── [other utility scripts]
├── tests/                     # Test suite
│   ├── test_integration.py    # Full integration tests
│   ├── test_integration_fast.py  # Fast mocked tests
│   └── [other test files]
├── docs/                      # Documentation
│   ├── ARCHITECTURE.md        # System architecture
│   ├── WORKFLOW.md            # Agent workflows & responsibilities
│   ├── DATA_STORAGE.md        # Data storage structure
│   ├── HOW_TO_ADD_AGENTS.md   # Extension guide
│   ├── EXPERIMENT_EXECUTION_GUIDE.md  # Experiment execution guide
│   ├── EVALUATION_PROCESS_UNIFICATION.md  # Evaluation process guide
│   ├── analysis/              # Historical analysis documents
│   ├── final_report_content/  # Final report content materials
│   ├── presentation/          # Presentation materials
│   └── ProjectRequirements/  # Project requirements documents
├── data/                      # Runtime data storage
│   ├── runs/                  # Timestamped run directories
│   ├── ablation_studies/      # Ablation study results
│   ├── baseline_comparison/   # Baseline comparison results
│   └── personas/              # Generated personas
├── main.py                    # Main workflow orchestrator
├── run_predefined_scenarios.py  # Main experiment script
├── run_ablation_minimal.py    # Ablation study script
├── run_baseline_comparison.py # Baseline comparison script
├── config.json                # API configuration
└── requirements.txt           # Python dependencies
```

## 🔄 Workflow Overview

The complete workflow consists of multiple phases:

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

### 3. Scale Generation Phase
The **Empathy Scale Generation Agent Group**:
- Generates scale items based on interview and literature findings
- Performs semantic deduplication to remove redundant items
- Organizes items by dimensions and constructs

### 4. Evaluation Phase
The **Evaluation Agent Group**:
- **Phase 1 (Selection)**: Evaluates all generated items using LLM personas
  - Generates empathic and non-empathic personas
  - Scores items for discriminant ability and quality
- **Phase 2 (Validation)**: Validates selected items using independent personas
  - Computes internal consistency (Cronbach's α)
  - Measures discriminant ability (Cohen's d)

### 5. Item Selection Phase
Statistical item selection using:
- Exploratory Factor Analysis (EFA)
- Confirmatory Factor Analysis (CFA)
- Item-total correlations
- Factor loadings

### 6. Data Storage
All data is saved in timestamped directories:
- Interview summaries and conversations
- Literature search queries and results
- Generated scale drafts and selected items
- Evaluation results and statistics
- Final validated scales

See [docs/DATA_STORAGE.md](docs/DATA_STORAGE.md) for detailed structure.

## 📚 Documentation

- **[Architecture Guide](docs/ARCHITECTURE.md)**: Agent groups, prompt management, design patterns
- **[Workflow Guide](docs/WORKFLOW.md)**: Agent responsibilities, data flow, execution steps
- **[Data Storage](docs/DATA_STORAGE.md)**: Run structure, file organization, data access
- **[Adding Agents](docs/HOW_TO_ADD_AGENTS.md)**: Step-by-step extension guide

## 🧪 Experiment Scripts

The project includes three main experiment scripts:

### 1. `run_predefined_scenarios.py` - Main Scale Generation
**Purpose**: Generate scenario-specific empathy scales for predefined scenarios

**Features**:
- Complete pipeline: generation → Phase 1 evaluation → statistical selection → Phase 2 validation
- Scenarios: `collab_robot_assembly`, `home_service_robot`, `counseling_chatbot`
- Two-phase evaluation with independent persona sets (100 empathic + 100 non-empathic per phase)
- Statistical item selection using EFA/CFA methodology

**Usage**:
```bash
python run_predefined_scenarios.py
```

### 2. `run_ablation_minimal.py` - Ablation Study
**Purpose**: Compare different generation configurations against baseline

**Features**:
- 3 ablation variants:
  - `fewer_generators`: 1 generator vs 5 (baseline)
  - `no_content`: Random selection vs content assessment (baseline)
  - `fewer_generators_no_content`: Combined variant
- Runs on `collab_robot_assembly` scenario
- Compares against main experiment baseline (5 generators + content assessment + EFA/CFA)
- Generates ablation summary report with metrics comparison

**Usage**:
```bash
python run_ablation_minimal.py
```

### 3. `run_baseline_comparison.py` - Baseline Comparison
**Purpose**: Evaluate baseline scales (PETS and RoPE) using the same personas

**Features**:
- Evaluates PETS and RoPE baseline scales
- Uses same personas as generated scales for fair comparison
- Generates comparison reports for each scenario

**Usage**:
```bash
python run_baseline_comparison.py
```

### Development Tools

Additional tools are located in the `tools/` directory:
- `tools/run_single_variant.py` - Re-run individual ablation variants (for debugging)
- `tools/run_statistical_item_selection.py` - Apply statistical selection to existing run results
- `tools/analyze_all_results.py` - Analyze results across multiple runs
- `tools/debug_prompts.py` - View, test, and reload agent prompts

For details on the evaluation process and persona configuration, see [docs/EVALUATION_PROCESS_UNIFICATION.md](docs/EVALUATION_PROCESS_UNIFICATION.md).

## 🧪 Testing

```bash
# Fast integration test (mocked operations)
python tests/test_integration_fast.py

# Full integration test (real API calls)
python tests/test_integration.py

# Quick single scenario test
python tests/test_single_scenario_quick.py

# Check API key
python tools/check_openai_key.py
```

See [tests/README.md](tests/README.md) for detailed testing documentation.

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
