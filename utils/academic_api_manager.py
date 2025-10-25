"""
Academic API Integration Module
集成主要学术API，专注于人机协作领域的免费开源网站
"""

import json
import os
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urlencode

import requests


class AcademicAPIManager:
    """学术API管理器，统一管理多个学术数据源"""
    
    def __init__(self, config_file: str = "config/academic_apis.json"):
        self.config_file = config_file
        self.apis = self._load_api_configs()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'EmpathyScale-Research-Agent/1.0 (Academic Research)'
        })
    
    def _load_api_configs(self) -> Dict[str, Dict]:
        """加载API配置"""
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), self.config_file)
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 默认配置
            return self._get_default_configs()
    
    def _get_default_configs(self) -> Dict[str, Dict]:
        """获取默认API配置"""
        return {
            "semantic_scholar": {
                "name": "Semantic Scholar",
                "base_url": "https://api.semanticscholar.org/graph/v1/paper",
                "search_url": "https://api.semanticscholar.org/graph/v1/paper/search",
                "rate_limit": 100,  # requests per minute
                "enabled": True,
                "description": "AI-powered research tool for scientific literature",
                "domains": ["computer science", "robotics", "human-computer interaction", "AI"]
            },
            "arxiv": {
                "name": "arXiv",
                "base_url": "http://export.arxiv.org/api/query",
                "rate_limit": 3,  # requests per second
                "enabled": True,
                "description": "Open access repository of electronic preprints",
                "domains": ["cs", "cs.RO", "cs.HC", "cs.AI", "cs.CV", "cs.CL"]
            },
            "pubmed": {
                "name": "PubMed",
                "base_url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
                "rate_limit": 3,  # requests per second
                "enabled": True,
                "description": "Database of biomedical literature",
                "domains": ["biomedical", "healthcare", "medical robotics"]
            },
            "crossref": {
                "name": "Crossref",
                "base_url": "https://api.crossref.org/works",
                "rate_limit": 50,  # requests per second
                "enabled": True,
                "description": "DOI registration and metadata service",
                "domains": ["all academic fields"]
            },
            "openalex": {
                "name": "OpenAlex",
                "base_url": "https://api.openalex.org/works",
                "rate_limit": 10,  # requests per second
                "enabled": True,
                "description": "Open catalog of the world's scholarly papers",
                "domains": ["all academic fields"]
            }
        }
    
    def search_papers(self, query: str, max_results: int = 20, 
                     apis: Optional[List[str]] = None) -> Dict[str, List[Dict]]:
        """搜索论文，支持多个API"""
        if apis is None:
            apis = [api_name for api_name, config in self.apis.items() if config.get("enabled", True)]
        
        results = {}
        
        for api_name in apis:
            if api_name not in self.apis:
                continue
            
            try:
                api_results = self._search_with_api(api_name, query, max_results)
                results[api_name] = api_results
                print(f"✅ {self.apis[api_name].get('name', api_name)}: Found {len(api_results)} papers")
                
                # 遵守速率限制
                rate_limit = self.apis[api_name].get("rate_limit", 1)
                time.sleep(60 / rate_limit)
                
            except Exception as e:
                print(f"❌ {self.apis[api_name].get('name', api_name)}: Error - {str(e)}")
                results[api_name] = []
        
        return results
    
    def _search_with_api(self, api_name: str, query: str, max_results: int) -> List[Dict]:
        """使用特定API搜索论文"""
        if api_name == "semantic_scholar":
            return self._search_semantic_scholar(query, max_results)
        elif api_name == "arxiv":
            return self._search_arxiv(query, max_results)
        elif api_name == "pubmed":
            return self._search_pubmed(query, max_results)
        elif api_name == "crossref":
            return self._search_crossref(query, max_results)
        elif api_name == "openalex":
            return self._search_openalex(query, max_results)
        else:
            return []
    
    def _search_semantic_scholar(self, query: str, max_results: int) -> List[Dict]:
        """搜索Semantic Scholar"""
        url = self.apis["semantic_scholar"]["search_url"]
        params = {
            'query': query,
            'limit': min(max_results, 100),
            'fields': 'paperId,title,authors,year,venue,abstract,citationCount,openAccessPdf,url,isOpenAccess'
        }
        
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        papers = []
        
        for paper in data.get('data', []):
            paper_info = {
                'title': paper.get('title', ''),
                'authors': [author.get('name', '') for author in paper.get('authors', [])],
                'year': paper.get('year'),
                'venue': paper.get('venue', ''),
                'abstract': paper.get('abstract', ''),
                'citation_count': paper.get('citationCount', 0),
                'paper_id': paper.get('paperId', ''),
                'url': paper.get('url', ''),
                'is_open_access': paper.get('isOpenAccess', False),
                'pdf_url': paper.get('openAccessPdf', {}).get('url', '') if paper.get('openAccessPdf') else '',
                'source': 'semantic_scholar',
                'search_query': query
            }
            papers.append(paper_info)
        
        return papers
    
    def _search_arxiv(self, query: str, max_results: int) -> List[Dict]:
        """搜索arXiv"""
        url = self.apis["arxiv"]["base_url"]
        params = {
            'search_query': query,
            'start': 0,
            'max_results': min(max_results, 2000),
            'sortBy': 'relevance',
            'sortOrder': 'descending'
        }
        
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        papers = []
        
        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            paper_info = {
                'title': entry.find('{http://www.w3.org/2005/Atom}title').text.strip(),
                'authors': [author.find('{http://www.w3.org/2005/Atom}name').text 
                           for author in entry.findall('{http://www.w3.org/2005/Atom}author')],
                'year': entry.find('{http://www.w3.org/2005/Atom}published').text[:4] if entry.find('{http://www.w3.org/2005/Atom}published') is not None else '',
                'venue': 'arXiv',
                'abstract': entry.find('{http://www.w3.org/2005/Atom}summary').text.strip(),
                'citation_count': 0,  # arXiv doesn't provide citation count
                'paper_id': entry.find('{http://www.w3.org/2005/Atom}id').text,
                'url': entry.find('{http://www.w3.org/2005/Atom}id').text,
                'is_open_access': True,  # arXiv is always open access
                'pdf_url': entry.find('{http://www.w3.org/2005/Atom}id').text.replace('abs/', 'pdf/') + '.pdf',
                'source': 'arxiv',
                'search_query': query
            }
            papers.append(paper_info)
        
        return papers
    
    def _search_pubmed(self, query: str, max_results: int) -> List[Dict]:
        """搜索PubMed"""
        # PubMed搜索需要两步：先搜索ID，再获取详细信息
        search_url = f"{self.apis['pubmed']['base_url']}/esearch.fcgi"
        search_params = {
            'db': 'pubmed',
            'term': query,
            'retmax': min(max_results, 100),
            'retmode': 'json'
        }
        
        response = self.session.get(search_url, params=search_params, timeout=30)
        response.raise_for_status()
        
        search_data = response.json()
        pmids = search_data.get('esearchresult', {}).get('idlist', [])
        
        if not pmids:
            return []
        
        # 获取详细信息
        fetch_url = f"{self.apis['pubmed']['base_url']}/efetch.fcgi"
        fetch_params = {
            'db': 'pubmed',
            'id': ','.join(pmids),
            'retmode': 'xml'
        }
        
        response = self.session.get(fetch_url, params=fetch_params, timeout=30)
        response.raise_for_status()
        
        # 解析XML响应
        root = ET.fromstring(response.content)
        papers = []
        
        for article in root.findall('.//PubmedArticle'):
            paper_info = self._parse_pubmed_article(article, query)
            if paper_info:
                papers.append(paper_info)
        
        return papers
    
    def _parse_pubmed_article(self, article: ET.Element, query: str) -> Optional[Dict]:
        """解析PubMed文章"""
        try:
            title_elem = article.find('.//ArticleTitle')
            title = title_elem.text if title_elem is not None else ''
            
            authors = []
            for author in article.findall('.//Author'):
                last_name = author.find('LastName')
                first_name = author.find('ForeName')
                if last_name is not None and first_name is not None:
                    authors.append(f"{first_name.text} {last_name.text}")
            
            journal_elem = article.find('.//Journal/Title')
            journal = journal_elem.text if journal_elem is not None else ''
            
            year_elem = article.find('.//PubDate/Year')
            year = year_elem.text if year_elem is not None else ''
            
            abstract_elem = article.find('.//AbstractText')
            abstract = abstract_elem.text if abstract_elem is not None else ''
            
            pmid_elem = article.find('.//PMID')
            pmid = pmid_elem.text if pmid_elem is not None else ''
            
            return {
                'title': title,
                'authors': authors,
                'year': year,
                'venue': journal,
                'abstract': abstract,
                'citation_count': 0,  # PubMed doesn't provide citation count
                'paper_id': pmid,
                'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                'is_open_access': False,  # Need to check separately
                'pdf_url': '',
                'source': 'pubmed',
                'search_query': query
            }
        except Exception as e:
            print(f"Error parsing PubMed article: {e}")
            return None
    
    def _search_crossref(self, query: str, max_results: int) -> List[Dict]:
        """搜索Crossref"""
        url = self.apis["crossref"]["base_url"]
        params = {
            'query': query,
            'rows': min(max_results, 1000),
            'mailto': 'research@empathyscale.com'  # Required by Crossref
        }
        
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        papers = []
        
        for item in data.get('message', {}).get('items', []):
            paper_info = {
                'title': ' '.join(item.get('title', [])),
                'authors': [author.get('given', '') + ' ' + author.get('family', '') 
                           for author in item.get('author', [])],
                'year': item.get('published-print', {}).get('date-parts', [[None]])[0][0],
                'venue': item.get('container-title', [''])[0],
                'abstract': '',
                'citation_count': 0,
                'paper_id': item.get('DOI', ''),
                'url': item.get('URL', ''),
                'is_open_access': item.get('is-referenced-by-count', 0) > 0,
                'pdf_url': '',
                'source': 'crossref',
                'search_query': query
            }
            papers.append(paper_info)
        
        return papers
    
    def _search_openalex(self, query: str, max_results: int) -> List[Dict]:
        """搜索OpenAlex"""
        url = self.apis["openalex"]["base_url"]
        params = {
            'search': query,
            'per-page': min(max_results, 200),
            'mailto': 'research@empathyscale.com'  # Required by OpenAlex
        }
        
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        papers = []
        
        for work in data.get('results', []):
            paper_info = {
                'title': work.get('title', ''),
                'authors': [author.get('author', {}).get('display_name', '') 
                           for author in work.get('authorships', [])],
                'year': work.get('publication_year'),
                'venue': work.get('primary_location', {}).get('source', {}).get('display_name', ''),
                'abstract': work.get('abstract_inverted_index', ''),
                'citation_count': work.get('cited_by_count', 0),
                'paper_id': work.get('id', '').split('/')[-1] if work.get('id') else '',
                'url': work.get('doi', ''),
                'is_open_access': work.get('open_access', {}).get('is_oa', False),
                'pdf_url': work.get('open_access', {}).get('oa_url', ''),
                'source': 'openalex',
                'search_query': query
            }
            papers.append(paper_info)
        
        return papers
    
    def download_paper_pdf(self, paper_info: Dict) -> Optional[str]:
        """下载论文PDF"""
        pdf_url = paper_info.get('pdf_url')
        if not pdf_url:
            return None
        
        try:
            response = self.session.get(pdf_url, timeout=60)
            response.raise_for_status()
            
            # 生成文件名
            title = paper_info.get('title', 'unknown')
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title[:50]
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_title}_{timestamp}.pdf"
            
            # 保存文件
            filepath = os.path.join("data", "pdfs", filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return filepath
            
        except Exception as e:
            print(f"Failed to download PDF: {e}")
            return None
    
    def get_api_status(self) -> Dict[str, Dict]:
        """获取所有API的状态"""
        status = {}
        
        for api_name, config in self.apis.items():
            # 跳过future_apis部分
            if api_name == "future_apis":
                continue
                
            try:
                # 简单的健康检查
                if api_name == "semantic_scholar":
                    test_url = f"{config['base_url']}/search"
                    response = self.session.get(test_url, params={'query': 'test', 'limit': 1}, timeout=10)
                    is_healthy = response.status_code == 200
                elif api_name == "arxiv":
                    test_url = config['base_url']
                    response = self.session.get(test_url, params={'search_query': 'test', 'max_results': 1}, timeout=10)
                    is_healthy = response.status_code == 200
                else:
                    is_healthy = True  # 其他API暂时跳过健康检查
                
                status[api_name] = {
                    'name': config.get('name', api_name),
                    'enabled': config.get('enabled', True),
                    'healthy': is_healthy,
                    'rate_limit': config.get('rate_limit', 1),
                    'description': config.get('description', ''),
                    'domains': config.get('domains', [])
                }
                
            except Exception as e:
                status[api_name] = {
                    'name': config.get('name', api_name),
                    'enabled': config.get('enabled', True),
                    'healthy': False,
                    'error': str(e),
                    'rate_limit': config.get('rate_limit', 1),
                    'description': config.get('description', ''),
                    'domains': config.get('domains', [])
                }
        
        return status


def create_api_config_file():
    """创建API配置文件"""
    config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")
    os.makedirs(config_dir, exist_ok=True)
    
    config_file = os.path.join(config_dir, "academic_apis.json")
    
    default_config = {
        "semantic_scholar": {
            "name": "Semantic Scholar",
            "base_url": "https://api.semanticscholar.org/graph/v1/paper",
            "search_url": "https://api.semanticscholar.org/graph/v1/paper/search",
            "rate_limit": 100,
            "enabled": True,
            "description": "AI-powered research tool for scientific literature",
            "domains": ["computer science", "robotics", "human-computer interaction", "AI"],
            "api_key": None,
            "notes": "Free, no API key required. Excellent for CS and AI papers."
        },
        "arxiv": {
            "name": "arXiv",
            "base_url": "http://export.arxiv.org/api/query",
            "rate_limit": 3,
            "enabled": True,
            "description": "Open access repository of electronic preprints",
            "domains": ["cs", "cs.RO", "cs.HC", "cs.AI", "cs.CV", "cs.CL"],
            "api_key": None,
            "notes": "Free, no API key required. Best for preprints in CS and robotics."
        },
        "pubmed": {
            "name": "PubMed",
            "base_url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
            "rate_limit": 3,
            "enabled": True,
            "description": "Database of biomedical literature",
            "domains": ["biomedical", "healthcare", "medical robotics"],
            "api_key": None,
            "notes": "Free, no API key required. Good for healthcare and medical robotics."
        },
        "crossref": {
            "name": "Crossref",
            "base_url": "https://api.crossref.org/works",
            "rate_limit": 50,
            "enabled": True,
            "description": "DOI registration and metadata service",
            "domains": ["all academic fields"],
            "api_key": None,
            "notes": "Free, no API key required. Good for DOI resolution and metadata."
        },
        "openalex": {
            "name": "OpenAlex",
            "base_url": "https://api.openalex.org/works",
            "rate_limit": 10,
            "enabled": True,
            "description": "Open catalog of the world's scholarly papers",
            "domains": ["all academic fields"],
            "api_key": None,
            "notes": "Free, no API key required. Comprehensive academic database."
        },
        "future_apis": {
            "ieee_xplore": {
                "name": "IEEE Xplore",
                "base_url": "https://ieeexploreapi.ieee.org/api/v1/search/articles",
                "rate_limit": 200,
                "enabled": False,
                "description": "IEEE digital library",
                "domains": ["engineering", "computer science", "robotics"],
                "api_key": "YOUR_IEEE_API_KEY",
                "notes": "Requires API key. Excellent for engineering and robotics papers."
            },
            "acm_digital_library": {
                "name": "ACM Digital Library",
                "base_url": "https://dl.acm.org/api/search",
                "rate_limit": 100,
                "enabled": False,
                "description": "ACM digital library",
                "domains": ["computer science", "human-computer interaction"],
                "api_key": "YOUR_ACM_API_KEY",
                "notes": "Requires API key. Good for HCI and CS papers."
            },
            "springer_nature": {
                "name": "Springer Nature",
                "base_url": "https://api.springernature.com/metadata/json",
                "rate_limit": 5000,
                "enabled": False,
                "description": "Springer Nature publications",
                "domains": ["all academic fields"],
                "api_key": "YOUR_SPRINGER_API_KEY",
                "notes": "Requires API key. Good for multidisciplinary research."
            }
        }
    }
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ API configuration file created: {config_file}")
    return config_file


if __name__ == "__main__":
    # 创建配置文件
    create_api_config_file()
    
    # 测试API管理器
    manager = AcademicAPIManager()
    
    print("🔍 Testing Academic API Manager...")
    
    # 检查API状态
    status = manager.get_api_status()
    print("\n📊 API Status:")
    for api_name, info in status.items():
        status_icon = "✅" if info.get('healthy', False) else "❌"
        print(f"{status_icon} {info['name']}: {info.get('description', '')}")
    
    # 测试搜索
    test_query = "human robot interaction empathy"
    print(f"\n🔍 Testing search with query: '{test_query}'")
    
    results = manager.search_papers(test_query, max_results=5)
    
    total_papers = sum(len(papers) for papers in results.values())
    print(f"\n📚 Total papers found: {total_papers}")
    
    for api_name, papers in results.items():
        print(f"\n📖 {manager.apis[api_name].get('name', api_name)}: {len(papers)} papers")
        for i, paper in enumerate(papers[:2], 1):  # 显示前2篇
            print(f"  {i}. {paper['title'][:80]}...")
            print(f"     Authors: {', '.join(paper['authors'][:3])}")
            print(f"     Year: {paper['year']}, Venue: {paper['venue']}")
            if paper.get('pdf_url'):
                print(f"     PDF: Available")
            print()
