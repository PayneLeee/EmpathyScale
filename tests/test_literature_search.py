#!/usr/bin/env python3
"""
Enhanced Test for Literature Search Agent Group
Shows real-time progress while running with detailed feedback
"""

import os
import sys
from pathlib import Path
import time

# Add agents and utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from literature_search_agent_group import LiteratureSearchAgentGroup
from data_manager import DataManager
from interview_agent_group import load_config

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent


def get_test_interview_summary():
    """Create a realistic fake interview summary for testing."""
    return {
        "assessment_context": "Collaborative dual-arm manipulator robot assisting "
                             "human workers in precision product assembly tasks on "
                             "a manufacturing floor",
        
        "robot_platform": "Dual-arm manipulator with force feedback sensors, vision "
                         "systems, and haptic response capabilities",
        
        "collaboration_pattern": "Peer-to-peer collaboration with shared workspace "
                               "and real-time task coordination",
        
        "environmental_setting": "Manufacturing floor with precision assembly "
                                "stations and safety equipment",
        
        "assessment_goals": [
            "Assess robot's ability to provide emotional support during tasks",
            "Evaluate robot empathy expression in collaborative work",
            "Measure emotional trust in human-robot collaboration"
        ],
        
        "expected_empathy_forms": [
            "Adaptive responses to human emotional states",
            "Stress recognition and supportive communication",
            "Non-verbal empathy expression"
        ],
        
        "assessment_challenges": [
            "Measuring emotional trust in high-stakes assembly scenarios"
        ],
        
        "measurement_requirements": [
            "Scale capturing technical coordination and emotional rapport"
        ]
    }


def print_header():
    """Print test header."""
    print("\n" + "=" * 80)
    print(" " * 28 + "ENHANCED LITERATURE SEARCH TEST")
    print("=" * 80)


def print_step(step_num, total_steps, description):
    """Print step header with progress indicator."""
    print(f"\n[{step_num}/{total_steps}] {description}")
    print("-" * 80)


def print_status(message, status="INFO"):
    """Print status message with prefix."""
    prefixes = {
        "OK": "   [✓]",
        "WARN": "   [!]",
        "ERROR": "   [✗]",
        "INFO": "   [...]",
        "SUCCESS": "   [✓]"
    }
    prefix = prefixes.get(status, "   [...]")
    
    # Use safe characters for Windows terminal
    safe_prefix = prefix.replace('✓', '[OK]').replace('✗', '[FAIL]').replace('!', '[WARN]')
    
    print(f"{safe_prefix} {message}")
    
    # Add slight delay for better readability
    time.sleep(0.1)


