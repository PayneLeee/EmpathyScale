# Agent Workflows and Responsibilities

This document describes how agent groups work together, their individual responsibilities, and the overall execution flow.

## Overview

The EmpathyScale system uses a sequential multi-agent workflow where agent groups execute in order, with each group's output feeding into the next:

```
User Input → Interview Agent → Literature Search Agent → Scale Generation Agent → 
Evaluation Agent (Phase 1) → Item Selection → Evaluation Agent (Phase 2) → Final Scale
```

## Agent Group Responsibilities

### Interview Agent Group

**Primary Goal**: Gather comprehensive information about the robot collaboration scenario

**Key Responsibilities**:
1. **Initiate conversation** with a welcoming opening message
2. **Ask strategic questions** about the assessment scenario
3. **Categorize responses** into structured data fields:
   - Assessment context (scenario description)
   - Robot platform (hardware, capabilities)
   - Environmental setting (workplace, conditions)
   - Collaboration pattern (interaction style)
   - **Interaction modalities** (speech, touch, visual cues) - **CRITICAL**
   - Assessment goals, expected empathy forms, challenges, requirements
4. **Track completion** and determine when sufficient information is gathered
5. **Generate summary** of collected data

**Sub-Agents**:
- **TaskCollectorAgent**: Focuses on task descriptions and activities
- **EnvironmentAnalyzerAgent**: Analyzes workplace and environmental factors
- **PlatformSpecialistAgent**: Investigates robot platform characteristics and capabilities
- **CollaborationExpertAgent**: Explores collaboration patterns and interaction modes

**Data Output**:
- Structured summary (assessment context, platform, modalities, etc.)
- Full conversation history
- Completion status

**Completion Criteria**:
- Required: `assessment_context`, `robot_platform`, `environmental_setting`
- Important: `interaction_modalities`, `collaboration_pattern`
- Additional: At least one of `assessment_goals`, `expected_empathy_forms`, `assessment_challenges`, or `measurement_requirements`

### Literature Search Agent Group

**Primary Goal**: Search, screen, and synthesize academic literature on robot empathy

**Key Responsibilities**:
1. **Generate search queries** based on interview summary:
   - Context-specific queries (healthcare, manufacturing, etc.)
   - Platform-specific queries (humanoid, manipulator, etc.)
   - **Modality-specific queries** (speech, tactile, visual empathy expression)
   - Scale construction queries
   - Interdisciplinary queries
2. **Search academic databases**:
   - arXiv (robotics, HRI papers)
   - Semantic Scholar (comprehensive academic literature)
   - Target: 20 papers per source per query
3. **Screen papers for relevance**:
   - Assess relevance to TWO equal priorities:
     1. How to construct perceived robot empathy scales
     2. How robot empathy is understood in collaboration scenarios
   - Accept papers with score ≥ 3 (potentially relevant included)
   - Screen up to 80 papers
4. **Extract findings** from relevant papers:
   - Definitions and frameworks
   - Empathic behaviors (organized by interaction modality)
   - Measurement methods and scale construction approaches
   - Interaction modality insights
5. **Download PDFs** organized by category:
   - `definitions/`: Papers on empathy definitions
   - `behaviors/`: Papers on empathic behaviors
   - `measurement/`: Papers on measurement methods
   - Target: Up to 50 papers downloaded
6. **Organize findings** for easy reference

**Data Output**:
- Generated queries
- Screened paper list
- Extracted findings organized by category
- Downloaded PDFs with file paths
- Organized findings summary

**Key Features**:
- **Dual priority focus**: Equal emphasis on (1) scale construction methods and (2) robot empathy understanding
- **Comprehensive search**: Searches 20 papers per source per query, screens up to 80 papers
- **Inclusive screening**: Accepts papers with relevance score ≥ 3 (includes potentially relevant)
- **Broad scope**: Covers robotics, HRI, psychology, affective computing, psychometrics
- **Modality-aware extraction**: Organizes behaviors by communication channel (speech, touch, visual)
- **Category-based organization**: Downloads PDFs organized by definitions/behaviors/measurement
- **Scale limits**: Extracts from up to 50 papers, downloads up to 50 PDFs

## Execution Flow

### Phase 1: Interview Session

```
1. User runs: python main.py
2. MultiAgentWorkflow initializes
   - Creates new run_id (timestamp-based)
   - Initializes DataManager
   - Creates InterviewAgentGroup instance
3. Interview starts
   - Agent displays opening message
   - User responds to questions
   - Agent processes each response:
     a. Saves categorized data via save_interview_data tool
     b. Generates follow-up question
     c. Checks completion status
4. Interview completes when sufficient data collected
5. Interview summary displayed
6. Interview data saved to: data/runs/{run_id}/interview_agent_group/
```

**User Interaction Points**:
- User can type responses to questions
- User can type "exit", "quit", "end", or "stop" to terminate early
- Agent provides real-time feedback and confirmation

### Phase 2: Literature Search

