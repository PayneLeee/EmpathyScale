#!/usr/bin/env python3
"""
Quick Test Script for Interview Agent Group
A simplified version for quick functionality verification
"""

import os
import sys

# Add the agents directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents'))

from interview_agent_group import InterviewAgentGroup, load_config


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
        "We want to evaluate a healthcare robot assisting nurses in patient care",
        "The robot is a humanoid platform with facial expressions and voice",
        "The collaboration is supervised with the robot following nurse instructions",
        "The environment is a hospital ward with multiple patients",
        "Our goal is to assess the robot's emotional support capabilities",
        "We expect to observe verbal empathy and comforting gestures",
        "The main challenge is measuring subtle emotional responses",
        "We need a scale that captures both verbal and non-verbal empathy"
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
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    quick_test()
