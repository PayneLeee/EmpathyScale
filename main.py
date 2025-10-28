"""
Multi-Agent LLM Workflow for Human-Robot Collaboration Analysis
Main application entry point.
"""

import os
import sys
from typing import Dict
from datetime import datetime

# Add the agents and utils directories to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from interview_agent_group import InterviewAgentGroup, load_config
from literature_search_agent_group import LiteratureSearchAgentGroup
from data_manager import DataManager


class MultiAgentWorkflow:
    """
    Main orchestrator for the multi-agent workflow.
    Currently manages a single interview agent, but designed to be extensible.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the multi-agent workflow.
        
        Args:
            config_path: Path to the configuration file. If None, will auto-detect.
        """
        self.config = load_config(config_path)
        self.agents = {}
        self.data_manager = DataManager()
        self.run_id = None
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all available agent groups."""
        # Initialize the interview agent group
        self.agents['interview'] = InterviewAgentGroup(
            api_key=self.config["openai_api_key"]
        )
        
        # Initialize literature search agent group
        self.agents['literature'] = LiteratureSearchAgentGroup(
            api_key=self.config["openai_api_key"]
        )
    
    def run_interview_session(self):
        """Run an interactive interview session."""
        print("=" * 60)
        print("Multi-Agent LLM Workflow for Human-Robot Collaboration")
        print("=" * 60)
        print("\nThis system will conduct an interview to understand your")
        print("human-robot collaboration situation.\n")
        
        # Create new run for data storage
        self.run_id = self.data_manager.new_run()
        print(f"[Data] Started run: {self.run_id}\n")
        
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
        
        # Save data automatically
        self._save_interview_data(interview_agent_group)
        
        # Run literature search after interview
        self._run_literature_search(interview_agent_group)
    
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
                        print(f"  - {item}")
                else:
                    print(f"  {value}")
        
        print("\n" + "=" * 60)
        print("Thank you for participating in the interview!")
        print("=" * 60)
    
    def _save_literature_results(self, run_id: str, literature_results: Dict):
        """Save minimal essential literature search results."""
        import json
        from pathlib import Path
        
        run_dir = self.data_manager.get_run_path(run_id)
        lit_dir = run_dir / "literature_search_agent_group"
        lit_dir.mkdir(parents=True, exist_ok=True)
        
        # Save only essential information
        essential_summary = {
            "search_queries": literature_results.get("search_queries", []),
            "statistics": {
                "total_papers_found": literature_results.get("total_papers_found", 0),
                "screened_papers": literature_results.get("screened_papers", 0),
                "pdfs_downloaded": literature_results.get("pdfs_downloaded", 0)
            },
            "downloaded_papers": [
                {
                    "title": paper.get("title", ""),
                    "category": paper.get("category", ""),
                    "year": paper.get("year", ""),
                    "local_pdf_path": paper.get("local_pdf_path", ""),
                    "downloaded_at": paper.get("downloaded_at", "")
                }
                for paper in literature_results.get("downloaded_papers", [])
                if paper.get("downloaded", False)
            ]
        }
        
        summary_path = lit_dir / "summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(essential_summary, f, indent=2, ensure_ascii=False)
    
    def _save_interview_data(self, interview_agent_group: InterviewAgentGroup):
        """Save interview data automatically."""
        if not self.run_id:
            print("[WARNING] No run_id set, cannot save interview data")
            return
        
        print("\n[Saving data...]")
        
        try:
            # Get summary and conversation
            summary = interview_agent_group.get_interview_summary()
            conversation = interview_agent_group.get_conversation_history()
            
            # Save to data directory
            self.data_manager.save_agent_group_data(
                self.run_id,
                "interview_agent_group",
                summary,
                conversation
            )
            
            # Mark run as complete
            self.data_manager.complete_run(self.run_id, ["interview_agent_group"])
            
            # Get path for user info
            run_path = self.data_manager.get_run_path(self.run_id)
            print(f"[Data] Saved to: {run_path}")
            print(f"[Data] Latest run: {self.data_manager.get_latest_run_id()}")
        except Exception as e:
            print(f"[ERROR] Failed to save interview data: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _run_literature_search(self, interview_agent_group: InterviewAgentGroup):
        """Run enhanced literature search using interview summary."""
        if not self.run_id:
            return
        
        literature_agent = self.agents.get('literature')
        if not literature_agent:
            print("\n[Literature] Agent not initialized, skipping literature search")
            return
        
        print("\n" + "=" * 60)
        print("STARTING ENHANCED LITERATURE SEARCH")
        print("=" * 60)
        
        # Get interview summary
        interview_summary = interview_agent_group.get_interview_summary()
        
        # Run enhanced literature search
        literature_results = literature_agent.search_and_download(
            self.run_id,
            interview_summary
        )
        
        # Save minimal essential results (queries, downloaded papers with paths, stats)
        self._save_literature_results(self.run_id, literature_results)
        
        # Update metadata to record literature search completion
        metadata = self.data_manager.load_metadata(self.run_id)
        if metadata:
            if "interview_agent_group" not in metadata["agent_groups"]:
                metadata["agent_groups"].append("interview_agent_group")
            if "literature_search_agent_group" not in metadata["agent_groups"]:
                metadata["agent_groups"].append("literature_search_agent_group")
            self.data_manager.save_metadata(self.run_id, metadata)
        
        print(f"\n[Literature] Enhanced search complete - {literature_results.get('pdfs_downloaded', 0)} PDFs downloaded")


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
