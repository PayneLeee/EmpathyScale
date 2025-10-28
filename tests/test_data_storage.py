#!/usr/bin/env python3
"""
Test Data Storage Functionality
Verifies that data storage system is working correctly
"""

import os
import sys
import json
from pathlib import Path

# Add utils directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from data_manager import DataManager


def test_data_storage():
    """Test data storage functionality."""
    print("=" * 70)
    print("DATA STORAGE SYSTEM TEST")
    print("=" * 70)
    
    # Initialize data manager
    data_manager = DataManager()
    print("[OK] DataManager initialized")
    
    # Create new run
    run_id = data_manager.new_run()
    print(f"[OK] Created new run: {run_id}")
    
    # Create sample data
    sample_summary = {
        "test_field_1": "Test value 1",
        "test_field_2": "Test value 2",
        "test_list": ["item1", "item2", "item3"]
    }
    
    sample_conversation = [
        {
            "timestamp": "2024-01-15T10:00:00",
            "type": "agent",
            "content": "Opening message"
        },
        {
            "timestamp": "2024-01-15T10:00:01",
            "type": "user",
            "content": "User response"
        }
    ]
    
    # Save agent group data
    data_manager.save_agent_group_data(
        run_id,
        "interview_agent_group",
        sample_summary,
        sample_conversation
    )
    print(f"[OK] Saved agent group data")
    
    # Verify files exist
    run_path = data_manager.get_run_path(run_id)
    
    checks = {
        "metadata.json": run_path / "metadata.json",
        "summary.json": run_path / "interview_agent_group" / "summary.json",
        "conversation.json": run_path / "interview_agent_group" / "conversation.json"
    }
    
    print("\nVerifying file existence:")
    for file_name, file_path in checks.items():
        if file_path.exists():
            print(f"  [OK] {file_name}")
        else:
            print(f"  [FAIL] {file_name} not found")
            return False
    
    # Load and verify data
    print("\nVerifying data integrity:")
    loaded_data = data_manager.load_agent_group_data(run_id, "interview_agent_group")
    
    if loaded_data:
        summary = loaded_data.get("summary")
        conversation = loaded_data.get("conversation")
        
        if summary == sample_summary:
            print("  [OK] Summary data matches")
        else:
            print("  [FAIL] Summary data mismatch")
            return False
        
        if len(conversation) == len(sample_conversation):
            print("  [OK] Conversation data matches")
        else:
            print(f"  [FAIL] Conversation data mismatch ({len(conversation)} vs {len(sample_conversation)})")
            return False
    else:
        print("  [FAIL] Could not load data")
        return False
    
    # Test metadata
    metadata = data_manager.load_metadata(run_id)
    if metadata and metadata["run_id"] == run_id:
        print(f"  [OK] Metadata correct: run_id = {metadata['run_id']}")
    else:
        print("  [FAIL] Metadata incorrect")
        return False
    
    # Complete run
    data_manager.complete_run(run_id, ["interview_agent_group"])
    updated_metadata = data_manager.load_metadata(run_id)
    
    if updated_metadata and updated_metadata["status"] == "completed":
        print(f"  [OK] Run marked as completed")
    else:
        print("  [FAIL] Run completion status incorrect")
        return False
    
    # Test latest run tracking
    latest_run = data_manager.get_latest_run_id()
    if latest_run == run_id:
        print(f"  [OK] Latest run tracking: {latest_run}")
    else:
        print(f"  [FAIL] Latest run tracking: expected {run_id}, got {latest_run}")
        return False
    
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED!")
    print("=" * 70)
    print(f"\nRun ID: {run_id}")
    print(f"Data saved to: {run_path}")
    print(f"\nStructure:")
    print(f"  {run_path}")
    print(f"  ├── metadata.json")
    print(f"  └── interview_agent_group/")
    print(f"      ├── summary.json")
    print(f"      └── conversation.json")
    
    return True


if __name__ == "__main__":
    success = test_data_storage()
    sys.exit(0 if success else 1)

