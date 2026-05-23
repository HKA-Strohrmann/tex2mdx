

from pathlib import Path


def fix_html_paths(html_file: Path) -> None:
    """Fix CSS and JavaScript paths in generated HTML to use forward slashes and relative paths."""
    if not html_file.exists():
        return
    
    content = html_file.read_text(encoding="utf-8")
    
    # Replace Windows-style paths (html\filename) with relative paths (filename)
    # This fixes paths like href="html\arxiv-html-papers-20260131.css" -> href="arxiv-html-papers-20260131.css"
    import re
    content = re.sub(r'href="html[/\\]([^"]+)"', r'href="\1"', content)
    content = re.sub(r'src="html[/\\]([^"]+)"', r'src="\1"', content)
    
    html_file.write_text(content, encoding="utf-8")