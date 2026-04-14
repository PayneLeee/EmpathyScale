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

try:
    from workflow_console import sub, sub_done, minor_separator, print_json_panel
except ImportError:
    def sub(msg, indent=2):
        print(f"{' ' * indent}▸ {msg}", flush=True)

    def sub_done(msg, indent=2):
        print(f"{' ' * indent}✓ {msg}", flush=True)

    def minor_separator(label=None):
        if label:
            print(f"  --- {label} ---", flush=True)
        else:
            print("  " + "·" * 60, flush=True)

    def print_json_panel(title, obj, max_chars=None):
        print(f"\n[{title}]\n{obj}\n")

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
        
        minor_separator("多库检索（原始命中，去重前）")
        sub(f"共 {len(queries)} 条查询；每源最多 20 条/查询")

        all_papers = []

        for i, query in enumerate(queries, 1):
            sub(f"检索 [{i}/{len(queries)}] 查询语句: {query}")
            papers = self.api_client.search_all(query, max_per_source=20)
            all_papers.extend(papers)
            sub_done(f"本查询命中 {len(papers)} 条（累计原始 {len(all_papers)} 条）")
            for j, p in enumerate(papers[:5], 1):
                t = (p.get("title") or "")[:76]
                src = p.get("source") or p.get("venue") or ""
                sub(f"样例{j}: [{src}] {t}{'…' if len(p.get('title') or '') > 76 else ''}", indent=6)
            if len(papers) > 5:
                sub(f"… 另有 {len(papers) - 5} 条本查询命中（略）", indent=6)

        sub("按标题去重 …")
        unique_papers = []
        seen_titles = set()
        for paper in all_papers:
            title_lower = paper["title"].lower()
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                unique_papers.append(paper)

        self.papers = unique_papers
        sub_done(f"去重后唯一论文 {len(unique_papers)} 篇（将进入 LLM 初筛，最多评 80 篇）")

        minor_separator("LLM 初筛循环（通用机器人共情/量表相关度 1–5，≥3 保留）")
        screened = self._screen_relevance(unique_papers, focus_areas, screening_label="初筛")
        
        self.screened_papers = screened
        return screened
    
    def _screen_relevance(
        self,
        papers: List[Dict],
        focus_areas: List[str],
        screening_label: str = "初筛",
    ) -> List[Dict]:
        """Screen papers for relevance using LLM; prints every paper for demo visibility."""
        screened = []

        screening_prompt_template = self.prompt_manager.get_agent_group_prompt(
            "literature_search_agent_group",
            "relevance_screening_prompt"
        )

        total = min(len(papers), 80)
        sub(f"{screening_label}：逐篇调用 LLM 打分（共 {total} 篇）…")

        for idx, paper in enumerate(papers[:80], 1):
            try:
                title_full = paper.get("title", "") or ""
                title_disp = (title_full[:72] + "…") if len(title_full) > 72 else title_full

                prompt = screening_prompt_template.format(
                    title=paper.get("title", ""),
                    abstract=paper.get("abstract", "")[:500],
                    focus=focus_areas[0] if focus_areas else "definitions",
                )

                response = self.llm.invoke(prompt)

                score = 3
                if "SCORE:" in response.content:
                    match = re.search(r"SCORE:\s*(\d+)", response.content)
                    if match:
                        score = int(match.group(1))

                reason = "Relevance assessment"
                if "REASON:" in response.content:
                    match = re.search(r"REASON:\s*(.+)", response.content, re.DOTALL)
                    if match:
                        reason = match.group(1).strip()

                kept = score >= 3
                if kept:
                    paper["relevance_score"] = score
                    paper["relevance_reason"] = reason
                    screened.append(paper)

            except Exception as e:
                continue

        sub_done(f"{screening_label}完成：保留 {len(screened)}/{total} 篇（阈值 ≥3）")
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

            coverage = self.coverage_check(high_rel, scenario_brief)
            gaps = coverage.get("gaps", [])

            new_queries = self.generate_expansion_queries(scenario_brief, used_queries, gaps)
            if not new_queries:
                sub("补检索：未能生成新查询，结束扩展。")
                break

            sub(f"补检索：新查询 {len(new_queries)} 条 → {new_queries}")

            lbl = f"补检·第{attempt + 1}轮"
            new_raw: List[Dict] = []
            for q in new_queries:
                found = self.api_client.search_all(q, max_per_source=15)
                for p in found:
                    if p['title'].lower() not in seen_titles:
                        seen_titles.add(p['title'].lower())
                        new_raw.append(p)
            sub_done(f"补检索：去重后新论文 {len(new_raw)} 篇，进入「{lbl}」")
            new_screened = (
                self._screen_relevance(new_raw, ["definitions", "behaviors", "measurement"], screening_label=lbl)
                if new_raw
                else []
            )

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
        minor_separator("摘要抽取循环（每篇 LLM → JSON：定义/行为/测量…）")
        sub(f"将对初筛保留列表中前 {min(len(papers), 50)} 篇逐篇抽取")

        extraction_template = self.prompt_manager.get_agent_group_prompt(
            "literature_search_agent_group",
            "extraction_prompt"
        )

        findings = []

        for idx, paper in enumerate(papers[:50], 1):
            try:
                title_short = (paper.get("title", "") or "")[:62]
                prompt = extraction_template.format(
                    title=paper.get("title", ""),
                    abstract=paper.get("abstract", ""),
                )

                response = self.llm.invoke(prompt)

                content = response.content.strip()
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    extracted = json.loads(json_match.group())
                    extracted["paper_title"] = paper.get("title")
                    extracted["paper_year"] = paper.get("year")
                    findings.append(extracted)
                    def_snip = (extracted.get("empathy_definition") or "")[:90]
                    if len(def_snip) == 90:
                        def_snip += "…"
                    beh = extracted.get("behaviors_identified")
                    beh_one = ""
                    if isinstance(beh, str) and beh.strip():
                        beh_one = beh.strip()[:70] + ("…" if len(beh.strip()) > 70 else "")
                    elif isinstance(beh, list) and beh:
                        beh_one = str(beh[0])[:70]
                    meth = str(extracted.get("measurement_methods") or "")[:70]
                else:
                    findings.append(None)

            except Exception as e:
                findings.append(None)

        findings = [f for f in findings if f is not None]
        self.extracted_findings = findings
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
        
        minor_separator("PDF 下载循环（按 definitions / behaviors / measurement 轮转分类）")
        sub(f"最多尝试下载前 {min(len(papers), 50)} 篇初筛保留论文")

        downloaded = []
        
        for i, paper in enumerate(papers[:50], 1):  # Download up to 50 papers for comprehensive collection
            # Determine category (simple assignment for now)
            category = categories[i % len(categories)]
            
            # Create category-specific directory using absolute path from project root
            pdfs_dir = PROJECT_ROOT / f"data/runs/{run_id}/literature_search_agent_group/pdfs/{category}"
            pdfs_dir.mkdir(parents=True, exist_ok=True)
            
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
                else:
                    paper['downloaded'] = False
            else:
                paper['downloaded'] = False
        
        self.downloaded = downloaded
        return downloaded
    
    def organize_results(self) -> Dict:
        
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

        minor_separator("Boateng Step 1b — 子过程")
        lit_input_preview = {
            k: interview_summary.get(k)
            for k in (
                "assessment_context",
                "robot_platform",
                "interaction_modalities",
                "collaboration_pattern",
                "environmental_setting",
                "assessment_goals",
                "expected_empathy_forms",
                "measurement_requirements",
            )
        }
        print_json_panel("文献检索输入 · 访谈关键字段（JSON）", lit_input_preview, max_chars=10000)

        sub("1b-i  基于访谈摘要生成检索查询（LLM）")
        queries = self.generate_queries(interview_summary)
        sub_done(f"已生成 {len(queries)} 条查询")

        sub("1b-ii 多源检索（arXiv / Semantic Scholar）与相关性初筛（LLM 1–5 分，≥3 保留）")
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
            sub(
                f"1b-iii 场景相关二次打分（对 {len(screened)} 篇初筛保留论文逐篇 LLM；"
                "SCENARIO_SCORE 1–5，≥4 记为高相关）"
            )
            for idx, paper in enumerate(screened, 1):
                title_full = paper.get("title", "") or ""
                title_disp = (title_full[:68] + "…") if len(title_full) > 68 else title_full
                score, dims, reason = self.compute_scenario_relevance_score(paper, scenario_brief)
                paper["scenario_relevance_score"] = score
                paper["scenario_covered_dimensions"] = dims
                paper["scenario_relevance_reason"] = reason
                scored_papers.append(paper)

            high_relevance_papers = self.high_relevance_filter(scored_papers, threshold=4)
            sub_done(f"高相关论文 {len(high_relevance_papers)} / {len(screened)}")

            if len(high_relevance_papers) < MIN_HIGH_RELEVANCE:
                sub(f"1b-iv  补检索循环（当前 {len(high_relevance_papers)} 篇，目标 ≥ {MIN_HIGH_RELEVANCE}）")
                high_relevance_papers, expansion_trace = self.query_expansion_loop(
                    scenario_brief=scenario_brief,
                    current_high_rel_papers=high_relevance_papers,
                    all_screened_papers=screened,
                    used_queries=queries,
                    min_high_relevance=MIN_HIGH_RELEVANCE,
                )
                sub_done(f"补检索结束：高相关论文共 {len(high_relevance_papers)} 篇")

            sub("1b-v   覆盖度检查（模态 / 用户群 / 测量 / 场景 四维）")
            coverage_report = self.coverage_check(high_relevance_papers, scenario_brief)
            sub_done(f"coverage_score = {coverage_report.get('coverage_score', 0):.2f}")
            if coverage_report.get("gaps"):
                sub(f"覆盖缺口: {coverage_report['gaps']}")
            print_json_panel("场景覆盖度报告 coverage_report（完整 JSON）", coverage_report, max_chars=8000)
        else:
            # Fallback: treat all screened papers as the high-relevance set
            scored_papers = screened
            high_relevance_papers = screened
            if scenario_brief and not scenario_brief.get("is_ready", False):
                sub(
                    "警告：scenario_brief 不完整，跳过场景相关打分；"
                    f"缺失: {scenario_brief.get('missing_slots', [])}"
                )

        sub("1b-vi 从摘要抽取结构化发现（定义 / 行为 / 测量方法）")
        findings = self.extract_findings(screened)

        sub("1b-vii 按类别下载 PDF（definitions / behaviors / measurement）")
        downloaded = self.download_pdfs(screened, run_id)

        sub("1b-viii 归纳 organized_findings 供量表生成使用")
        organized = self.organize_results()
        sub_done("文献管线子步骤全部完成")

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

        minor_separator("Step 1b 统计摘要")
        sub(f"检索命中论文数: {len(self.papers)}")
        sub(f"初筛保留: {len(screened)}")
        sub(f"场景高相关: {len(high_relevance_papers)} | 门控通过: {gate_report['gate_passed']}")
        sub(f"抽取发现条数: {len(findings)} | PDF 下载成功: {len(downloaded)}")
        sub_done(f"数据目录 data/runs/{run_id}/literature_search_agent_group/")

        org_preview = {
            "empathy_definitions_n": len(organized.get("empathy_definitions") or []),
            "empathy_definitions_sample": (organized.get("empathy_definitions") or [])[:2],
            "measurement_approaches_n": len(organized.get("measurement_approaches") or []),
            "measurement_sample": (organized.get("measurement_approaches") or [])[:2],
            "behaviors_verbal_n": len((organized.get("empathic_behaviors") or {}).get("verbal") or []),
            "behaviors_nonverbal_n": len((organized.get("empathic_behaviors") or {}).get("nonverbal") or []),
            "behaviors_adaptive_n": len((organized.get("empathic_behaviors") or {}).get("adaptive") or []),
        }
        print_json_panel("文献归纳 organized_findings（终端节选，完整在内存/下游提示词）", org_preview, max_chars=10000)

        print_json_panel(
            "文献门控与补检索轨迹 gate_report（JSON）",
            {
                "gate_passed": gate_report.get("gate_passed"),
                "high_relevance_count": gate_report.get("high_relevance_count"),
                "scenario_scoring_enabled": gate_report.get("scenario_scoring_enabled"),
                "expansion_trace": gate_report.get("expansion_trace"),
                "totals": {
                    "papers_unique": gate_report.get("total_papers_found"),
                    "screened_kept": gate_report.get("total_screened"),
                    "scenario_scored": gate_report.get("total_scored"),
                },
            },
            max_chars=12000,
        )

        return results
