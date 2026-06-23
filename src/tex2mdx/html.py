from pathlib import Path
from typing import Callable
import re

from tex2mdx import ui


def fix_html_paths(content: str) -> str:
    content = re.sub(r'href="html[/\\]([^"]+)"', r'href="\1"', content)
    content = re.sub(r'src="html[/\\]([^"]+)"', r'src="\1"', content)
    return content

FormatRule = Callable[[str], str]
HTML_PIPELINE: list[FormatRule] = [
    fix_html_paths,
]


def process_html(files: list[Path]) -> None:

    for rule in HTML_PIPELINE:
        for file in files:
            if not file.exists():
                ui.console.print(f"[bold red]File does not exist: {file}[/bold red]")
                continue

            content = file.read_text(encoding="utf-8")
            content = rule(content)
            file.write_text(content, encoding="utf-8")

        ui.console.print(f"[dim]Applied HTML processing rule: '{rule.__name__}'[/dim]")