import re
from pathlib import Path

from . import ui


def replace_documentclass(tex_file: Path) -> None:
    """
    Replace KOMA scrbook class with standard book class.
    KOMA is not supported by LaTeXML, so we replace it with the standard book class.
    Handles multiline documentclass declarations with optional arguments and comments.
    """
    if not tex_file.exists():
        return
    
    content = tex_file.read_text()
    
    # Match \documentclass with optional arguments (possibly spanning multiple lines)
    # followed by {scrbook}, and replace scrbook with book.
    # [\s\S]*? matches any character including newlines (non-greedy)
    new_content = re.sub(
        r"\\documentclass\s*(?:\[[\s\S]*?\])?\s*\{scrbook\}",
        lambda m: m.group(0).replace("scrbook", "book"),
        content
    )
    
    if new_content != content:
        tex_file.write_text(new_content)
        ui.console.print(f"Replaced 'scrbook' with 'book' in '{tex_file}'.")