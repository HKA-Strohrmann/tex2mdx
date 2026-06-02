

from pathlib import Path
import re


def fix_html_paths(html_file: Path) -> None:
    """Fix CSS and JavaScript paths in all generated HTML files to use relative paths."""
    if not html_file.exists():
        return
    
    output_dir = html_file.parent
    
    # Process the main output file and all generated chapter files
    html_files_to_fix = [html_file]
    html_files_to_fix.extend(output_dir.glob("Ch*.html"))
    
    for file in html_files_to_fix:
        if not file.exists():
            continue
            
        content = file.read_text(encoding="utf-8")
        
        # Replace Windows-style paths (html\filename) with relative paths (filename)
        # This fixes paths like href="html\arxiv-html-papers-20260131.css" -> href="arxiv-html-papers-20260131.css"
        content = re.sub(r'href="html[/\\]([^"]+)"', r'href="\1"', content)
        content = re.sub(r'src="html[/\\]([^"]+)"', r'src="\1"', content)
        
        file.write_text(content, encoding="utf-8")


ANCHOR_REGEX = re.compile(r'\b(href|src|data)\s*=\s*"(?![/#])(?!http)(?!data:)', re.IGNORECASE)

def add_prefix_to_relative_links(prefix: str, html_file_path: str) -> None:
    """Add a given prefix to all relative links in an HTML file."""
    with open(html_file_path, "r+") as html:
        new_text = re.sub(ANCHOR_REGEX, rf'\1="{prefix}/', html.read())
        html.truncate(0)
        html.seek(0)
        html.write(new_text)#
