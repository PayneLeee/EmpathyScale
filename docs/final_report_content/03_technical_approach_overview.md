# Technical Approach - Overview

## 1. System Architecture Overview

### 1.1 High-Level Workflow

Our system implements a sequential multi-agent workflow where agent groups execute in order, with each group's output feeding into the next:

```
User Input 
  → Interview Agent Group 
  → Literature Search Agent Group 
  → Empathy Scale Generation Agent Group 
  → Evaluation Agent Group (Phase 1: Selection) 
  → Item Selection Agent (Statistical Selection) 
  → Evaluation Agent Group (Phase 2: Validation) 
  → Final Scale
```

### 1.2 Core Design Principles

1. **Separation of Concerns**: Prompts (what agents say/think) are separate from Code (how agents work)
2. **Externalization**: All prompts in JSON files, not hardcoded
3. **Modularity**: Each agent group is self-contained with clear interfaces
4. **Consistency**: Standardized initialization patterns and naming conventions

### 1.3 Mapping to Boateng's Nine-Step Framework

Our system automates the core steps of Boateng et al.'s psychometric framework:

| Boateng Step | Our System Implementation |
|-------------|--------------------------|
| **Phase 1: Item Development** | |
| Step 1: Domain identification & item generation | Interview Agent + Literature Search Agent |
| Step 2: Content validity assessment | Content Assessment Agent |
| **Phase 2: Scale Development** | |
| Step 3: Pre-testing questions | Evaluation Agent (Phase 1) |
| Step 4: Survey administration | Evaluation Agent (200 personas) |
| Step 5: Item reduction | Statistical Selection (EFA/CFA) |
| Step 6: Factor extraction | Statistical Selection (EFA) |
| **Phase 3: Scale Evaluation** | |
| Step 7: Dimensionality testing | Statistical Selection (CFA) |
| Step 8: Reliability testing | Evaluation Agent (Cronbach's α) |
| Step 9: Validity testing | Evaluation Agent (Cohen's d) |

## 2. Agent Group Structure

### 2.1 Hierarchical Organization

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
├── LiteratureSearchAgentGroup
│   ├── LLM Integration (direct ChatOpenAI calls)
│   └── Methods (generate_queries, search_and_screen, extract_findings, etc.)
│
├── EmpathyScaleGenerationAgentGroup
│   ├── Multiple item generators (parallel generation)
│   ├── Content assessment (LLM-based item quality check)
│   └── Semantic deduplication (removes redundant items)
│
├── EvaluationAgentGroup
│   ├── PersonaGenerationAgent (generates LLM personas)
│   └── Evaluation methods (Phase 1 selection, Phase 2 validation)
│
└── ItemSelectionAgent
    ├── Statistical selection (EFA/CFA)
    └── Random selection (for ablation studies)
```

### 2.2 Base Agent Group Pattern

All agent groups follow a consistent structure:

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
```

## 3. Key Technical Components

### 3.1 Prompt Management

- **Location**: `utils/prompt_manager.py`
- **Purpose**: Centralized prompt loading and management
- **Features**: 
  - Auto-detects project root and prompts directory
  - Loads all prompts from JSON files on initialization
  - Supports variable formatting using Python `.format()`
  - Hot-reload capability for development

### 3.2 Data Management

- **Location**: `utils/data_manager.py`
- **Purpose**: Timestamp-isolated data storage with agent group separation
- **Structure**: `data/runs/YYYY-MM-DD_HHMMSS/agent_group_name/`
- **Features**:
  - Automatic run ID generation
  - Agent group data isolation
  - Summary and conversation storage

### 3.3 Statistical Analysis

- **Location**: `utils/statistical_item_selection.py`
- **Purpose**: Item selection based on evaluation statistics
- **Methods**:
  - Exploratory Factor Analysis (EFA)
  - Confirmatory Factor Analysis (CFA)
  - Item-total correlations
  - Distribution checks

## 4. Implementation Details

### 4.1 Language Model

- **Primary Model**: GPT-4o-mini (for cost efficiency)
- **Temperature**: 0.7 (for evaluation), 0.0 (for structured tasks)
- **Timeout**: 300s (5 minutes) for large prompts

### 4.2 Parallel Processing

- **Persona Evaluation**: Up to 5 parallel workers
- **Item Generation**: Multiple generators run in parallel
- **Batch Processing**: Items processed in batches of 100 for large scales

### 4.3 Error Handling

- **Retry Logic**: Automatic retry with exponential backoff for API failures
- **Graceful Degradation**: Continues processing even if some items fail
- **Progress Tracking**: Real-time progress updates for long-running tasks

## 5. System Workflow

### 5.1 Phase 1: Information Gathering

1. **Interview Agent Group**: Conducts structured interview
2. **Literature Search Agent Group**: Searches and synthesizes literature

### 5.2 Phase 2: Scale Generation

1. **Empathy Scale Generation Agent Group**: 
   - Defines constructs
   - Generates candidate items (multiple generators)
   - Performs content assessment
   - Semantic deduplication

### 5.3 Phase 3: Evaluation and Selection

1. **Evaluation Agent Group (Phase 1)**:
   - Generates personas
   - Evaluates all candidate items
   - Computes statistics for selection

2. **Item Selection Agent**:
   - Statistical selection (EFA/CFA)
   - Selects optimal items

3. **Evaluation Agent Group (Phase 2)**:
   - Generates independent validation personas
   - Evaluates selected items
   - Computes final metrics

## 6. Key Innovations

1. **Multi-Agent Collaboration**: Specialized agents work together to emulate expert workflows
2. **Scenario-Specific Generation**: Scales adapt to specific HRI contexts
3. **LLM-Based Evaluation**: Simulated personas enable rapid iteration
4. **Statistical Rigor**: Follows psychometric best practices (EFA/CFA, reliability, validity)

## 7. Technical Advantages

- **Rapid Development**: Hours instead of months/years
- **Cost-Effective**: Reduces need for expert and participant resources
- **Scalable**: Can generate scales for multiple scenarios
- **Reproducible**: Deterministic workflow with version-controlled prompts
- **Extensible**: Easy to add new agent groups or modify existing ones
