"""
Multi-Database Research API Client
Supports arXiv, Semantic Scholar, and other academic sources
"""

import requests
import arxiv
from typing import List, Dict, Optional
import time
import json


class ResearchAPIClient:
    """Unified client for searching multiple academic databases."""
    
    def __init__(self):
        self.client = arxiv.Client()
        self.semantic_scholar_base = "https://api.semanticscholar.org/graph/v1"
    
    def search_arxiv(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search arXiv for papers."""
        papers = []
        
        try:
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            for paper in self.client.results(search):
                papers.append({
                    "title": paper.title,
                    "abstract": paper.summary,
                    "url": paper.pdf_url,
                    "year": paper.published.year if paper.published else None,
                    "authors": [author.name for author in paper.authors],
                    "source": "arXiv",
                    "entry_id": paper.entry_id,
                    "doi": None  # arXiv doesn't have DOI in basic response
                })
        except Exception as e:
            print(f"arXiv search error: {e}")
        
        return papers
    
    def search_semantic_scholar(self, query: str, limit: int = 5) -> List[Dict]:
        """Search Semantic Scholar (free, no API key needed for basic search)."""
        papers = []
        
        try:
            url = f"{self.semantic_scholar_base}/paper/search"
            params = {
                "query": query,
                "limit": limit,
                "fields": "title,abstract,url,year,authors,openAccessPdf,citationCount"
            }
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                for paper in data.get("data", []):
                    paper_dict = {
                        "title": paper.get("title", ""),
                        "abstract": paper.get("abstract", ""),
                        "url": paper.get("openAccessPdf", {}).get("url") or paper.get("url", ""),
                        "year": paper.get("year"),
                        "authors": [author.get("name", "") for author in paper.get("authors", [])],
                        "source": "Semantic Scholar",
                        "entry_id": paper.get("paperId", ""),
                        "doi": None,
                        "citation_count": paper.get("citationCount", 0)
                    }
                    
                    # Only add if has PDF or abstract
                    if paper_dict["url"] or paper_dict["abstract"]:
                        papers.append(paper_dict)
            
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"Semantic Scholar search error: {e}")
        
        return papers
    
    def search_all(self, query: str, sources: List[str] = None, max_per_source: int = 5) -> List[Dict]:
        """
        Search all configured sources.
        
        Args:
            query: Search query
            sources: List of sources to search (default: ["arxiv", "semantic_scholar"])
            max_per_source: Max results per source
            
        Returns:
            List of unique papers from all sources
        """
        if sources is None:
            sources = ["arxiv", "semantic_scholar"]
        
        all_papers = []
        seen_titles = set()
        
        for source in sources:
            if source == "arxiv":
                papers = self.search_arxiv(query, max_per_source)
            elif source == "semantic_scholar":
                papers = self.search_semantic_scholar(query, max_per_source)
            else:
                continue
            
            # Deduplicate by title
            for paper in papers:
                title_lower = paper['title'].lower()
                if title_lower not in seen_titles:
                    seen_titles.add(title_lower)
                    all_papers.append(paper)
        
        return all_papers


def download_pdf(url: str, save_path: str) -> bool:
    """
    Download PDF from URL and save to file.
    
    Args:
        url: PDF URL
        save_path: Path to save the PDF file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        time.sleep(1)  # Rate limiting
        
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('content-type', '')
        if 'pdf' not in content_type.lower() and not url.endswith('.pdf'):
            print(f"Warning: Content may not be a PDF. Content-Type: {content_type}")
        
        # Write PDF to file
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return True
        
    except Exception as e:
        print(f"PDF download error from {url}: {e}")
        return False


# Backward compatibility
def search_papers(query: str, max_results: int = 5) -> List[Dict]:
    """Backward compatible function for existing code."""
    client = ResearchAPIClient()
    return client.search_arxiv(query, max_results)

