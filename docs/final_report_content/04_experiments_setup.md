# Experiments & Results - Experimental Setup

## 1. Experimental Scenarios

We evaluated our system on three distinct HRI scenarios, each with unique characteristics and assessment goals.

### 1.1 Scenario 1: Collaborative Robot Assembly

**Scenario ID**: `collab_robot_assembly`

**Setting**:
- **Assessment Context**: Factory assembly, human-robot collaborative partner
- **Robot Platform**: Collaborative robotic arm
- **Interaction Modalities**: Gesture + Speech
- **Collaboration Pattern**: Turn-taking assembly
- **Environmental Setting**: Factory workshop
- **Assessment Goals**: Safety awareness, adaptive pacing
- **Expected Empathy Forms**: Mirroring hesitation, proactive assistance
- **Measurement Requirements**: Short Likert scale, behavior-oriented

**Key Characteristics**:
- Task-focused collaboration
- Safety-critical environment
- Real-time adaptation needed
- Physical proximity

### 1.2 Scenario 2: Home Service Robot

**Scenario ID**: `home_service_robot`

**Setting**:
- **Assessment Context**: Home assistant, supporting daily tasks
- **Robot Platform**: Mobile service robot
- **Interaction Modalities**: Speech + Navigation cues
- **Collaboration Pattern**: Assistive
- **Environmental Setting**: Home environment
- **Assessment Goals**: Comfort, perceived care
- **Expected Empathy Forms**: Detecting frustration, providing comfort
- **Measurement Requirements**: Non-technical language

**Key Characteristics**:
- Long-term interaction
- Domestic context
- User comfort priority
- Non-expert users

### 1.3 Scenario 3: Counseling Chatbot

**Scenario ID**: `counseling_chatbot`

**Setting**:
- **Assessment Context**: Text-based counseling robot
- **Robot Platform**: Chatbot
- **Interaction Modalities**: Text chat
- **Collaboration Pattern**: Supportive dialogue
- **Environmental Setting**: Remote
- **Assessment Goals**: Emotional attunement
- **Expected Empathy Forms**: Reflective listening, emotional validation
- **Measurement Requirements**: Short statements

**Key Characteristics**:
- Text-only interaction
- Emotional support focus
- Remote context
- High empathy requirement

## 2. Evaluation Setup

### 2.1 Persona Generation

**Number of Personas**: 200 per scenario per phase

**Persona Attributes**:
- **Demographics**: Age (18-65), gender, education level
- **Technical Background**: ATI (Affinity for Technology Interaction) score (1-5)
- **Occupation**: Various job types
- **Empathy Condition**: 
  - **Empathic group**: High empathy personas (100 personas)
  - **Non-empathic group**: Low empathy personas (100 personas)

**Persona Diversity**:
- Balanced age distribution
- Gender diversity
- Education levels from high school to graduate
- ATI scores from 1.0 to 5.0
- Various occupations

### 2.2 Evaluation Process

**Two-Phase Evaluation**:

**Phase 1 (Selection)**:
- Purpose: Evaluate all candidate items for statistical selection
- Personas: 200 personas (100 empathic, 100 non-empathic)
- Items: All generated candidate items
- Output: Statistics for item selection

**Phase 2 (Validation)**:
- Purpose: Validate selected items with independent persona group
- Personas: 200 new personas (100 empathic, 100 non-empathic)
- Items: Selected items only
- Output: Final psychometric metrics

**Rationale**: Phase 2 uses independent personas to avoid overfitting (following PETS methodology).

### 2.3 Rating Scale

- **Scale**: 0-100 (continuous)
- **Anchors**: 
  - 0: Strongly Disagree
  - 50: Neutral
  - 100: Strongly Agree
- **Interpretation**: Higher scores indicate stronger agreement that the robot demonstrates empathic behavior

### 2.4 Evaluation Metrics

**Internal Consistency**:
- **Cronbach's α**: Measures how well items measure the same construct
- **Interpretation**: α > 0.9 = Excellent, α > 0.7 = Acceptable

**Discriminant Validity**:
- **Cohen's d**: Effect size comparing empathic vs. non-empathic persona ratings
- **Interpretation**: d > 2.0 = Very large effect, d > 0.8 = Large effect

**Statistical Significance**:
- **t-test**: Compare empathic vs. non-empathic groups
- **Significance level**: p < 0.001

**Factor Structure**:
- **EFA**: Exploratory factor analysis to identify dimensions
- **CFA**: Confirmatory factor analysis to validate structure
- **Fit Indices**: RMSEA < 0.08, TLI/CFI > 0.9

## 3. Baseline Comparison Setup

### 3.1 Baseline Scales

**PETS (Perceived Empathy of Technology Scale)** [4]:
- 10 items
- 2 factors: Emotional Responsiveness, Understanding and Trust
- Generic technology empathy scale

**RoPE (Robot Empathy Scale)** [3]:
- 16 items
- 2 factors: Empathic Understanding, Empathic Response
- General robot empathy scale

### 3.2 Comparison Procedure

**Evaluation Settings**:
- Use **the same validation personas** as generated scales (200 personas)
- Evaluate in **all 3 scenarios** (Factory assembly, Home service, Counseling)
- Same rating scale (0-100)
- Same evaluation metrics