```
1. Interview summary automatically passed to LiteratureSearchAgentGroup
2. Generate queries
   - LLM analyzes interview summary
   - Generates 5-6 comprehensive queries
   - Focuses on context, platform, and interaction modalities
3. Search databases
   - Execute queries on arXiv and Semantic Scholar
   - Collect papers (up to 20 per source per query)
4. Screen for relevance
   - LLM evaluates each paper
   - Scores relevance (1-5 scale)
   - Keeps papers with score ≥ 3
   - Progress logged every 10 papers
5. Extract findings
   - Process up to 50 most relevant papers
   - Extract definitions, behaviors, measurement methods
   - Pay special attention to interaction modalities
6. Download PDFs
   - Download papers organized by category
   - Save to pdfs/{category}/ directories
   - Progress displayed
7. Organize findings
   - Structure findings for easy reference
   - Create organized summary
8. Save results to: data/runs/{run_id}/literature_search_agent_group/
```

**Progress Indicators**:
- Query generation status
- Papers found per query
- Screening progress (every 10th paper)
- Extraction progress
- Download progress

## Data Flow

```
Interview Agent Group
    ↓ (get_interview_summary())
    {
        "assessment_context": "...",
        "robot_platform": "...",
        "interaction_modalities": "...",
        ...
    }
    ↓
Literature Search Agent Group
    ↓ (generate_queries())
    ["query1", "query2", ...]
    ↓ (search_and_screen())
    [screened_papers]
    ↓ (extract_findings())
    [findings]
    ↓ (download_pdfs())
    [downloaded_papers_with_paths]
    ↓ (organize_results())
    {
        "empathy_definitions": [...],
        "empathic_behaviors": {
            "verbal": [...],
            "nonverbal": [...],
            "adaptive": [...]
        },
        "measurement_approaches": [...],
        "existing_scales": [...]
    }
    ↓
Data Storage (data/runs/{run_id}/)
```

## Key Interactions

### Interview → Literature Search Handoff

The interview summary is automatically extracted and passed to the literature search agent:

```python
# In main.py
interview_summary = interview_agent_group.get_interview_summary()
literature_results = literature_agent.search_and_download(
    run_id,
    interview_summary
)
```

**Critical Fields Passed**:
- `assessment_context`: Informs scenario-specific queries
- `robot_platform`: Informs platform-specific queries
- `interaction_modalities`: **Critical** - informs modality-specific queries
- `assessment_goals`: Helps prioritize search focus

### Agent State Management

**Interview Agent**:
- Maintains `interview_data` dictionary throughout conversation
- Updates fields incrementally as user responds
- Uses conversation memory (LangChain) for context

**Literature Search Agent**:
- Maintains lists: `papers`, `screened_papers`, `extracted_findings`, `downloaded`
- Processes data in batches (queries → screening → extraction → download)
- State cleared between runs

## Error Handling

### Interview Phase
- **Empty responses**: Prompted to provide input or exit
- **API errors**: Error message displayed, user can retry
- **Incomplete data**: Agent continues until minimum requirements met
- **Early exit**: Current data saved, run marked as completed

### Literature Search Phase
- **No papers found**: Falls back to generic queries
- **Download failures**: Paper marked as failed, continues with others
- **API errors**: Error logged, search continues with remaining queries
- **Empty results**: Still saves structure with empty arrays

## Optimization Strategies

### Interview Agent
- Uses sub-agents to focus questions efficiently
- Prioritizes critical fields (interaction modalities)
- Accepts partial data to avoid over-questioning

### Literature Search Agent
- Parallel processing where possible (multiple queries)
- Filters early (screening before extraction/download)
- Category-based organization enables targeted retrieval
- Caches results to avoid redundant API calls

### Scale Generation Agent Group

**Primary Goal**: Generate empathy scale items based on interview and literature findings

**Key Responsibilities**:
1. **Define construct dimensions** from interview and literature data
2. **Generate scale items** using multiple parallel generators
3. **Content assessment** (if enabled): LLM evaluates item quality
4. **Semantic deduplication**: Remove semantically similar items
5. **Organize items** by dimensions and constructs

**Data Output**:
- Scale draft with all generated items
- Filtered scale draft (after deduplication and assessment)
- Semantic deduplication statistics

### Evaluation Agent Group

**Primary Goal**: Evaluate scale items using LLM personas

**Key Responsibilities**:
1. **Phase 1 (Selection)**:
   - Generate personas (empathic and non-empathic groups)
   - Evaluate all generated items
   - Compute statistics for item selection
2. **Phase 2 (Validation)**:
   - Generate independent validation personas
   - Evaluate selected items
   - Compute final metrics (Cronbach's α, Cohen's d)

**Sub-Components**:
- **PersonaGenerationAgent**: Generates LLM personas with different empathy conditions
- Evaluation methods for scoring items

**Data Output**:
- Phase 1 evaluation results (for item selection)
- Phase 2 validation results (final metrics)
- Persona files (saved for reuse)

### Item Selection Agent

**Primary Goal**: Select final items using statistical methods

**Key Methods**:
1. **Statistical Selection** (EFA/CFA):
   - Exploratory Factor Analysis (EFA)
   - Confirmatory Factor Analysis (CFA)
   - Item-total correlations
   - Factor loadings
2. **Random Selection** (for ablation studies):
   - Random item selection for comparison

**Data Output**:
- Selected items
- Selection statistics
- EFA/CFA results (if applicable)

## Future Extensions

Potential additional capabilities:
- **Report Generation Agent**: Generate comprehensive analysis reports
- **Multi-scenario Comparison Agent**: Compare scales across scenarios

Each would follow the same pattern: receive input, process, produce output, save results.

