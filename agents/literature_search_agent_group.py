"""
Enhanced Literature Search Agent Group for Empathy Scale Design
Intelligent, targeted search for papers supporting empathy scale development
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import json
import re

from langchain_openai import ChatOpenAI

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from research_api import ResearchAPIClient, download_pdf
from prompt_manager import PromptManager

# Get project root for absolute paths
PROJECT_ROOT = Path(__file__).parent.parent.resolve()


class LiteratureSearchAgentGroup:
    """
    Enhanced agent for searching and processing academic papers on robot empathy.
    Supports targeted searches for empathy scale design.
    """
    
    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini", prompts_dir: str = None):
        """
        Initialize the enhanced literature search agent.
        
        Args:
            api_key: OpenAI API key for LLM
            model_name: LLM model to use
            prompts_dir: Path to prompts directory
        """
        self.llm = ChatOpenAI(api_key=api_key, model_name=model_name)
        self.prompt_manager = PromptManager(prompts_dir)
        self.api_client = ResearchAPIClient()
        
        self.papers = []
        self.downloaded = []
        self.screened_papers = []
        self.extracted_findings = []
    
    def generate_queries(self, interview_summary: Dict) -> List[str]:
        """
        Generate targeted search queries from interview summary.
        
        Args:
            interview_summary: Interview data from previous agent
            
        Returns:
            List of search query strings
        """
        context = interview_summary.get('assessment_context', 'N/A')
        platform = interview_summary.get('robot_platform', 'N/A')
        interaction_modalities = interview_summary.get('interaction_modalities', 'N/A')
        goals = interview_summary.get('assessment_goals', [])
        goals_str = ', '.join(goals) if goals else 'N/A'
        
        # Get prompt template from external file
        template = self.prompt_manager.get_agent_group_prompt(
            "literature_search_agent_group",
            "query_generation_prompt"
        )
        
        # Format prompt with interview data (include interaction modalities)
        prompt = template.format(
            context=context,
            platform=platform,
            interaction_modalities=interaction_modalities,
            goals=goals_str
        )
        
        try:
            response = self.llm.invoke(prompt)
            
            # Parse queries from response
            queries = []
            for line in response.content.split('\n'):
                line = line.strip()
                # Remove numbering and quotes
                line = line.split('. ', 1)[-1].strip()
                line = line.strip('"').strip("'")
                
                if line and len(line) > 10 and not line.startswith(('Query', 'Format', 'Generate')):
                    queries.append(line)
            
            # Ensure we have at least 5 queries for comprehensive coverage
            while len(queries) < 5:
                queries.append("robot empathy human-robot interaction")
            
            # Return up to 6 queries for broader coverage
            return queries[:6]
            
        except Exception as e:
            print(f"Query generation error: {e}")
            # Get fallback queries
            fallback = self.prompt_manager.get_agent_group_prompt(
                "literature_search_agent_group",
                "fallback_queries"
            )
            return [
                fallback.get("definitions", ["robot empathy"])[0],
                fallback.get("behaviors", ["empathic robot"])[0],
                fallback.get("measurement", ["empathy measurement"])[0]
            ]
    
    def search_and_screen(self, queries: List[str], focus_areas: List[str] = None) -> List[Dict]:
        """
        Search across databases and screen for relevance.
        
        Args:
            queries: List of search queries
            focus_areas: Areas to focus on (definitions, behaviors, measurement)
            
        Returns:
            List of screened and relevant papers
        """
        if focus_areas is None:
            focus_areas = ["definitions", "behaviors", "measurement"]
        
        print("\n[Searching databases...]")
        sys.stdout.flush()
        
        all_papers = []
        
        # Search with all queries - increased max_per_source for broader coverage
        for i, query in enumerate(queries, 1):
            print(f"  Query {i}/{len(queries)}: '{query}'...", end=" ")
            sys.stdout.flush()
            papers = self.api_client.search_all(query, max_per_source=20)
            all_papers.extend(papers)
            print(f"Found {len(papers)} papers")
        
        # Basic deduplication
        print("  Deduplicating papers...", end=" ")
        sys.stdout.flush()
        unique_papers = []
        seen_titles = set()
        for paper in all_papers:
            title_lower = paper['title'].lower()
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                unique_papers.append(paper)
        
        self.papers = unique_papers
        print(f"OK - Found {len(unique_papers)} unique papers")
        
        # Screen for relevance
        print("\n[Screening papers for relevance...]")
        screened = self._screen_relevance(unique_papers, focus_areas)
        
        self.screened_papers = screened
        return screened
    
    def _screen_relevance(self, papers: List[Dict], focus_areas: List[str]) -> List[Dict]:
        """Screen papers for relevance using LLM."""
        screened = []
        
        screening_prompt_template = self.prompt_manager.get_agent_group_prompt(
            "literature_search_agent_group",
            "relevance_screening_prompt"
        )
        
        for idx, paper in enumerate(papers[:80], 1):  # Screen first 80 for comprehensive coverage
            try:
                title_short = paper.get('title', '')[:60]
                if idx % 10 == 0 or idx == 1:
                    print(f"  Screening [{idx}/{min(len(papers), 80)}]: {title_short}...", end=" ")
                sys.stdout.flush()
                
                # Format screening prompt
                prompt = screening_prompt_template.format(
                    title=paper.get('title', ''),
                    abstract=paper.get('abstract', '')[:500],
                    focus=focus_areas[0] if focus_areas else "definitions"
                )
                
                response = self.llm.invoke(prompt)
                
                # Parse score
                score = 3  # Default
                if "SCORE:" in response.content:
                    match = re.search(r'SCORE:\s*(\d+)', response.content)
                    if match:
                        score = int(match.group(1))
                
                # Extract reason
                reason = "Relevance assessment"
                if "REASON:" in response.content:
                    match = re.search(r'REASON:\s*(.+)', response.content, re.DOTALL)
                    if match:
                        reason = match.group(1).strip()
                
                if score >= 3:  # Accept papers with score 3 or higher for comprehensive coverage
                    paper['relevance_score'] = score
                    paper['relevance_reason'] = reason
                    screened.append(paper)
                    if idx % 10 == 0 or idx == 1:
                        print(f"[RELEVANT - Score: {score}]")
                elif idx % 10 == 0 or idx == 1:
                    print(f"[Not relevant - Score: {score}]")
            
            except Exception as e:
                print(f"  [ERROR]: {paper.get('title', '')[:50]}...")
                continue
        
        print(f"\nScreening complete: {len(screened)}/{min(len(papers), 80)} papers relevant (score >= 3)")
        sys.stdout.flush()
        return screened
    
    def compute_scenario_relevance_score(self, paper: Dict, scenario_brief: Dict) -> tuple:
        """
        Score a paper's relevance against the user's specific HCI scenario (1-5 scale).

        Returns (score: int, covered_dimensions: List[str], reason: str).
        """
        template = self.prompt_manager.get_agent_group_prompt(
            "literature_search_agent_group",
            "scenario_relevance_scoring_prompt"
        )
        prompt = template.format(
            assessment_context=scenario_brief.get("assessment_context", ""),
            robot_platform=scenario_brief.get("robot_platform", ""),
            interaction_modalities=scenario_brief.get("interaction_modalities", ""),
            collaboration_pattern=scenario_brief.get("collaboration_pattern", ""),
            environmental_setting=scenario_brief.get("environmental_setting", ""),
            title=paper.get("title", ""),
            abstract=paper.get("abstract", "")[:500],
        )
        try:
            response = self.llm.invoke(prompt)
            content = response.content

            score = 3
            m = re.search(r'SCENARIO_SCORE:\s*(\d+)', content)
            if m:
                score = max(1, min(5, int(m.group(1))))

            dimensions: List[str] = []
            m = re.search(r'DIMENSIONS:\s*\[([^\]]*)\]', content)
            if m:
                dimensions = [d.strip() for d in m.group(1).split(',') if d.strip()]

            reason = ""
            m = re.search(r'REASON:\s*(.+)', content, re.DOTALL)
            if m:
                reason = m.group(1).strip()[:200]

            return score, dimensions, reason
        except Exception as e:
            return 3, [], f"Scoring error: {e}"

    def high_relevance_filter(self, papers: List[Dict], threshold: int = 4) -> List[Dict]:
        """Return only papers whose scenario_relevance_score >= threshold."""
        return [p for p in papers if p.get("scenario_relevance_score", 0) >= threshold]

    def coverage_check(self, high_rel_papers: List[Dict], scenario_brief: Dict) -> Dict:
        """
        Check whether the high-relevance paper set covers key scenario dimensions.

        Returns a coverage report dict with per-dimension booleans, gaps list,
        and an overall coverage_score (0-1).
        """
        template = self.prompt_manager.get_agent_group_prompt(
            "literature_search_agent_group",
            "coverage_check_prompt"
        )
        paper_summaries = "\n".join(
            f"- {p.get('title', '')[:80]} [dims: {', '.join(p.get('scenario_covered_dimensions', []))}]"
            for p in high_rel_papers[:25]
        ) or "No high-relevance papers found yet."

        prompt = template.format(
            assessment_context=scenario_brief.get("assessment_context", ""),
            robot_platform=scenario_brief.get("robot_platform", ""),
            interaction_modalities=scenario_brief.get("interaction_modalities", ""),
            collaboration_pattern=scenario_brief.get("collaboration_pattern", ""),
            environmental_setting=scenario_brief.get("environmental_setting", ""),
            paper_summaries=paper_summaries,
        )
        try:
            response = self.llm.invoke(prompt)
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                report = json.loads(json_match.group())
                # Ensure coverage_score is present
                if "coverage_score" not in report:
                    covered = sum([
                        report.get("modality_coverage", False),
                        report.get("user_group_coverage", False),
                        report.get("measurement_coverage", False),
                        report.get("context_coverage", False),
                    ])
                    report["coverage_score"] = round(covered / 4, 2)
                return report
        except Exception as e:
            print(f"  [Coverage check error]: {e}")

        # Fallback: derive from dimension tags
        covered_dims: set = set()
        for p in high_rel_papers:
            for d in p.get("scenario_covered_dimensions", []):
                covered_dims.add(d.strip().upper())
        return {
            "modality_coverage": "MODALITY" in covered_dims,
            "user_group_coverage": "USER_GROUP" in covered_dims,
            "measurement_coverage": "MEASUREMENT" in covered_dims,
            "context_coverage": "CONTEXT" in covered_dims,
            "gaps": ["Coverage check LLM failed; derived from dimension tags."],
            "coverage_score": round(len(covered_dims & {"MODALITY", "USER_GROUP", "MEASUREMENT", "CONTEXT"}) / 4, 2),
        }

    def generate_expansion_queries(
        self, scenario_brief: Dict, existing_queries: List[str], gaps: List[str]
    ) -> List[str]:
        """Generate new search queries that target identified coverage gaps."""
        template = self.prompt_manager.get_agent_group_prompt(
            "literature_search_agent_group",
            "query_expansion_prompt"
        )
        prompt = template.format(
            assessment_context=scenario_brief.get("assessment_context", ""),
            robot_platform=scenario_brief.get("robot_platform", ""),
            interaction_modalities=scenario_brief.get("interaction_modalities", ""),
            collaboration_pattern=scenario_brief.get("collaboration_pattern", ""),
            environmental_setting=scenario_brief.get("environmental_setting", ""),
            coverage_gaps="\n".join(gaps) if gaps else "General coverage improvement needed.",
            existing_queries="\n".join(existing_queries),
        )
        try:
            response = self.llm.invoke(prompt)
            queries = []
            for line in response.content.split('\n'):
                line = line.strip().split('. ', 1)[-1].strip().strip('"').strip("'")
                if line and len(line) > 10:
                    queries.append(line)
            return queries[:3]
        except Exception:
            return []

    def query_expansion_loop(
        self,
        scenario_brief: Dict,
        current_high_rel_papers: List[Dict],
        all_screened_papers: List[Dict],
        used_queries: List[str],
        min_high_relevance: int = 3,
        max_retries: int = 2,
    ) -> tuple:
        """
        Iteratively generate new queries and search until min_high_relevance
        papers are found or max_retries is exhausted.

        Returns (final_high_rel_papers: List[Dict], expansion_trace: List[Dict]).
        """
        high_rel = list(current_high_rel_papers)
        seen_titles = {p['title'].lower() for p in all_screened_papers}
        expansion_trace = []

        for attempt in range(max_retries):
            if len(high_rel) >= min_high_relevance:
                break

            print(
                f"\n  [Query Expansion] Attempt {attempt + 1}/{max_retries}: "
                f"{len(high_rel)} high-relevance papers found, need {min_high_relevance}."
            )

            coverage = self.coverage_check(high_rel, scenario_brief)
            gaps = coverage.get("gaps", [])

            new_queries = self.generate_expansion_queries(scenario_brief, used_queries, gaps)
            if not new_queries:
                print("  [Query Expansion] No new queries generated; stopping expansion.")
                break

            print(f"  [Query Expansion] New queries: {new_queries}")

            # Search with new queries
            new_raw: List[Dict] = []
            for q in new_queries:
                found = self.api_client.search_all(q, max_per_source=15)
                for p in found:
                    if p['title'].lower() not in seen_titles:
                        seen_titles.add(p['title'].lower())
                        new_raw.append(p)
            print(f"  [Query Expansion] Found {len(new_raw)} new unique papers.")

            new_screened = self._screen_relevance(new_raw, ["definitions", "behaviors", "measurement"]) if new_raw else []

            new_scored: List[Dict] = []
            for p in new_screened:
                score, dims, reason = self.compute_scenario_relevance_score(p, scenario_brief)
                p["scenario_relevance_score"] = score
                p["scenario_covered_dimensions"] = dims
                p["scenario_relevance_reason"] = reason
                new_scored.append(p)

            new_high_rel = self.high_relevance_filter(new_scored, threshold=4)
            high_rel.extend(new_high_rel)
            all_screened_papers.extend(new_screened)
            used_queries.extend(new_queries)

            expansion_trace.append({
                "attempt": attempt + 1,
                "new_queries": new_queries,
                "new_papers_searched": len(new_raw),
                "new_screened": len(new_screened),
                "new_high_relevance": len(new_high_rel),
                "total_high_relevance_after": len(high_rel),
                "coverage_gaps_targeted": gaps,
            })

        return high_rel, expansion_trace

    def extract_findings(self, papers: List[Dict]) -> List[Dict]:
        """
        Extract empathy-specific findings from paper abstracts.
        
        Args:
            papers: List of screened papers
            
        Returns:
            List of extracted findings
        """
        print("\n[Extracting key findings from abstracts...]")
        
        extraction_template = self.prompt_manager.get_agent_group_prompt(
            "literature_search_agent_group",
            "extraction_prompt"
        )
        
        findings = []
        
        for idx, paper in enumerate(papers[:50], 1):  # Extract from top 50 for comprehensive analysis
            try:
                title_short = paper.get('title', '')[:60]
                print(f"  Extracting [{idx}/{min(len(papers), 50)}]: {title_short}...", end=" ")
                sys.stdout.flush()
                
                prompt = extraction_template.format(
                    title=paper.get('title', ''),
                    abstract=paper.get('abstract', '')
                )
                
                response = self.llm.invoke(prompt)
                
                # Try to parse JSON from response
                content = response.content.strip()
                # Find JSON in response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    extracted = json.loads(json_match.group())
                    extracted['paper_title'] = paper.get('title')
                    extracted['paper_year'] = paper.get('year')
                    findings.append(extracted)
                    print("[OK]")
                    sys.stdout.flush()
                else:
                    print("[No findings]")
                    sys.stdout.flush()
            
            except Exception as e:
                print(f"[ERROR: {e}]")
                sys.stdout.flush()
                continue
        
        self.extracted_findings = findings
        print(f"\nExtraction complete: {len(findings)} findings extracted")
        sys.stdout.flush()
        return findings
    
    def download_pdfs(self, papers: List[Dict], run_id: str, categories: List[str] = None) -> List[Dict]:
        """
        Download PDFs organized by category.
        
        Args:
            papers: List of papers to download
            run_id: Current run ID
            categories: List of categories (definitions, behaviors, measurement)
            
        Returns:
            List of downloaded papers with paths
        """
        if categories is None:
            categories = ["definitions", "behaviors", "measurement"]
        
        print("\n[Downloading PDFs...]")
        
        downloaded = []
        
        for i, paper in enumerate(papers[:50], 1):  # Download up to 50 papers for comprehensive collection
            # Determine category (simple assignment for now)
            category = categories[i % len(categories)]
            
            # Create category-specific directory using absolute path from project root
            pdfs_dir = PROJECT_ROOT / f"data/runs/{run_id}/literature_search_agent_group/pdfs/{category}"
            pdfs_dir.mkdir(parents=True, exist_ok=True)
            
            title_short = paper['title'][:60]
            print(f"  [{i}/{min(len(papers), 50)}] {category}/{title_short}...")
            
            if paper.get('url'):
                year = paper.get('year') or 'unknown'
                filename = f"paper_{i:02d}_{year}.pdf"
                filepath = pdfs_dir / filename
                
                if download_pdf(paper['url'], str(filepath)):
                    paper['local_pdf_path'] = str(filepath)
                    paper['downloaded'] = True
                    paper['downloaded_at'] = datetime.now().isoformat()
                    paper['category'] = category
                    downloaded.append(paper)
                    print(f"    [OK] Downloaded")
                else:
                    paper['downloaded'] = False
                    print(f"    [FAIL] Failed")
            else:
                paper['downloaded'] = False
                print(f"    [FAIL] No URL")
        
        self.downloaded = downloaded
        print(f"\nDownload complete: {len(downloaded)} PDFs successfully downloaded")
        sys.stdout.flush()
        return downloaded
    
    def organize_results(self) -> Dict:
        """Organize findings into structured format for scale design."""
        print("\n[Organizing findings for scale design...]")
        
        organized = {
            "empathy_definitions": [],
            "empathic_behaviors": {
                "verbal": [],
                "nonverbal": [],
                "adaptive": []
            },
            "measurement_approaches": [],
            "existing_scales": []
        }
        
        # Organize extracted findings
        for finding in self.extracted_findings:
            # Add definitions
            if finding.get('empathy_definition'):
                organized['empathy_definitions'].append({
                    "definition": finding['empathy_definition'],
                    "source": finding['paper_title'],
                    "year": finding.get('paper_year')
                })
            
            # Add behaviors (simplified categorization)
            behaviors = finding.get('behaviors_identified', '')
            if behaviors:
                # Convert to string if list
                if isinstance(behaviors, list):
                    behaviors = ', '.join(str(b) for b in behaviors)
                if isinstance(behaviors, str) and behaviors.strip():
                    # Simple categorization based on keywords
                    behaviors_lower = behaviors.lower()
                    if any(kw in behaviors_lower for kw in ['speech', 'verbal', 'language', 'words']):
                        organized['empathic_behaviors']['verbal'].append(behaviors)
                    elif any(kw in behaviors_lower for kw in ['gesture', 'gaze', 'expression', 'face']):
                        organized['empathic_behaviors']['nonverbal'].append(behaviors)
                    else:
                        organized['empathic_behaviors']['adaptive'].append(behaviors)
            
            # Add measurement methods
            methods = finding.get('measurement_methods', '')
            if methods:
                organized['measurement_approaches'].append({
                    "method": methods,
                    "source": finding['paper_title']
                })
        
        return organized
    
    def search_and_download(self, run_id: str, interview_summary: Dict, scenario_brief: Dict = None) -> Dict:
        """
        Complete enhanced pipeline with intelligent search, screening, scenario scoring,
        query expansion, and extraction.

        Args:
            run_id: Current run ID
            interview_summary: Interview data from previous agent
            scenario_brief: Optional structured ScenarioBrief for high-relevance filtering.
                            When provided, enables scenario-specific scoring and query expansion.

        Returns:
            Dictionary with all results organized for scale design, plus gate artifacts.
        """
        MIN_HIGH_RELEVANCE = 3

        print("\n" + "=" * 70)
        print("ENHANCED LITERATURE SEARCH PIPELINE")
        print("=" * 70)

        # Step 1: Generate targeted queries
        print("\n[Step 1/5] Generating targeted search queries...")
        queries = self.generate_queries(interview_summary)
        for i, q in enumerate(queries, 1):
            print(f"  {i}. {q}")

        # Step 2: Search and screen (generic robot empathy relevance)
        print("\n[Step 2/5] Searching multiple databases and screening...")
        screened = self.search_and_screen(queries)

        # ----------------------------------------------------------------
        # Step 2.5: Scenario-specific relevance scoring (when scenario_brief is available)
        # ----------------------------------------------------------------
        scored_papers: List[Dict] = []
        high_relevance_papers: List[Dict] = []
        expansion_trace: List[Dict] = []
        coverage_report: Dict = {"coverage_score": None, "note": "No scenario_brief provided"}

        use_scenario_scoring = scenario_brief and scenario_brief.get("is_ready", False)

        if use_scenario_scoring:
            print(f"\n[Step 2.5] Scoring {len(screened)} screened papers against your scenario...")
            for idx, paper in enumerate(screened, 1):
                if idx == 1 or idx % 10 == 0 or idx == len(screened):
                    print(f"  Scoring [{idx}/{len(screened)}]...", end=" ", flush=True)
                score, dims, reason = self.compute_scenario_relevance_score(paper, scenario_brief)
                paper["scenario_relevance_score"] = score
                paper["scenario_covered_dimensions"] = dims
                paper["scenario_relevance_reason"] = reason
                scored_papers.append(paper)
                if idx == 1 or idx % 10 == 0 or idx == len(screened):
                    print(f"score={score}")

            high_relevance_papers = self.high_relevance_filter(scored_papers, threshold=4)
            print(f"\n  High-relevance papers (scenario score >= 4): {len(high_relevance_papers)}/{len(screened)}")

            # Step 2.6: Query expansion if high-relevance count is insufficient
            if len(high_relevance_papers) < MIN_HIGH_RELEVANCE:
                print(f"\n[Step 2.6] Query expansion (have {len(high_relevance_papers)}, need {MIN_HIGH_RELEVANCE})...")
                high_relevance_papers, expansion_trace = self.query_expansion_loop(
                    scenario_brief=scenario_brief,
                    current_high_rel_papers=high_relevance_papers,
                    all_screened_papers=screened,
                    used_queries=queries,
                    min_high_relevance=MIN_HIGH_RELEVANCE,
                )
                print(f"  After expansion: {len(high_relevance_papers)} high-relevance papers.")

            # Coverage check on final high-relevance set
            print("\n[Coverage Check] Analysing scenario dimension coverage...")
            coverage_report = self.coverage_check(high_relevance_papers, scenario_brief)
            print(f"  Coverage score: {coverage_report.get('coverage_score', 0):.2f}")
            if coverage_report.get("gaps"):
                print(f"  Gaps: {coverage_report['gaps']}")
        else:
            # Fallback: treat all screened papers as the high-relevance set
            scored_papers = screened
            high_relevance_papers = screened
            if scenario_brief and not scenario_brief.get("is_ready", False):
                print(
                    "\n  [WARNING] scenario_brief is incomplete "
                    f"(missing: {scenario_brief.get('missing_slots', [])}). "
                    "Skipping scenario-specific relevance scoring."
                )

        # ----------------------------------------------------------------
        # Step 3: Extract findings
        # ----------------------------------------------------------------
        print("\n[Step 3/5] Extracting empathy-specific findings...")
        findings = self.extract_findings(screened)

        # Step 4: Download PDFs
        print("\n[Step 4/5] Downloading PDFs by category...")
        downloaded = self.download_pdfs(screened, run_id)

        # Step 5: Organize results
        print("\n[Step 5/5] Organizing findings for scale design...")
        organized = self.organize_results()

        # Build gate report
        gate_report = {
            "timestamp": datetime.now().isoformat(),
            "scenario_scoring_enabled": use_scenario_scoring,
            "high_relevance_threshold": 4,
            "min_high_relevance_required": MIN_HIGH_RELEVANCE,
            "high_relevance_count": len(high_relevance_papers),
            "gate_passed": len(high_relevance_papers) >= MIN_HIGH_RELEVANCE,
            "coverage_report": coverage_report,
            "expansion_trace": expansion_trace,
            "total_papers_found": len(self.papers),
            "total_screened": len(screened),
            "total_scored": len(scored_papers),
        }

        # Compile final results
        results = {
            "search_queries": queries,
            "total_papers_found": len(self.papers),
            "screened_papers": len(screened),
            "extracted_findings": len(findings),
            "pdfs_downloaded": len(downloaded),
            "organized_findings": organized,
            "downloaded_papers": downloaded,
            "all_findings": findings,
            "high_relevance_papers": high_relevance_papers,
            "relevance_scored_papers": scored_papers,
            "gate_report": gate_report,
            "coverage_report": coverage_report,
        }

        print("\n" + "=" * 70)
        print("ENHANCED LITERATURE SEARCH COMPLETE")
        print(f"  Papers found:          {len(self.papers)}")
        print(f"  Screened (relevant):   {len(screened)}")
        print(f"  High-relevance:        {len(high_relevance_papers)}")
        print(f"  Gate passed:           {gate_report['gate_passed']}")
        print(f"  Coverage score:        {coverage_report.get('coverage_score', 'N/A')}")
        print(f"  Findings extracted:    {len(findings)}")
        print(f"  PDFs downloaded:       {len(downloaded)}")
        print(f"  Location: data/runs/{run_id}/literature_search_agent_group/")
        print("=" * 70)

        return results
