"""
Multi-Agent LLM Workflow for Human-Robot Collaboration Analysis
Main application entry point.
"""

import os
import sys
from datetime import datetime
from typing import Dict

# Add the agents directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from interview_agent_group import InterviewAgentGroup, load_config
from research_agent_group import ResearchAgentGroup
from run_manager import DataSaver, RunManager


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
        
        # Initialize run manager and data saver
        self.data_dir = os.path.join(os.path.dirname(__file__), "data")
        self.run_manager = RunManager(self.data_dir)
        self.data_saver = DataSaver(self.run_manager)
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all available agent groups."""
        # Initialize the interview agent group
        self.agents['interview'] = InterviewAgentGroup(
            api_key=self.config["openai_api_key"],
            run_manager=self.run_manager
        )
        
        # Initialize the research agent group
        self.agents['research'] = ResearchAgentGroup(
            api_key=self.config["openai_api_key"],
            run_manager=self.run_manager
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
    
    def run_complete_workflow(self):
        """Run the complete workflow from interview to research."""
        # Create new run
        run_id = self.run_manager.create_new_run()
        print("=" * 60)
        print(f"Complete Multi-Agent Workflow - Run ID: {run_id}")
        print("Phase 1: Interview → Phase 2: Research")
        print("=" * 60)
        
        # Update phase status
        self.run_manager.update_phase_status("interview", "started")
        
        # Phase 1: Interview
        print("\n" + "=" * 40)
        print("PHASE 1: INTERVIEW")
        print("=" * 40)
        
        interview_agent_group = self.agents['interview']
        
        # Start the interview
        print("Agent Group:", interview_agent_group.start_interview())
        
        # Interactive interview loop
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
                    print("\nInterview complete! Moving to research phase...")
                    break
                    
            except EOFError:
                print("\n\nInput stream ended. Ending interview session.")
                break
        
        # Get interview summary
        interview_summary = interview_agent_group.get_interview_summary()
        
        # Update interview phase status
        self.run_manager.update_phase_status("interview", "completed")
        self.run_manager.update_phase_status("research", "started")
        
        # Save interview results
        self._save_interview_results(interview_summary)
        
        # Phase 2: Research
        print("\n" + "=" * 40)
        print("PHASE 2: RESEARCH")
        print("=" * 40)
        
        research_agent_group = self.agents['research']
        
        # Start research based on interview summary
        print("Research Agent:", research_agent_group.start_research(interview_summary))
        
        # Automated research tasks
        research_tasks = [
            f"Search for academic papers on empathy scale construction in {interview_summary.get('assessment_context', 'human-robot collaboration')} scenarios",
            f"Analyze methodologies used in robot empathy evaluation studies for {interview_summary.get('robot_platform', 'robot platforms')}",
            f"Extract insights about context-specific empathy measurement approaches for {interview_summary.get('environmental_setting', 'collaborative environments')}",
            "Generate comprehensive recommendations for empathy scale design based on research findings"
        ]
        
        for i, task in enumerate(research_tasks, 1):
            print(f"\nResearch Task {i}: {task}")
            response = research_agent_group.process_research_task(task)
            print(f"Research Agent: {response}")
            
            # Check if research is complete
            if research_agent_group.is_research_complete():
                print("\nResearch phase complete!")
                break
        
        # Get research summary
        research_summary = research_agent_group.get_research_summary()
        
        # Update research phase status
        self.run_manager.update_phase_status("research", "completed")
        self.run_manager.update_phase_status("workflow", "started")
        
        # Finalize research and save all data
        finalization_result = research_agent_group.finalize_research()
        print(f"\nResearch Finalization: {finalization_result}")
        
        # Save research results
        self._save_research_results(research_summary)
        
        # Save workflow summary
        workflow_summary = {
            "run_id": run_id,
            "interview_summary": interview_summary,
            "research_summary": research_summary,
            "completed_at": datetime.now().isoformat(),
            "status": "completed"
        }
        
        self.data_saver.save_workflow_summary(workflow_summary)
        self.run_manager.update_phase_status("workflow", "completed")
        
        # Display final summary
        self._display_complete_summary(interview_summary, research_summary)
        
        print(f"\n" + "=" * 60)
        print(f"Workflow completed successfully!")
        print(f"Run ID: {run_id}")
        print(f"Results saved in: {self.run_manager.get_run_path()}")
        print("=" * 60)
    
    def _save_interview_results(self, interview_summary: Dict):
        """Save interview results to intermediate data folder."""
        try:
            import json
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"interview_summary_{timestamp}.json"
            filepath = os.path.join("data", "intermediate_results", "interview_agent_group", filename)
            
            result_data = {
                "timestamp": timestamp,
                "agent_group": "interview_agent_group",
                "summary": interview_summary
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)
            
            print(f"\nInterview results saved to: {filename}")
            
        except Exception as e:
            print(f"Failed to save interview results: {str(e)}")
    
    def _save_research_results(self, research_summary: Dict):
        """Save research results to intermediate data folder."""
        try:
            import json
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"research_summary_{timestamp}.json"
            filepath = os.path.join("data", "intermediate_results", "research_agent_group", filename)
            
            result_data = {
                "timestamp": timestamp,
                "agent_group": "research_agent_group",
                "summary": research_summary
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)
            
            print(f"\nResearch results saved to: {filename}")
            
        except Exception as e:
            print(f"Failed to save research results: {str(e)}")
    
    def _display_complete_summary(self, interview_summary: Dict, research_summary: Dict):
        """Display complete workflow summary."""
        print("\n" + "=" * 60)
        print("COMPLETE WORKFLOW SUMMARY")
        print("=" * 60)
        
        print("\n" + "-" * 30)
        print("INTERVIEW FINDINGS")
        print("-" * 30)
        
        for key, value in interview_summary.items():
            if value:
                formatted_key = key.replace('_', ' ').title()
                print(f"\n{formatted_key}:")
                if isinstance(value, list):
                    for item in value:
                        print(f"  • {item}")
                else:
                    print(f"  {value}")
        
        print("\n" + "-" * 30)
        print("RESEARCH FINDINGS")
        print("-" * 30)
        
        for key, value in research_summary.items():
            if value:
                formatted_key = key.replace('_', ' ').title()
                print(f"\n{formatted_key}:")
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            print(f"  • {item.get('query', item.get('result', item.get('analysis', item.get('insight', item.get('recommendation', str(item))))))}")
                        else:
                            print(f"  • {item}")
                elif isinstance(value, dict):
                    print(f"  {value.get('summary', str(value))}")
                else:
                    print(f"  {value}")
        
        print("\n" + "=" * 60)
        print("Workflow Complete! Check data/ folder for detailed results.")
        print("=" * 60)


def main():
    """Main entry point for the application."""
    try:
        # Initialize the workflow
        workflow = MultiAgentWorkflow()
        
        print("Multi-Agent LLM Workflow for Human-Robot Collaboration")
        print("Choose workflow mode:")
        print("1. Interview only")
        print("2. Complete workflow (Interview → Research)")
        print("3. Research only (requires existing interview data)")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            # Run interview session only
            workflow.run_interview_session()
        elif choice == "2":
            # Run complete workflow
            workflow.run_complete_workflow()
        elif choice == "3":
            # Run research only (would need to load existing interview data)
            print("Research-only mode not yet implemented. Please run complete workflow.")
        else:
            print("Invalid choice. Running complete workflow by default.")
            workflow.run_complete_workflow()
        
    except FileNotFoundError as e:
        print(f"Configuration Error: {e}")
        print("Please ensure config.json exists and contains your OpenAI API key.")
    except Exception as e:
        print(f"Unexpected Error: {e}")
        print("Please check your configuration and try again.")


if __name__ == "__main__":
    main()
