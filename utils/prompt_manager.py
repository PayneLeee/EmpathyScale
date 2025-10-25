"""
Prompt management utilities for the multi-agent workflow.
Handles loading and managing prompts from configuration files organized by agent.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict


class PromptManager:
    """
    Manages prompts for different agents in the multi-agent workflow.
    Loads prompts from JSON configuration files organized by agent in a prompts directory.
    """
    
    def __init__(self, prompts_dir: str = None):
        """
        Initialize the prompt manager.
        
        Args:
            prompts_dir: Path to the prompts directory containing agent-specific JSON files.
                        If None, will auto-detect based on current working directory.
        """
        if prompts_dir is None:
            # Auto-detect prompts directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            prompts_dir = os.path.join(project_root, "prompts")
        
        self.prompts_dir = prompts_dir
        self.prompts = self._load_all_prompts()
    
    def _load_all_prompts(self) -> Dict[str, Any]:
        """
        Load all prompts from the prompts directory.
        
        Returns:
            Dictionary containing all prompts organized by agent
            
        Raises:
            FileNotFoundError: If prompts directory doesn't exist
            ValueError: If any prompt file contains invalid JSON
        """
        prompts = {}
        
        if not os.path.exists(self.prompts_dir):
            raise FileNotFoundError(f"Prompts directory {self.prompts_dir} not found.")
        
        # Load all JSON files in the prompts directory
        for filename in os.listdir(self.prompts_dir):
            if filename.endswith('.json'):
                agent_name = filename[:-5]  # Remove .json extension
                file_path = os.path.join(self.prompts_dir, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        prompts[agent_name] = json.load(file)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON in prompt file {file_path}: {e}")
                except Exception as e:
                    raise ValueError(f"Error loading prompt file {file_path}: {e}")
        
        return prompts
    
    def _load_agent_prompts(self, agent_name: str) -> Dict[str, str]:
        """
        Load prompts for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Dictionary containing prompts for the agent
            
        Raises:
            FileNotFoundError: If agent prompt file doesn't exist
            ValueError: If prompt file contains invalid JSON
        """
        file_path = os.path.join(self.prompts_dir, f"{agent_name}.json")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Prompt file for agent '{agent_name}' not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in prompt file {file_path}: {e}")
    
    def get_agent_group_prompt(self, agent_group_name: str, prompt_key: str) -> str:
        """
        Get a specific prompt for an agent group.
        
        Args:
            agent_group_name: Name of the agent group (e.g., 'interview_agent_group')
            prompt_key: Key of the prompt (e.g., 'system_prompt')
            
        Returns:
            The requested prompt string
            
        Raises:
            KeyError: If agent group or prompt key doesn't exist
        """
        try:
            return self.prompts[agent_group_name][prompt_key]
        except KeyError as e:
            raise KeyError(f"Prompt not found: {agent_group_name}.{prompt_key}")
    
    def get_agent_group_prompts(self, agent_group_name: str) -> Dict[str, str]:
        """
        Get all prompts for a specific agent group.
        
        Args:
            agent_group_name: Name of the agent group
            
        Returns:
            Dictionary of all prompts for the agent group
            
        Raises:
            KeyError: If agent group doesn't exist
        """
        try:
            return self.prompts[agent_group_name]
        except KeyError:
            raise KeyError(f"Agent group '{agent_group_name}' not found in prompts configuration")
    
    def reload_agent_group_prompts(self, agent_group_name: str):
        """
        Reload prompts for a specific agent group.
        
        Args:
            agent_group_name: Name of the agent group to reload
            
        Raises:
            FileNotFoundError: If agent group prompt file doesn't exist
            ValueError: If prompt file contains invalid JSON
        """
        self.prompts[agent_group_name] = self._load_agent_prompts(agent_group_name)
    
    def format_agent_group_prompt(self, agent_group_name: str, prompt_key: str, **kwargs) -> str:
        """
        Get and format an agent group prompt with provided variables.
        
        Args:
            agent_group_name: Name of the agent group
            prompt_key: Key of the prompt
            **kwargs: Variables to format into the prompt
            
        Returns:
            Formatted prompt string
        """
        prompt_template = self.get_agent_group_prompt(agent_group_name, prompt_key)
        try:
            return prompt_template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required variable for prompt formatting: {e}")
    
    def add_agent_prompts(self, agent_name: str, prompts: Dict[str, str]):
        """
        Add or update prompts for a specific agent.
        
        Args:
            agent_name: Name of the agent
            prompts: Dictionary of prompts to add/update
        """
        if agent_name not in self.prompts:
            self.prompts[agent_name] = {}
        self.prompts[agent_name].update(prompts)
    
    def save_agent_prompts(self, agent_name: str):
        """
        Save prompts for a specific agent to its JSON file.
        
        Args:
            agent_name: Name of the agent
            
        Raises:
            KeyError: If agent doesn't exist
            IOError: If unable to write to file
        """
        if agent_name not in self.prompts:
            raise KeyError(f"Agent '{agent_name}' not found in prompts configuration")
        
        file_path = os.path.join(self.prompts_dir, f"{agent_name}.json")
        
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(self.prompts[agent_name], file, indent=2, ensure_ascii=False)
        except Exception as e:
            raise IOError(f"Unable to save prompts for agent '{agent_name}': {e}")


# Global prompt manager instance
prompt_manager = PromptManager()


def get_prompt(agent_name: str, prompt_key: str, **kwargs) -> str:
    """
    Convenience function to get a formatted prompt.
    
    Args:
        agent_name: Name of the agent
        prompt_key: Key of the prompt
        **kwargs: Variables to format into the prompt
        
    Returns:
        Formatted prompt string
    """
    return prompt_manager.format_prompt(agent_name, prompt_key, **kwargs)


def reload_prompts():
    """Convenience function to reload all prompts."""
    prompt_manager.reload_prompts()


def get_agent_group_prompt(agent_group_name: str, prompt_key: str, **kwargs) -> str:
    """
    Convenience function to get a formatted agent group prompt.
    
    Args:
        agent_group_name: Name of the agent group
        prompt_key: Key of the prompt
        **kwargs: Variables to format into the prompt
        
    Returns:
        Formatted prompt string
    """
    return prompt_manager.format_agent_group_prompt(agent_group_name, prompt_key, **kwargs)


def reload_agent_group_prompts(agent_group_name: str):
    """Convenience function to reload prompts for a specific agent group."""
    prompt_manager.reload_agent_group_prompts(agent_group_name)


if __name__ == "__main__":
    # Example usage and testing
    try:
        pm = PromptManager()
        
        print("Available agents:")
        for agent in pm.list_available_agents():
            print(f"  - {agent}")
            prompts = pm.list_agent_prompts(agent)
            print(f"    Prompts: {', '.join(prompts)}")
        
        print("\nExample - Interview Agent System Prompt:")
        system_prompt = pm.get_agent_prompt("interview_agent", "system_prompt")
        print(system_prompt[:200] + "...")
        
        print("\nExample - Error Message with Formatting:")
        error_msg = pm.format_prompt("interview_agent", "error_message", error="Test error")
        print(error_msg)
        
    except Exception as e:
        print(f"Error: {e}")
