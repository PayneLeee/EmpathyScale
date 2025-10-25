#!/usr/bin/env python3
"""
Test script for the complete multi-agent workflow
Tests the integration between interview and research agent groups
"""

import os
import sys
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import MultiAgentWorkflow


def test_research_agent_group():
    """Test the research agent group independently."""
    print("=" * 60)
    print("TESTING RESEARCH AGENT GROUP")
    print("=" * 60)
    
    try:
        workflow = MultiAgentWorkflow()
        research_agent = workflow.agents['research']
        
        # Test with example interview summary
        example_summary = {
            "assessment_context": "Healthcare robot assisting nurses with patient care in hospital ward",
            "robot_platform": "Humanoid robot with facial expressions and voice capabilities",
            "collaboration_pattern": "Supervised collaboration with emotional support functions",
            "environmental_setting": "Hospital ward environment with high-stress situations",
            "assessment_goals": ["Measure robot empathy effectiveness", "Evaluate user emotional response"],
            "expected_empathy_forms": ["Verbal empathy", "Facial expressions", "Proactive emotional support"],
            "assessment_challenges": ["High-stress environment", "Patient privacy concerns"],
            "measurement_requirements": ["Real-time assessment", "Multi-modal evaluation"]
        }
        
        print("Starting research with example interview summary...")
        response = research_agent.start_research(example_summary)
        print(f"Research Agent: {response}")
        
        # Test research tasks
        test_tasks = [
            "Search for papers on empathy measurement in healthcare robot scenarios",
            "Analyze methodologies used in robot empathy evaluation studies",
            "Extract insights about context-specific empathy measurement approaches"
        ]
        
        for i, task in enumerate(test_tasks, 1):
            print(f"\nTest Task {i}: {task}")
            response = research_agent.process_research_task(task)
            print(f"Research Agent: {response}")
        
        # Get research summary
        summary = research_agent.get_research_summary()
        print(f"\nResearch Summary Keys: {list(summary.keys())}")
        
        print("\n✅ Research Agent Group test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Research Agent Group test failed: {str(e)}")
        return False


def test_data_structure():
    """Test that the data structure is properly created."""
    print("=" * 60)
    print("TESTING DATA STRUCTURE")
    print("=" * 60)
    
    required_dirs = [
        "data",
        "data/intermediate_results",
        "data/intermediate_results/interview_agent_group",
        "data/intermediate_results/research_agent_group",
        "data/papers",
        "data/summaries"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ {dir_path} exists")
        else:
            print(f"❌ {dir_path} missing")
            all_exist = False
    
    if all_exist:
        print("\n✅ Data structure test passed!")
    else:
        print("\n❌ Data structure test failed!")
    
    return all_exist


def test_prompt_configuration():
    """Test that prompt configurations are properly loaded."""
    print("=" * 60)
    print("TESTING PROMPT CONFIGURATION")
    print("=" * 60)
    
    try:
        workflow = MultiAgentWorkflow()
        
        # Test interview agent prompts
        interview_agent = workflow.agents['interview']
        system_prompt = interview_agent._get_system_prompt()
        print(f"✅ Interview agent system prompt loaded ({len(system_prompt)} characters)")
        
        # Test research agent prompts
        research_agent = workflow.agents['research']
        system_prompt = research_agent._get_system_prompt()
        print(f"✅ Research agent system prompt loaded ({len(system_prompt)} characters)")
        
        print("\n✅ Prompt configuration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Prompt configuration test failed: {str(e)}")
        return False


def test_workflow_integration():
    """Test the integration between agent groups."""
    print("=" * 60)
    print("TESTING WORKFLOW INTEGRATION")
    print("=" * 60)
    
    try:
        workflow = MultiAgentWorkflow()
        
        # Test that both agent groups are initialized
        assert 'interview' in workflow.agents, "Interview agent group not initialized"
        assert 'research' in workflow.agents, "Research agent group not initialized"
        
        print("✅ Both agent groups initialized successfully")
        
        # Test that agent groups have required methods
        interview_agent = workflow.agents['interview']
        research_agent = workflow.agents['research']
        
        required_interview_methods = ['start_interview', 'process_response', 'get_interview_summary', 'is_interview_complete']
        required_research_methods = ['start_research', 'process_research_task', 'get_research_summary', 'is_research_complete']
        
        for method in required_interview_methods:
            assert hasattr(interview_agent, method), f"Interview agent missing method: {method}"
        
        for method in required_research_methods:
            assert hasattr(research_agent, method), f"Research agent missing method: {method}"
        
        print("✅ All required methods present")
        
        print("\n✅ Workflow integration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Workflow integration test failed: {str(e)}")
        return False


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("RUNNING ALL TESTS")
    print("=" * 60)
    
    tests = [
        ("Data Structure", test_data_structure),
        ("Prompt Configuration", test_prompt_configuration),
        ("Workflow Integration", test_workflow_integration),
        ("Research Agent Group", test_research_agent_group)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The multi-agent workflow is ready to use.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
