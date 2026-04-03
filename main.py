"""
Multi-Agent LLM Workflow for Human-Robot Collaboration Analysis
Main application entry point.
"""

import os
import sys
import json
from typing import Dict
from datetime import datetime
from pathlib import Path

# Add the agents and utils directories to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from interview_agent_group import InterviewAgentGroup, load_config
from literature_search_agent_group import LiteratureSearchAgentGroup
from empathy_scale_generation_agent_group import EmpathyScaleGenerationAgentGroup
from evaluation_agent_group import EvaluationAgentGroup
from data_manager import DataManager


MIN_HIGH_RELEVANCE_PAPERS = 3   # Minimum required high-relevance papers before scale generation
RESEARCH_MIN_COVERAGE_SCORE = 0.5  # Minimum scenario coverage score (0-1)


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
        
        # Initialize empathy scale generation agent group
        self.agents['scale_generation'] = EmpathyScaleGenerationAgentGroup(
            api_key=self.config["openai_api_key"]
        )
    
    # ------------------------------------------------------------------
    # Gate helpers
    # ------------------------------------------------------------------

    def _scenario_readiness_check(self, scenario_brief: Dict) -> tuple:
        """
        Check whether the ScenarioBrief has all required slots filled.

        Returns (passed: bool, report: Dict).
        """
        missing = scenario_brief.get("missing_slots", [])
        readiness = scenario_brief.get("readiness_score", 0.0)
        passed = scenario_brief.get("is_ready", False)
        report = {
            "passed": passed,
            "readiness_score": readiness,
            "missing_slots": missing,
            "required_slots": [
                "assessment_context", "robot_platform", "interaction_modalities",
                "environmental_setting", "collaboration_pattern",
            ],
        }
        return passed, report

    def _research_quality_gate(self, research_results: Dict, scenario_brief: Dict) -> tuple:
        """
        Check whether the literature search produced sufficient high-relevance results.

        Returns (passed: bool, report: Dict).
        """
        gate_report = research_results.get("gate_report", {})
        high_rel_count = gate_report.get("high_relevance_count", len(research_results.get("high_relevance_papers", [])))
        coverage = research_results.get("coverage_report", {})
        coverage_score = coverage.get("coverage_score") or 0.0

        passed = (
            high_rel_count >= MIN_HIGH_RELEVANCE_PAPERS
            and (coverage_score >= RESEARCH_MIN_COVERAGE_SCORE or coverage_score == 0.0)
        )

        report = {
            "passed": passed,
            "high_relevance_count": high_rel_count,
            "min_required": MIN_HIGH_RELEVANCE_PAPERS,
            "coverage_score": coverage_score,
            "min_coverage_score": RESEARCH_MIN_COVERAGE_SCORE,
            "coverage_details": coverage,
            "expansion_trace": gate_report.get("expansion_trace", []),
        }
        return passed, report

    # ------------------------------------------------------------------
    # Main session
    # ------------------------------------------------------------------

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

                # Check for exit command
                if user_input.lower() in ["exit", "quit", "end", "stop"]:
                    print("\n[Interview ended by user]")
                    break

                if not user_input:
                    print("Please provide a response or type 'exit' to end the interview.")
                    continue

                # Process the response
                response = interview_agent_group.process_response(user_input)
                print(f"\nAgent: {response}")

                # Check if interview is complete (all required fields collected)
                if interview_agent_group.is_interview_complete():
                    print("\n[All required information collected. Interview complete!]")
                    break

            except EOFError:
                print("\n\nInput stream ended. Ending interview session.")
                break

        # Display summary
        self._display_interview_summary(interview_agent_group)

        # --- Gate 1: Scenario Readiness ---
        scenario_brief = interview_agent_group.get_scenario_brief()
        passed, readiness_report = self._scenario_readiness_check(scenario_brief)

        print("\n" + "=" * 60)
        print("SCENARIO READINESS CHECK")
        print("=" * 60)
        print(f"  Readiness score : {readiness_report['readiness_score']:.0%}")
        if passed:
            print("  Status          : PASSED — all required slots filled.")
        else:
            print(f"  Status          : WARNING — missing slots: {readiness_report['missing_slots']}")
            print(
                "  The literature search will proceed, but scenario-specific\n"
                "  relevance scoring may be less accurate."
            )

        # Save interview data + scenario_brief
        self._save_interview_data(interview_agent_group)
        scenario_brief_path = self.data_manager.save_scenario_brief(self.run_id, scenario_brief)
        print(f"[Data] Scenario brief saved to: {scenario_brief_path}")

        # --- Literature search (with scenario_brief for high-relevance scoring) ---
        research_results = self._run_literature_search(interview_agent_group, scenario_brief)

        # --- Gate 2: Research Quality ---
        if research_results:
            res_passed, res_report = self._research_quality_gate(research_results, scenario_brief)
            self.data_manager.save_research_gate_report(self.run_id, res_report)
            print("\n" + "=" * 60)
            print("RESEARCH QUALITY GATE")
            print("=" * 60)
            print(f"  High-relevance papers : {res_report['high_relevance_count']} (need >= {MIN_HIGH_RELEVANCE_PAPERS})")
            print(f"  Coverage score        : {res_report['coverage_score']}")
            if res_passed:
                print("  Status                : PASSED — sufficient high-relevance literature found.")
            else:
                print(
                    "  Status                : WARNING — fewer high-relevance papers than recommended.\n"
                    "  Scale items may lack strong scenario-specific evidence."
                )

        # --- Scale generation ---
        self._run_scale_generation()
    
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
    
    def _run_literature_search(
        self, interview_agent_group: InterviewAgentGroup, scenario_brief: Dict = None
    ) -> Dict:
        """Run enhanced literature search using interview summary and scenario_brief."""
        if not self.run_id:
            return {}

        literature_agent = self.agents.get('literature')
        if not literature_agent:
            print("\n[Literature] Agent not initialized, skipping literature search")
            return {}

        print("\n" + "=" * 60)
        print("STARTING ENHANCED LITERATURE SEARCH")
        print("=" * 60)

        interview_summary = interview_agent_group.get_interview_summary()

        # Run the full pipeline; pass scenario_brief for high-relevance scoring
        literature_results = literature_agent.search_and_download(
            self.run_id,
            interview_summary,
            scenario_brief=scenario_brief,
        )

        # Persist relevance-scored papers
        scored_papers = literature_results.get("relevance_scored_papers", [])
        if scored_papers:
            scored_path = self.data_manager.save_relevance_scored_papers(self.run_id, scored_papers)
            print(f"[Data] Relevance-scored papers saved to: {scored_path}")

        # Save essential summary (existing helper)
        self._save_literature_results(self.run_id, literature_results)

        # Update metadata
        metadata = self.data_manager.load_metadata(self.run_id)
        if metadata:
            for grp in ("interview_agent_group", "literature_search_agent_group"):
                if grp not in metadata["agent_groups"]:
                    metadata["agent_groups"].append(grp)
            self.data_manager.save_metadata(self.run_id, metadata)

        print(
            f"\n[Literature] Search complete — "
            f"{literature_results.get('pdfs_downloaded', 0)} PDFs downloaded, "
            f"{len(literature_results.get('high_relevance_papers', []))} high-relevance papers."
        )
        return literature_results

    def _run_scale_generation(self):
        """Run empathy scale generation using prior results and expert PDFs."""
        if not self.run_id:
            return
        scale_agent = self.agents.get('scale_generation')
        if not scale_agent:
            print("\n[Scale] Agent not initialized, skipping scale generation")
            return
        print("\n" + "=" * 60)
        print("GENERATING EMPATHY SCALE DRAFT")
        print("=" * 60)
        results = scale_agent.generate_scale(self.run_id)
        if results.get("scale_draft_path"):
            print(f"[Scale] Draft saved to: {results['scale_draft_path']}")
            # Report evidence coverage
            ev = results.get("evidence_coverage", {})
            ev_score = ev.get("evidence_coverage_score", "N/A")
            print(f"[Scale] Evidence coverage score: {ev_score}")
            if results.get("needs_more_research"):
                print(
                    "[Scale] WARNING: One or more dimensions lack direct paper support.\n"
                    "        Consider re-running with a more specific scenario to improve literature coverage."
                )
            # Run evaluation automatically after generation
            self._run_evaluation()
        else:
            print(f"[Scale] {results.get('error', 'Unknown error')}")

    def _run_evaluation(self, n_participants: int = 25):
        """Run LLM-simulated participant evaluation for generated scale and baselines."""
        if not self.run_id:
            return

        # Load scenario context
        interview_path = self.data_manager.get_run_path(self.run_id) / "interview_agent_group" / "summary.json"
        if not interview_path.exists():
            print("[Eval] interview summary not found; skipping evaluation")
            return
        interview_summary = json.loads(interview_path.read_text(encoding="utf-8"))

        # Load generated items
        scale_dir = self.data_manager.get_run_path(self.run_id) / "empathy_scale_generation_agent_group"
        draft_path = scale_dir / "scale_draft.md"
        if not draft_path.exists():
            print("[Eval] scale_draft.md not found; skipping evaluation")
            return
        md_text = draft_path.read_text(encoding="utf-8", errors="replace")
        items = EmpathyScaleGenerationAgentGroup.parse_scale_markdown(md_text)
        if not items:
            print("[Eval] No items parsed from draft; skipping evaluation")
            return

        eval_agent = EvaluationAgentGroup(api_key=self.config["openai_api_key"])
        print("\n" + "=" * 60)
        print("LLM-SIMULATED ITEM TESTING (PETS-style with Personas)")
        print("=" * 60)
        
        # Extract scenario name from interview summary if available
        scenario_id = interview_summary.get("name") if isinstance(interview_summary, dict) else None
        if scenario_id:
            print(f"[Eval] Using scenario_id: {scenario_id}")
        else:
            print(f"[Eval] No scenario_id found, generating temporary personas")
        
        print(f"[Eval] Each persona rates all {len(items)} items on system empathy (0-100 scale)")
        result = eval_agent.evaluate_items(self.run_id, items, interview_summary, n_participants=n_participants, scenario_id=scenario_id)
        print(f"[Eval] Summary saved to: {result.get('summary_path')}")

        # Baseline evaluations (PETS / ROPE) if available
        txt_dir = Path("agents/expert_pdfs/txt")
        baselines = {
            "PETS": txt_dir / "Schmidmaier et al. - 2024 - Perceived Empathy of Technology Scale (PETS) Measuring Empathy of Systems Toward the User.txt",
            "ROPE": txt_dir / "Charrier et al. - 2019 - The RoPE Scale a Measure of How Empathic a Robot is Perceived.txt",
        }
        for label, path in baselines.items():
            if path.exists():
                b_res = eval_agent.evaluate_baseline_txt(self.run_id, path, interview_summary, n_participants, label=label)
                print(f"[Eval] Baseline {label} summary: {b_res.get('summary_path')}")

        self._write_run_readme(items, result.get("summary_path"))

    def _write_run_readme(self, items: list, eval_summary_path: str):
        """Create a lightweight README for the run."""
        run_dir = self.data_manager.get_run_path(self.run_id)
        lines = [
            f"# Run {self.run_id}",
            "",
            "## Artifacts",
            f"- Scale draft: data/runs/{self.run_id}/empathy_scale_generation_agent_group/scale_draft.md",
            f"- Evaluation summary: {eval_summary_path}",
            "- Interview summary: data/runs/{self.run_id}/interview_agent_group/summary.json",
            "- Literature summary: data/runs/{self.run_id}/literature_search_agent_group/summary.json",
            "",
            "## Items (preview)",
        ]
        for it in items[:10]:
            lines.append(f"- [{it.get('dimension','Dim')}] {it.get('item_text')}")
        readme_path = run_dir / "README.md"
        readme_path.write_text("\n".join(lines), encoding="utf-8")


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
