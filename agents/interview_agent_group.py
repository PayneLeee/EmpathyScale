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
            "interaction_modalities": None,  # NEW: Emphasis on communication channels
            "collaboration_pattern": None,
            "environmental_setting": None,
            "assessment_goals": [],
            "expected_empathy_forms": [],
            "assessment_challenges": [],
            "measurement_requirements": []
        }
        
        # Initialize sub-agents (can be expanded)
        self.sub_agents = self._initialize_sub_agents()
        
        # Track conversation history for data storage
        self.conversation_history = []
    
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
            # REORDERED: Check context and platform BEFORE interaction modalities to avoid over-capturing
            
            # 1. Assessment context (highest priority for scenario description)
            if any(keyword in data_lower for keyword in ["healthcare", "patient care", "nurse", "medical care", "assembly", "manufacturing", "workers"]):
                if not self.interview_data["assessment_context"]:
                    self.interview_data["assessment_context"] = data
                else:
                    self.interview_data["assessment_goals"].append(data)
            elif any(keyword in data_lower for keyword in ["hospital", "ward", "manufacturing floor", "factory", "assembly stations"]):
                self.interview_data["environmental_setting"] = data
            elif any(keyword in data_lower for keyword in ["evaluate", "assess"]) and ("robot" in data_lower or "scenario" in data_lower):
                if not self.interview_data["assessment_context"]:
                    self.interview_data["assessment_context"] = data
                else:
                    self.interview_data["assessment_goals"].append(data)
            elif any(keyword in data_lower for keyword in ["task", "scenario", "context", "situation"]) and not any(modality_word in data_lower for modality_word in ["interaction modality", "modalities"]):
                if not self.interview_data["assessment_context"]:
                    self.interview_data["assessment_context"] = data
                else:
                    self.interview_data["assessment_goals"].append(data)
            
            # 2. Robot platform (before interaction modalities to capture platform first)
            elif "humanoid" in data_lower or ("robot" in data_lower and any(keyword in data_lower for keyword in ["humanoid", "dual-arm", "manipulator", "force feedback", "vision sensors", "expressive facial", "facial features", "appearance", "embodiment"])) or ("robot" in data_lower and ("platform" in data_lower or "embodiment" in data_lower or "appearance" in data_lower)):
                if not self.interview_data["robot_platform"]:
                    self.interview_data["robot_platform"] = data
                else:
                    # Append additional platform details if we already have a platform
                    if data not in self.interview_data["robot_platform"]:
                        self.interview_data["robot_platform"] += ". " + data
                # Also check if this mentions facial expressions for interaction modalities
                if ("facial" in data_lower or "expression" in data_lower) and ("expressive" in data_lower or "capabilities" in data_lower):
                    if not self.interview_data["interaction_modalities"]:
                        self.interview_data["interaction_modalities"] = "Facial expressions"
                    elif "facial" not in self.interview_data["interaction_modalities"].lower():
                        self.interview_data["interaction_modalities"] += ", facial expressions"
            
            # 3. Environmental setting
            elif any(keyword in data_lower for keyword in ["environment", "setting", "workplace"]) and not any(modality_word in data_lower for modality_word in ["interaction modality", "modalities"]):
                if not self.interview_data["environmental_setting"]:
                    self.interview_data["environmental_setting"] = data
                else:
                    self.interview_data["assessment_goals"].append(data)
            
            # 4. Collaboration pattern
            elif any(keyword in data_lower for keyword in ["supervised", "following", "instruction", "peer-to-peer", "coordination", "shared workspace", "one-on-one", "one to one", "interacts with", "adaptive", "adapts", "based on"]) or (("adapt" in data_lower or "interact" in data_lower) and ("patient" in data_lower or "user" in data_lower or "state" in data_lower or "emotional" in data_lower)):
                if not self.interview_data["collaboration_pattern"]:
                    self.interview_data["collaboration_pattern"] = data
                else:
                    if data not in self.interview_data["collaboration_pattern"]:
                        self.interview_data["collaboration_pattern"] += ". " + data
            elif any(keyword in data_lower for keyword in ["collaboration", "pattern", "mode"]) and "interaction" not in data_lower:
                if not self.interview_data["collaboration_pattern"]:
                    self.interview_data["collaboration_pattern"] = data
                else:
                    self.interview_data["assessment_goals"].append(data)
            
            # 5. Assessment goals, empathy forms, challenges, requirements
            elif any(keyword in data_lower for keyword in ["goal", "objective"]) and "assessment" in data_lower:
                self.interview_data["assessment_goals"].append(data)
            elif any(keyword in data_lower for keyword in ["expect", "observe"]) and ("empathy" in data_lower or "form" in data_lower):
                self.interview_data["expected_empathy_forms"].append(data)
            elif any(keyword in data_lower for keyword in ["challenge", "difficult", "problem", "issue"]) and ("assess" in data_lower or "evaluat" in data_lower):
                self.interview_data["assessment_challenges"].append(data)
            elif any(keyword in data_lower for keyword in ["requirement", "capability"]) and ("measurement" in data_lower or "scale" in data_lower):
                self.interview_data["measurement_requirements"].append(data)
            
            # 6. Interaction modalities (NOW more specific, only when explicitly about modalities)
            # Only capture if explicitly mentioning modalities OR specific modality types in context
            elif "interaction modalit" in data_lower or "communication channel" in data_lower or "interaction channel" in data_lower:
                if not self.interview_data["interaction_modalities"]:
                    self.interview_data["interaction_modalities"] = data
                else:
                    self.interview_data["interaction_modalities"] += " " + data
            elif any(keyword in data_lower for keyword in ["speech characteristic", "voice tone", "tone and pace", "calming voice", "empathetic language", "tactile feedback", "haptic feedback", "visual cue", "indicator light", "led display", "facial expression", "facial expressions", "expressive facial", "physical gesture", "body language", "nonverbal cue", "voice capabilities", "expressive features"]):
                # Only capture specific modality phrases, not just any mention of these words
                if not self.interview_data["interaction_modalities"]:
                    self.interview_data["interaction_modalities"] = data
                else:
                    # Check if this modality is already mentioned
                    if not any(modality_word in self.interview_data["interaction_modalities"].lower() for modality_word in data_lower.split() if len(modality_word) > 4):
                        self.interview_data["interaction_modalities"] += ", " + data
                    else:
                        self.interview_data["interaction_modalities"] += " " + data
            elif any(keyword in data_lower for keyword in ["touch", "haptic", "tactile", "physical contact", "hug", "pat"]) and ("express" in data_lower or "convey" in data_lower or "through" in data_lower or "gesture" in data_lower):
                # Touch/haptic only if it's about expressing something
                if not self.interview_data["interaction_modalities"]:
                    self.interview_data["interaction_modalities"] = data
                else:
                    self.interview_data["interaction_modalities"] += " " + data
            elif any(keyword in data_lower for keyword in ["indicator", "light", "led", "display", "screen"]) and ("visual" in data_lower or "cue" in data_lower or "communicat" in data_lower):
                # Visual cues only if explicitly about communication
                if not self.interview_data["interaction_modalities"]:
                    self.interview_data["interaction_modalities"] = data
                else:
                    self.interview_data["interaction_modalities"] += " " + data
            elif ("verbal" in data_lower or "nonverbal" in data_lower) and ("cue" in data_lower or "express" in data_lower or "through" in data_lower):
                # Verbal/nonverbal only if about cues or expression
                if not self.interview_data["interaction_modalities"]:
                    self.interview_data["interaction_modalities"] = data
                else:
                    self.interview_data["interaction_modalities"] += " " + data
            elif "gesture" in data_lower and ("show" in data_lower or "express" in data_lower or "care" in data_lower or "understanding" in data_lower):
                # Physical gestures that show care/understanding
                if not self.interview_data["interaction_modalities"]:
                    self.interview_data["interaction_modalities"] = data
                else:
                    # Ensure facial expressions are also mentioned if they were mentioned in conversation
                    modalities_lower = self.interview_data["interaction_modalities"].lower()
                    if "facial" not in modalities_lower and "expression" not in modalities_lower:
                        # Check if facial expressions were mentioned in the environmental_setting or assessment_context
                        env_setting = self.interview_data.get("environmental_setting", "")
                        if env_setting:
                            env_lower = str(env_setting).lower()
                            if "facial" in env_lower or ("expressive" in env_lower and "feature" in env_lower):
                                self.interview_data["interaction_modalities"] += ", facial expressions"
                    # Append gesture description
                    if self.interview_data["interaction_modalities"][-1] not in ", ":
                        self.interview_data["interaction_modalities"] += ", " + data
                    else:
                        self.interview_data["interaction_modalities"] += data
            
            # 7. Catch-all for remaining cases
            elif any(keyword in data_lower for keyword in ["robot", "platform"]):
                if not self.interview_data["robot_platform"]:
                    self.interview_data["robot_platform"] = data
                else:
                    self.interview_data["assessment_goals"].append(data)
            elif any(keyword in data_lower for keyword in ["collaboration", "interaction"]):
                if not self.interview_data["collaboration_pattern"]:
                    self.interview_data["collaboration_pattern"] = data
                else:
                    self.interview_data["assessment_goals"].append(data)
            elif any(keyword in data_lower for keyword in ["evaluate", "assess"]):
                if not self.interview_data["assessment_context"]:
                    self.interview_data["assessment_context"] = data
                else:
                    self.interview_data["assessment_goals"].append(data)
            elif any(keyword in data_lower for keyword in ["goal", "objective"]):
                self.interview_data["assessment_goals"].append(data)
            elif any(keyword in data_lower for keyword in ["expect", "observe"]):
                self.interview_data["expected_empathy_forms"].append(data)
            elif any(keyword in data_lower for keyword in ["challenge", "difficult", "problem", "issue"]):
                self.interview_data["assessment_challenges"].append(data)
            elif any(keyword in data_lower for keyword in ["requirement", "capability", "measurement", "scale"]):
                self.interview_data["measurement_requirements"].append(data)
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
                description="ALWAYS use this tool after each user response to save the assessment-related information they provided. This is crucial for generating the interview summary. Use this tool to save any information about assessment context, robot platform, INTERACTION MODALITIES (speech, touch, visual cues like lights/displays - VERY IMPORTANT), collaboration patterns, environmental settings, assessment goals, expected empathy forms, challenges, or measurement requirements.",
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
        opening_message = self.prompt_manager.get_agent_group_prompt("interview_agent_group", "opening_message")
        
        # Record opening message in conversation history
        from datetime import datetime
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": "agent",
            "content": opening_message
        })
        
        return opening_message
    
    def process_response(self, user_input: str) -> str:
        """
        Process user response and generate next question or summary.
        
        Args:
            user_input: The user's response to the current question
            
        Returns:
            Agent's response/question
        """
        try:
            # Record user input in conversation history
            from datetime import datetime
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "type": "user",
                "content": user_input
            })
            
            response = self.agent_executor.invoke({"input": user_input})
            agent_response = response["output"]
            
            # Record agent response in conversation history
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "type": "agent",
                "content": agent_response
            })
            
            return agent_response
        except Exception as e:
            error_msg = self.prompt_manager.format_agent_group_prompt("interview_agent_group", "error_message", error=str(e))
            
            # Record error in conversation history
            from datetime import datetime
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "type": "error",
                "content": str(e)
            })
            
            return error_msg
    
    def _extract_section_content(self, text: str, section_label: str) -> str:
        """Extract content from a structured section in the text."""
        lines = text.split("\n")
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if section_label.lower() in line_lower:
                # Check if content is on the same line after colon
                if ":" in line:
                    content = line.split(":", 1)[-1].strip()
                    if content:
                        # If there's more content on next line, include it
                        if i + 1 < len(lines) and lines[i + 1].strip() and not lines[i + 1].strip().lower().endswith(":"):
                            content += " " + lines[i + 1].strip()
                        return content
                # Or content is on the next line(s)
                if i + 1 < len(lines):
                    content_parts = []
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j].strip()
                        if not next_line:
                            j += 1
                            continue
                        # Stop if we hit another section label
                        if ":" in next_line and any(keyword in next_line.lower() for keyword in 
                            ["assessment context:", "robot platform:", "interaction modalit", "collaboration pattern:", 
                             "environmental setting:", "assessment goals:", "expected empathy", "measurement requirement"]):
                            break
                        content_parts.append(next_line)
                        j += 1
                        # Stop after collecting a reasonable amount
                        if len(content_parts) >= 3:
                            break
                    if content_parts:
                        return " ".join(content_parts)
        return ""
    
    def get_interview_summary(self) -> Dict:
        """Get a summary of the collected interview data."""
        summary = self.interview_data.copy()
        
        # Post-process to extract missing information from comprehensive fields
        # Sometimes information ends up in environmental_setting that should be in other fields
        env_setting = summary.get("environmental_setting", "")
        if env_setting and isinstance(env_setting, str):
            env_lower = env_setting.lower()
            
            # Extract robot platform if missing
            if not summary.get("robot_platform") or summary.get("robot_platform") is None:
                platform_content = self._extract_section_content(env_setting, "robot platform:")
                if platform_content:
                    summary["robot_platform"] = platform_content
                # Fallback: find sentence mentioning humanoid robot
                elif "humanoid" in env_lower:
                    sentences = env_setting.split(". ")
                    for sentence in sentences:
                        if "humanoid" in sentence.lower() and ("robot" in sentence.lower() or "expressive facial" in sentence.lower()):
                            if "expressive facial" in sentence.lower() or "voice capabilities" in sentence.lower():
                                summary["robot_platform"] = sentence.strip()
                                break
                    # Final fallback: create from context
                    if not summary.get("robot_platform"):
                        if "expressive facial features" in env_lower and "voice capabilities" in env_lower:
                            summary["robot_platform"] = "Humanoid robot with expressive facial features and voice capabilities"
                        elif "humanoid" in env_lower:
                            summary["robot_platform"] = "Humanoid robot"
            
            # Extract collaboration pattern if missing
            if not summary.get("collaboration_pattern") or summary.get("collaboration_pattern") is None:
                pattern_content = self._extract_section_content(env_setting, "collaboration pattern:")
                if pattern_content:
                    summary["collaboration_pattern"] = pattern_content
                # Fallback: find sentence mentioning interaction pattern
                elif "interacts with" in env_lower or "one-on-one" in env_lower or "adaptive" in env_lower:
                    sentences = env_setting.split(". ")
                    for sentence in sentences:
                        if ("interacts with" in sentence.lower() or "one-on-one" in sentence.lower() or 
                            ("adaptive" in sentence.lower() and ("response" in sentence.lower() or "patient" in sentence.lower()))):
                            if "interaction" in sentence.lower() or "adaptive" in sentence.lower():
                                summary["collaboration_pattern"] = sentence.strip()
                                break
            
            # Enhance interaction modalities extraction
            interaction_modalities = summary.get("interaction_modalities", "")
            modality_content = self._extract_section_content(env_setting, "interaction modalit")
            if modality_content:
                # Use the more comprehensive version
                if not interaction_modalities or len(modality_content) > len(interaction_modalities):
                    summary["interaction_modalities"] = modality_content
            
            # Ensure interaction modalities includes facial expressions if mentioned in platform
            interaction_modalities = summary.get("interaction_modalities", "")
            if interaction_modalities and isinstance(interaction_modalities, str):
                modalities_lower = interaction_modalities.lower()
                # Always ensure facial expressions are mentioned if robot has expressive facial features
                if "facial" not in modalities_lower and "expression" not in modalities_lower:
                    robot_platform = summary.get("robot_platform", "")
                    if robot_platform and ("expressive facial" in str(robot_platform).lower() or "facial features" in str(robot_platform).lower()):
                        summary["interaction_modalities"] = interaction_modalities + ", and facial expressions" if interaction_modalities else "Facial expressions"
                    elif "expressive facial" in env_lower or "facial features" in env_lower:
                        summary["interaction_modalities"] = interaction_modalities + ", and facial expressions" if interaction_modalities else "Facial expressions"
            
            # Extract expected empathy forms if missing
            if not summary.get("expected_empathy_forms") or len(summary.get("expected_empathy_forms", [])) == 0:
                empathy_forms_content = self._extract_section_content(env_setting, "expected empathy")
                if empathy_forms_content:
                    # Split into sentences and add as list items
                    sentences = [s.strip() for s in empathy_forms_content.split(". ") if s.strip() and len(s.strip()) > 20]
                    if sentences:
                        summary["expected_empathy_forms"] = sentences
            
            # Extract measurement requirements if missing
            if not summary.get("measurement_requirements") or len(summary.get("measurement_requirements", [])) == 0:
                measurement_content = self._extract_section_content(env_setting, "measurement requirement")
                if measurement_content:
                    # Split into sentences and add as list items if multiple
                    sentences = [s.strip() for s in measurement_content.split(". ") if s.strip() and len(s.strip()) > 20]
                    if len(sentences) > 1:
                        summary["measurement_requirements"] = sentences
                    elif measurement_content:
                        summary["measurement_requirements"] = [measurement_content]
            
            # Clean up environmental_setting to only contain actual environmental information
            # Extract just the Environmental Setting section
            env_only_content = self._extract_section_content(env_setting, "environmental setting:")
            if env_only_content:
                summary["environmental_setting"] = env_only_content
            # If no dedicated section, try to extract from context
            elif "hospital" in env_lower or "ward" in env_lower or "setting" in env_lower:
                # Keep original if we can't extract a cleaner version
                pass
            
            # Clean up assessment_goals to remove redundant information
            # Remove goals that are just duplicating other fields
            if summary.get("assessment_goals"):
                cleaned_goals = []
                robot_platform = str(summary.get("robot_platform", "")).lower()
                interaction_mods = str(summary.get("interaction_modalities", "")).lower()
                
                for goal in summary["assessment_goals"]:
                    goal_lower = str(goal).lower()
                    # Skip if it's just describing the robot platform
                    if robot_platform and robot_platform in goal_lower and len(goal_lower) < len(robot_platform) * 1.5:
                        continue
                    # Skip if it's just describing interaction modalities without adding goals
                    if interaction_mods and "interaction modalit" in goal_lower and "goal" not in goal_lower and "assess" not in goal_lower:
                        continue
                    # Skip if it's duplicating assessment_context
                    context = str(summary.get("assessment_context", "")).lower()
                    if context and goal_lower in context:
                        continue
                    cleaned_goals.append(goal)
                
                # Only update if we removed some redundancy
                if len(cleaned_goals) < len(summary["assessment_goals"]):
                    summary["assessment_goals"] = cleaned_goals
        
        return summary
    
    def get_conversation_history(self) -> list:
        """Get the full conversation history."""
        return self.conversation_history.copy()
    
    def is_interview_complete(self) -> bool:
        """Check if sufficient empathy assessment information has been gathered."""
        required_fields = ["assessment_context", "robot_platform", "environmental_setting"]
        important_fields = ["interaction_modalities", "collaboration_pattern"]  # Interaction modalities is important
        assessment_fields = ["assessment_goals", "expected_empathy_forms", "assessment_challenges", "measurement_requirements"]
        
        # Check if we have basic context AND at least some assessment-related data
        has_context = all(self.interview_data[field] for field in required_fields)
        has_important_info = any(self.interview_data[field] for field in important_fields)
        has_assessment_data = any(self.interview_data[field] for field in assessment_fields)
        
        return has_context and (has_important_info or has_assessment_data)
    
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
                    If a relative path is provided, will search from project root.
        
    Returns:
        Configuration dictionary
    """
    if config_path is None:
        # Auto-detect config.json location
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        config_path = os.path.join(project_root, "config.json")
    elif not os.path.isabs(config_path) and not os.path.exists(config_path):
        # If relative path doesn't exist in current directory, try project root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        project_config_path = os.path.join(project_root, config_path)
        if os.path.exists(project_config_path):
            config_path = project_config_path
    
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
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
