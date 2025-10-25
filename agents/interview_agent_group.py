"""
Interview Agent Group for Human-Robot Collaboration Analysis
This agent group specializes in conducting interviews and collecting information from users.
Contains multiple sub-agents for different aspects of information gathering.
"""

import json
import os
import sys
from typing import Dict, List, Optional

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import AIMessage, HumanMessage
from langchain.tools import Tool
from langchain_openai import ChatOpenAI

# Add the utils directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from prompt_manager import PromptManager


class InterviewAgentGroup:
    """
    Agent group specialized in conducting interviews about human-robot collaboration scenarios.
    This group contains multiple sub-agents for comprehensive information gathering.
    """
    
    def __init__(self, api_key: str, model_name: str = "gpt-4", prompts_dir: str = None):
        """
        Initialize the interview agent group.
        
        Args:
            api_key: OpenAI API key
            model_name: The LLM model to use
            prompts_dir: Path to the prompts directory. If None, will auto-detect.
        """
        self.llm = ChatOpenAI(
            api_key=api_key,
            model_name=model_name,
            temperature=0.7
        )
        
        # Initialize prompt manager for this agent group
        self.prompt_manager = PromptManager(prompts_dir)
        
        # Initialize conversation memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Define the interview prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Define tools for the agent group
        self.tools = self._create_tools()
        
        # Create the main agent
        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True
        )
        
        # Track interview progress - updated for empathy assessment focus
        self.interview_data = {
            "assessment_context": None,
            "robot_platform": None,
            "collaboration_pattern": None,
            "environmental_setting": None,
            "assessment_goals": [],
            "expected_empathy_forms": [],
            "assessment_challenges": [],
            "measurement_requirements": []
        }
        
        # Initialize sub-agents (can be expanded)
        self.sub_agents = self._initialize_sub_agents()
    
    def _initialize_sub_agents(self) -> Dict[str, any]:
        """
        Initialize sub-agents within this group.
        Each sub-agent handles a specific aspect of information gathering.
        
        Returns:
            Dictionary of sub-agents
        """
        sub_agents = {
            "task_collector": TaskCollectorAgent(self.prompt_manager),
            "environment_analyzer": EnvironmentAnalyzerAgent(self.prompt_manager),
            "platform_specialist": PlatformSpecialistAgent(self.prompt_manager),
            "collaboration_expert": CollaborationExpertAgent(self.prompt_manager)
        }
        return sub_agents
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the interview agent group."""
        return self.prompt_manager.get_agent_group_prompt("interview_agent_group", "system_prompt")
    
    def _create_tools(self) -> List[Tool]:
        """Create tools for the agent group."""
        def save_interview_data(data: str) -> str:
            """Save empathy assessment-related interview data to memory."""
            # Parse assessment-related data and save to appropriate fields
            data_lower = data.lower()
            
            # Check each field in order of priority - more specific first
            if "supervised" in data_lower or "following" in data_lower or "instruction" in data_lower:
                self.interview_data["collaboration_pattern"] = data
            elif "healthcare" in data_lower or "patient care" in data_lower or "nurse" in data_lower or "medical care" in data_lower:
                if not self.interview_data["assessment_context"]:
                    self.interview_data["assessment_context"] = data
                else:
                    self.interview_data["assessment_goals"].append(data)
            elif "hospital" in data_lower or "ward" in data_lower:
                self.interview_data["environmental_setting"] = data
            elif "environment" in data_lower or "setting" in data_lower or "workplace" in data_lower:
                if not self.interview_data["environmental_setting"]:
                    self.interview_data["environmental_setting"] = data
                else:
                    self.interview_data["assessment_goals"].append(data)
            elif "humanoid" in data_lower or "facial" in data_lower or "voice" in data_lower:
                self.interview_data["robot_platform"] = data
            elif "goal" in data_lower or "objective" in data_lower:
                self.interview_data["assessment_goals"].append(data)
            elif "expect" in data_lower or "observe" in data_lower:
                self.interview_data["expected_empathy_forms"].append(data)
            elif "challenge" in data_lower or "difficult" in data_lower or "problem" in data_lower or "issue" in data_lower:
                self.interview_data["assessment_challenges"].append(data)
            elif "requirement" in data_lower or "capability" in data_lower or "measurement" in data_lower or "scale" in data_lower:
                self.interview_data["measurement_requirements"].append(data)
            elif "evaluate" in data_lower or "assess" in data_lower:
                if not self.interview_data["assessment_context"]:
                    self.interview_data["assessment_context"] = data
                else:
                    self.interview_data["assessment_goals"].append(data)
            elif "task" in data_lower or "scenario" in data_lower or "context" in data_lower or "situation" in data_lower:
                if not self.interview_data["assessment_context"]:
                    self.interview_data["assessment_context"] = data
                else:
                    self.interview_data["assessment_goals"].append(data)
            elif "robot" in data_lower or "platform" in data_lower or "embodiment" in data_lower or "appearance" in data_lower:
                if not self.interview_data["robot_platform"]:
                    self.interview_data["robot_platform"] = data
                else:
                    self.interview_data["assessment_goals"].append(data)
            elif "collaboration" in data_lower or "interaction" in data_lower or "pattern" in data_lower or "mode" in data_lower:
                if not self.interview_data["collaboration_pattern"]:
                    self.interview_data["collaboration_pattern"] = data
                else:
                    self.interview_data["assessment_goals"].append(data)
            else:
                # Default to assessment goals if unclear
                self.interview_data["assessment_goals"].append(data)
            
            return f"Assessment-related data saved: {data}"
        
        def get_interview_progress() -> str:
            """Get current interview progress."""
            progress = []
            for key, value in self.interview_data.items():
                if value:
                    progress.append(f"{key}: {value}")
            return "Interview progress: " + ", ".join(progress) if progress else "No data collected yet."
        
        def delegate_to_sub_agent(sub_agent_name: str, task: str) -> str:
            """Delegate specific tasks to sub-agents."""
            if sub_agent_name in self.sub_agents:
                return self.sub_agents[sub_agent_name].process_task(task)
            return f"Sub-agent {sub_agent_name} not found."
        
        return [
            Tool(
                name="save_interview_data",
                description="ALWAYS use this tool after each user response to save the assessment-related information they provided. This is crucial for generating the interview summary. Use this tool to save any information about assessment context, robot platform, collaboration patterns, environmental settings, assessment goals, expected empathy forms, challenges, or measurement requirements.",
                func=save_interview_data
            ),
            Tool(
                name="get_interview_progress",
                description="Get current interview progress to see what information has been collected so far",
                func=get_interview_progress
            ),
            Tool(
                name="delegate_to_sub_agent",
                description="Delegate specific assessment tasks to specialized sub-agents for deeper analysis",
                func=delegate_to_sub_agent
            )
        ]
    
    def start_interview(self) -> str:
        """Start the interview with an opening question."""
        return self.prompt_manager.get_agent_group_prompt("interview_agent_group", "opening_message")
    
    def process_response(self, user_input: str) -> str:
        """
        Process user response and generate next question or summary.
        
        Args:
            user_input: The user's response to the current question
            
        Returns:
            Agent's response/question
        """
        try:
            response = self.agent_executor.invoke({"input": user_input})
            return response["output"]
        except Exception as e:
            return self.prompt_manager.format_agent_group_prompt("interview_agent_group", "error_message", error=str(e))
    
    def get_interview_summary(self) -> Dict:
        """Get a summary of the collected interview data."""
        return self.interview_data.copy()
    
    def is_interview_complete(self) -> bool:
        """Check if sufficient empathy assessment information has been gathered."""
        required_fields = ["assessment_context", "robot_platform", "collaboration_pattern", "environmental_setting"]
        assessment_fields = ["assessment_goals", "expected_empathy_forms", "assessment_challenges", "measurement_requirements"]
        
        # Check if we have basic context AND at least some assessment-related data
        has_context = all(self.interview_data[field] for field in required_fields)
        has_assessment_data = any(self.interview_data[field] for field in assessment_fields)
        
        return has_context and has_assessment_data
    
    def reload_prompts(self):
        """Reload prompts for this agent group."""
        self.prompt_manager.reload_agent_group_prompts("interview_agent_group")
        # Update the prompt template with new system prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        # Recreate the agent with updated prompt
        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        # Recreate agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True
        )


class TaskCollectorAgent:
    """Sub-agent specialized in collecting task-related information."""
    
    def __init__(self, prompt_manager: PromptManager):
        self.prompt_manager = prompt_manager
    
    def process_task(self, task_description: str) -> str:
        """Process task-related information."""
        prompt = self.prompt_manager.get_agent_group_prompt("interview_agent_group", "task_collector_prompt")
        return f"Task analysis: {prompt} - Processing: {task_description}"


class EnvironmentAnalyzerAgent:
    """Sub-agent specialized in analyzing environment information."""
    
    def __init__(self, prompt_manager: PromptManager):
        self.prompt_manager = prompt_manager
    
    def process_task(self, environment_info: str) -> str:
        """Process environment-related information."""
        prompt = self.prompt_manager.get_agent_group_prompt("interview_agent_group", "environment_analyzer_prompt")
        return f"Environment analysis: {prompt} - Processing: {environment_info}"


class PlatformSpecialistAgent:
    """Sub-agent specialized in robot platform information."""
    
    def __init__(self, prompt_manager: PromptManager):
        self.prompt_manager = prompt_manager
    
    def process_task(self, platform_info: str) -> str:
        """Process platform-related information."""
        prompt = self.prompt_manager.get_agent_group_prompt("interview_agent_group", "platform_specialist_prompt")
        return f"Platform analysis: {prompt} - Processing: {platform_info}"


class CollaborationExpertAgent:
    """Sub-agent specialized in collaboration patterns."""
    
    def __init__(self, prompt_manager: PromptManager):
        self.prompt_manager = prompt_manager
    
    def process_task(self, collaboration_info: str) -> str:
        """Process collaboration-related information."""
        prompt = self.prompt_manager.get_agent_group_prompt("interview_agent_group", "collaboration_expert_prompt")
        return f"Collaboration analysis: {prompt} - Processing: {collaboration_info}"


def load_config(config_path: str = None) -> Dict:
    """
    Load configuration from JSON file.
    
    Args:
        config_path: Path to the configuration file. If None, will auto-detect.
        
    Returns:
        Configuration dictionary
    """
    if config_path is None:
        # Auto-detect config.json location
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        config_path = os.path.join(project_root, "config.json")
    
    try:
        with open(config_path, 'r') as file:
            config = json.load(file)
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file {config_path} not found.")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in configuration file {config_path}.")


if __name__ == "__main__":
    # Example usage
    config = load_config()
    agent_group = InterviewAgentGroup(config["openai_api_key"])
    
    print("=== Human-Robot Collaboration Interview Agent Group ===")
    print(agent_group.start_interview())
    
    while True:
        user_input = input("\nYour response: ")
        if user_input.lower() in ["exit", "quit", "end"]:
            break
        
        response = agent_group.process_response(user_input)
        print(f"\nAgent Group: {response}")
    
    print("\n=== Interview Summary ===")
    summary = agent_group.get_interview_summary()
    for key, value in summary.items():
        print(f"{key}: {value}")
