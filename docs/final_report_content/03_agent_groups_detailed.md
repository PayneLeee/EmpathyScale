# Technical Approach - Agent Groups Detailed

## 1. Interview Agent Group

### 1.1 Purpose

Conducts structured interviews to gather comprehensive information about the robot collaboration scenario.

### 1.2 Key Responsibilities

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

### 1.3 Implementation

**Type**: LangChain-based agent with tools

**Components**:
- `ChatOpenAI`: LLM integration
- `AgentExecutor`: Manages agent execution
- `ConversationBufferMemory`: Maintains conversation context
- `Tools`: 
  - `save_interview_data`: Saves categorized data
  - `get_interview_progress`: Checks completion status
  - `delegate_to_sub_agent`: Delegates to specialized sub-agents

**Sub-Agents**:
- **TaskCollectorAgent**: Focuses on task descriptions and activities
- **EnvironmentAnalyzerAgent**: Analyzes workplace and environmental factors
- **PlatformSpecialistAgent**: Investigates robot platform characteristics and capabilities
- **CollaborationExpertAgent**: Explores collaboration patterns and interaction modes

### 1.4 Completion Criteria

- **Required**: `assessment_context`, `robot_platform`, `environmental_setting`
- **Important**: `interaction_modalities`, `collaboration_pattern`
- **Additional**: At least one of `assessment_goals`, `expected_empathy_forms`, `assessment_challenges`, or `measurement_requirements`

### 1.5 Output

- Structured summary (JSON format)
- Full conversation history
- Completion status

## 2. Literature Search Agent Group

### 2.1 Purpose

Searches, screens, and synthesizes academic literature on robot empathy.

### 2.2 Key Responsibilities

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

### 2.3 Implementation

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
- `search_and_download(run_id, interview_summary)`: Execute full workflow

### 2.4 Output

- Generated queries
- Screened paper list
- Extracted findings organized by category
- Downloaded PDFs with file paths
- Organized findings summary

## 3. Empathy Scale Generation Agent Group

### 3.1 Purpose

Generates empathy scale items based on interview and literature findings.

### 3.2 Key Responsibilities

1. **Define construct dimensions** from interview and literature data
2. **Generate scale items** using multiple parallel generators
3. **Content assessment** (if enabled): LLM evaluates item quality
4. **Semantic deduplication**: Remove semantically similar items
5. **Organize items** by dimensions and constructs

### 3.3 Implementation

**Components**:
- `ConstructDefinitionAgent`: Defines empathy constructs and dimensions
- `ItemGenerationAgent`: Generates candidate items (multiple instances)
- `ContentAssessmentAgent`: Evaluates and refines item quality
- `SemanticDeduplication`: Removes redundant items

**Workflow**:
1. Load interview summary and literature findings
2. Define constructs using ConstructDefinitionAgent
3. Generate items using multiple ItemGenerationAgents (parallel)
4. Perform content assessment (if enabled)
5. Apply semantic deduplication
6. Organize items by dimensions

**Configuration**:
- `num_item_generators`: Number of parallel generators (default: 3-5)
- `enable_content_assessment`: Whether to perform content assessment (default: True)

### 3.4 Output

- Scale draft with all generated items
- Filtered scale draft (after deduplication and assessment)
- Semantic deduplication statistics
- Generation summary

## 4. Evaluation Agent Group

### 4.1 Purpose

Evaluates scale items using LLM personas.

### 4.2 Key Responsibilities

**Phase 1 (Selection)**:
- Generate personas (empathic and non-empathic groups)
- Evaluate all generated items
- Compute statistics for item selection

**Phase 2 (Validation)**:
- Generate independent validation personas
- Evaluate selected items
- Compute final metrics (Cronbach's α, Cohen's d)

### 4.3 Implementation

**Components**:
- `PersonaGenerationAgent`: Generates LLM personas with different empathy conditions
- Evaluation methods for scoring items
- Parallel processing for persona evaluation

**Persona Generation**:
- **Diversity**: Age, gender, education, ATI scores, occupation
- **Empathy Conditions**: Empathic vs. non-empathic personas
- **Scenario Context**: Personas adapted to specific scenario

