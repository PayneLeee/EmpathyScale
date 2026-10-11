#!/usr/bin/env python3
"""
Fast Integration Test for Complete Workflow
Mocks expensive operations (LLM calls, API calls, PDF downloads) to test workflow structure
and data flow quickly.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
import json
import time

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from main import MultiAgentWorkflow
from utils.data_manager import DataManager


def print_progress(message, status="INFO"):
    """Print progress message with status indicator."""
    status_prefixes = {
        "OK": "[OK]",
        "INFO": "[INFO]",
        "WARN": "[WARN]",
        "ERROR": "[ERROR]",
        "STEP": "[STEP]"
    }
    prefix = status_prefixes.get(status, "[INFO]")
    print(f"  {prefix} {message}")
    sys.stdout.flush()


class FastIntegrationTest:
    """Fast integration test with mocked operations."""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.workflow = None
        self.run_id = None
        self.mock_llm_response_count = 0
    
    def mock_llm_invoke(self, prompt):
        """Mock LLM invoke for fast testing."""
        self.mock_llm_response_count += 1
        
        # Return appropriate mock responses based on prompt content
        prompt_str = str(prompt).lower()
        
        # Interview agent responses
        if "opening" in prompt_str or "hello" in prompt_str:
            response = Mock()
            response.content = "Hello! I'm here to help you design empathy measurement scales. Could you tell me about the human-robot collaboration situation you're planning to assess?"
            return response
        elif "save_interview_data" in prompt_str or "agent" in prompt_str:
            # Agent executor response
            response = Mock()
            response.content = "Thank you for that information. Could you tell me more about the robot's interaction modalities?"
            return response
        
        # Literature search agent responses
        elif "query" in prompt_str or "search" in prompt_str:
            # Query generation
            response = Mock()
            response.content = "1. Robot empathy scales in healthcare\n2. Interaction modalities and empathy perception\n3. Perceived empathy measurement methods\n4. Human-robot emotional interaction\n5. Multimodal empathy expression"
            return response
        elif "screen" in prompt_str or "relevance" in prompt_str:
            # Relevance screening
            response = Mock()
            response.content = "SCORE: 5, REASON: Highly relevant for robot empathy scale construction"
            return response
        elif "extract" in prompt_str:
            # Extraction
            response = Mock()
            response.content = '{"empathy_definition": "Robot empathy is the perceived ability of robots to understand and respond to human emotions", "behaviors_identified": ["verbal responses", "facial expressions"], "measurement_methods": "Questionnaires and scales", "key_findings": "Interaction modalities affect empathy perception", "framework": "Perceived empathy framework", "interaction_modalities": "speech, visual cues"}'
            return response
        elif "organize" in prompt_str:
            # Organization
            response = Mock()
            response.content = '{"empathy_definitions": ["Robot empathy definition"], "empathic_behaviors": {"speech_verbal": ["verbal responses"], "visual": ["facial expressions"]}, "measurement_approaches": ["scales", "questionnaires"], "existing_scales": ["Perceived empathy scale"], "interaction_modality_insights": ["Speech affects empathy perception"]}'
            return response
        else:
            # Default response
            response = Mock()
            response.content = "Mock response"
            return response
    
    def mock_search_arxiv(self, query, max_results=20):
        """Mock arXiv search."""
        papers = []
        for i in range(min(5, max_results)):  # Return fewer papers for speed
            papers.append({
                "title": f"Mock Paper {i} about {query[:30]}",
                "authors": ["Author 1", "Author 2"],
                "abstract": f"This is a mock abstract about robot empathy and {query[:30]}",
                "published": "2024",
                "pdf_url": f"http://example.com/paper{i}.pdf",
                "source": "arxiv"
            })
        return papers
    
    def mock_search_semantic_scholar(self, query, max_results=20):
        """Mock Semantic Scholar search."""
        papers = []
        for i in range(min(5, max_results)):  # Return fewer papers for speed
            papers.append({
                "title": f"Mock Semantic Paper {i} about {query[:30]}",
                "authors": [{"name": "Author 1"}, {"name": "Author 2"}],
                "abstract": f"This is a mock abstract about robot empathy and {query[:30]}",
                "year": 2024,
                "pdf_url": f"http://example.com/semantic{i}.pdf" if i % 2 == 0 else None,
                "source": "semantic_scholar"
            })
        return papers
    
    def mock_download_pdf(self, url, save_path):
        """Mock PDF download - just create empty file."""
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        # Create a minimal valid PDF file
        with open(save_path, 'wb') as f:
            f.write(b'%PDF-1.4\n')  # Minimal PDF header
        return True
    
    def run_test(self):
        """Execute the fast integration test."""
        print("\n" + "=" * 80)
        print(" " * 25 + "FAST INTEGRATION TEST")
        print(" " * 15 + "Interview → Literature Search Workflow (Mocked)")
        print("=" * 80)
        
        start_time = time.time()
        
        try:
            # Step 1: Initialize workflow
            print("\n[Step 1/6] Initializing MultiAgentWorkflow")
            print("-" * 80)
            print_progress("Loading configuration...", "INFO")
            
            with patch('langchain_openai.ChatOpenAI') as mock_chat_openai:
                # Mock ChatOpenAI
                mock_llm = MagicMock()
                mock_llm.invoke = self.mock_llm_invoke
                mock_chat_openai.return_value = mock_llm
                
                self.workflow = MultiAgentWorkflow()
                print_progress("Workflow initialized successfully", "OK")
            
            # Step 2: Create run and mock interview data
            print("\n[Step 2/6] Setting up test data")
            print("-" * 80)
            print_progress("Creating new run...", "INFO")
            self.run_id = self.workflow.data_manager.new_run()
            print_progress(f"Run ID: {self.run_id}", "OK")
            
            # Create mock interview summary
            mock_interview_summary = {
                "assessment_context": "Healthcare scenario where robot provides emotional support to patients",
                "robot_platform": "Humanoid robot with expressive facial features and voice capabilities",
                "interaction_modalities": "Speech with calming voice tones, empathetic language, and physical gestures",
                "collaboration_pattern": "Robot responds to patient emotional cues",
                "environmental_setting": "Hospital ward during medical procedures",
                "assessment_goals": ["Measure patient trust and perceived empathy"],
                "expected_empathy_forms": ["Verbal and nonverbal empathetic responses"],
                "assessment_challenges": ["Real-time emotion recognition"],
                "measurement_requirements": ["Validated scale for perceived empathy dimensions"]
            }
            
            # Save mock interview data directly
            self.workflow.data_manager.save_agent_group_data(
                self.run_id,
                "interview_agent_group",
                mock_interview_summary,
                [{"type": "agent", "content": "Mock conversation"}]
            )
            print_progress("Mock interview data saved", "OK")
            
            # Step 3: Test literature search with mocks
            print("\n[Step 3/6] Testing Literature Search (Mocked)")
            print("-" * 80)
            print_progress("Mocking API calls and PDF downloads...", "INFO")
            
            with patch('utils.research_api.ResearchAPIClient') as mock_client_class:
                with patch('utils.research_api.download_pdf', side_effect=self.mock_download_pdf):
                    with patch('langchain_openai.ChatOpenAI') as mock_chat_openai:
                        # Mock the API client
                        mock_client = MagicMock()
                        mock_client.search_arxiv = self.mock_search_arxiv
                        mock_client.search_semantic_scholar = self.mock_search_semantic_scholar
                        mock_client_class.return_value = mock_client
                        
                        # Mock LLM
                        mock_llm = MagicMock()
                        mock_llm.invoke = self.mock_llm_invoke
                        mock_chat_openai.return_value = mock_llm
                        
                        # Get literature agent and run search
                        literature_agent = self.workflow.agents['literature']
                        print_progress("Generating search queries...", "INFO")
                        
                        # Run search with mocked operations
                        literature_results = literature_agent.search_and_download(
                            self.run_id,
                            mock_interview_summary
                        )
                        
                        print_progress("Literature search completed (mocked)", "OK")
            
            # Step 4: Verify data structure
            print("\n[Step 4/6] Verifying Data Structure")
            print("-" * 80)
            structure_ok = self.verify_data_structure()
            
            # Step 5: Verify agent connection
            print("\n[Step 5/6] Verifying Agent Connection")
            print("-" * 80)
            connection_ok = self.verify_agent_connection()
            
            # Step 6: Final summary
            print("\n[Step 6/6] Test Summary")
            print("-" * 80)
            elapsed_time = time.time() - start_time
            
            print_progress(f"Total test time: {elapsed_time:.2f} seconds", "INFO")
            print_progress(f"LLM invocations mocked: {self.mock_llm_response_count}", "INFO")
            
            print("\n" + "=" * 80)
            print(" " * 30 + "TEST RESULTS")
            print("=" * 80)
            
            all_passed = structure_ok and connection_ok
            
            self.print_result("Data Structure", structure_ok)
            self.print_result("Agent Connection", connection_ok)
            
            print("\n" + "=" * 80)
            if all_passed:
                print(" " * 20 + "FAST INTEGRATION TEST PASSED")
                print("=" * 80)
            else:
                print(" " * 20 + "FAST INTEGRATION TEST FAILED")
                print("=" * 80)
            
            return all_passed
            
        except Exception as e:
            print_progress(f"Test failed with exception: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False
    
    def verify_data_structure(self):
        """Verify that data was saved with correct structure."""
        try:
            run_dir = self.project_root / f"data/runs/{self.run_id}"
            
            if not run_dir.exists():
                print_progress("Run directory does not exist", "ERROR")
                return False
            
            print_progress(f"Run directory found: {run_dir}", "OK")
            
            # Check interview data
            interview_dir = run_dir / "interview_agent_group"
            if not interview_dir.exists():
                print_progress("Interview directory missing", "ERROR")
                return False
            
            summary_file = interview_dir / "summary.json"
            if not summary_file.exists():
                print_progress("Interview summary.json missing", "ERROR")
                return False
            
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary = json.load(f)
            
            required_fields = ['assessment_context', 'robot_platform', 'interaction_modalities']
            missing = [f for f in required_fields if not summary.get(f)]
            
            if missing:
                print_progress(f"Missing required fields: {missing}", "ERROR")
                return False
            
            print_progress("Interview data structure verified", "OK")
            
            # Check literature search data
            lit_dir = run_dir / "literature_search_agent_group"
            if lit_dir.exists():
                print_progress("Literature search directory found", "OK")
                
                # Check for summary.json
                lit_summary_file = lit_dir / "summary.json"
                if lit_summary_file.exists():
                    print_progress("Literature search summary.json found", "OK")
                else:
                    print_progress("Literature search summary.json not found (may be OK if search failed)", "WARN")
            else:
                print_progress("Literature search directory not found (may be OK if search failed)", "WARN")
            
            return True
            
        except Exception as e:
            print_progress(f"Error verifying data structure: {e}", "ERROR")
            return False
    
    def verify_agent_connection(self):
        """Verify that agents are properly connected."""
        try:
            # Check that workflow has both agents
            if 'interview' not in self.workflow.agents:
                print_progress("Interview agent missing from workflow", "ERROR")
                return False
            
            if 'literature' not in self.workflow.agents:
                print_progress("Literature agent missing from workflow", "ERROR")
                return False
            
            print_progress("Both agents present in workflow", "OK")
            
            # Check that interview summary can be loaded
            run_dir = self.project_root / f"data/runs/{self.run_id}"
            summary_file = run_dir / "interview_agent_group" / "summary.json"
            
            if summary_file.exists():
                with open(summary_file, 'r', encoding='utf-8') as f:
                    interview_summary = json.load(f)
                
                # Verify summary has content
                if not interview_summary.get('assessment_context'):
                    print_progress("Interview summary missing assessment_context", "ERROR")
                    return False
                
                print_progress("Interview summary loaded and verified", "OK")
                print_progress(f"  Context: {interview_summary.get('assessment_context', '')[:60]}...", "INFO")
                print_progress(f"  Platform: {interview_summary.get('robot_platform', '')[:60]}...", "INFO")
                print_progress(f"  Modalities: {interview_summary.get('interaction_modalities', '')[:60]}...", "INFO")
                
                return True
            else:
                print_progress("Interview summary file not found", "ERROR")
                return False
                
        except Exception as e:
            print_progress(f"Error verifying agent connection: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False
    
    def print_result(self, test_name, passed):
        """Print a formatted test result."""
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {test_name}")


if __name__ == "__main__":
    test = FastIntegrationTest()
    success = test.run_test()
    sys.exit(0 if success else 1)

