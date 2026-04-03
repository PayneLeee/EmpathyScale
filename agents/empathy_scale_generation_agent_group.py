"""
Empathy Scale Generation Agent Group
Combines interview summary, literature findings, and expert reference PDFs
to generate a structured empathy scale draft aligned with expert templates.
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Any

from langchain_openai import ChatOpenAI

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from prompt_manager import PromptManager

# Local agents
from scale_generation_agents import (
    ConstructDefinitionAgent,
    ItemGenerationAgent,
    ContentAssessmentAgent,
    retry_llm_call,
)


PROJECT_ROOT = Path(__file__).parent.parent.resolve()


class EmpathyScaleGenerationAgentGroup:
    """Agent group that generates an empathy scale draft for expert review."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gpt-4o-mini",
        prompts_dir: str = None,
        num_item_generators: int = 3,
        enable_content_assessment: bool = True,
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.llm = ChatOpenAI(api_key=api_key, model_name=model_name)
        self.prompt_manager = PromptManager(prompts_dir)
        self.num_item_generators = num_item_generators
        self.enable_content_assessment = enable_content_assessment

    def _load_interview_summary(self, run_id: str) -> Dict[str, Any]:
        path = PROJECT_ROOT / f"data/runs/{run_id}/interview_agent_group/summary.json"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _load_literature_summary(self, run_id: str) -> Dict[str, Any]:
        path = PROJECT_ROOT / f"data/runs/{run_id}/literature_search_agent_group/summary.json"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _load_high_relevance_papers(self, run_id: str) -> List[Dict[str, Any]]:
        """Load scenario-scored papers and return those with score >= 4."""
        path = PROJECT_ROOT / f"data/runs/{run_id}/literature_search_agent_group/relevance_scored_papers.json"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                all_papers = json.load(f)
            return [p for p in all_papers if p.get("scenario_relevance_score", 0) >= 4]
        return []

    def _check_evidence_coverage(
        self, dimensions: List[Dict[str, str]], high_rel_papers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Check whether each dimension has at least one supporting high-relevance paper.

        Matching is keyword-based: a paper is considered evidence for a dimension if
        its title or abstract contains any significant word from the dimension name.

        Returns a coverage dict with per-dimension evidence lists and a flag
        indicating whether supplemental research is needed.
        """
        coverage: Dict[str, Any] = {"dimensions": {}, "needs_more_research": False}

        for dim in dimensions:
            dim_name = dim.get("name") or dim.get("dimension") or "Unknown"
            # Build keyword set from dimension name (ignore short/common words)
            keywords = {
                w.lower() for w in re.split(r'[\s\-_/]+', dim_name)
                if len(w) > 3
            }
            supporting: List[str] = []
            for paper in high_rel_papers:
                text = (paper.get("title", "") + " " + paper.get("abstract", "")).lower()
                if any(kw in text for kw in keywords):
                    supporting.append(paper.get("title", "Unknown"))
            coverage["dimensions"][dim_name] = {
                "supporting_paper_count": len(supporting),
                "supporting_papers": supporting[:5],
                "has_evidence": len(supporting) > 0,
            }
            if len(supporting) == 0:
                coverage["needs_more_research"] = True

        covered = sum(
            1 for d in coverage["dimensions"].values() if d["has_evidence"]
        )
        total = len(dimensions) or 1
        coverage["evidence_coverage_score"] = round(covered / total, 2)
        return coverage

    def _build_evidence_section(
        self, high_rel_papers: List[Dict[str, Any]], evidence_coverage: Dict[str, Any]
    ) -> str:
        """Build a markdown Evidence Base section for the scale draft."""
        lines = ["## Evidence Base", ""]

        if not high_rel_papers:
            lines.append(
                "_No scenario-specific high-relevance papers were found. "
                "Scale items are grounded in expert reference PDFs only. "
                "Consider re-running with a more specific scenario description._"
            )
            lines.append("")
            return "\n".join(lines)

        lines.append(
            f"This scale is supported by **{len(high_rel_papers)} high-relevance papers** "
            f"(scenario relevance score ≥ 4/5)."
        )
        lines.append("")
        lines.append("### Supporting Papers")
        for paper in high_rel_papers:
            title = paper.get("title", "Unknown title")
            year = paper.get("year", "")
            score = paper.get("scenario_relevance_score", "—")
            dims = ", ".join(paper.get("scenario_covered_dimensions", []))
            reason = paper.get("scenario_relevance_reason", "")
            lines.append(f"- **{title}** ({year}) — scenario score: {score}/5 | dims: [{dims}]")
            if reason:
                lines.append(f"  _{reason}_")
        lines.append("")

        lines.append("### Evidence Coverage by Dimension")
        for dim_name, info in evidence_coverage.get("dimensions", {}).items():
            status = "✓" if info["has_evidence"] else "✗ NO EVIDENCE"
            count = info["supporting_paper_count"]
            lines.append(f"- **{dim_name}**: {status} ({count} supporting papers)")
        lines.append("")

        if evidence_coverage.get("needs_more_research"):
            lines.append(
                "> **Note**: One or more dimensions lack direct paper support. "
                "Running additional literature search passes is recommended."
            )
            lines.append("")

        return "\n".join(lines)

    def _list_expert_pdfs(self) -> List[str]:
        expert_dir = PROJECT_ROOT / "agents" / "expert_pdfs"
        if not expert_dir.exists():
            return []
        return [str(p.name) for p in expert_dir.glob("*.pdf")]

    def _build_generation_prompt(self, interview: Dict[str, Any], literature: Dict[str, Any], expert_pdfs: List[str]) -> str:
        template = self.prompt_manager.get_agent_group_prompt(
            "empathy_scale_generation_agent_group",
            "generation_prompt"
        )

        context = {
            "assessment_context": interview.get("assessment_context", ""),
            "robot_platform": interview.get("robot_platform", ""),
            "interaction_modalities": interview.get("interaction_modalities", ""),
            "collaboration_pattern": interview.get("collaboration_pattern", ""),
            "environmental_setting": interview.get("environmental_setting", ""),
            "assessment_goals": ", ".join(interview.get("assessment_goals", [])),
            "expected_empathy_forms": ", ".join(interview.get("expected_empathy_forms", [])),
            "measurement_requirements": ", ".join(interview.get("measurement_requirements", [])),
        }

        lit_findings = literature.get("organized_findings") or {}
        downloaded = literature.get("downloaded_papers", [])
        # Create detailed reference list with authors if available
        # Use ALL downloaded papers, not just a subset
        downloaded_brief = []
        downloaded_detailed = []
        for item in downloaded:  # Include all downloaded papers
            year = item.get('year', '')
            title = item.get('title', '')
            category = item.get('category', '')
            authors = item.get('authors', [])
            
            # Brief format for main prompt
            brief = f"{year}: {title} ({category})"
            downloaded_brief.append(brief)
            
            # Detailed format with authors for reference
            if authors:
                author_str = ", ".join(authors[:5])  # Limit to first 5 authors
                if len(authors) > 5:
                    author_str += " et al."
                detailed = f"{author_str} ({year}). {title}"
            else:
                detailed = f"{title} ({year})"
            downloaded_detailed.append({"brief": brief, "detailed": detailed, "category": category})

        # Format detailed references for prompt
        literature_detailed_refs = "\n".join([ref["detailed"] for ref in downloaded_detailed])
        
        prompt = template.format(
            assessment_context=context["assessment_context"],
            robot_platform=context["robot_platform"],
            interaction_modalities=context["interaction_modalities"],
            collaboration_pattern=context["collaboration_pattern"],
            environmental_setting=context["environmental_setting"],
            assessment_goals=context["assessment_goals"],
            expected_empathy_forms=context["expected_empathy_forms"],
            measurement_requirements=context["measurement_requirements"],
            literature_overview=json.dumps(lit_findings, ensure_ascii=False, indent=2),
            literature_samples="\n".join(downloaded_brief),
            literature_references=literature_detailed_refs,
            expert_pdf_names=", ".join(expert_pdfs) if expert_pdfs else "",
        )
        return prompt

    def generate_scale(self, run_id: str) -> Dict[str, Any]:
        """Generate the empathy scale draft and save outputs under the run directory."""
        interview = self._load_interview_summary(run_id)
        literature = self._load_literature_summary(run_id)
        expert_pdfs = self._list_expert_pdfs()
        high_relevance_papers = self._load_high_relevance_papers(run_id)

        # Step 1: construct definition
        print("    [LLM Call] Defining empathy constructs...", flush=True)
        constructs = self._run_construct_definition(interview)
        print(f"    [OK] Constructs defined: {len(self._extract_dimensions(constructs.get('raw', '')))} dimensions", flush=True)

        # Step 2: multi-generator candidates
        print(f"    [LLM Call] Generating items with {self.num_item_generators} parallel generator(s)...", flush=True)
        candidates = self._run_multi_item_generation(constructs, interview)
        # Calculate total number of items across all dimensions
        total_items = sum(len(block.get("items", [])) for block in candidates)
        print(f"    [OK] Generated {total_items} candidate items across {len(candidates)} dimensions", flush=True)

        # Step 3: content assessment (optional)
        if self.enable_content_assessment:
            print("    [LLM Call] Running content assessment and refinement...", flush=True)
            refined = self._run_content_assessment(candidates, interview)
            total_refined = sum(len(block.get("items", [])) for block in refined)
            print(f"    [OK] Refined to {total_refined} items across {len(refined)} dimensions", flush=True)
        else:
            refined = candidates
            print("    [SKIP] Content assessment disabled", flush=True)

        # Step 3.5a: Evidence coverage check
        if self.enable_content_assessment:
            print("    [Evidence] Checking literature evidence coverage per dimension...", flush=True)
            dimensions_meta = [{"name": blk.get("dimension", "Unknown")} for blk in refined]
            evidence_coverage = self._check_evidence_coverage(dimensions_meta, high_relevance_papers)
            print(
                f"    [Evidence] Coverage score: {evidence_coverage['evidence_coverage_score']:.2f} | "
                f"needs_more_research: {evidence_coverage['needs_more_research']}",
                flush=True,
            )
        else:
            dimensions_meta = [{"name": blk.get("dimension", "Unknown")} for blk in refined]
            evidence_coverage = self._check_evidence_coverage(dimensions_meta, high_relevance_papers)

        # Step 3.5: Semantic deduplication (remove semantically similar items before evaluation)
        print("    [Semantic Dedup] Removing semantically similar items...", flush=True)
        try:
            from utils.pre_evaluation_semantic_deduplication import remove_semantic_duplicates_before_evaluation
            
            # Flatten refined items for deduplication
            all_items = []
            for block in refined:
                dim = block.get("dimension") or "Unknown"
                for item_text in block.get("items", []):
                    all_items.append({"dimension": dim, "item_text": item_text})
            
            if all_items:
                filtered_items, dedup_stats = remove_semantic_duplicates_before_evaluation(
                    all_items,
                    similarity_threshold=0.80,  # Same-dimension threshold
                    cross_dimension_threshold=0.75,  # Stricter threshold for cross-dimension (ensure dimension distinction)
                    use_sentence_transformers=True
                )
                
                # Re-group by dimension
                refined_by_dim = {}
                for item in filtered_items:
                    dim = item.get("dimension", "Unknown")
                    if dim not in refined_by_dim:
                        refined_by_dim[dim] = []
                    refined_by_dim[dim].append(item.get("item_text", ""))
                
                refined = [{"dimension": dim, "items": items} for dim, items in refined_by_dim.items()]
                
                total_after_dedup = sum(len(block.get("items", [])) for block in refined)
                print(f"    [OK] After semantic deduplication: {total_after_dedup} items (removed {dedup_stats['n_removed']} semantic duplicates)", flush=True)
                
                # Save deduplication stats
                out_dir = PROJECT_ROOT / f"data/runs/{run_id}/empathy_scale_generation_agent_group"
                out_dir.mkdir(parents=True, exist_ok=True)
                dedup_stats_path = out_dir / "semantic_deduplication_stats.json"
                with open(dedup_stats_path, 'w', encoding='utf-8') as f:
                    json.dump(dedup_stats, f, indent=2, ensure_ascii=False)
            else:
                print("    [WARN] No items to deduplicate", flush=True)
        except ImportError as e:
            print(f"    [WARN] Semantic deduplication not available ({e}), skipping...", flush=True)
        except Exception as e:
            print(f"    [WARN] Semantic deduplication failed: {e}, continuing without it...", flush=True)
            import traceback
            traceback.print_exc()

        # Step 4: assemble markdown (with evidence section)
        print("    [Assembling] Creating scale draft markdown...", flush=True)
        scale_markdown = self._assemble_markdown(
            interview, literature, refined, expert_pdfs,
            high_relevance_papers=high_relevance_papers,
            evidence_coverage=evidence_coverage,
        )

        # Save artifacts
        out_dir = PROJECT_ROOT / f"data/runs/{run_id}/empathy_scale_generation_agent_group"
        out_dir.mkdir(parents=True, exist_ok=True)
        draft_path = out_dir / "scale_draft.md"
        with open(draft_path, 'w', encoding='utf-8') as f:
            f.write(scale_markdown)

        summary = {
            "status": "completed",
            "used_expert_pdfs": expert_pdfs,
            "evidence_coverage": evidence_coverage,
            "needs_more_research": evidence_coverage.get("needs_more_research", False),
            "high_relevance_paper_count": len(high_relevance_papers),
            "inputs": {
                "interview_fields_present": [k for k, v in interview.items() if v],
                "literature_keys_present": list(literature.keys()),
            },
            "outputs": {
                "draft_path": str(draft_path),
            },
        }
        with open(out_dir / "summary.json", 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        return {
            "scale_draft_path": str(draft_path),
            "summary": summary,
            "needs_more_research": evidence_coverage.get("needs_more_research", False),
            "evidence_coverage": evidence_coverage,
        }

    # ---------- New sub-steps ----------
    def _run_construct_definition(self, interview: Dict[str, Any]) -> Dict[str, Any]:
        agent = ConstructDefinitionAgent(api_key=self.api_key, prompts_dir=self.prompt_manager.prompts_dir)
        return agent.define_constructs(interview)

    def _run_multi_item_generation(self, constructs: Dict[str, Any], scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Expect constructs["raw"] to contain LLM JSON-ish; fallback to single default dimension
        dimensions = self._extract_dimensions(constructs.get("raw"))
        if not dimensions:
            dimensions = [{"name": "Empathy", "description": "Perceived empathy in this scenario"}]

        gens = [
            ItemGenerationAgent(api_key=self.api_key, prompts_dir=self.prompt_manager.prompts_dir)
            for _ in range(self.num_item_generators)
        ]
        results = []
        import time
        for idx, g in enumerate(gens):
            # Add small delay between sequential calls to avoid rate limiting
            # Even though calls are sequential, rapid successive calls can trigger rate limits
            if idx > 0:
                time.sleep(1)  # 1 second delay between calls
            print(f"    [Generator {idx + 1}/{self.num_item_generators}] Generating items...", flush=True)
            results.append(g.generate_items(dimensions, scenario))
        return self._merge_item_candidates(results)

    def _run_content_assessment(self, candidates: List[Dict[str, Any]], scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
        agent = ContentAssessmentAgent(api_key=self.api_key, prompts_dir=self.prompt_manager.prompts_dir)
        refined = agent.refine(candidates, scenario)
        return self._parse_items_from_raw(refined.get("raw"))

    def _assemble_markdown(
        self, interview, literature, items, expert_pdfs,
        high_relevance_papers: List[Dict[str, Any]] = None,
        evidence_coverage: Dict[str, Any] = None,
    ) -> str:
        """
        Assemble markdown directly from items without LLM selection.
        This ensures all items are included in the final draft.
        """
        # Build context information
        context_lines = [
            f"assessment_context: {interview.get('assessment_context', '')}",
            f"robot_platform: {interview.get('robot_platform', '')}",
            f"interaction_modalities: {interview.get('interaction_modalities', '')}",
            f"collaboration_pattern: {interview.get('collaboration_pattern', '')}",
            f"environmental_setting: {interview.get('environmental_setting', '')}",
        ]
        
        # Build markdown directly from items
        md_lines = ["# Empathy Scale (Draft)", ""]
        md_lines.append("## Purpose and Context")
        md_lines.append(f"This empathy scale is designed to assess perceived empathy in the context: {interview.get('assessment_context', 'N/A')}.")
        md_lines.append("")
        md_lines.append("## Structure")
        
        # Collect dimensions
        dimensions = {}
        for block in items:
            dim = block.get("dimension") or block.get("name") or "Unknown"
            if dim not in dimensions:
                dimensions[dim] = []
            dimensions[dim].extend(block.get("items", []))
        
        dim_list = "、".join([f"**{d}**" for d in dimensions.keys()])
        md_lines.append(f"- **Dimensions/Subscales**: {dim_list}")
        md_lines.append("- **Response Format**: 5-point Likert scale (1 = Strongly Disagree, 5 = Strongly Agree)")
        md_lines.append("- **Administration Notes**: Participants rate items based on their interaction experience.")
        md_lines.append("")
        md_lines.append("## Items by Dimension")
        md_lines.append("")
        
        # Add items by dimension
        item_num = 1
        for dim, dim_items in dimensions.items():
            md_lines.append(f"### {dim}")
            for item_text in dim_items:
                md_lines.append(f"- Item {item_num}: {item_text}")
                item_num += 1
            md_lines.append("")
        
        md_lines.append("## Scoring")
        md_lines.append("Items will be scored on a Likert scale from 1 to 5. Subscale totals can be calculated by summing items within each dimension.")
        md_lines.append("")

        # Append evidence base section when available
        if high_relevance_papers is not None or evidence_coverage is not None:
            evidence_section = self._build_evidence_section(
                high_relevance_papers or [],
                evidence_coverage or {},
            )
            md_lines.append(evidence_section)

        return "\n".join(md_lines)

    # ---------- Helpers ----------
    def _extract_dimensions(self, raw: str) -> List[Dict[str, str]]:
        if not raw:
            return []
        try:
            data = json.loads(self._extract_json(raw))
            return data.get("dimensions") or []
        except Exception:
            # fallback: simple regex for lines like "- Name: desc"
            dims = []
            for line in raw.splitlines():
                if line.strip().startswith("-"):
                    parts = line.strip("- ").split(":", 1)
                    if parts:
                        dims.append({"name": parts[0].strip(), "description": parts[1].strip() if len(parts) > 1 else ""})
            return dims

    def _merge_item_candidates(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge item candidates from multiple generators.
        Uses set() for exact duplicate removal only - preserves all unique items.
        """
        merged = {}
        for res in results:
            blocks = self._parse_items_from_raw(res.get("raw"))
            for blk in blocks:
                dim = blk.get("dimension") or "Unknown"
                # Normalize dimension name for consistent grouping
                dim_normalized = dim.strip()
                merged.setdefault(dim_normalized, set())
                for it in blk.get("items", []):
                    # Only remove exact duplicates (case-insensitive, whitespace-normalized)
                    it_normalized = " ".join(it.strip().split())
                    merged[dim_normalized].add(it_normalized)
        # Return as list preserving all unique items
        return [{"dimension": d, "items": list(v)} for d, v in merged.items()]

    def _parse_items_from_raw(self, raw: str) -> List[Dict[str, Any]]:
        if not raw:
            return []
        # Try JSON first
        try:
            data = json.loads(self._extract_json(raw))
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "items" in data:
                return [data]
        except Exception:
            pass
        # Fallback: parse lines "- item"
        blocks = []
        current = {"dimension": "Unknown", "items": []}
        for line in raw.splitlines():
            line = line.strip()
            if line.lower().startswith("dimension"):
                if current["items"]:
                    blocks.append(current)
                current = {"dimension": line.split(":", 1)[-1].strip() or "Unknown", "items": []}
            elif line.startswith("- "):
                current["items"].append(line[2:].strip())
        if current["items"]:
            blocks.append(current)
        return blocks

    def _extract_json(self, text: str) -> str:
        match = re.search(r"\{.*\}|\[.*\]", text, re.DOTALL)
        return match.group() if match else text

    @staticmethod
    def parse_scale_markdown(md_text: str) -> List[Dict[str, str]]:
        """Extract items from a scale draft markdown."""
        items = []
        current_dim = None
        for line in md_text.splitlines():
            # Match dimension headers like "### Safety Awareness" or "## Dimension: Safety Awareness"
            dim_match = re.match(r"^###\s+(.+)$", line.strip())
            if dim_match:
                current_dim = dim_match.group(1).strip()
            # Match items like "- Item 1: The robot..." or "* Item 2: ..."
            item_match = re.match(r"^[-*]\s*Item\s+\d+:\s*(.+)$", line.strip(), re.IGNORECASE)
            if item_match:
                items.append({
                    "dimension": current_dim or "Unknown",
                    "item_text": item_match.group(1).strip()
                })
        return items