def test_literature_search_agent():
    """Test the complete literature search agent functionality with detailed progress."""
    print_header()
    
    total_steps = 7
    results_summary = {}
    
    try:
        # Step 1: Load configuration
        print_step(1, total_steps, "Loading Configuration")
        config = load_config()
        print_status("Configuration loaded successfully", "OK")
        print_status(f"Data directory: data/runs/")
        results_summary["config"] = "OK"
        
        # Step 2: Create test interview summary
        print_step(2, total_steps, "Creating Test Interview Summary")
        interview_summary = get_test_interview_summary()
        print_status("Interview summary created", "OK")
        print_status(f"Context: {interview_summary['assessment_context'][:70]}...", "INFO")
        print_status(f"Platform: {interview_summary['robot_platform'][:70]}...", "INFO")
        print_status(f"Assessment goals: {len(interview_summary['assessment_goals'])} items", "INFO")
        results_summary["interview_summary"] = "OK"
        
        # Step 3: Initialize agent
        print_step(3, total_steps, "Initializing Literature Search Agent")
        print_status("Creating literature search agent...", "INFO")
        
        literature_agent = LiteratureSearchAgentGroup(
            api_key=config["openai_api_key"]
        )
        
        print_status("Agent initialized successfully", "OK")
        print_status("Multi-database search: Enabled", "INFO")
        print_status("LLM-based screening: Enabled", "INFO")
        print_status("Structured extraction: Enabled", "INFO")
        results_summary["agent"] = "OK"
        
        # Step 4: Create data manager and run
        print_step(4, total_steps, "Setting Up Data Storage")
        # Use absolute path to ensure data is saved in project root
        data_manager = DataManager(base_dir=str(PROJECT_ROOT / "data"))
        run_id = data_manager.new_run()
        print_status(f"Test run created: {run_id}", "OK")
        print_status(f"Run directory: data/runs/{run_id}/", "INFO")
        results_summary["run_id"] = run_id
        
        # Step 5: Run enhanced literature search
        print_step(5, total_steps, "Running Enhanced Literature Search Pipeline")
        print_status("Starting comprehensive literature search...", "INFO")
        print_status("This may take several minutes due to LLM calls...", "WARN")
        
        start_time = time.time()
        
        search_results = literature_agent.search_and_download(
            run_id,
            interview_summary
        )
        
        elapsed_time = time.time() - start_time
        
        print_status(f"Pipeline completed in {elapsed_time:.1f} seconds", "OK")
        results_summary["search_time"] = f"{elapsed_time:.1f}s"
        
        # Step 6: Verify results
        print_step(6, total_steps, "Verifying Search Results")
        
        queries = search_results.get("search_queries", [])
        total_papers = search_results.get("total_papers_found", 0)
        screened = search_results.get("screened_papers", 0)
        pdfs_downloaded = search_results.get("pdfs_downloaded", 0)
        
        print_status(f"Search queries: {len(queries)} generated", "OK")
        for i, q in enumerate(queries, 1):
            print_status(f"   {i}. {q}", "INFO")
        
        print_status(f"Total papers found: {total_papers}", "OK")
        print_status(f"Papers screened (relevant): {screened}", "OK")
        print_status(f"PDFs downloaded: {pdfs_downloaded}", "OK")
        
        results_summary["queries"] = len(queries)
        results_summary["papers_found"] = total_papers
        results_summary["screened"] = screened
        results_summary["pdfs_downloaded"] = pdfs_downloaded
        
        # Step 7: Validate PDFs on disk
        print_step(7, total_steps, "Validating Downloaded PDFs")
        
        pdfs_dir = PROJECT_ROOT / f"data/runs/{run_id}/literature_search_agent_group/pdfs"
        
        if not pdfs_dir.exists():
            print_status("PDFs directory does not exist", "ERROR")
            return False
        
        pdf_files = list(pdfs_dir.rglob("*.pdf"))
        print_status(f"Found {len(pdf_files)} PDF files on disk", "OK")
        
        if pdf_files:
            print_status("PDF File Details:", "INFO")
            valid_pdfs = 0
            total_size_mb = 0
            
            for pdf_file in pdf_files:
                try:
                    size_kb = pdf_file.stat().st_size / 1024
                    total_size_mb += size_kb / 1024
                    
                    # Validate PDF
                    with open(pdf_file, 'rb') as f:
                        header = f.read(4)
                        is_valid = header == b'%PDF'
                        if is_valid:
                            valid_pdfs += 1
                    
                    category = pdf_file.parent.name
                    print_status(f"  {category}/{pdf_file.name}: {size_kb:.1f} KB {'[VALID]' if is_valid else '[INVALID]'}", 
                               "OK" if is_valid else "ERROR")
                except Exception as e:
                    print_status(f"  Error reading {pdf_file.name}: {e}", "ERROR")
            
            print_status(f"Valid PDFs: {valid_pdfs}/{len(pdf_files)}", "OK")
            print_status(f"Total size: {total_size_mb:.2f} MB", "INFO")
            
            results_summary["pdfs_valid"] = valid_pdfs
            results_summary["total_size_mb"] = f"{total_size_mb:.2f}"
            
            # Show organized findings if available
            organized = search_results.get("organized_findings", {})
            if organized:
                print_status("Organized findings for scale design:", "INFO")
                def_count = len(organized.get("empathy_definitions", []))
                beh_count = sum(len(v) for v in organized.get("empathic_behaviors", {}).values())
                meas_count = len(organized.get("measurement_approaches", []))
                
                print_status(f"  Empathy definitions: {def_count}", "OK")
                print_status(f"  Empathic behaviors: {beh_count}", "OK")
                print_status(f"  Measurement approaches: {meas_count}", "OK")
        else:
            print_status("No PDF files found on disk", "WARN")
            results_summary["pdfs_valid"] = 0
        
        # Final Summary
        print("\n" + "=" * 80)
        print(" " * 30 + "TEST RESULTS SUMMARY")
        print("=" * 80)
        
        for key, value in results_summary.items():
            if key != "interview_summary":
                label = key.replace('_', ' ').title()
                print(f"  {label:30s}: {value}")
        
        print("=" * 80)
        
        # Final verdict
        pdfs_valid = results_summary.get("pdfs_valid", 0)
        if pdfs_valid > 0:
            print("\n" + "=" * 80)
            print(" " * 18 + "TEST PASSED - PDFs Successfully Downloaded and Validated!")
            print("=" * 80)
            return True
        else:
            print("\n" + "=" * 80)
            print(" " * 20 + "TEST FAILED - No Valid PDFs Downloaded")
            print("=" * 80)
            return False
            
    except Exception as e:
        print_status(f"Test failed with error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_literature_search_agent()
    sys.exit(0 if success else 1)
