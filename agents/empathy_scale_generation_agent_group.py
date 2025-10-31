"""
Empathy Scale Generation Agent Group
Combines interview summary, literature findings, and expert reference PDFs
to generate a structured empathy scale draft aligned with expert templates.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any

from langchain_openai import ChatOpenAI

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from prompt_manager import PromptManager


PROJECT_ROOT = Path(__file__).parent.parent.resolve()


class EmpathyScaleGenerationAgentGroup:
    """Agent group that generates an empathy scale draft for expert review."""

    def __init__(self, api_key: str, model_name: str = "gpt-4", prompts_dir: str = None):
        self.llm = ChatOpenAI(api_key=api_key, model_name=model_name)
        self.prompt_manager = PromptManager(prompts_dir)

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

        system_prompt = self.prompt_manager.get_agent_group_prompt(
            "empathy_scale_generation_agent_group", "system_prompt"
        )
        main_prompt = self._build_generation_prompt(interview, literature, expert_pdfs)

        try:
            # Compose with system instructions first
            prompt = f"{system_prompt}\n\n{main_prompt}"
            response = self.llm.invoke(prompt)
            scale_markdown = response.content.strip()

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
        except Exception as e:
            error_msg = self.prompt_manager.get_agent_group_prompt(
                "empathy_scale_generation_agent_group", "error_message"
            )
            return {"error": error_msg.format(error=str(e))}


