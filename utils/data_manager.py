"""
Data Manager for EmpathyScale Project
Handles timestamp-isolated data storage with agent group separation
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class DataManager:
    """
    Simple data manager with timestamp isolation and agent group separation.
    Each run gets a unique folder: data/runs/YYYY-MM-DD_HHMMSS/
    Each agent group stores data in its own subfolder.
    """
    
    def __init__(self, base_dir: str = None):
        """
        Initialize the data manager.
        
        Args:
            base_dir: Base directory for data storage. If None, uses project root/data.
        """
        if base_dir is None:
            # Auto-detect project root (assumes this file is in utils/)
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent
            base_dir = str(project_root / "data")
        
        # Ensure absolute path
        self.base_dir = Path(base_dir).resolve()
        self.runs_dir = self.base_dir / "runs"
        self.latest_run_file = self.base_dir / "latest_run.txt"
        
        # Create directories if they don't exist
        self.runs_dir.mkdir(parents=True, exist_ok=True)
    
    def new_run(self) -> str:
        """
        Create a new timestamped run directory.
        
        Returns:
            run_id: Timestamp string in format YYYY-MM-DD_HHMMSS
        """
        run_id = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        run_dir = self.runs_dir / run_id
        
        # Create run directory
        run_dir.mkdir(parents=True, exist_ok=True)
        
        # Save basic metadata
        metadata = {
            "run_id": run_id,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "status": "running",
            "agent_groups": []
        }
        self.save_metadata(run_id, metadata)
        
        # Track as latest run
        self._update_latest_run(run_id)
        
        return run_id
    
    def save_agent_group_data(self, run_id: str, agent_group_name: str, 
                             summary: Dict[str, Any], conversation: list) -> None:
        """
        Save data for an agent group.
        
        Args:
            run_id: The run identifier
            agent_group_name: Name of the agent group (e.g., "interview_agent_group")
            summary: Summary data from the agent
            conversation: Full conversation history
        """
        try:
            run_dir = self.runs_dir / run_id
            agent_dir = run_dir / agent_group_name
            agent_dir.mkdir(parents=True, exist_ok=True)
            
            # Save summary
            summary_path = agent_dir / "summary.json"
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            # Save conversation
            conversation_path = agent_dir / "conversation.json"
            with open(conversation_path, 'w', encoding='utf-8') as f:
                json.dump(conversation, f, indent=2, ensure_ascii=False)
        except Exception as e:
            import traceback
            print(f"[ERROR] Failed to save {agent_group_name} data: {e}")
            traceback.print_exc()
            raise
    
    def save_metadata(self, run_id: str, metadata: Dict[str, Any]) -> None:
        """Save run metadata."""
        run_dir = self.runs_dir / run_id
        metadata_file = run_dir / "metadata.json"
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def load_metadata(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Load metadata for a run."""
        metadata_file = self.runs_dir / run_id / "metadata.json"
        
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def complete_run(self, run_id: str, agent_groups: list) -> None:
        """
        Mark a run as complete.
        
        Args:
            run_id: The run identifier
            agent_groups: List of agent group names that were used in this run
        """
        metadata = self.load_metadata(run_id)
        
        if metadata:
            metadata["end_time"] = datetime.now().isoformat()
            metadata["status"] = "completed"
            metadata["agent_groups"] = agent_groups
            self.save_metadata(run_id, metadata)
    
    def get_latest_run_id(self) -> Optional[str]:
        """Get the latest run ID from latest_run.txt."""
        if self.latest_run_file.exists():
            with open(self.latest_run_file, 'r') as f:
                return f.read().strip()
        return None
    
    def _update_latest_run(self, run_id: str) -> None:
        """Update the latest_run.txt file with current run_id."""
        with open(self.latest_run_file, 'w') as f:
            f.write(run_id)
    
    def get_run_path(self, run_id: str) -> Path:
        """Get the path for a specific run."""
        return self.runs_dir / run_id
    
    def load_agent_group_data(self, run_id: str, agent_group_name: str) -> Dict[str, Any]:
        """
        Load data for an agent group.
        
        Args:
            run_id: The run identifier
            agent_group_name: Name of the agent group
            
        Returns:
            Dict containing 'summary' and 'conversation'
        """
        agent_dir = self.runs_dir / run_id / agent_group_name
        
        data = {}
        
        # Load summary
        summary_file = agent_dir / "summary.json"
        if summary_file.exists():
            with open(summary_file, 'r', encoding='utf-8') as f:
                data['summary'] = json.load(f)
        
        # Load conversation
        conversation_file = agent_dir / "conversation.json"
        if conversation_file.exists():
            with open(conversation_file, 'r', encoding='utf-8') as f:
                data['conversation'] = json.load(f)
        
        return data

