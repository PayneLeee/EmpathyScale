"""
PDF reading utilities for extracting text from PDF files.
"""

from pathlib import Path
from typing import Optional

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    try:
        import PyPDF2
        PYPDF2_AVAILABLE = True
    except ImportError:
        PYPDF2_AVAILABLE = False


def read_pdf_text(pdf_path: str) -> str:
    """
    Read text content from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text content as a string
        
    Raises:
        ImportError: If neither pypdf nor PyPDF2 is available
        FileNotFoundError: If PDF file doesn't exist
        Exception: If PDF reading fails
    """
    if not PYPDF_AVAILABLE and not PYPDF2_AVAILABLE:
        raise ImportError("Install pypdf (pip install pypdf) or PyPDF2.")
    
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    text_parts = []
    
    try:
        if PYPDF_AVAILABLE:
            # Use pypdf (preferred)
            with open(pdf_file, 'rb') as f:
                reader = pypdf.PdfReader(f)
                for page_num, page in enumerate(reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text_parts.append(page_text)
                    except Exception as e:
                        print(f"Warning: Failed to extract text from page {page_num}: {e}")
        else:
            # Fallback to PyPDF2
            with open(pdf_file, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page_num, page in enumerate(reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text_parts.append(page_text)
                    except Exception as e:
                        print(f"Warning: Failed to extract text from page {page_num}: {e}")
    except Exception as e:
        raise Exception(f"Failed to read PDF {pdf_path}: {e}")
    
    return "\n\n".join(text_parts)


def extract_sections(pdf_path: str, section_keywords: list = None) -> dict:
    """
    Extract specific sections from a PDF based on keywords.
    
    Args:
        pdf_path: Path to the PDF file
        section_keywords: List of keywords to identify sections
        
    Returns:
        Dictionary mapping section names to text content
    """
    full_text = read_pdf_text(pdf_path)
    
    if section_keywords is None:
        return {"full_text": full_text}
    
    sections = {}
    lines = full_text.split('\n')
    
    current_section = "introduction"
    current_content = []
    
    for line in lines:
        line_lower = line.lower().strip()
        # Check if line matches any section keyword
        matched_keyword = None
        for keyword in section_keywords:
            if keyword.lower() in line_lower and len(line.strip()) < 100:
                matched_keyword = keyword
                break
        
        if matched_keyword:
            # Save previous section
            if current_content:
                sections[current_section] = '\n'.join(current_content)
            # Start new section
            current_section = matched_keyword
            current_content = [line]
        else:
            current_content.append(line)
    
    # Save last section
    if current_content:
        sections[current_section] = '\n'.join(current_content)
    
    return sections







