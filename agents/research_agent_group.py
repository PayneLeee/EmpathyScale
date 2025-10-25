"""
Research Agent Group for Empathy Scale Construction
This agent group specializes in conducting research on empathy scale construction
for human-robot collaboration scenarios based on interview summaries.
Contains multiple sub-agents for different aspects of research and analysis.
"""

import hashlib
import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import AIMessage, HumanMessage
from langchain.tools import Tool
from langchain_openai import ChatOpenAI

# Add the utils directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from academic_api_manager import AcademicAPIManager
from prompt_manager import PromptManager
from run_manager import DataSaver, RunManager


class ResearchAgentGroup:
    """
    Agent group specialized in researching empathy scale construction
    for human-robot collaboration scenarios.
    This group contains multiple sub-agents for comprehensive research.
    """
    
    def __init__(self, api_key: str, model_name: str = "gpt-4", prompts_dir: str = None, run_manager: RunManager = None):
        """
        Initialize the research agent group.
        
        Args:
            api_key: OpenAI API key
            model_name: The LLM model to use
            prompts_dir: Path to the prompts directory. If None, will auto-detect.
            run_manager: Run manager for data storage
        """
        self.llm = ChatOpenAI(
            api_key=api_key,
            model_name=model_name,
            temperature=0.3  # Lower temperature for more focused research
        )
        
        # Initialize prompt manager for this agent group
        self.prompt_manager = PromptManager(prompts_dir)
        
        # Initialize conversation memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Define the research prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Define tools for the agent group
        self.tools = self._create_tools()
        
        # Create the main agent
        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True
        )
        
        # Track research progress
        self.research_data = {
            "interview_summary": None,
            "research_queries": [],
            "paper_search_results": [],
            "paper_metadata": [],
            "methodology_analysis": [],
            "context_insights": [],
            "scale_design_recommendations": [],
            "research_summary": None
        }
        
        # Initialize sub-agents
        self.sub_agents = self._initialize_sub_agents()
        
        # Initialize run manager and data saver
        self.run_manager = run_manager
        self.data_saver = DataSaver(run_manager) if run_manager else None
        
        # Initialize academic API manager
        self.api_manager = AcademicAPIManager()
        
        # Legacy data directory paths (for backward compatibility only)
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        self.intermediate_dir = os.path.join(self.data_dir, "intermediate_results", "research_agent_group")
        self.papers_dir = os.path.join(self.data_dir, "papers")
        self.summaries_dir = os.path.join(self.data_dir, "summaries")
        self.pdfs_dir = os.path.join(self.data_dir, "pdfs")
        
        # Note: These legacy directories are deprecated. Use RunManager paths instead.
    
    def _initialize_sub_agents(self) -> Dict[str, any]:
        """
        Initialize sub-agents within this group.
        Each sub-agent handles a specific aspect of research.
        
        Returns:
            Dictionary of sub-agents
        """
        sub_agents = {
            "paper_searcher": PaperSearcherAgent(self.prompt_manager),
            "methodology_analyzer": MethodologyAnalyzerAgent(self.prompt_manager),
            "context_specialist": ContextSpecialistAgent(self.prompt_manager),
            "scale_designer": ScaleDesignerAgent(self.prompt_manager)
        }
        return sub_agents
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the research agent group."""
        return self.prompt_manager.get_agent_group_prompt("research_agent_group", "system_prompt")
    
    def _create_tools(self) -> List[Tool]:
        """Create tools for the agent group."""
        def save_research_data(data: str) -> str:
            """Save research findings and analysis data."""
            timestamp = datetime.now().isoformat()
            
            # Parse and categorize research data
            data_lower = data.lower()
            
            if "query" in data_lower or "search" in data_lower:
                self.research_data["research_queries"].append({
                    "query": data,
                    "timestamp": timestamp
                })
            elif "paper" in data_lower and ("found" in data_lower or "result" in data_lower):
                self.research_data["paper_search_results"].append({
                    "result": data,
                    "timestamp": timestamp
                })
                # Auto-save paper metadata
                save_paper_metadata(data)
            elif "methodology" in data_lower or "method" in data_lower:
                self.research_data["methodology_analysis"].append({
                    "analysis": data,
                    "timestamp": timestamp
                })
            elif "context" in data_lower or "scenario" in data_lower:
                self.research_data["context_insights"].append({
                    "insight": data,
                    "timestamp": timestamp
                })
            elif "recommendation" in data_lower or "design" in data_lower:
                self.research_data["scale_design_recommendations"].append({
                    "recommendation": data,
                    "timestamp": timestamp
                })
            elif "summary" in data_lower:
                self.research_data["research_summary"] = {
                    "summary": data,
                    "timestamp": timestamp
                }
                # Auto-save research summary
                save_research_summary(data)
            else:
                # Default to general research data
                self.research_data["paper_search_results"].append({
                    "result": data,
                    "timestamp": timestamp
                })
            
            # Save to new run-based structure if available
            if self.data_saver:
                research_data = {
                    "timestamp": timestamp,
                    "data": data,
                    "source": "research_agent_group",
                    "run_id": self.run_manager.current_run_id if self.run_manager else None,
                    "categorized_data": self.research_data
                }
                
                filepath = self.data_saver.save_research_data(research_data)
                if filepath:
                    return f"Research data saved to run directory: {filepath}"
            
            return f"Research data saved: {data}"
        
        def search_academic_papers(query: str) -> str:
            """Search for academic papers using multiple APIs."""
            try:
                # Use the academic API manager to search multiple sources
                results = self.api_manager.search_papers(query, max_results=20)
                
                all_papers = []
                successful_apis = 0
                
                for api_name, papers in results.items():
                    if papers:  # Only process APIs that returned results
                        successful_apis += 1
                        for paper in papers:
                            paper['api_source'] = api_name
                            all_papers.append(paper)
                
                # Sort by citation count and year
                all_papers.sort(key=lambda x: (x.get('citation_count', 0) or 0, x.get('year', 0) or 0), reverse=True)
                
                # Store results
                self.research_data["paper_search_results"].extend(all_papers)
                self.research_data["research_queries"].append(query)
                
                # Format results for display
                formatted_results = []
                for i, paper in enumerate(all_papers[:10], 1):  # Show top 10
                    authors = ', '.join(paper.get('authors', [])[:3])
                    if len(paper.get('authors', [])) > 3:
                        authors += ' et al.'
                    
                    result_text = f"{i}. {paper.get('title', 'No title')}\n"
                    result_text += f"   Authors: {authors}\n"
                    result_text += f"   Year: {paper.get('year', 'N/A')}, Venue: {paper.get('venue', 'N/A')}\n"
                    result_text += f"   Citations: {paper.get('citation_count', 0)}\n"
                    result_text += f"   Source: {paper.get('api_source', 'Unknown')}\n"
                    if paper.get('pdf_url'):
                        result_text += f"   PDF: Available\n"
                    result_text += f"   Abstract: {paper.get('abstract', 'No abstract')[:200]}...\n"
                    formatted_results.append(result_text)
                
                summary = f"Found {len(all_papers)} papers from {successful_apis} sources. Top results:\n\n"
                summary += "\n".join(formatted_results)
                
                return summary
                
            except Exception as e:
                # Even if there's an error, try to return partial results
                if 'all_papers' in locals() and all_papers:
                    self.research_data["paper_search_results"].extend(all_papers)
                    self.research_data["research_queries"].append(query)
                    return f"Partial search completed with {len(all_papers)} papers. Error: {str(e)}"
                else:
                    return f"Failed to search academic papers: {str(e)}"
        
        def analyze_paper_methodology(paper_info: str) -> str:
            """Analyze methodology from paper information."""
            return self.sub_agents["methodology_analyzer"].process_task(paper_info)
        
        def extract_context_insights(scenario_info: str) -> str:
            """Extract context-specific insights."""
            return self.sub_agents["context_specialist"].process_task(scenario_info)
        
        def generate_scale_recommendations(analysis_data: str) -> str:
            """Generate recommendations for scale design."""
            return self.sub_agents["scale_designer"].process_task(analysis_data)
        
        def save_paper_metadata(paper_data: str) -> str:
            """Save paper metadata to files."""
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"paper_metadata_{timestamp}.json"
                
                # Use run-based path if available, otherwise fallback to legacy path
                if self.data_saver and self.run_manager.current_run_dir:
                    papers_dir = os.path.join(self.run_manager.current_run_dir, "research", "papers")
                    os.makedirs(papers_dir, exist_ok=True)
                    filepath = os.path.join(papers_dir, filename)
                else:
                    filepath = os.path.join(self.papers_dir, filename)
                
                metadata = {
                    "timestamp": timestamp,
                    "data": paper_data,
                    "source": "research_agent_group"
                }
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                
                return f"Paper metadata saved to {filename}"
            except Exception as e:
                return f"Failed to save paper metadata: {str(e)}"
        
        def save_research_summary(summary_data: str) -> str:
            """Save research summary to files."""
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"research_summary_{timestamp}.json"
                
                # Use run-based path if available, otherwise fallback to legacy path
                if self.data_saver and self.run_manager.current_run_dir:
                    summaries_dir = os.path.join(self.run_manager.current_run_dir, "research", "summaries")
                    os.makedirs(summaries_dir, exist_ok=True)
                    filepath = os.path.join(summaries_dir, filename)
                else:
                    filepath = os.path.join(self.summaries_dir, filename)
                
                summary = {
                    "timestamp": timestamp,
                    "summary": summary_data,
                    "source": "research_agent_group",
                    "research_data": self.research_data
                }
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(summary, f, indent=2, ensure_ascii=False)
                
                return f"Research summary saved to {filename}"
            except Exception as e:
                return f"Failed to save research summary: {str(e)}"
        
        def download_paper_pdf(paper_info: str) -> str:
            """Download PDF papers for RAG tasks using real APIs."""
            try:
                # Parse paper information to extract title and potential DOI/URL
                paper_title = paper_info.split(' - ')[0] if ' - ' in paper_info else paper_info
                journal_info = paper_info.split(' - ')[1] if ' - ' in paper_info else "Unknown Journal"
                
                # Generate a safe filename
                safe_title = "".join(c for c in paper_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_title = safe_title[:50]  # Limit length
                
                # Create filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{safe_title}_{timestamp}.pdf"
                
                # Use run-based path if available, otherwise fallback to legacy path
                if self.data_saver and self.run_manager.current_run_dir:
                    pdfs_dir = os.path.join(self.run_manager.current_run_dir, "research", "pdfs")
                else:
                    pdfs_dir = self.pdfs_dir
                
                filepath = os.path.join(pdfs_dir, filename)
                
                # Try to find the paper in our search results
                paper_data = None
                for paper in self.research_data.get("paper_search_results", []):
                    if paper_title.lower() in paper.get('title', '').lower():
                        paper_data = paper
                        break
                
                if paper_data and paper_data.get('pdf_url'):
                    # Try to download the actual PDF
                    try:
                        response = requests.get(paper_data['pdf_url'], timeout=30)
                        response.raise_for_status()
                        
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        
                        # Create metadata file
                        metadata_filename = f"{safe_title}_{timestamp}_metadata.json"
                        metadata_filepath = os.path.join(pdfs_dir, metadata_filename)
                        
                        paper_metadata = {
                            "title": paper_data.get('title', paper_title),
                            "authors": paper_data.get('authors', []),
                            "year": paper_data.get('year', ''),
                            "venue": paper_data.get('venue', journal_info),
                            "download_timestamp": timestamp,
                            "source": "research_agent_group",
                            "api_source": paper_data.get('api_source', 'unknown'),
                            "status": "pdf_downloaded",
                            "pdf_file": filename,
                            "pdf_url": paper_data['pdf_url'],
                            "paper_id": paper_data.get('paper_id', ''),
                            "citation_count": paper_data.get('citation_count', 0),
                            "abstract": paper_data.get('abstract', ''),
                            "is_open_access": paper_data.get('is_open_access', False)
                        }
                        
                        with open(metadata_filepath, 'w', encoding='utf-8') as f:
                            json.dump(paper_metadata, f, indent=2, ensure_ascii=False)
                        
                        # Add to research data
                        self.research_data["paper_metadata"].append({
                            "title": paper_data.get('title', paper_title),
                            "journal": paper_data.get('venue', journal_info),
                            "metadata_file": metadata_filename,
                            "pdf_file": filename,
                            "timestamp": timestamp,
                            "api_source": paper_data.get('api_source', 'unknown')
                        })
                        
                        return f"✅ PDF downloaded successfully: {filename}. Metadata saved: {metadata_filename}"
                        
                    except Exception as download_error:
                        # Fallback to metadata only
                        metadata_filename = f"{safe_title}_{timestamp}_metadata.json"
                        metadata_filepath = os.path.join(pdfs_dir, metadata_filename)
                        
                        paper_metadata = {
                            "title": paper_data.get('title', paper_title),
                            "authors": paper_data.get('authors', []),
                            "year": paper_data.get('year', ''),
                            "venue": paper_data.get('venue', journal_info),
                            "download_timestamp": timestamp,
                            "source": "research_agent_group",
                            "api_source": paper_data.get('api_source', 'unknown'),
                            "status": "metadata_only",
                            "error": f"PDF download failed: {str(download_error)}",
                            "pdf_url": paper_data.get('pdf_url', ''),
                            "paper_id": paper_data.get('paper_id', ''),
                            "citation_count": paper_data.get('citation_count', 0),
                            "abstract": paper_data.get('abstract', ''),
                            "is_open_access": paper_data.get('is_open_access', False)
                        }
                        
                        with open(metadata_filepath, 'w', encoding='utf-8') as f:
                            json.dump(paper_metadata, f, indent=2, ensure_ascii=False)
                        
                        return f"⚠️ PDF download failed, metadata saved: {metadata_filename}. Error: {str(download_error)}"
                
                else:
                    # No PDF available, create metadata only
                    metadata_filename = f"{safe_title}_{timestamp}_metadata.json"
                    metadata_filepath = os.path.join(pdfs_dir, metadata_filename)
                    
                    paper_metadata = {
                        "title": paper_title,
                        "journal": journal_info,
                        "download_timestamp": timestamp,
                        "source": "research_agent_group",
                        "status": "metadata_only",
                        "note": "No PDF URL available from search results",
                        "paper_info": paper_info
                    }
                    
                    with open(metadata_filepath, 'w', encoding='utf-8') as f:
                        json.dump(paper_metadata, f, indent=2, ensure_ascii=False)
                    
                    return f"📄 Metadata saved: {metadata_filename}. No PDF URL available."
                
            except Exception as e:
                return f"❌ Failed to process paper: {str(e)}"
        
        def search_and_download_papers(query: str) -> str:
            """Search for papers and download their PDFs/metadata."""
            try:
                # This would integrate with real academic search APIs
                # For now, we'll simulate the process
                
                # Simulate finding papers
                simulated_papers = [
                    f"Empathy Measurement in Human-Robot Interaction - Journal of HRI",
                    f"Scale Construction for Robot Empathy Assessment - IEEE Transactions",
                    f"Emotional Intelligence in Collaborative Robotics - ACM HRI",
                    f"Context-Aware Empathy Evaluation in Healthcare Robots - Robotics and Autonomous Systems",
                    f"Multi-Modal Empathy Assessment Framework - International Journal of Social Robotics"
                ]
                
                downloaded_count = 0
                results = []
                
                for paper in simulated_papers:
                    if any(keyword.lower() in paper.lower() for keyword in query.lower().split()):
                        result = download_paper_pdf(paper)
                        results.append(f"✓ {paper}: {result}")
                        downloaded_count += 1
                
                if downloaded_count == 0:
                    return f"No papers found matching query: {query}"
                
                summary = f"Successfully processed {downloaded_count} papers for query: {query}"
                return summary + "\n" + "\n".join(results)
                
            except Exception as e:
                return f"Failed to search and download papers: {str(e)}"
        
        def get_research_progress() -> str:
            """Get current research progress."""
            progress = []
            for key, value in self.research_data.items():
                if value:
                    if isinstance(value, list):
                        progress.append(f"{key}: {len(value)} items")
                    else:
                        progress.append(f"{key}: Available")
            return "Research progress: " + ", ".join(progress) if progress else "No research data collected yet."
        
        def delegate_to_sub_agent(sub_agent_name: str, task: str) -> str:
            """Delegate specific research tasks to sub-agents."""
            if sub_agent_name in self.sub_agents:
                return self.sub_agents[sub_agent_name].process_task(task)
            return f"Sub-agent {sub_agent_name} not found."
        
        return [
            Tool(
                name="save_research_data",
                description="ALWAYS use this tool after every research action to save findings, paper metadata, and analysis results. This ensures all research progress is tracked.",
                func=save_research_data
            ),
            Tool(
                name="search_academic_papers",
                description="Search for academic papers related to empathy scale construction in human-robot interaction contexts",
                func=search_academic_papers
            ),
            Tool(
                name="analyze_paper_methodology",
                description="Analyze methodology and approaches used in research papers",
                func=analyze_paper_methodology
            ),
            Tool(
                name="extract_context_insights",
                description="Extract context-specific insights about empathy measurement approaches",
                func=extract_context_insights
            ),
            Tool(
                name="generate_scale_recommendations",
                description="Generate recommendations for empathy scale design based on research findings",
                func=generate_scale_recommendations
            ),
            Tool(
                name="save_paper_metadata",
                description="Save paper metadata and findings to organized files",
                func=save_paper_metadata
            ),
            Tool(
                name="save_research_summary",
                description="Save research summary and findings to organized files",
                func=save_research_summary
            ),
            Tool(
                name="download_paper_pdf",
                description="Download PDF papers and metadata for RAG tasks. Use this to collect actual papers for retrieval augmentation.",
                func=download_paper_pdf
            ),
            Tool(
                name="search_and_download_papers",
                description="Search for papers and automatically download their PDFs/metadata for RAG integration",
                func=search_and_download_papers
            ),
            Tool(
                name="get_research_progress",
                description="Get current research progress and status",
                func=get_research_progress
            ),
            Tool(
                name="delegate_to_sub_agent",
                description="Delegate specific research tasks to specialized sub-agents",
                func=delegate_to_sub_agent
            )
        ]
    
    def _perform_web_search(self, query: str) -> List[str]:
        """Perform web search for academic papers."""
        # This is a simplified implementation - in practice, you'd use
        # academic search APIs like Semantic Scholar, arXiv, or Google Scholar
        search_terms = [
            f"empathy scale human robot interaction {query}",
            f"emotional assessment robot collaboration {query}",
            f"empathy measurement HRI {query}",
            f"robot empathy evaluation {query}"
        ]
        
        results = []
        for term in search_terms:
            # Simulate search results - in practice, implement actual API calls
            results.append(f"Paper: 'Empathy Measurement in {query}' - Journal of HRI")
            results.append(f"Paper: 'Scale Construction for Robot Empathy' - IEEE Transactions")
            results.append(f"Paper: 'Emotional Intelligence Assessment in HRI' - ACM HRI")
        
        return results[:10]  # Limit results
    
    def start_research(self, interview_summary: Dict) -> str:
        """Start research based on interview summary."""
        self.research_data["interview_summary"] = interview_summary
        
        # Save interview summary to intermediate results
        self._save_intermediate_results("interview_summary", interview_summary)
        
        return self.prompt_manager.get_agent_group_prompt("research_agent_group", "opening_message")
    
    def process_research_task(self, task: str) -> str:
        """
        Process a research task.
        
        Args:
            task: The research task to process
            
        Returns:
            Agent's response
        """
        try:
            response = self.agent_executor.invoke({"input": task})
            return response["output"]
        except Exception as e:
            return self.prompt_manager.format_agent_group_prompt("research_agent_group", "error_message", error=str(e))
    
    def get_research_summary(self) -> Dict:
        """Get a summary of the research findings."""
        summary = self.research_data.copy()
        
        # Save summary to run directory if available
        if self.data_saver:
            timestamp = datetime.now().isoformat()
            summary_data = {
                "timestamp": timestamp,
                "summary": summary,
                "source": "research_agent_group",
                "run_id": self.run_manager.current_run_id if self.run_manager else None,
                "is_complete": self.is_research_complete()
            }
            
            filepath = self.data_saver.save_research_data(summary_data, "research_summary.json")
            if filepath:
                print(f"Research summary saved to: {filepath}")
        
        return summary
    
    def _save_intermediate_results(self, filename: str, data: Any):
        """Save intermediate results to files."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            full_filename = f"{filename}_{timestamp}.json"
            filepath = os.path.join(self.intermediate_dir, full_filename)
            
            result_data = {
                "timestamp": timestamp,
                "agent_group": "research_agent_group",
                "data": data
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Failed to save intermediate results: {str(e)}")
    
    def is_research_complete(self) -> bool:
        """Check if research is complete."""
        required_fields = ["research_queries", "paper_search_results", "methodology_analysis"]
        return all(self.research_data[field] for field in required_fields)
    
    def finalize_research(self):
        """Finalize research by saving all data to files."""
        try:
            # Save final research summary
            if self.research_data.get("research_summary"):
                summary_data = self.research_data["research_summary"]["summary"]
            else:
                summary_data = "Research completed with collected data"
            
            # Save to summaries folder
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            summary_filename = f"final_research_summary_{timestamp}.json"
            
            # Use run-based path if available, otherwise fallback to legacy path
            if self.data_saver and self.run_manager.current_run_dir:
                summaries_dir = os.path.join(self.run_manager.current_run_dir, "research", "summaries")
                os.makedirs(summaries_dir, exist_ok=True)
                summary_filepath = os.path.join(summaries_dir, summary_filename)
            else:
                summary_filepath = os.path.join(self.summaries_dir, summary_filename)
            
            final_summary = {
                "timestamp": timestamp,
                "summary": summary_data,
                "source": "research_agent_group",
                "research_data": self.research_data,
                "status": "completed"
            }
            
            with open(summary_filepath, 'w', encoding='utf-8') as f:
                json.dump(final_summary, f, indent=2, ensure_ascii=False)
            
            # Save comprehensive paper collection
            papers_filename = None
            if self.research_data.get("paper_search_results"):
                papers_filename = f"collected_papers_{timestamp}.json"
                
                # Use run-based path if available, otherwise fallback to legacy path
                if self.data_saver and self.run_manager.current_run_dir:
                    papers_dir = os.path.join(self.run_manager.current_run_dir, "research", "papers")
                    os.makedirs(papers_dir, exist_ok=True)
                    papers_filepath = os.path.join(papers_dir, papers_filename)
                else:
                    papers_filepath = os.path.join(self.papers_dir, papers_filename)
                
                papers_data = {
                    "timestamp": timestamp,
                    "source": "research_agent_group",
                    "papers": self.research_data["paper_search_results"],
                    "queries": self.research_data.get("research_queries", []),
                    "methodology": self.research_data.get("methodology_analysis", []),
                    "context_insights": self.research_data.get("context_insights", []),
                    "recommendations": self.research_data.get("scale_design_recommendations", []),
                    "downloaded_papers": self.research_data.get("paper_metadata", []),
                    "pdf_directory": os.path.join(self.run_manager.current_run_dir, "research", "pdfs") if self.run_manager.current_run_dir else self.pdfs_dir,
                    "rag_ready": True
                }
                
                with open(papers_filepath, 'w', encoding='utf-8') as f:
                    json.dump(papers_data, f, indent=2, ensure_ascii=False)
            
            papers_msg = f", papers saved to {papers_filename}" if papers_filename else ""
            return f"Research finalized. Summary saved to {summary_filename}{papers_msg}"
            
        except Exception as e:
            return f"Failed to finalize research: {str(e)}"
    
    def reload_prompts(self):
        """Reload prompts for this agent group."""
        self.prompt_manager.reload_agent_group_prompts("research_agent_group")
        # Update the prompt template with new system prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        # Recreate the agent with updated prompt
        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        # Recreate agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True
        )


