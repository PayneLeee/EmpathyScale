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
    
    def __init__(self, api_key: str, model_name: str = "gpt-4", prompts_dir: str = None):
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
    
    def search_and_download(self, run_id: str, interview_summary: Dict) -> Dict:
        """
        Complete enhanced pipeline with intelligent search, screening, and extraction.
        
        Args:
            run_id: Current run ID
            interview_summary: Interview data from previous agent
            
        Returns:
            Dictionary with all results organized for scale design
        """
        print("\n" + "=" * 70)
        print("ENHANCED LITERATURE SEARCH PIPELINE")
        print("=" * 70)
        
        # Step 1: Generate targeted queries
        print("\n[Step 1/5] Generating targeted search queries...")
        queries = self.generate_queries(interview_summary)
        for i, q in enumerate(queries, 1):
            print(f"  {i}. {q}")
        
        # Step 2: Search and screen
        print("\n[Step 2/5] Searching multiple databases and screening...")
        screened = self.search_and_screen(queries)
        
        # Step 3: Extract findings
        print("\n[Step 3/5] Extracting empathy-specific findings...")
        findings = self.extract_findings(screened)
        
        # Step 4: Download PDFs
        print("\n[Step 4/5] Downloading PDFs by category...")
        downloaded = self.download_pdfs(screened, run_id)
        
        # Step 5: Organize results
        print("\n[Step 5/5] Organizing findings for scale design...")
        organized = self.organize_results()
        
        # Compile final results
        results = {
            "search_queries": queries,
            "total_papers_found": len(self.papers),
            "screened_papers": len(screened),
            "extracted_findings": len(findings),
            "pdfs_downloaded": len(downloaded),
            "organized_findings": organized,
            "downloaded_papers": downloaded,
            "all_findings": findings
        }
        
        print("\n" + "=" * 70)
        print("ENHANCED LITERATURE SEARCH COMPLETE")
        print(f"  Papers found: {len(self.papers)}")
        print(f"  Screened (relevant): {len(screened)}")
        print(f"  Findings extracted: {len(findings)}")
        print(f"  PDFs downloaded: {len(downloaded)}")
        print(f"  Location: data/runs/{run_id}/literature_search_agent_group/")
        print("=" * 70)
        
        return results
