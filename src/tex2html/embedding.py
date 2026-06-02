import json
import re
from pathlib import Path
from typing import Iterable

from bs4 import BeautifulSoup

from tex2html import ui

DEFAULT_TITLE = "My LaTeX Document"
DEFAULT_SIDEBAR_POSITION = 1
DEFAULT_ASSET_BASE_PATH = "/eit/digitale-signalverarbeitung/latex-assets"


def _extract_title(soup: BeautifulSoup, html_path: Path, title: str | None) -> str:
    if title is not None:
        return title

    title_node = soup.find(class_="ltx_title") or soup.find("title")
    if title_node is not None:
        raw_title = title_node.get_text().strip()
        return re.sub(r"^chapter\s+", "", raw_title, flags=re.IGNORECASE)

    return html_path.stem.replace("_", " ").title()


def _select_article_node(soup: BeautifulSoup):
    return (
        soup.find("article", class_="ltx_document")
        or soup.find("div", class_="ltx_page_main")
        or soup.find("div", class_="ltx_page_content")
        or soup.body
        or soup
    )


def _remove_document_title(article_node) -> None:
    title_node = article_node.find(
        lambda tag: getattr(tag, "name", None) in {"h1", "h2", "div", "span"}
        and "ltx_title" in (tag.get("class") or [])
        and any(
            title_class in (tag.get("class") or [])
            for title_class in {
                "ltx_title_document",
                "ltx_title_chapter",
                "ltx_title_part",
            }
        )
    )

    if title_node is not None:
        title_node.decompose()


def _rewrite_asset_paths(article_node, asset_base_path: str) -> None:
    for img in article_node.find_all("img"):
        old_src = img.get("src")
        if old_src is None:
            continue

        old_src_text = str(old_src)
        if old_src_text and not old_src_text.startswith(("http", "/")):
            img["src"] = f"{asset_base_path}/{old_src_text}"

    for obj in article_node.find_all("object"):
        old_data = obj.get("data")
        if old_data is None:
            continue

        old_data_text = str(old_data)
        if old_data_text and not old_data_text.startswith(("http", "/")):
            obj["data"] = f"{asset_base_path}/{old_data_text}"


def _rewrite_internal_links(article_node) -> None:
    for anchor in article_node.find_all("a", href=True):
        href = str(anchor["href"])
        if href.startswith(("http", "https", "mailto:", "#", "/")):
            continue

        anchor["href"] = re.sub(r"^([^?#]+)\.html", r"./\1", href)


def _build_mdx_content(
    html_path: Path,
    article_node,
    *,
    title: str,
    sidebar_position: int,
    asset_base_path: str,
) -> str:
    article_html = str(article_node)
    safe_html_string = json.dumps(article_html)

    return "\n".join(
        [
            "---",
            f"title: {title}",
            f"sidebar_position: {sidebar_position}",
            "---",
            "",
            "import Head from '@docusaurus/Head';",
            "",
            "<Head>",
            f'  <link rel="stylesheet" href="{asset_base_path}/LaTeXML.css" />',
            f'  <link rel="stylesheet" href="{asset_base_path}/ltx-book.css" />',
            f'  <link rel="stylesheet" href="{asset_base_path}/cleanup.css" />',
            "</Head>",
            "",
            f"<div dangerouslySetInnerHTML={{{{ __html: {safe_html_string} }}}} />",
            "",
        ]
    )


def _generate_mdx_from_html(
    html_file: str | Path,
    mdx_file: str | Path | None = None,
    *,
    title: str | None = None,
    sidebar_position: int = DEFAULT_SIDEBAR_POSITION,
    asset_base_path: str = DEFAULT_ASSET_BASE_PATH,
)-> Path:
    """Generate a Docusaurus MDX file from a LaTeXML main page or sub-chapter HTML file."""
    html_path = Path(html_file)
    if mdx_file is None:
        mdx_path = html_path.with_suffix(".mdx")
    else:
        mdx_path = Path(mdx_file)

    raw_html = html_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(raw_html, "html.parser")
    resolved_title = _extract_title(soup, html_path, title)
    article_node = _select_article_node(soup)

    _remove_document_title(article_node)
    _rewrite_asset_paths(article_node, asset_base_path)
    _rewrite_internal_links(article_node)

    mdx_content = _build_mdx_content(
        html_path,
        article_node,
        title=resolved_title,
        sidebar_position=sidebar_position,
        asset_base_path=asset_base_path,
    )

    mdx_path.parent.mkdir(parents=True, exist_ok=True)
    mdx_path.write_text(mdx_content, encoding="utf-8")
    return mdx_path


def generate_mdx_from_html_files(
    html_files: Iterable[str | Path],
    *,
    mdx_directory: str | Path | None = None,
    title: str | None = None,
    sidebar_position: int = DEFAULT_SIDEBAR_POSITION,
    asset_base_path: str = DEFAULT_ASSET_BASE_PATH,
):
    """Generate MDX files for multiple HTML files."""
    generated_files: list[Path] = []
    for html_file in html_files:
        html_path = Path(html_file)
        if mdx_directory is None:
            mdx_path = None
        else:
            mdx_path = Path(mdx_directory) / html_path.with_suffix(".mdx").name

        generated_files.append(
            _generate_mdx_from_html(
                html_path,
                mdx_path,
                title=title,
                sidebar_position=sidebar_position,
                asset_base_path=asset_base_path,
            )
        )
    
    ui.console.print(f"Generated MDX files at '{mdx_directory}'.")