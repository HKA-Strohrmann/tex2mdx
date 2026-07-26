from pathlib import Path
from typing import Callable
import re

from tex2mdx import ui


def fix_html_paths(content: str) -> str:
    content = re.sub(r'href="html[/\\]([^"]+)"', r'href="\1"', content)
    content = re.sub(r'src="html[/\\]([^"]+)"', r'src="\1"', content)
    return content


def remove_latexml_page_chrome(content: str) -> str:
    patterns = [
        r"<header\b[^>]*class=\"[^\"]*ltx_page_header[^\"]*\"[^>]*>.*?</header>",
        r"<footer\b[^>]*class=\"[^\"]*ltx_page_footer[^\"]*\"[^>]*>.*?</footer>",
        r"<div\b[^>]*class=\"[^\"]*ltx_page_logo[^\"]*\"[^>]*>.*?</div>",
        r"<[^>]+class=\"[^\"]*(?:ltx_title_document|ltx_title_abstract|ltx_dates|ltx_date|ltx_authors)[^\"]*\"[^>]*>.*?</[^>]+>",
    ]

    cleaned = content
    for pattern in patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL)

    return cleaned


def extract_image_sources(source_tex: Path) -> list[str]:
    text = source_tex.read_text(encoding="utf-8")
    text = re.sub(r"(?<!\\)%.*", "", text)
    pattern = re.compile(r"\\(?:includegraphics|includesvg)(?:\[[^\]]*\])?\{([^}]+)\}", re.DOTALL)
    return [match.strip() for match in pattern.findall(text)]


def restore_image_sources(content: str, source_tex: Path | None) -> str:
    if source_tex is None or not source_tex.exists():
        return content

    source_paths = extract_image_sources(source_tex)
    if not source_paths:
        return content

    source_index = 0

    def replace_img(match: re.Match[str]) -> str:
        nonlocal source_index
        tag = match.group(0)
        if "ltx_missing_image" not in tag and 'src=""' not in tag:
            return tag

        if source_index >= len(source_paths):
            return tag

        replacement_src = source_paths[source_index]
        source_index += 1

        if 'src=""' in tag:
            return tag.replace('src=""', f'src="{replacement_src}"', 1)

        return re.sub(r'src="[^"]*"', f'src="{replacement_src}"', tag, count=1)

    return re.sub(r'<img\b[^>]*>', replace_img, content)

FormatRule = Callable[[str], str]
HTML_PIPELINE: list[FormatRule] = [
    fix_html_paths,
    remove_latexml_page_chrome,
]


def process_html(files: list[Path], source_texs: list[Path | None] | None = None) -> None:
    if source_texs is None:
        source_texs = [None] * len(files)

    if len(source_texs) != len(files):
        raise ValueError("files and source_texs must have the same length")

    for file, source_tex in zip(files, source_texs):
        if not file.exists():
            ui.console.print(f"[bold red]File does not exist: {file}[/bold red]")
            continue

        content = file.read_text(encoding="utf-8")
        for rule in HTML_PIPELINE:
            content = rule(content)
        content = restore_image_sources(content, source_tex)
        file.write_text(content, encoding="utf-8")

    for rule in HTML_PIPELINE:
        ui.console.print(f"[dim]Applied HTML processing rule: '{rule.__name__}'[/dim]")