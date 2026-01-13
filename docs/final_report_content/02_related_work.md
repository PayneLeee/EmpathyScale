# Related Work

## 1. Empathy Measurement in HRI

### 1.1 Importance of Empathy in HRI

Prior studies highlight empathy's importance for trust, acceptance, and interaction quality [11,12]. Empathy in human-robot interaction has been shown to:

- Enhance user trust and willingness to collaborate
- Improve task performance in collaborative scenarios
- Increase long-term acceptance of robots in daily life
- Facilitate better communication and understanding

### 1.2 Existing Scales

**RoPE (Robot Empathy Scale)** [3]
- Focuses on general robot empathy perception
- Measures how empathic a robot is perceived
- **Limitation**: Lacks scenario sensitivity, cannot adapt to different interaction contexts

**PETS (Perceived Empathy of Technology Scale)** [4]
- Addresses technology empathy broadly
- Measures empathy of systems toward users
- **Limitation**: Too general to capture contextual nuances of specific HRI scenarios

**Key Gap**: Both scales are either too specialized or too general, lacking the ability to capture scenario-dependent differences in empathy expression and perception.

## 2. Scale Development Methodology

### 2.1 The Nine-Step Framework

The widely adopted nine-step framework by Boateng et al. [5] provides a comprehensive approach to scale development:

**Phase 1: Item Development**
- Step 1: Domain identification and item generation
- Step 2: Content validity assessment

**Phase 2: Scale Development**
- Step 3: Pre-testing questions
- Step 4: Survey administration and sample size
- Step 5: Item reduction
- Step 6: Factor extraction

**Phase 3: Scale Evaluation**
- Step 7: Dimensionality testing
- Step 8: Reliability testing
- Step 9: Validity testing

### 2.2 Recent HCI Work

Recent HCI work such as:
- **PETS** [4]: Follows the nine-step process for technology empathy
- **PSC (Perceived System Curiosity Scale)** [13]: Uses similar methodology for system curiosity

### 2.3 Limitations of Traditional Methods

While rigorous, the traditional approach has significant limitations:

- **Time-Consuming**: Typically requires months to years
- **Costly**: Requires substantial expert and participant resources
- **Resource-Intensive**: Needs professional statistical knowledge
- **Limited Scalability**: Difficult to repeat for diverse scenarios

## 3. LLMs for Item Generation

### 3.1 Psychometric Item Generation

Prior work demonstrates that LLMs can produce coherent, high-quality assessment items:

- **Laverghetta & Licato (2023)** [6]: Generating better items for cognitive assessments using LLMs
- **Laverghetta et al. (2024)** [7]: Creative Psychometric Item Generator framework

### 3.2 Structured Evaluation Tasks

LLMs can perform structured evaluation tasks:
- **Hsueh et al. (2024)** [8]: Applying Large Language Models to User Experience Testing

### 3.3 Gap in HRI Empathy

However, applications to HRI empathy remain unexplored. Our work extends LLM-based item generation to the domain of HRI empathy measurement.

## 4. Multi-Agent LLM Systems

### 4.1 Collaborative Agent Systems

Systems like ChatDev [9] and MetaGPT [10] show that role-specialized LLM agents can collaborate effectively:

- **ChatDev**: Communicative agents for software development
- **MetaGPT**: Meta programming for multi-agent collaborative framework

### 4.2 Promise for Scale Development

These developments suggest that similar architectures could support automated scale development by:

- Emulating expert workflows through specialized agents
- Coordinating multiple agents for complex tasks
- Maintaining consistency through structured communication

### 4.3 Our Extension

Our work extends this paradigm to psychometric scale generation, demonstrating that multi-agent systems can automate the core steps of traditional scale development.

## 5. Our Contribution in Context

### 5.1 What We Build On

- **Boateng's Framework**: We follow the nine-step methodology
- **LLM Item Generation**: We use LLMs for item generation
- **Multi-Agent Systems**: We employ multi-agent architecture
- **HRI Empathy Research**: We focus on HRI empathy measurement

### 5.2 What We Add

- **Scenario-Specific Generation**: Context-adaptive scales for specific HRI scenarios
- **End-to-End Automation**: Complete workflow from interview to validated scale
- **LLM-Based Evaluation**: Preliminary psychometric validation using simulated participants
- **Empirical Comparison**: Direct comparison with baseline scales (PETS, RoPE)

### 5.3 How We Differ

- **Focus**: HRI empathy (not general technology empathy)
- **Approach**: Scenario-specific (not generic)
- **Method**: Multi-agent automation (not manual expert-driven)
- **Evaluation**: LLM-based preliminary validation (not full human validation)

## 6. Related Work Summary

| Aspect | Existing Work | Our Contribution |
|--------|--------------|------------------|
| **Scale Type** | Generic (PETS, RoPE) | Scenario-specific |
| **Development** | Manual, expert-driven | Automated, LLM-based |
| **Time** | Months to years | Hours |
| **Item Generation** | Expert interviews | Multi-agent LLM |
| **Evaluation** | Human participants | LLM personas (preliminary) |
| **Scope** | Single scale | Multiple scenarios |

## 7. Positioning

Our work sits at the intersection of:
- **HRI Research**: Understanding empathy in human-robot interaction
- **Psychometrics**: Scale development methodology
- **LLM Applications**: Using language models for structured tasks
- **Multi-Agent Systems**: Coordinated agent collaboration

This positioning enables rapid, context-adaptive scale development while maintaining psychometric rigor.