class PaperSearcherAgent:
    """Sub-agent specialized in searching for academic papers."""
    
    def __init__(self, prompt_manager: PromptManager):
        self.prompt_manager = prompt_manager
    
    def process_task(self, search_task: str) -> str:
        """Process paper search tasks."""
        prompt = self.prompt_manager.get_agent_group_prompt("research_agent_group", "paper_searcher_prompt")
        return f"Paper search analysis: {prompt} - Processing: {search_task}"


class MethodologyAnalyzerAgent:
    """Sub-agent specialized in analyzing research methodologies."""
    
    def __init__(self, prompt_manager: PromptManager):
        self.prompt_manager = prompt_manager
    
    def process_task(self, methodology_info: str) -> str:
        """Process methodology analysis tasks."""
        prompt = self.prompt_manager.get_agent_group_prompt("research_agent_group", "methodology_analyzer_prompt")
        return f"Methodology analysis: {prompt} - Processing: {methodology_info}"


class ContextSpecialistAgent:
    """Sub-agent specialized in context analysis."""
    
    def __init__(self, prompt_manager: PromptManager):
        self.prompt_manager = prompt_manager
    
    def process_task(self, context_info: str) -> str:
        """Process context analysis tasks."""
        prompt = self.prompt_manager.get_agent_group_prompt("research_agent_group", "context_specialist_prompt")
        return f"Context analysis: {prompt} - Processing: {context_info}"


