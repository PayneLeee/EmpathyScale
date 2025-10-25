"""
Multi-Agent LLM Workflow for Human-Robot Collaboration Analysis
Main application entry point.
"""

import os
import sys
from typing import Dict

# Add the agents directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))

from interview_agent_group import InterviewAgentGroup, load_config


class MultiAgentWorkflow:
    """
    Main orchestrator for the multi-agent workflow.
    Currently manages a single interview agent, but designed to be extensible.
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the multi-agent workflow.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config = load_config(config_path)
        self.agents = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all available agent groups."""
        # Initialize the interview agent group
        self.agents['interview'] = InterviewAgentGroup(
            api_key=self.config["openai_api_key"]
        )
    
    def run_interview_session(self):
        """Run an interactive interview session."""
        print("=" * 60)
        print("Multi-Agent LLM Workflow for Human-Robot Collaboration")
        print("=" * 60)
        print("\nThis system will conduct an interview to understand your")
        print("human-robot collaboration situation.\n")
        
        interview_agent_group = self.agents['interview']
        
        # Start the interview
        print("Agent Group:", interview_agent_group.start_interview())
        
        # Interactive loop
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() in ["exit", "quit", "end", "stop"]:
                    break
                
                if not user_input:
                    print("Please provide a response or type 'exit' to end the interview.")
                    continue
                
                # Process the response
                response = interview_agent_group.process_response(user_input)
                print(f"\nAgent Group: {response}")
                
                # Check if interview is complete
                if interview_agent_group.is_interview_complete():
                    print("\nInterview appears to be complete!")
                    break
                    
            except EOFError:
                print("\n\nInput stream ended. Ending interview session.")
                break
        
        # Display summary
        self._display_interview_summary(interview_agent_group)
    
    def _display_interview_summary(self, interview_agent_group: InterviewAgentGroup):
        """Display the interview summary."""
        print("\n" + "=" * 60)
        print("INTERVIEW SUMMARY")
        print("=" * 60)
        
        summary = interview_agent_group.get_interview_summary()
        
        for key, value in summary.items():
            if value:
                formatted_key = key.replace('_', ' ').title()
                print(f"\n{formatted_key}:")
                if isinstance(value, list):
                    for item in value:
                        print(f"  • {item}")
                else:
                    print(f"  {value}")
        
        print("\n" + "=" * 60)
        print("Thank you for participating in the interview!")
        print("=" * 60)


def main():
    """Main entry point for the application."""
    try:
        # Initialize the workflow
        workflow = MultiAgentWorkflow()
        
        # Run the interview session
        workflow.run_interview_session()
        
    except FileNotFoundError as e:
        print(f"Configuration Error: {e}")
        print("Please ensure config.json exists and contains your OpenAI API key.")
    except Exception as e:
        print(f"Unexpected Error: {e}")
        print("Please check your configuration and try again.")


if __name__ == "__main__":
    main()
