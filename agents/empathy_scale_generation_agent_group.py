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

        # Step 1: construct definition
        print("    [LLM Call] Defining empathy constructs...")
        constructs = self._run_construct_definition(interview)
        print(f"    [OK] Constructs defined: {len(self._extract_dimensions(constructs.get('raw', '')))} dimensions")

        # Step 2: multi-generator candidates
        print(f"    [LLM Call] Generating items with {self.num_item_generators} parallel generator(s)...")
        candidates = self._run_multi_item_generation(constructs, interview)
        print(f"    [OK] Generated {len(candidates)} candidate items")

        # Step 3: content assessment (optional)
        if self.enable_content_assessment:
            print("    [LLM Call] Running content assessment and refinement...")
            refined = self._run_content_assessment(candidates, interview)
            print(f"    [OK] Refined to {len(refined)} items")
        else:
            refined = candidates
            print("    [SKIP] Content assessment disabled")

        # Step 4: assemble markdown
        print("    [Assembling] Creating scale draft markdown...")
        scale_markdown = self._assemble_markdown(interview, literature, refined, expert_pdfs)

        # Save artifacts
        out_dir = PROJECT_ROOT / f"data/runs/{run_id}/empathy_scale_generation_agent_group"
        out_dir.mkdir(parents=True, exist_ok=True)
        draft_path = out_dir / "scale_draft.md"
        with open(draft_path, 'w', encoding='utf-8') as f:
            f.write(scale_markdown)

        summary = {
            "status": "completed",
            "used_expert_pdfs": expert_pdfs,
            "inputs": {
                "interview_fields_present": [k for k, v in interview.items() if v],
                "literature_keys_present": list(literature.keys()),
            },
            "outputs": {
                "draft_path": str(draft_path),
            }
        }
        with open(out_dir / "summary.json", 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        return {
            "scale_draft_path": str(draft_path),
            "summary": summary,
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
        for g in gens:
            results.append(g.generate_items(dimensions, scenario))
        return self._merge_item_candidates(results)

    def _run_content_assessment(self, candidates: List[Dict[str, Any]], scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
        agent = ContentAssessmentAgent(api_key=self.api_key, prompts_dir=self.prompt_manager.prompts_dir)
        refined = agent.refine(candidates, scenario)
        return self._parse_items_from_raw(refined.get("raw"))

    def _assemble_markdown(self, interview, literature, items, expert_pdfs) -> str:
        system_prompt = self.prompt_manager.get_agent_group_prompt(
            "empathy_scale_generation_agent_group", "system_prompt"
        )
        main_prompt = self._build_generation_prompt(interview, literature, expert_pdfs)
        # Append item list as context hint
        if items:
            item_lines = []
            for block in items:
                dim = block.get("dimension") or block.get("name") or "Dimension"
                for it in block.get("items", []):
                    item_lines.append(f"- {dim}: {it}")
            main_prompt += "\n\nPreselected items:\n" + "\n".join(item_lines)

        prompt = f"{system_prompt}\n\n{main_prompt}"
        response = retry_llm_call(lambda: self.llm.invoke(prompt))
        return response.content.strip()

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
        merged = {}
        for res in results:
            blocks = self._parse_items_from_raw(res.get("raw"))
            for blk in blocks:
                dim = blk.get("dimension") or "Unknown"
                merged.setdefault(dim, set())
                for it in blk.get("items", []):
                    merged[dim].add(it)
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


