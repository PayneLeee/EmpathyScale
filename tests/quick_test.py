#!/usr/bin/env python3
"""
Quick Test Script for Interview Agent Group
A simplified version for quick functionality verification
"""

import os
import sys

# Add the agents and utils directories to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from interview_agent_group import InterviewAgentGroup, load_config
from data_manager import DataManager


def quick_test():
    """Quick test of interview functionality."""
    print("=" * 60)
    print("QUICK INTERVIEW AGENT TEST")
    print("=" * 60)
    
    # Load configuration and create agent
    config = load_config()
    agent_group = InterviewAgentGroup(api_key=config["openai_api_key"])
    
    # Start interview
    print("\n1. Opening Message:")
    print(agent_group.start_interview())
    
    # Simulate key responses
    test_responses = [
        "We want to evaluate a collaborative robot assisting human workers in industrial assembly tasks",
        "The robot is a dual-arm manipulator with force feedback sensors and visual perception",
        "The collaboration is peer-to-peer with shared workspace and real-time task coordination",
        "The environment is a manufacturing floor with precision assembly stations and safety equipment",
        "Our goal is to assess the robot's ability to provide emotional and cognitive support during complex tasks",
        "We expect to observe adaptive responses, stress recognition, and supportive communication",
        "The main challenge is measuring emotional trust and collaboration quality in high-stakes assembly",
        "We need a scale that captures both technical coordination and emotional rapport in collaborative work"
    ]
    
    print("\n2. Simulating Conversation:")
    for i, response in enumerate(test_responses, 1):
        print(f"\nTurn {i}:")
        print(f"User: {response}")
        
        agent_response = agent_group.process_response(response)
        print(f"Agent: {agent_response[:100]}...")  # Truncate for readability
    
    # Display summary
    print("\n3. Interview Summary:")
    print("-" * 40)
    
    summary = agent_group.get_interview_summary()
    for key, value in summary.items():
        if value:
            formatted_key = key.replace('_', ' ').title()
            if isinstance(value, list):
                print(f"{formatted_key}: {len(value)} items")
                for item in value:
                    print(f"  - {item}")
            else:
                print(f"{formatted_key}: {value}")
    
    # Completion status
    print(f"\n4. Completion Status: {agent_group.is_interview_complete()}")
    
    # Test data storage
    print("\n5. Testing Data Storage:")
    print("-" * 40)
    
    data_manager = DataManager()
    run_id = data_manager.new_run()
    print(f"[OK] Created run: {run_id}")
    
    # Get summary and conversation
    summary = agent_group.get_interview_summary()
    conversation = agent_group.get_conversation_history()
    
    # Save data
    data_manager.save_agent_group_data(
        run_id,
        "interview_agent_group",
        summary,
        conversation
    )
    print("[OK] Saved agent group data")
    
    # Complete run
    data_manager.complete_run(run_id, ["interview_agent_group"])
    print("[OK] Marked run as complete")
    
    # Verify data can be loaded
    loaded_data = data_manager.load_agent_group_data(run_id, "interview_agent_group")
    if loaded_data:
        print("[OK] Data can be loaded back")
        print(f"    Summary fields: {len(loaded_data.get('summary', {}))}")
        print(f"    Conversation turns: {len(loaded_data.get('conversation', []))}")
    
    # Verify latest run tracking
    latest_run = data_manager.get_latest_run_id()
    print(f"[OK] Latest run ID: {latest_run}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    quick_test()
