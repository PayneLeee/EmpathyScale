# 如何添加新的Agent Group

## 当前状态
目前项目中有两个agent group：
- `agents/interview_agent_group.py` ↔ `prompts/interview_agent_group.json`
- `agents/research_agent_group.py` ↔ `prompts/research_agent_group.json`

## 命名约定
每个agent group必须遵循严格的命名约定：
- **Agent Group文件**: `agents/{group_name}_agent_group.py`
- **Prompt文件**: `prompts/{group_name}_agent_group.json`

例如：
- `agents/interview_agent_group.py` ↔ `prompts/interview_agent_group.json`
- `agents/research_agent_group.py` ↔ `prompts/research_agent_group.json`
- `agents/analysis_agent_group.py` ↔ `prompts/analysis_agent_group.json`

## Agent Group架构
每个agent group包含：
1. **主Agent Group类**: 协调整个组的工作
2. **子Agent类**: 处理特定功能领域
3. **统一的Prompt文件**: 包含主prompt和所有子agent的prompts

## 添加新Agent Group的步骤

### 1. 创建Agent Group类文件

在 `agents/` 目录下创建新的agent group文件，例如 `analysis_agent_group.py`：

```python
"""
Analysis Agent Group for Human-Robot Collaboration Analysis
This agent group specializes in analyzing collected data and generating insights.
"""

import sys
import os
from typing import Dict, List, Optional

# Add the utils directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from prompt_manager import PromptManager

class AnalysisAgentGroup:
    """
    Agent group specialized in analyzing human-robot collaboration data.
    Contains multiple sub-agents for different analysis aspects.
    """
    
    def __init__(self, api_key: str, model_name: str = "gpt-4", prompts_dir: str = "prompts"):
        """
        Initialize the analysis agent group.
        
        Args:
            api_key: OpenAI API key
            model_name: The LLM model to use
            prompts_dir: Path to the prompts directory
        """
        # Initialize prompt manager for this agent group
        self.prompt_manager = PromptManager(prompts_dir)
        
        # Initialize sub-agents
        self.sub_agents = self._initialize_sub_agents()
    
    def _initialize_sub_agents(self) -> Dict[str, any]:
        """Initialize sub-agents within this group."""
        sub_agents = {
            "pattern_analyzer": PatternAnalyzerAgent(self.prompt_manager),
            "recommendation_engine": RecommendationEngineAgent(self.prompt_manager),
            "insight_generator": InsightGeneratorAgent(self.prompt_manager)
        }
        return sub_agents
    
    def analyze_data(self, interview_data: Dict) -> str:
        """Analyze interview data using sub-agents."""
        # Get system prompt from analysis_agent_group.json
        system_prompt = self.prompt_manager.get_agent_group_prompt("analysis_agent_group", "system_prompt")
        
        # Use sub-agents for analysis
        analysis_results = {}
        for name, agent in self.sub_agents.items():
            analysis_results[name] = agent.process_data(interview_data)
        
        return analysis_results

# Sub-agent classes
class PatternAnalyzerAgent:
    """Sub-agent for pattern analysis."""
    
    def __init__(self, prompt_manager: PromptManager):
        self.prompt_manager = prompt_manager
    
    def process_data(self, data: Dict) -> str:
        prompt = self.prompt_manager.get_agent_group_prompt("analysis_agent_group", "pattern_analyzer_prompt")
        return f"Pattern analysis: {prompt}"

class RecommendationEngineAgent:
    """Sub-agent for generating recommendations."""
    
    def __init__(self, prompt_manager: PromptManager):
        self.prompt_manager = prompt_manager
    
    def process_data(self, data: Dict) -> str:
        prompt = self.prompt_manager.get_agent_group_prompt("analysis_agent_group", "recommendation_engine_prompt")
        return f"Recommendations: {prompt}"

class InsightGeneratorAgent:
    """Sub-agent for generating insights."""
    
    def __init__(self, prompt_manager: PromptManager):
        self.prompt_manager = prompt_manager
    
    def process_data(self, data: Dict) -> str:
        prompt = self.prompt_manager.get_agent_group_prompt("analysis_agent_group", "insight_generator_prompt")
        return f"Insights: {prompt}"
```

### 2. 创建对应的Prompt文件

在 `prompts/` 目录下创建对应的JSON文件，例如 `analysis_agent_group.json`：

```json
{
  "system_prompt": "You are an expert analyst specializing in human-robot collaboration scenarios. Your role is to analyze interview data and provide insights about the collaboration setup.",
  "analysis_template": "Based on the interview data, here is my analysis: {analysis}",
  "pattern_analyzer_prompt": "Focus on identifying patterns and trends in the collaboration data. Look for recurring themes and behaviors.",
  "recommendation_engine_prompt": "Generate specific, actionable recommendations based on the analysis findings.",
  "insight_generator_prompt": "Provide deep insights about the collaboration dynamics and potential improvements."
}
```

### 3. 更新主工作流

在 `main.py` 中添加新agent group：

```python
# Add import
from agents.analysis_agent_group import AnalysisAgentGroup

class MultiAgentWorkflow:
    def _initialize_agents(self):
        # Existing agent groups
        self.agents['interview'] = InterviewAgentGroup(
            api_key=self.config["openai_api_key"]
        )
        
        # New agent group
        self.agents['analysis'] = AnalysisAgentGroup(
            api_key=self.config["openai_api_key"]
        )
```

### 4. 测试新Agent Group

运行调试工具来测试新agent group的prompts：

```bash
python debug_prompts.py
```

选择新添加的agent group来查看和测试其prompts。

## 重要提醒

1. **文件命名必须一致**: `{group_name}_agent_group.py` 和 `{group_name}_agent_group.json`
2. **PromptManager自动加载**: 只要文件名遵循约定，PromptManager会自动找到对应的prompt文件
3. **子Agent管理**: 每个agent group内部管理自己的子agent
4. **统一Prompt管理**: 所有子agent的prompts都存储在同一个JSON文件中
5. **独立功能领域**: 每个agent group专注于特定的功能领域
6. **当前项目状态**: 目前有interview_agent_group和research_agent_group，其他agent group需要按需添加

## 优势

- **功能分组**: 相关功能组织在同一个agent group中
- **清晰的对应关系**: 每个agent group文件都有对应的prompt文件
- **模块化设计**: 每个agent group完全独立
- **易于维护**: 修改agent group或prompts都很直观
- **扩展性强**: 添加新agent group只需遵循命名约定
- **子Agent协调**: 主agent group可以协调多个子agent的工作
- **避免冗余**: 只创建实际需要的agent group，避免未使用的文件