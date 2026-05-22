import re
from pathlib import Path

RELATIVE_LINKS_PATTERN = re.compile(
    r'\b(href|src|data)\s*=\s*"(?![/#])(?!http)(?!data:)',
    re.IGNORECASE
)

def add_prefix_to_relative_links(prefix: str, html_file: str) -> None:
    """Add a given prefix to all relative links in an HTML file."""
    path = Path(html_file)
    content = path.read_text()
    new_content = RELATIVE_LINKS_PATTERN.sub(rf'\1="{prefix}/', content)
    path.write_text(new_content)


MISSING_PACKAGE_PATTERN = re.compile(
    r"missing files?\[([^\]]+)\]",
    flags=re.IGNORECASE,
)

def list_missing_packages(log_path: Path) -> list[str]:
    """Extract missing package/file names from LaTeXML log output."""
    if not log_path.exists():
        return []

    text = log_path.read_text()
    matches = MISSING_PACKAGE_PATTERN.findall(text)
    
    packages = []
    for match in matches:
        # Handle comma-separated items within brackets
        items = [item.strip() for item in match.split(",")]
        for item in items:
            pkg = format_missing_dependency(item, "")
            if pkg:
                packages.append(pkg)
    
    return packages


def format_missing_dependency(name: str, message_fragment: str) -> str | None:
    if name.endswith((".sty", ".cls")):
        return name
    # Ignore some common low-level issues, this report focuses on the high-level latexml requirements
    elif name.endswith((".css", ".js", ".tex", ".ltx", ".def")):
        return None
    else:
        ext = "cls" if message_fragment == "binding for class" else "sty"
        return f"{name}.{ext}"
    
def list_undefined_macros(log_path: Path) -> list[str]:
    """Extract undefined macro names from LaTeXML log output."""
    if not log_path.exists():
        return []

    text = log_path.read_text()
    pattern = re.compile(r"undefined macros?\[([^\]]+)\]", flags=re.IGNORECASE)
    matches = pattern.findall(text)
    
    macros = []
    for match in matches:
        # Handle comma-separated items within brackets
        items = [item.strip() for item in match.split(",")]
        macros.extend(items)
    
    return macros

def list_unresolved_errors(log_path: Path) -> list[str]:
    """Extract unresolved error messages from LaTeXML log output, excluding undefined errors."""
    if not log_path.exists():
        return []

    text = log_path.read_text()
    # Match Error: lines that don't contain undefined: (using negative lookahead)
    pattern = re.compile(r"Error:(?!undefined:)([^\n]+)", flags=re.IGNORECASE)
    matches = pattern.findall(text)
    
    errors = []
    for match in matches:
        error_msg = match.strip()
        if error_msg:
            errors.append(error_msg)
    
    return errors