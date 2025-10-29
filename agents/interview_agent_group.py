"""
Interview Agent Group for Human-Robot Collaboration Analysis
This agent group specializes in conducting interviews and collecting information from users.
Contains multiple sub-agents for different aspects of information gathering.
"""

import json
import os
import re
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
    
    def _infer_interaction_modalities(self, summary: Dict) -> Optional[str]:
        """Infer interaction modalities from robot platform capabilities."""
        robot_platform = summary.get("robot_platform", "")
        if not robot_platform or robot_platform is None:
            return None
        
        platform_lower = str(robot_platform).lower()
        inferred_modalities = []
        
        # Voice/speech inference
        if any(keyword in platform_lower for keyword in ["voice", "speech", "audio", "speaker", "microphone", "sound", "verbal", "speech understanding", "audio perception"]):
            inferred_modalities.append("voice/speech")
        
        # Visual cues inference
        if any(keyword in platform_lower for keyword in ["display", "screen", "led", "light", "indicator", "visual", "facial", "expression", "eye", "camera"]):
            inferred_modalities.append("visual cues (lights/displays)")
        
        # Gesture/movement inference
        if any(keyword in platform_lower for keyword in ["arm", "manipulator", "movement", "gesture", "motion", "dual-arm", "limb"]):
            inferred_modalities.append("gestures/movements")
        
        # Haptic inference
        if any(keyword in platform_lower for keyword in ["haptic", "touch", "tactile", "force feedback", "tactile feedback"]):
            inferred_modalities.append("haptic feedback")
        
        if inferred_modalities:
            return ", ".join(inferred_modalities)
        return None
    
    def _get_missing_required_fields(self) -> List[str]:
        """Get list of missing required fields, prioritizing interaction_modalities."""
        summary = self.get_interview_summary()
        missing = []
        
        # Check interaction_modalities first (highest priority)
        if not summary.get("interaction_modalities") or summary.get("interaction_modalities") is None:
            # Try to infer from robot platform first
            inferred = self._infer_interaction_modalities(summary)
            if inferred:
                # We can infer it, but user confirmation is preferred
                # Still mark as missing to get explicit confirmation
                missing.append("interaction_modalities")
            else:
                missing.append("interaction_modalities")
        
        required_fields = ["assessment_context", "robot_platform", "environmental_setting"]
        important_fields = ["collaboration_pattern"]
        
        for field in required_fields:
            if not summary.get(field) or summary.get(field) is None:
                missing.append(field)
        
        for field in important_fields:
            if not summary.get(field) or summary.get(field) is None:
                missing.append(field)
        
        return missing
    
    def _generate_targeted_question(self, missing_field: str) -> str:
        """Generate a brief, targeted question for a missing field."""
        summary = self.get_interview_summary()
        
        questions = {
            "assessment_context": "What specific human-robot collaboration scenario are you evaluating? (Briefly describe the tasks humans and robots perform together.)",
            "robot_platform": "What type of robot is being used? (Briefly describe the robot's form, appearance, or capabilities.)",
            "environmental_setting": "Where does this collaboration take place? (Briefly describe the physical environment or setting.)",
            "interaction_modalities": self._generate_interaction_modalities_question(summary),
            "collaboration_pattern": "How do humans and robots interact? (Briefly: one-on-one, group, peer-to-peer, etc.)"
        }
        return questions.get(missing_field, f"Could you provide more information about {missing_field.replace('_', ' ')}?")
    
    def _generate_interaction_modalities_question(self, summary: Dict) -> str:
        """Generate a targeted question about interaction modalities."""
        robot_platform = summary.get("robot_platform", "")
        
        # Try to infer first
        inferred = self._infer_interaction_modalities(summary)
        
        if inferred and robot_platform:
            # We have inference, ask for confirmation/expansion
            return f"Based on the robot's capabilities, I infer it might use {inferred}. Can the robot communicate or interact with humans? If yes, through which modalities? (e.g., voice/speech, gestures/movements, indicator lights, screen display, haptic feedback, or none)"
        else:
            # No inference possible, ask directly
            return "Can the robot communicate or interact with humans? If yes, through which modalities? (e.g., voice/speech, gestures/movements, indicator lights, screen display, haptic feedback, or none)"
    
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
            
            # Check for missing required fields and append targeted question if needed
            missing_fields = self._get_missing_required_fields()
            if missing_fields and not self.is_interview_complete():
                # Prioritize interaction_modalities if it's missing
                first_missing = missing_fields[0]
                
                # Special handling for interaction_modalities - check if user explicitly said "no communication"
                if first_missing == "interaction_modalities":
                    user_input_lower = user_input.lower()
                    # Check if user explicitly stated no communication
                    if any(phrase in user_input_lower for phrase in ["no communication", "cannot communicate", "no interaction", "doesn't communicate", "has no", "no way to communicate"]):
                        # User said no communication, set to explicit value
                        self.interview_data["interaction_modalities"] = "No interactive communication"
                        # Don't ask again
                    else:
                        # Continue asking about interaction modalities
                        targeted_question = self._generate_targeted_question(first_missing)
                        if targeted_question not in agent_response.lower():
                            agent_response += f"\n\nAlso: {targeted_question}"
                else:
                    # For other fields, add targeted question
                    targeted_question = self._generate_targeted_question(first_missing)
                    if targeted_question not in agent_response.lower():
                        agent_response += f"\n\nAlso: {targeted_question}"
            
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
    
    def _extract_summary_from_conversation(self) -> Dict:
        """Use LLM to extract structured summary from conversation history."""
        if not self.conversation_history or len(self.conversation_history) < 2:
            # Not enough conversation yet, return current data
            return self.interview_data.copy()
        
        # Format conversation history for LLM
        conversation_text = ""
        for entry in self.conversation_history:
            if entry.get("type") == "user":
                conversation_text += f"User: {entry.get('content', '')}\n"
            elif entry.get("type") == "agent":
                conversation_text += f"Agent: {entry.get('content', '')}\n"
        
        # Get extraction prompt
        extraction_prompt_template = self.prompt_manager.get_agent_group_prompt(
            "interview_agent_group",
            "summary_extraction_prompt"
        )
        
        extraction_prompt = extraction_prompt_template.format(
            conversation_history=conversation_text
        )
        
        try:
            # Use LLM to extract summary
            response = self.llm.invoke(extraction_prompt)
            content = response.content.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                extracted_summary = json.loads(json_match.group())
                return extracted_summary
            else:
                # Fallback to keyword-based extraction
                return self.interview_data.copy()
        except Exception as e:
            # If LLM extraction fails, fallback to keyword-based
            print(f"[WARNING] LLM summary extraction failed: {e}. Using keyword-based extraction.")
            return self.interview_data.copy()
    
    def get_interview_summary(self) -> Dict:
        """Get a summary of the collected interview data, extracted from conversation history."""
        # First, try LLM-based extraction from conversation history
        llm_summary = self._extract_summary_from_conversation()
        
        # Merge with keyword-based data (as fallback/supplement)
        keyword_summary = self.interview_data.copy()
        
        # Use LLM summary as primary, fill gaps from keyword summary
        summary = {}
        for field in ["assessment_context", "robot_platform", "interaction_modalities", 
                     "collaboration_pattern", "environmental_setting"]:
            # Prefer LLM-extracted value if it exists and is not null
            if llm_summary.get(field) and llm_summary[field] not in [None, "null", ""]:
                summary[field] = llm_summary[field]
            elif keyword_summary.get(field) and keyword_summary[field] not in [None, ""]:
                summary[field] = keyword_summary[field]
            else:
                summary[field] = None
        
        # Special handling for interaction_modalities: infer from robot platform if still missing
        if (not summary.get("interaction_modalities") or summary.get("interaction_modalities") is None) and summary.get("robot_platform"):
            inferred = self._infer_interaction_modalities(summary)
            if inferred:
                summary["interaction_modalities"] = inferred
        
        # For list fields, merge both sources
        for field in ["assessment_goals", "expected_empathy_forms", "assessment_challenges", "measurement_requirements"]:
            llm_list = llm_summary.get(field, [])
            keyword_list = keyword_summary.get(field, [])
            if isinstance(llm_list, list) and llm_list:
                summary[field] = llm_list
            elif isinstance(keyword_list, list) and keyword_list:
                summary[field] = keyword_list
            else:
                summary[field] = []
        
        # Apply post-processing to fill any remaining gaps
        summary = self._post_process_summary(summary)
        
        return summary
    
    def _post_process_summary(self, summary: Dict) -> Dict:
        """Post-process summary to extract missing information from existing fields."""
        
        # Post-process to extract missing information from comprehensive fields
        # First, try to extract from environmental_setting if it has structured format
        env_setting = summary.get("environmental_setting", "")
        
        # Also check assessment_goals for items that should be in other fields
        assessment_goals = summary.get("assessment_goals", [])
        
        # Check assessment_context for information that might be mixed in
        assessment_context = summary.get("assessment_context", "")
        
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
        
        # Additional post-processing: Extract from assessment_goals if fields are still missing
        if assessment_goals and isinstance(assessment_goals, list):
            goals_to_remove = []
            
            # Extract robot_platform from assessment_goals if missing
            if not summary.get("robot_platform") or summary.get("robot_platform") is None:
                for goal in assessment_goals:
                    goal_str = str(goal).lower()
                    if ("dual-arm" in goal_str or "manipulator" in goal_str or "haptic" in goal_str or 
                        "force feedback" in goal_str or "vision sensor" in goal_str):
                        if "robot" in goal_str or "platform" in goal_str:
                            summary["robot_platform"] = goal
                            goals_to_remove.append(goal)
                            break
            
            # Extract collaboration_pattern from assessment_goals if missing
            if not summary.get("collaboration_pattern") or summary.get("collaboration_pattern") is None:
                for goal in assessment_goals:
                    goal_str = str(goal).lower()
                    if ("peer-to-peer" in goal_str or "collaboration" in goal_str or "coordination" in goal_str or
                        "shared workspace" in goal_str or "task handoff" in goal_str):
                        if "collaboration" in goal_str or "coordination" in goal_str:
                            summary["collaboration_pattern"] = goal
                            goals_to_remove.append(goal)
                            break
            
            # Extract environmental_setting from assessment_goals if missing
            if not summary.get("environmental_setting") or summary.get("environmental_setting") is None:
                for goal in assessment_goals:
                    goal_str = str(goal).lower()
                    if ("manufacturing floor" in goal_str or "assembly station" in goal_str or 
                        "environment" in goal_str or "factory" in goal_str or "quality control" in goal_str):
                        summary["environmental_setting"] = goal
                        goals_to_remove.append(goal)
                        break
            
            # Extract assessment_challenges from assessment_goals if missing
            if not summary.get("assessment_challenges") or len(summary.get("assessment_challenges", [])) == 0:
                for goal in assessment_goals:
                    goal_str = str(goal).lower()
                    if ("challenge" in goal_str or ("measuring" in goal_str and ("trust" in goal_str or "quality" in goal_str))):
                        if "challenge" in goal_str:
                            summary["assessment_challenges"] = [goal]
                            goals_to_remove.append(goal)
                            break
            
            # Extract measurement_requirements from assessment_goals if missing
            if not summary.get("measurement_requirements") or len(summary.get("measurement_requirements", [])) == 0:
                for goal in assessment_goals:
                    goal_str = str(goal).lower()
                    if ("scale" in goal_str or "measurement" in goal_str or "capture" in goal_str):
                        if "scale" in goal_str or "measurement" in goal_str:
                            summary["measurement_requirements"] = [goal]
                            goals_to_remove.append(goal)
                            break
            
            # Extract expected_empathy_forms from assessment_goals if missing
            if not summary.get("expected_empathy_forms") or len(summary.get("expected_empathy_forms", [])) == 0:
                for goal in assessment_goals:
                    goal_str = str(goal).lower()
                    if ("expect" in goal_str or "observe" in goal_str) and ("adaptive" in goal_str or "behavior" in goal_str or "trust" in goal_str):
                        if "expect" in goal_str or "observe" in goal_str:
                            summary["expected_empathy_forms"] = [goal]
                            goals_to_remove.append(goal)
                            break
            
            # Remove extracted items from assessment_goals
            if goals_to_remove:
                remaining_goals = [g for g in assessment_goals if g not in goals_to_remove]
                summary["assessment_goals"] = remaining_goals
        
        # Also check assessment_context for robot platform info if robot_platform is still null
        if not summary.get("robot_platform") or summary.get("robot_platform") is None:
            if assessment_context and isinstance(assessment_context, str):
                context_lower = assessment_context.lower()
                if ("dual-arm" in context_lower or "manipulator" in context_lower or "haptic" in context_lower or
                    "force feedback" in context_lower or "vision sensor" in context_lower):
                    # Extract robot platform description
                    if "robot" in context_lower:
                        # Try to extract the robot description sentence
                        sentences = assessment_context.split(". ")
                        for sentence in sentences:
                            if "dual-arm" in sentence.lower() or "manipulator" in sentence.lower():
                                summary["robot_platform"] = sentence.strip()
                                break
        
        # Clean up assessment_context if it contains robot platform info that should be separated
        if assessment_context and summary.get("robot_platform"):
            # Remove robot platform description from assessment_context if duplicated
            context_lower = str(assessment_context).lower()
            platform_lower = str(summary.get("robot_platform", "")).lower()
            if platform_lower in context_lower and len(platform_lower) > 20:
                # Remove the robot platform part from context
                summary["assessment_context"] = assessment_context.replace(
                    summary["robot_platform"], ""
                ).replace("Assessment Context:", "").strip()
                if not summary["assessment_context"]:
                    summary["assessment_context"] = "Human-robot collaboration scenario"
        
        # Clean up collaboration_pattern if it contains robot platform info
        if summary.get("collaboration_pattern") and summary.get("robot_platform"):
            pattern = str(summary.get("collaboration_pattern", ""))
            platform = str(summary.get("robot_platform", ""))
            if platform in pattern:
                # Remove robot platform part from collaboration pattern
                summary["collaboration_pattern"] = pattern.replace(platform, "").strip()
                if summary["collaboration_pattern"].startswith("."):
                    summary["collaboration_pattern"] = summary["collaboration_pattern"][1:].strip()
        
        # Final check: infer interaction_modalities from robot_platform if still missing after all processing
        if (not summary.get("interaction_modalities") or summary.get("interaction_modalities") is None) and summary.get("robot_platform"):
            inferred = self._infer_interaction_modalities(summary)
            if inferred:
                summary["interaction_modalities"] = inferred
        
        return summary
    
    def get_conversation_history(self) -> list:
        """Get the full conversation history."""
        return self.conversation_history.copy()
    
    def is_interview_complete(self) -> bool:
        """Check if sufficient empathy assessment information has been gathered."""
        summary = self.get_interview_summary()
        
        # Required fields for completion
        required_fields = ["assessment_context", "robot_platform", "environmental_setting"]
        important_fields = ["interaction_modalities", "collaboration_pattern"]
        
        # Check if all required fields are present
        has_all_required = all(summary.get(field) for field in required_fields)
        
        # For interaction_modalities, accept either explicit answer or inferred value
        interaction_modalities = summary.get("interaction_modalities")
        has_interaction_modalities = (
            interaction_modalities and 
            interaction_modalities not in [None, ""] and
            interaction_modalities != "null"
        )
        
        # Check other important field
        has_collaboration_pattern = summary.get("collaboration_pattern") and summary.get("collaboration_pattern") not in [None, ""]
        
        # Interview is complete if we have all required fields AND interaction_modalities (even if inferred)
        return has_all_required and has_interaction_modalities and has_collaboration_pattern
    
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
