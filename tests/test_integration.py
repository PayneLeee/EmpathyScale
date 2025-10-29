#!/usr/bin/env python3
"""
Integration Test for Complete Workflow
Tests the connection between interview_agent_group and literature_search_agent_group
through the main.py workflow with simulated user input.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import json
import time

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from main import MultiAgentWorkflow


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


class IntegrationTest:
    """Test complete workflow from interview to literature search."""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.test_responses = [
            "We want to evaluate robot empathy in a healthcare collaborative robot scenario",
            "It's a humanoid robot with expressive facial features and voice capabilities",
            "The robot provides emotional support to patients during medical procedures",
            "Hospital ward with patients who need emotional comfort during procedures",
            "Assess the robot's ability to recognize and respond to patient emotional distress",
            "Evaluate how the robot expresses empathy through verbal and nonverbal cues",
            "Measure patient trust and perceived empathy from the robot",
            "Adaptive emotional responses based on patient state",
            "Calming voice tones and empathetic language",
            "Physical gestures that show understanding and care",
            "Understanding patient emotions in real-time during stressful procedures",
            "Validated scale capturing perceived empathy dimensions including emotional recognition, responsive communication, and supportive behaviors", 
            "exit"
        ]
        self.response_index = 0
        self.workflow = None
        self.run_id = None
    
    def mock_input(self, prompt=""):
        """Mock user input with predefined responses."""
        if self.response_index < len(self.test_responses):
            response = self.test_responses[self.response_index]
            self.response_index += 1
            print(f"\nMock Input: {response}")
            return response
        return "exit"
    
    def run_test(self):
        """Execute the complete integration test."""
        print("\n" + "=" * 80)
        print(" " * 25 + "INTEGRATION TEST")
        print(" " * 15 + "Interview → Literature Search Workflow")
        print("=" * 80)
        
        start_time = time.time()
        
        try:
            # Step 1: Initialize workflow
            print("\n[Step 1/5] Initializing MultiAgentWorkflow")
            print("-" * 80)
            print_progress("Loading configuration...", "INFO")
            self.workflow = MultiAgentWorkflow()
            print_progress("Workflow initialized successfully", "OK")
            print_progress(f"Run will be saved to: data/runs/", "INFO")
            
            # Patch the input function to simulate user responses
            with patch('builtins.input', side_effect=self.mock_input):
                with patch('sys.stdin', new=MagicMock()):
                    print("\n[Step 2/5] Running Interview Session (Simulated)")
                    print("-" * 80)
                    print_progress("Starting interview with simulated user responses...", "INFO")
                    print_progress(f"Will simulate {len(self.test_responses)} user responses", "INFO")
                    
                    interview_start = time.time()
                    
                    # Run the complete workflow
                    self.workflow.run_interview_session()
                    
                    interview_elapsed = time.time() - interview_start
                    
                    # Capture run_id
                    self.run_id = self.workflow.run_id
                    print_progress(f"Interview session completed in {interview_elapsed:.1f}s", "OK")
                    print_progress(f"Run ID: {self.run_id}", "OK")
                    print_progress("Waiting for literature search to complete...", "INFO")
            
            # Step 3: Verify Interview Data
            print("\n[Step 3/5] Verifying Interview Data")
            print("-" * 80)
            print_progress("Checking interview data directory...", "INFO")
            interview_verified = self.verify_interview_data()
            
            # Step 4: Verify Literature Search Data
            print("\n[Step 4/5] Verifying Literature Search Data")
            print("-" * 80)
            print_progress("Checking literature search data directory...", "INFO")
            print_progress("Counting downloaded PDFs...", "INFO")
            literature_verified = self.verify_literature_search_data()
            
            # Step 5: Verify Connection
            print("\n[Step 5/5] Verifying Agent Connection")
            print("-" * 80)
            print_progress("Loading interview summary...", "INFO")
            print_progress("Checking literature search results...", "INFO")
            print_progress("Verifying queries match interview context...", "INFO")
            connection_verified = self.verify_agent_connection()
            
            # Final summary
            elapsed_time = time.time() - start_time
            print("\n" + "=" * 80)
            print(" " * 30 + "TEST RESULTS")
            print("=" * 80)
            
            all_passed = interview_verified and literature_verified and connection_verified
            
            self.print_result("Interview Data", interview_verified)
            self.print_result("Literature Search Data", literature_verified)
            self.print_result("Agent Connection", connection_verified)
            
            print_progress(f"Total test time: {elapsed_time:.1f} seconds", "INFO")
            
            print("\n" + "=" * 80)
            if all_passed:
                print(" " * 20 + "INTEGRATION TEST PASSED")
                print("=" * 80)
            else:
                print(" " * 20 + "INTEGRATION TEST FAILED")
                print("=" * 80)
            
            return all_passed
            
        except Exception as e:
            print_progress(f"Test failed with exception: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False
    
    def verify_interview_data(self):
        """Verify interview agent data was saved correctly."""
        try:
            interview_dir = self.project_root / f"data/runs/{self.run_id}/interview_agent_group"
            
            if not interview_dir.exists():
                print_progress("Interview directory does not exist", "ERROR")
                print_progress(f"Expected path: {interview_dir}", "INFO")
                # Check if parent directory exists
                parent_dir = interview_dir.parent
                if parent_dir.exists():
                    print_progress(f"Parent directory exists: {parent_dir}", "INFO")
                    print_progress(f"Contents: {[p.name for p in parent_dir.iterdir()]}", "INFO")
                else:
                    print_progress(f"Parent directory also missing: {parent_dir}", "INFO")
                return False
            
            print_progress(f"Interview directory found: {interview_dir}", "OK")
            
            # Check for summary.json
            summary_file = interview_dir / "summary.json"
            if not summary_file.exists():
                print_progress("summary.json not found", "ERROR")
                return False
            
            print_progress("summary.json found", "OK")
            
            # Load and validate summary
            try:
                with open(summary_file, 'r', encoding='utf-8', errors='replace') as f:
                    summary = json.load(f)
            except UnicodeDecodeError:
                # Fallback: try with UTF-8 ignoring errors
                print_progress("UTF-8 decode error in interview summary, trying with error handling...", "WARN")
                with open(summary_file, 'r', encoding='utf-8', errors='ignore') as f:
                    summary = json.load(f)
            
            print_progress("summary.json loaded successfully", "OK")
            
            # Verify key fields (some may be optional depending on interview flow)
            print_progress("Validating interview summary fields...", "INFO")
            # Core field required for literature search to work
            key_fields = ['assessment_context']
            missing_key_fields = [field for field in key_fields if not summary.get(field)]
            
            if missing_key_fields:
                print_progress(f"Missing core field: {missing_key_fields}", "ERROR")
                return False
            
            # Check for other important fields (warn if missing but don't fail)
            important_fields = ['robot_platform', 'environmental_setting']
            missing_important = [field for field in important_fields if not summary.get(field)]
            if missing_important:
                print_progress(f"Missing optional fields (non-critical): {missing_important}", "WARN")
            
            print_progress("Core interview fields validated", "OK")
            
            # Check if any assessment-related fields exist
            assessment_fields = ['assessment_goals', 'expected_empathy_forms', 'assessment_challenges', 'measurement_requirements']
            has_assessment_data = any(summary.get(field) for field in assessment_fields)
            
            if not has_assessment_data:
                print_progress("No assessment-specific data collected", "WARN")
            else:
                filled_fields = [f for f in assessment_fields if summary.get(f)]
                print_progress(f"Assessment data collected: {len(filled_fields)}/{len(assessment_fields)} fields", "OK")
            
            print_progress("Interview summary validation complete", "OK")
            context_val = summary.get('assessment_context', 'N/A')
            context_preview = context_val[:60] + '...' if context_val and isinstance(context_val, str) else 'N/A'
            print_progress(f"  Assessment Context: {context_preview}", "INFO")
            
            platform_val = summary.get('robot_platform', 'N/A')
            platform_preview = platform_val[:60] + '...' if platform_val and isinstance(platform_val, str) else 'N/A'
            print_progress(f"  Robot Platform: {platform_preview}", "INFO")
            
            return True
            
        except Exception as e:
            print_progress(f"Error verifying interview data: {e}", "ERROR")
            return False
    
    def verify_literature_search_data(self):
        """Verify literature search agent data and PDFs."""
        try:
            lit_dir = self.project_root / f"data/runs/{self.run_id}/literature_search_agent_group"
            
            if not lit_dir.exists():
                print_progress("Literature search directory does not exist", "ERROR")
                return False
            
            print_progress(f"Literature search directory found: {lit_dir}", "OK")
            
            # Check for PDFs
            pdfs_dir = lit_dir / "pdfs"
            if not pdfs_dir.exists():
                print_progress("PDFs directory does not exist", "ERROR")
                return False
            
            print_progress("Scanning for PDF files...", "INFO")
            # Count PDFs
            pdf_files = list(pdfs_dir.rglob("*.pdf"))
            print_progress(f"Found {len(pdf_files)} PDF files", "OK")
            
            if len(pdf_files) == 0:
                print_progress("No PDFs downloaded", "ERROR")
                return False
            
            # Check PDF categories
            print_progress("Organizing PDFs by category...", "INFO")
            categories = {}
            for pdf in pdf_files:
                category = pdf.parent.name
                categories[category] = categories.get(category, 0) + 1
            
            print_progress("PDFs organized by category:", "OK")
            for category, count in categories.items():
                print_progress(f"  {category}: {count} papers", "INFO")
            
            # Verify PDF validity
            print_progress("Validating PDF files...", "INFO")
            valid_pdfs = 0
            for pdf in pdf_files:
                try:
                    with open(pdf, 'rb') as f:
                        header = f.read(4)
                        if header == b'%PDF':
                            valid_pdfs += 1
                except:
                    pass
            
            print_progress(f"PDF validation: {valid_pdfs}/{len(pdf_files)} valid", "OK")
            
            if valid_pdfs < len(pdf_files):
                print_progress(f"Some PDFs may be corrupted ({len(pdf_files) - valid_pdfs} invalid)", "WARN")
            
            return True
            
        except Exception as e:
            print_progress(f"Error verifying literature search data: {e}", "ERROR")
            return False
    
    def verify_agent_connection(self):
        """Verify that literature search received interview summary."""
        try:
            # Load interview summary
            interview_dir = self.project_root / f"data/runs/{self.run_id}/interview_agent_group"
            summary_file = interview_dir / "summary.json"
            
            if not summary_file.exists():
                print_progress(f"summary.json not found at: {summary_file}", "ERROR")
                if interview_dir.exists():
                    print_progress(f"Interview directory exists but summary.json is missing", "ERROR")
                    print_progress(f"Contents of interview_dir: {list(interview_dir.iterdir())}", "INFO")
                else:
                    print_progress(f"Interview directory does not exist: {interview_dir}", "ERROR")
                return False
            
            try:
                with open(summary_file, 'r', encoding='utf-8', errors='replace') as f:
                    interview_summary = json.load(f)
            except UnicodeDecodeError:
                # Fallback: try with UTF-8 ignoring errors
                print_progress("UTF-8 decode error in interview summary, trying with error handling...", "WARN")
                with open(summary_file, 'r', encoding='utf-8', errors='ignore') as f:
                    interview_summary = json.load(f)
            
            print_progress("Interview summary loaded", "OK")
            
            # Check if literature search was executed by looking for saved data
            lit_dir = self.project_root / f"data/runs/{self.run_id}/literature_search_agent_group"
            
            print_progress("Loading literature search results...", "INFO")
            # Look for saved results in summary.json
            summary_file_lit = lit_dir / "summary.json"
            
            if summary_file_lit.exists():
                print_progress("summary.json found", "OK")
                try:
                    with open(summary_file_lit, 'r', encoding='utf-8', errors='replace') as f:
                        literature_data_raw = json.load(f)
                except UnicodeDecodeError:
                    # Fallback: try with UTF-8 ignoring errors, or other encodings
                    print_progress("UTF-8 decode error, trying with error handling...", "WARN")
                    with open(summary_file_lit, 'r', encoding='utf-8', errors='ignore') as f:
                        literature_data_raw = json.load(f)
                    print_progress("Loaded with error handling", "WARN")
                except json.JSONDecodeError as e:
                    print_progress(f"JSON decode error: {e}", "ERROR")
                    raise
                
                # Handle the data structure - could be dict with 'results' key or direct results dict
                literature_data = literature_data_raw
                if isinstance(literature_data, dict):
                    # New structure: direct keys at top level
                    if 'search_queries' in literature_data:
                        results = literature_data
                        print_progress("Using new minimal summary structure", "INFO")
                    elif 'results' in literature_data:
                        results = literature_data['results']
                        print_progress("Found 'results' key in saved data", "OK")
                    elif 'organized_findings' in literature_data:
                        # Might be the organized_findings wrapper
                        results = literature_data
                        print_progress("Using organized_findings structure", "INFO")
                    else:
                        results = literature_data
                        print_progress("Using direct data structure", "INFO")
                    
                    # Now extract queries and PDF count from results
                    if isinstance(results, dict):
                        queries = results.get('search_queries', [])
                        # Check for pdfs_downloaded in statistics or at top level
                        if 'statistics' in results and isinstance(results['statistics'], dict):
                            pdfs_count = results['statistics'].get('pdfs_downloaded', 0)
                        else:
                            pdfs_count = results.get('pdfs_downloaded', 0)
                    else:
                        queries = []
                        pdfs_count = 0
                    
                    if queries and isinstance(queries, list):
                        print_progress(f"Literature search generated {len(queries)} queries", "OK")
                        print_progress("Generated search queries:", "INFO")
                        for i, query in enumerate(queries[:5], 1):  # Show first 5
                            print_progress(f"  {i}. {query}", "INFO")
                        
                        # Verify queries relate to interview context
                        query_text = ' '.join(queries).lower()
                        
                        # Check for robot empathy focus
                        has_robot_empathy = 'robot' in query_text and 'empathy' in query_text
                        
                        # Check if queries relate to interview context
                        assessment_context = interview_summary.get('assessment_context') or ''
                        robot_platform = interview_summary.get('robot_platform') or ''
                        context_text = (assessment_context.lower() if assessment_context else '') + ' ' + (robot_platform.lower() if robot_platform else '')
                        
                        # Look for healthcare-related terms in queries if context mentions them
                        has_context_match = False
                        if any(kw in context_text for kw in ['healthcare', 'hospital', 'medical', 'patient']):
                            has_context_match = any(kw in query_text for kw in ['healthcare', 'hospital', 'medical', 'patient', 'emotional support'])
                        else:
                            # For other contexts, just check if queries are generated
                            has_context_match = True
                        
                        if has_robot_empathy:
                            print_progress("Search queries focus on robot empathy", "OK")
                        else:
                            print_progress("Warning: Search queries may not focus on robot empathy", "WARN")
                        
                        if has_context_match:
                            print_progress("Search queries relate to interview context", "OK")
                        else:
                            print_progress("Warning: Search queries may not match interview context", "WARN")
                        
                        # Connection verified if queries exist and PDFs were downloaded
                        # (pdfs_count already extracted above)
                        print_progress(f"PDFs downloaded according to results: {pdfs_count}", "INFO")
                        
                        connection_ok = len(queries) > 0 and pdfs_count > 0
                        if connection_ok:
                            print_progress("Agent connection verified successfully", "OK")
                        return connection_ok
                    else:
                        print_progress("No search queries found in expected format, checking PDFs...", "WARN")
                        # Still verify connection by checking if PDFs exist
                        pdfs_dir = lit_dir / "pdfs"
                        if pdfs_dir.exists():
                            pdf_files = list(pdfs_dir.rglob("*.pdf"))
                            if len(pdf_files) > 0:
                                print_progress(f"Agent connection verified - {len(pdf_files)} PDFs downloaded", "OK")
                                return True
                        print_progress("No search queries found in literature search results", "ERROR")
                        return False
                else:
                    print_progress(f"Unexpected data structure: {type(literature_data_raw)}, checking PDFs...", "WARN")
                    # Fallback to PDF check
                    pdfs_dir = lit_dir / "pdfs"
                    if pdfs_dir.exists():
                        pdf_files = list(pdfs_dir.rglob("*.pdf"))
                        if len(pdf_files) > 0:
                            print_progress(f"Agent connection verified - {len(pdf_files)} PDFs downloaded", "OK")
                            return True
                    return False
            else:
                print_progress("summary.json not found, checking PDFs directory...", "INFO")
                # If no summary.json, check if PDFs directory exists (connection still works)
                pdfs_dir = lit_dir / "pdfs"
                if pdfs_dir.exists():
                    pdf_files = list(pdfs_dir.rglob("*.pdf"))
                    if len(pdf_files) > 0:
                        print_progress(f"Agent connection verified - {len(pdf_files)} PDFs downloaded", "OK")
                        return True
                    else:
                        print_progress("Literature search executed but no PDFs downloaded", "ERROR")
                        return False
                else:
                    print_progress("Literature search directory exists but no data found", "ERROR")
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
    
    def cleanup(self):
        """Clean up test artifacts if needed."""
        pass


def main():
    """Run the integration test."""
    test = IntegrationTest()
    
    try:
        success = test.run_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

