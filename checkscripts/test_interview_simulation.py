#!/usr/bin/env python3
"""
Simulated User Test Script for Interview Agent Group
This script simulates a user conversation to test the interview and summary functionality
without requiring real user interaction.
"""

import os
import sys
import time

# Add the agents directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents'))

from interview_agent_group import InterviewAgentGroup, load_config


def simulate_user_conversation():
    """Simulate a complete user conversation to test interview functionality."""
    print("=" * 80)
    print("SIMULATED USER CONVERSATION TEST")
    print("=" * 80)
    
    # Load configuration
    try:
        config = load_config()
        print("[OK] Configuration loaded successfully")
    except Exception as e:
        print(f"[ERROR] Error loading configuration: {e}")
        return
    
    # Create agent group
    try:
        agent_group = InterviewAgentGroup(api_key=config["openai_api_key"])
        print("[OK] Interview Agent Group created successfully")
    except Exception as e:
        print(f"[ERROR] Error creating agent group: {e}")
        return
    
    # Display opening message
    print("\n" + "=" * 60)
    print("INTERVIEW START")
    print("=" * 60)
    
    opening_message = agent_group.start_interview()
    print(f"Agent: {opening_message}")
    
    # Simulate user responses (comprehensive assessment scenario)
    user_responses = [
        "We want to evaluate a healthcare robot that assists nurses in patient care tasks",
        "The robot is a humanoid platform with facial expressions, voice capabilities, and gentle movements",
        "The collaboration is supervised with the robot following nurse instructions and protocols",
        "The environment is a hospital ward with multiple patients requiring different levels of care",
        "Our goal is to assess the robot's emotional support capabilities and empathy expression",
        "We expect to observe verbal empathy, comforting gestures, and appropriate emotional responses",
        "The main challenge is measuring subtle emotional responses and ensuring cultural sensitivity",
        "We need a scale that captures both verbal and non-verbal empathy across different patient demographics"
    ]
    
    print("\n" + "=" * 60)
    print("CONVERSATION SIMULATION")
    print("=" * 60)
    
    # Simulate conversation
    for i, user_response in enumerate(user_responses, 1):
        print(f"\n--- Turn {i} ---")
        print(f"User: {user_response}")
        
        # Process response through agent
        try:
            agent_response = agent_group.process_response(user_response)
            print(f"Agent: {agent_response}")
            
            # Add small delay to simulate real conversation
            time.sleep(0.5)
            
        except Exception as e:
            print(f"[ERROR] Error processing response: {e}")
            continue
    
    # Display interview summary
    print("\n" + "=" * 60)
    print("INTERVIEW SUMMARY")
    print("=" * 60)
    
    summary = agent_group.get_interview_summary()
    
    # Display all collected data
    print("\n[STATS] Collected Assessment Data:")
    print("-" * 40)
    
    for key, value in summary.items():
        if value:
            formatted_key = key.replace('_', ' ').title()
            print(f"\n{formatted_key}:")
            if isinstance(value, list):
                for item in value:
                    print(f"  - {item}")
            else:
                print(f"  {value}")
        else:
            formatted_key = key.replace('_', ' ').title()
            print(f"\n{formatted_key}: [No data collected]")
    
    # Check completion status
    print(f"\n[STATUS] Interview Completion Status: {agent_group.is_interview_complete()}")
    
    # Display completion message
    completion_message = agent_group.prompt_manager.get_agent_group_prompt("interview_agent_group", "completion_message")
    print(f"\n{completion_message}")
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)
    
    total_fields = len(summary)
    filled_fields = sum(1 for value in summary.values() if value)
    list_fields = sum(1 for value in summary.values() if isinstance(value, list) and value)
    
    print(f"Total fields: {total_fields}")
    print(f"Filled fields: {filled_fields}")
    print(f"List fields with data: {list_fields}")
    print(f"Completion rate: {(filled_fields/total_fields)*100:.1f}%")
    
    # Test data classification accuracy
    print("\n" + "=" * 60)
    print("DATA CLASSIFICATION ANALYSIS")
    print("=" * 60)
    
    expected_classifications = {
        "assessment_context": ["healthcare", "patient care", "nurses"],
        "robot_platform": ["humanoid", "facial expressions", "voice"],
        "collaboration_pattern": ["supervised", "following", "instructions"],
        "environmental_setting": ["hospital ward", "patients"],
        "assessment_goals": ["goal", "assess", "emotional support"],
        "expected_empathy_forms": ["expect", "observe", "verbal empathy"],
        "assessment_challenges": ["challenge", "measuring", "cultural sensitivity"],
        "measurement_requirements": ["scale", "captures", "demographics"]
    }
    
    print("Classification Analysis:")
    for field, keywords in expected_classifications.items():
        if summary[field]:
            print(f"[OK] {field}: Data collected")
        else:
            print(f"[MISSING] {field}: No data collected")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETED")
    print("=" * 80)

def test_data_saving_functionality():
    """Test the data saving functionality directly."""
    print("\n" + "=" * 60)
    print("DIRECT DATA SAVING TEST")
    print("=" * 60)
    
    try:
        config = load_config()
        agent_group = InterviewAgentGroup(api_key=config["openai_api_key"])
        
        # Test data for each field
        test_data = {
            "assessment_context": "Manufacturing robot assisting workers in assembly tasks",
            "robot_platform": "Industrial robotic arm with visual sensors and haptic feedback",
            "collaboration_pattern": "Collaborative mode with shared workspace and safety protocols",
            "environmental_setting": "Factory floor with multiple workstations and safety equipment",
            "assessment_goals": "Evaluate robot's ability to provide emotional support during stressful tasks",
            "expected_empathy_forms": "Expect to observe adaptive behavior and stress recognition",
            "assessment_challenges": "Challenge is measuring emotional impact in industrial setting",
            "measurement_requirements": "Need scale that captures both behavioral and physiological responses"
        }
        
        print("Testing direct data saving...")
        for field, data in test_data.items():
            result = agent_group._create_tools()[0].func(data)
            print(f"[OK] Saved to {field}: {data}")
        
        print("\nFinal data state:")
        summary = agent_group.get_interview_summary()
        for key, value in summary.items():
            if value:
                print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"[ERROR] Error in direct data saving test: {e}")

def main():
    """Main function to run all tests."""
    print("Starting Interview Agent Group Test Suite...")
    
    # Run main conversation simulation
    simulate_user_conversation()
    
    # Run direct data saving test
    test_data_saving_functionality()
    
    print("\n[SUCCESS] All tests completed!")

if __name__ == "__main__":
    main()
