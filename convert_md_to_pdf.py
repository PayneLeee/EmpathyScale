#!/usr/bin/env python3
"""
Convert Markdown files to PDF using markdown and weasyprint
Requires: pip install markdown weasyprint
"""

import markdown
from weasyprint import HTML, CSS
from pathlib import Path
import sys

def md_to_pdf(md_path, pdf_path):
    """Convert Markdown file to PDF"""
    # Read markdown file
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convert markdown to HTML
    html_content = markdown.markdown(
        md_content,
        extensions=['extra', 'codehilite', 'tables']
    )
    
    # Add CSS styling
    html_doc = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: A4;
                margin: 1in;
            }}
            body {{
                font-family: 'Times New Roman', serif;
                line-height: 1.6;
                max-width: 800px;
                margin: 0 auto;
            }}
            h1 {{
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
            }}
            h2 {{
                color: #34495e;
                margin-top: 30px;
            }}
            h3 {{
                color: #7f8c8d;
                margin-top: 20px;
            }}
            ul, ol {{
                margin-left: 20px;
            }}
            code {{
                background-color: #f4f4f4;
                padding: 2px 4px;
                border-radius: 3px;
            }}
            pre {{
                background-color: #f4f4f4;
                padding: 10px;
                border-radius: 5px;
                overflow-x: auto;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Generate PDF
    HTML(string=html_doc).write_pdf(pdf_path)
    print(f"✓ Converted: {md_path} -> {pdf_path}")

if __name__ == "__main__":
    # File paths
    co_assembly_md = Path("data/runs/2025-10-31_131000/empathy_scale_generation_agent_group/scale_draft.md")
    chat_collab_md = Path("data/runs/2025-10-31_132506/empathy_scale_generation_agent_group/scale_draft.md")
    
    # Output paths
    co_assembly_pdf = co_assembly_md.with_suffix('.pdf')
    chat_collab_pdf = chat_collab_md.with_suffix('.pdf')
    
    # Convert files
    try:
        md_to_pdf(co_assembly_md, co_assembly_pdf)
        md_to_pdf(chat_collab_md, chat_collab_pdf)
        print("\n✅ All files converted successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure to install required packages:")
        print("  pip install markdown weasyprint")

