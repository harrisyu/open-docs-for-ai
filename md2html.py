#!/usr/bin/env python3
"""
Convert Markdown file to styled HTML file
Requires: pip install markdown pygments
"""

import sys
import argparse
import markdown

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
{css}
</style>
</head>
<body>
<article class="markdown-body">
{content}
</article>
</body>
</html>"""

CSS_STYLES = """
/* Minimal GitHub-like styles */
body {
    box-sizing: border-box;
    min-width: 200px;
    max-width: 980px;
    margin: 0 auto;
    padding: 45px;
}

@media (max-width: 767px) {
    body {
        padding: 15px;
    }
}

.markdown-body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    line-height: 1.5;
}

.markdown-body pre {
    padding: 16px;
    overflow: auto;
    background-color: #f6f8fa;
    border-radius: 6px;
}

.markdown-body code {
    padding: 0.2em 0.4em;
    background-color: #f6f8fa;
    border-radius: 6px;
}

.markdown-body table {
    border-spacing: 0;
    border-collapse: collapse;
}

.markdown-body th,
.markdown-body td {
    padding: 6px 13px;
    border: 1px solid #dfe2e5;
}
"""

def convert_md_to_html(input_file, output_file):
    """Convert markdown file to styled HTML document"""
    with open(input_file, encoding='utf-8') as f:
        md_content = f.read()
    
    html_content = markdown.markdown(
        md_content,
        extensions=['extra', 'codehilite', 'tables']
    )
    
    title = input_file.replace('.md', '').replace('_', ' ').title()
    final_html = HTML_TEMPLATE.format(
        title=title,
        content=html_content,
        css=CSS_STYLES
    )
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_html)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert Markdown to HTML')
    parser.add_argument('input', help='Input markdown file')
    parser.add_argument('-o', '--output', help='Output HTML file')
    args = parser.parse_args()
    
    output_file = args.output if args.output else args.input.replace('.md', '.html')
    
    try:
        convert_md_to_html(args.input, output_file)
        print(f"Successfully converted to {output_file}")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1) 

"""
# Basic conversion
python md2html.py input.md

# Specify output file
python md2html.py input.md -o output.html

# Requirements (install first)
pip install markdown pygments
"""