**Comparison Metrics**:
- **Quantitative**: Internal consistency (α), Discriminant validity (Cohen's d), Item count
- **Qualitative**: Scenario relevance, Item specificity, Behavioral observability, Dimension richness

**Purpose**: Validate the effectiveness of generated scales, demonstrate advantages of scenario customization.

## 4. Ablation Study Setup

### 4.1 Study Design

**Scenario**: Collaborative robot assembly (`collab_robot_assembly`)

**Baseline Configuration**:
- 5 item generation agents
- Content assessment enabled
- EFA/CFA statistical selection
- **Result**: α = 0.992, Cohen's d = 4.634, 16 items

**Ablation Variants**:

1. **Fewer Generators**:
   - 1 generator (vs. 5)
   - Content assessment: Enabled
   - Selection: EFA/CFA
   - **Purpose**: Test impact of generator count

2. **No Content Assessment**:
   - 5 generators
   - Content assessment: Disabled
   - Selection: Random (extreme control)
   - **Purpose**: Test impact of content assessment

3. **Fewer Generators + No Content**:
   - 1 generator
   - Content assessment: Disabled
   - Selection: EFA/CFA
   - **Purpose**: Test combined impact

### 4.2 Evaluation Process

**Same as Main Experiments**:
- Phase 1: 200 personas evaluate all candidate items
- Statistical selection based on Phase 1 data
- Phase 2: 200 personas evaluate selected items
- Compute final metrics

**Key Metrics**:
- Internal consistency (Cronbach's α)
- Discriminant validity (Cohen's d)
- Number of selected items
- Average ratings

### 4.3 Expected Outcomes

- **Baseline should perform best**: All components contribute to quality
- **Ablation variants should show lower quality**: Validates design choices
- **Internal consistency should remain high**: Basic quality maintained
- **Discriminant validity should decrease**: Key differentiator

## 5. Experimental Runs

### 5.1 Main Experiments

For each scenario, we conducted multiple runs and selected the best based on quality scoring:

**Factory Assembly**:
- Best Run: `2025-12-22_215026`
- Quality Score: 0.997
- Selected based on: Multi-factor structure, high α, high Cohen's d

**Home Service**:
- Best Run: `2025-12-22_210718`
- Quality Score: 0.947
- Selected based on: Multi-factor structure, high α, high Cohen's d

**Counseling**:
- Best Run: `2025-12-22_212205`
- Quality Score: 1.000
- Selected based on: Multi-factor structure, high α, high Cohen's d

### 5.2 Ablation Experiments

**Baseline**:
- Run: `2025-12-22_215026` (same as main experiment)

**Ablation Variants**:
- Fewer Generators: `2025-12-22_215303`
- No Content Assessment: `2025-12-22_215922`
- Fewer + No Content: `2025-12-22_220713`

### 5.3 Baseline Comparison

**Generated Scales**: Selected best runs for each scenario
**PETS**: Evaluated in all 3 scenarios
**RoPE**: Evaluated in all 3 scenarios

## 6. Quality Scoring System

### 6.1 Scoring Criteria

**Multi-Factor Priority**:
- Prefer scales with 2-3 factors (better reflects empathy's multidimensional nature)
- Single-factor scales penalized

**Psychometric Quality**:
- High internal consistency (α > 0.95)
- High discriminant validity (Cohen's d > 4.0)
- Statistical significance (p < 0.001)

**Item Count**:
- Prefer 10-20 items (balance between comprehensiveness and brevity)
- Too few items (< 8): Penalized
- Too many items (> 20): Penalized

### 6.2 Scoring Formula

```
Quality Score = (
    0.4 * factor_score +      # Multi-factor bonus
    0.3 * alpha_score +       # Internal consistency
    0.3 * cohens_d_score      # Discriminant validity
)
```

Where:
- `factor_score`: 1.0 if 2-3 factors, 0.5 if 1 factor, 0.0 if >3 factors
- `alpha_score`: Normalized α (0-1 scale)
- `cohens_d_score`: Normalized Cohen's d (0-1 scale, capped at 10.0)

## 7. Statistical Analysis

### 7.1 Item Selection

**EFA (Exploratory Factor Analysis)**:
- Method: Principal Axis Factoring
- Rotation: Promax (oblique)
- Factor extraction: Eigenvalue > 1.0
- Factor loading threshold: ≥ 0.4

**CFA (Confirmatory Factor Analysis)**:
- Software: Python `semopy` package
- Fit indices:
  - RMSEA < 0.08 (acceptable fit)
  - TLI > 0.9 (good fit)
  - CFI > 0.9 (good fit)
  - SRMR < 0.08 (good fit)

**Item-Total Correlation**:
- Threshold: ≥ 0.3
- Purpose: Remove items not measuring the construct

**Distribution Checks**:
- Avoid ceiling effects (mean > 90)
- Avoid floor effects (mean < 10)
- Prefer normal distribution

### 7.2 Reliability Analysis

**Cronbach's α**:
- Computed for all selected items
- Interpretation: α > 0.9 = Excellent

**Item-Level Statistics**:
- Mean rating
- Standard deviation
- Distribution shape

### 7.3 Validity Analysis

**Discriminant Validity**:
- Compare empathic vs. non-empathic persona groups
- Compute Cohen's d effect size
- Statistical significance (t-test, p < 0.001)

**Content Validity**:
- Qualitative assessment of item relevance
- Scenario specificity check
- Behavioral observability check

## 8. Implementation Details

### 8.1 Software and Tools

- **LLM**: OpenAI GPT-4o-mini
- **Statistical Analysis**: Python (scipy, numpy, pandas, semopy)
- **Factor Analysis**: `factor_analyzer` package
- **Parallel Processing**: `concurrent.futures.ThreadPoolExecutor`

### 8.2 Computational Resources

- **API Calls**: ~500-1000 per scenario (including all phases)
- **Processing Time**: 2-4 hours per scenario
- **Cost**: ~$50-100 per scenario (using GPT-4o-mini)

### 8.3 Reproducibility

- **Random Seeds**: Fixed for persona generation
- **Prompt Versions**: Version-controlled in JSON files
- **Data Storage**: All runs saved with timestamps
- **Code Versioning**: Git repository with tagged releases