**Evaluation Process**:
1. Generate or load personas (200 per phase)
2. Each persona rates all items (0-100 scale)
3. Compute statistics:
   - Item-level statistics (mean, std, distribution)
   - Persona-level statistics
   - Discriminant validity (Cohen's d)
   - Internal consistency (Cronbach's α)

**Parallel Processing**:
- Up to 5 parallel workers for persona evaluation
- Batch processing for large item sets (100 items per batch)
- Progress tracking and error handling

### 4.4 Output

- Phase 1 evaluation results (for item selection)
- Phase 2 validation results (final metrics)
- Persona files (saved for reuse)
- Evaluation summary with statistics

## 5. Item Selection Agent

### 5.1 Purpose

Selects final items using statistical methods.

### 5.2 Methods

**Statistical Selection (EFA/CFA)**:
- **Exploratory Factor Analysis (EFA)**:
  - Principal Axis Factoring
  - Promax rotation
  - Factor extraction and interpretation
- **Confirmatory Factor Analysis (CFA)**:
  - Model fitting
  - Fit indices (RMSEA, TLI, CFI, SRMR)
  - Factor structure validation
- **Item-total correlations**: Remove items with low correlation (< 0.3)
- **Distribution checks**: Avoid ceiling/floor effects
- **Item-item correlations**: Remove highly redundant items (> 0.8)

**Random Selection** (for ablation studies):
- Random item selection for comparison
- Same number of items as statistical selection

### 5.3 Implementation

**Location**: `utils/statistical_item_selection.py`

**Key Functions**:
- `select_items_efa_cfa()`: Statistical selection using EFA/CFA
- `select_items_random()`: Random selection for ablation
- `perform_efa()`: Exploratory factor analysis
- `perform_cfa()`: Confirmatory factor analysis

**Selection Criteria**:
1. Item-total correlation ≥ 0.3
2. Factor loading ≥ 0.4
3. No ceiling/floor effects
4. Item-item correlation < 0.8
5. Balanced representation across factors

### 5.4 Output

- Selected items (item IDs)
- Selection statistics
- EFA results (factors, loadings, eigenvalues)
- CFA results (fit indices, factor structure)

## 6. Persona Generation Agent

### 6.1 Purpose

Generates diverse LLM personas for evaluation.

### 6.2 Persona Attributes

- **Demographics**: Age, gender, education level
- **Technical Background**: ATI (Affinity for Technology Interaction) score
- **Occupation**: Job type and experience
- **Empathy Condition**: Empathic vs. non-empathic
- **Scenario Context**: Adapted to specific HRI scenario

### 6.3 Implementation

**Location**: `agents/persona_generation_agent.py`

**Generation Process**:
1. Generate base persona attributes
2. Assign empathy condition (empathic/non-empathic)
3. Adapt to scenario context
4. Generate interaction experience description
5. Save personas for reuse

**Persona Storage**:
- Saved by scenario ID and phase
- Phase 1 (selection) and Phase 2 (validation) use independent persona groups
- JSON format for easy loading

### 6.4 Output

- List of persona dictionaries
- Saved to `data/personas/{scenario_id}_{phase}.json`

## 7. Agent Group Interactions

### 7.1 Data Flow

```
InterviewAgentGroup
    ↓ (summary.json)
LiteratureSearchAgentGroup
    ↓ (findings.json)
EmpathyScaleGenerationAgentGroup
    ↓ (scale_draft.md)
EvaluationAgentGroup (Phase 1)
    ↓ (evaluation_summary.json)
ItemSelectionAgent
    ↓ (selected_items.json)
EvaluationAgentGroup (Phase 2)
    ↓ (final_evaluation_summary.json)
```

### 7.2 Error Handling

Each agent group handles errors independently:
- **API Failures**: Retry with exponential backoff
- **Partial Failures**: Continue processing remaining items
- **Data Validation**: Check input data before processing
- **User Feedback**: Display progress and errors

### 7.3 Performance Optimization

- **Parallel Processing**: Multiple generators, parallel persona evaluation
- **Batch Processing**: Large item sets processed in batches
- **Caching**: Personas and intermediate results cached
- **Progress Tracking**: Real-time progress updates
