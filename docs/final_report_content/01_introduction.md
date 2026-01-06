# Introduction & Problem Statement

## 1. Background

### 1.1 The Importance of Empathy in HRI

Empathy plays a foundational role in interactive AI systems, especially in human-robot interaction (HRI), where empathic behavior influences trust, cooperation, and long-term acceptance [1,2]. Research has consistently shown that users' perception of robot empathy significantly impacts:

- **Trust**: Users are more likely to trust robots that demonstrate empathic understanding
- **Cooperation**: Empathic robots facilitate better collaborative performance
- **Acceptance**: Long-term acceptance of robots in daily life depends on perceived empathy
- **User Satisfaction**: Empathic interactions lead to higher user satisfaction and engagement

### 1.2 The Contextual Nature of Empathy

Crucially, empathy in HRI is highly **contextual**: its expression—and users' perception of it—varies widely across tasks, roles, and interaction settings. Consider these examples:

- **Collaborative Robot in Assembly Task**: Expresses empathy through adaptive task coordination (e.g., slowing down when a human hesitates, providing proactive assistance)
- **Counseling-Oriented Conversational Agent**: Demonstrates empathy through reflective dialogue, emotional validation, and attuned responses
- **Home Service Robot**: Conveys empathy by anticipating user needs, adjusting behavior in response to frustration, and providing supportive feedback

Although all represent "empathy," their forms differ sharply across platforms and use cases. This variability makes measurement challenging.

### 1.3 The Measurement Challenge

This variability makes measurement difficult. Existing instruments such as:

- **RoPE (Robot Empathy Scale)** [3]: Focuses on general robot empathy perception but lacks scenario specificity
- **PETS (Perceived Empathy of Technology Scale)** [4]: Addresses technology empathy broadly but cannot capture contextual nuances

These scales provide useful baselines but are either too specialized or too general to capture scenario-dependent differences. As a result, researchers lack tools that reflect how empathy **should** appear within a specific interaction context.

## 2. Problem Statement

### 2.1 Traditional Scale Development

Developing scenario-specific empathy scales traditionally requires the full nine-step psychometric framework [5], including:

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

### 2.2 Limitations of Traditional Methods

While rigorous, this process has significant limitations:

- **Time-Consuming**: Typically requires months to years
- **Costly**: Requires substantial expert and participant resources
- **Resource-Intensive**: Needs professional statistical knowledge and large human resources
- **Impractical for Scale**: Difficult to repeat for the diverse and rapidly expanding range of HRI scenarios

### 2.3 The Opportunity: LLM-Based Automation

Advances in large language models (LLMs) offer a potential path toward scalable solutions:

- **Item Generation**: LLMs can generate psychometric items [6,7]
- **Structured Evaluation**: LLMs can perform structured evaluation tasks such as UX analysis [8]
- **Multi-Agent Systems**: Systems like ChatDev [9] and MetaGPT [10] show that coordinated, role-specialized agents can emulate complex expert workflows

These developments motivate exploring whether similar architectures can support rapid creation of **scenario-sensitive** empathy scales for HRI.

## 3. Research Questions

This project addresses three key research questions:

1. **RQ1**: Can multi-agent LLMs generate coherent, scenario-specific empathy items?
2. **RQ2**: Can LLM evaluation agents provide consistent preliminary judgments?
3. **RQ3**: Do generated items appear more contextually appropriate than baseline scales such as PETS?

## 4. Project Objectives

This project aims to develop a lightweight, non-iterative multi-agent LLM prototype that:

- Generates scenario-specific empathy items
- Conducts preliminary evaluation using simulated "participants"
- Produces scales with good psychometric properties
- Demonstrates superiority over generic baseline scales

Comprehensive validation with human users is reserved for future work.

## 5. Expected Contributions

The main contributions of this work are:

1. **Novel Architecture**: A multi-agent system for automated psychometric scale generation
2. **Scenario-Specific Generation**: Demonstration of context-adaptive scale generation for HRI
3. **LLM-Based Evaluation**: Validation of LLM-based evaluation for preliminary psychometric assessment
4. **Empirical Evidence**: Superior performance compared to baseline scales

## 6. Scope and Limitations

### 6.1 Scope

- Focus on three HRI scenarios: collaborative assembly, home service, and counseling
- LLM-based evaluation (no human participants in this phase)
- Preliminary psychometric validation (not full validation)

### 6.2 Limitations

- No human data collection
- Single-run generation (no iterative refinement)
- Limited to three scenarios
- LLM simulation may not fully capture human variability

These limitations are addressed in the Limitations & Future Work section.
