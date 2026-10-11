"""
Simple API Client for Literature Search
Provides arXiv search and PDF download functionality
"""

import requests
import arxiv
from typing import List, Dict
import time


def search_papers(query: str, max_results: int = 5) -> List[Dict]:
    """
    Search papers from arXiv.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        
    Returns:
        List of paper dictionaries with title, abstract, url, year, authors
    """
    papers = []
    
    try:
        # Use the newer Client API
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        # Get results using the client
        for paper in client.results(search):
            papers.append({
                "title": paper.title,
                "abstract": paper.summary,
                "url": paper.pdf_url,  # Direct PDF download URL
                "year": paper.published.year if paper.published else None,
                "authors": [author.name for author in paper.authors],
                "source": "arXiv",
                "entry_id": paper.entry_id
            })
        
    except Exception as e:
        print(f"arXiv search error: {e}")
    
    return papers


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
        # Add delay to respect rate limits
        time.sleep(1)
        
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Write PDF to file
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return True
        
    except Exception as e:
        print(f"PDF download error from {url}: {e}")
        return False