class ScaleDesignerAgent:
    """Sub-agent specialized in scale design recommendations."""
    
    def __init__(self, prompt_manager: PromptManager):
        self.prompt_manager = prompt_manager
    
    def process_task(self, design_task: str) -> str:
        """Process scale design tasks."""
        prompt = self.prompt_manager.get_agent_group_prompt("research_agent_group", "scale_designer_prompt")
        return f"Scale design analysis: {prompt} - Processing: {design_task}"


def load_config(config_path: str = None) -> Dict:
    """
    Load configuration from JSON file.
    
    Args:
        config_path: Path to the configuration file. If None, will auto-detect.
        
    Returns:
        Configuration dictionary
    """
    if config_path is None:
        # Auto-detect config.json location
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        config_path = os.path.join(project_root, "config.json")
    
    try:
        with open(config_path, 'r') as file:
            config = json.load(file)
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file {config_path} not found.")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in configuration file {config_path}.")


if __name__ == "__main__":
    # Example usage
    config = load_config()
    agent_group = ResearchAgentGroup(config["openai_api_key"])
    
    # Example interview summary
    example_summary = {
        "assessment_context": "Healthcare robot assisting nurses with patient care",
        "robot_platform": "Humanoid robot with facial expressions and voice",
        "collaboration_pattern": "Supervised collaboration with emotional support",
        "environmental_setting": "Hospital ward environment"
    }
    
    print("=== Research Agent Group for Empathy Scale Construction ===")
    print(agent_group.start_research(example_summary))
    
    # Example research tasks
    research_tasks = [
        "Search for papers on empathy measurement in healthcare robot scenarios",
        "Analyze methodologies used in robot empathy evaluation studies",
        "Extract insights about context-specific empathy measurement approaches",
        "Generate recommendations for empathy scale design"
    ]
    
    for task in research_tasks:
        print(f"\nResearch Task: {task}")
        response = agent_group.process_research_task(task)
        print(f"Agent Response: {response}")
    
    print("\n=== Research Summary ===")
    summary = agent_group.get_research_summary()
    for key, value in summary.items():
        if value:
            print(f"{key}: {value}")
