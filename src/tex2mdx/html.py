from pathlib import Path
from typing import Callable
import re

import ui


HtmlRule = Callable[[str], str]


def fix_html_paths(content: str) -> str:
    content = re.sub(r'href="html[/\\]([^"]+)"', r'href="\1"', content)
    content = re.sub(r'src="html[/\\]([^"]+)"', r'src="\1"', content)
    return content


HTML_PIPELINE: list[HtmlRule] = [
    fix_html_paths,
]


def process_html(files: list[Path], rules: list[HtmlRule] = HTML_PIPELINE) -> None:
    for file in files:
        if not file.exists():
            ui.console.print(f"[red]Missing file: {file}[/red]")
            continue

        content = file.read_text(encoding="utf-8")

        for rule in rules:
            content = rule(content)

        file.write_text(content, encoding="utf-8")