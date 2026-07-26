import html
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

from tex2mdx import ui

DEFAULT_TITLE = "My LaTeX Document"
DEFAULT_SIDEBAR_POSITION = 1
DEFAULT_ASSET_BASE_PATH = "/eit/digitale-signalverarbeitung/latex-assets"


def _extract_title(soup: BeautifulSoup, html_path: Path) -> str:

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
    supported_asset_extensions = {
        ".png",
        ".jpg",
        ".jpeg",
        ".svg",
        ".gif",
        ".webp",
        ".bmp",
        ".tiff",
        ".ico",
        ".pdf",
        ".mp4",
        ".webm",
    }

    for element in article_node.find_all(True):
        for attribute_name in ("src", "href", "poster", "data"):
            attribute_value = element.get(attribute_name)
            if attribute_value is None:
                continue

            value = str(attribute_value).strip()
            if not value or value.startswith(("http://", "https://", "mailto:", "#", "/", "data:")):
                continue

            normalized_value = value.replace("\\", "/")
            split_index = min(
                [idx for idx in [normalized_value.find("?"), normalized_value.find("#")] if idx != -1],
                default=-1,
            )
            if split_index == -1:
                path_part = normalized_value
                suffix_part = ""
            else:
                path_part = normalized_value[:split_index]
                suffix_part = normalized_value[split_index:]

            if path_part.endswith(".html"):
                continue

            extension = Path(path_part).suffix.lower()
            if extension not in supported_asset_extensions:
                continue

            if path_part.startswith("media/"):
                rewritten_path = f"{asset_base_path}/{path_part}"
            else:
                rewritten_path = f"{asset_base_path}/media/{Path(path_part).name}"

            element[attribute_name] = f"{rewritten_path}{suffix_part}"


def _rewrite_internal_links(article_node) -> None:
    for anchor in article_node.find_all("a", href=True):
        href = str(anchor["href"])
        if href.startswith(("http", "https", "mailto:", "#", "/")):
            continue

        anchor["href"] = re.sub(r"^([^?#]+)\.html", r"./\1", href)


def _build_mdx_content(
    article_node,
    *,
    title: str,
    sidebar_position: int,
    asset_base_path: str,
    displayed_sidebar: str | None = None,
) -> str:
    escaped_title = title.replace('"', '\\"')
    article_html = str(article_node)
    safe_html_string = json.dumps(article_html)
    toc_proxy_html = _build_toc_proxy(article_node)

    return "\n".join(
        [
            "---",
            f'title: "{escaped_title}"',
            f"sidebar_position: {sidebar_position}",
            *( [f"displayed_sidebar: {displayed_sidebar}"] if displayed_sidebar else [] ),
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
            toc_proxy_html,
            "",
            f"<div dangerouslySetInnerHTML={{{{ __html: {safe_html_string} }}}} />",
            "",
        ]
    )


def _build_toc_proxy(article_node) -> str:
    heading_lines: list[str] = []

    for section_node in article_node.find_all("section"):
        section_id = section_node.get("id")
        if not section_id:
            continue

        heading_tag = section_node.find(
            ["h2", "h3", "h4"],
            class_=lambda class_names: (
                bool(class_names)
                and any(
                    css_class in (
                        class_names
                        if isinstance(class_names, list)
                        else str(class_names).split()
                    )
                    for css_class in {"ltx_title_section", "ltx_title_subsection", "ltx_title_subsubsection"}
                )
            ),
        )
        if heading_tag is None:
            continue

        heading_text = heading_tag.get_text(" ", strip=True)
        if not heading_text:
            continue

        heading_level = heading_tag.name
        heading_lines.append(f'<{heading_level} id="{section_id}">{html.escape(heading_text)}</{heading_level}>')

    if not heading_lines:
        return ""

    return "\n".join(
        [
            '<div className="tex2mdx-toc-proxy" hidden>',
            *heading_lines,
            "</div>",
        ]
    )


def _infer_sidebar_position(relative_html_path: Path | None, fallback_stem: str) -> int:
    if relative_html_path is None:
        return DEFAULT_SIDEBAR_POSITION

    if relative_html_path.stem in {"main", "combined", "index"}:
        return DEFAULT_SIDEBAR_POSITION

    chapter_match = re.fullmatch(r"Ch(\d+)", relative_html_path.stem)
    if chapter_match:
        return int(chapter_match.group(1)) + 1

    leading_number_match = re.match(r"(\d+)", fallback_stem)
    if leading_number_match:
        return int(leading_number_match.group(1)) + 1

    return DEFAULT_SIDEBAR_POSITION


def _generate_mdx_from_html(
    html_path: Path,
    mdx_path: Path,
    sidebar_position: int = DEFAULT_SIDEBAR_POSITION,
    asset_base_path: str = DEFAULT_ASSET_BASE_PATH,
    media_relative_root: Path | None = None,
    displayed_sidebar: str | None = None,
)-> Path:
    """Generate a Docusaurus MDX file from a LaTeXML main page or sub-chapter HTML file."""

    raw_html = html_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(raw_html, "html.parser")
    resolved_title = _extract_title(soup, html_path)
    article_node = _select_article_node(soup)

    _remove_document_title(article_node)
    _rewrite_asset_paths(article_node, asset_base_path)
    _rewrite_internal_links(article_node)

    mdx_content = _build_mdx_content(
        article_node,
        title=resolved_title,
        sidebar_position=sidebar_position,
        asset_base_path=asset_base_path,
        displayed_sidebar=displayed_sidebar,
    )

    mdx_path.parent.mkdir(parents=True, exist_ok=True)
    mdx_path.write_text(mdx_content, encoding="utf-8")
    return mdx_path


def build_mdx(
    html_paths: list[Path],
    mdx_dir: Path,
    source_root: Path | None = None,
    title: str | None = None,
    sidebar_position: int = DEFAULT_SIDEBAR_POSITION,
    asset_base_path: str = DEFAULT_ASSET_BASE_PATH,
    displayed_sidebar: str | None = None,
):
    """Generate MDX files for multiple HTML files."""
    generated_files: list[Path] = []

    for html_path in html_paths:
        relative_html_path = html_path.relative_to(source_root) if source_root is not None else None
        is_root_landing_page = relative_html_path is None or (
            relative_html_path.parent == Path(".") and relative_html_path.stem in {"main", "combined", "index"}
        )

        if source_root is None:
            mdx_name = "index.mdx" if is_root_landing_page else html_path.with_suffix(".mdx").name
            mdx_path = Path(mdx_dir) / mdx_name
        else:
            if is_root_landing_page:
                mdx_path = Path(mdx_dir) / relative_html_path.parent / "index.mdx"
            else:
                mdx_path = Path(mdx_dir) / relative_html_path.with_suffix(".mdx")

        resolved_sidebar_position = _infer_sidebar_position(
            relative_html_path,
            html_path.stem,
        )

        generated_files.append(
            _generate_mdx_from_html(
                html_path,
                mdx_path,
                sidebar_position=resolved_sidebar_position if sidebar_position == DEFAULT_SIDEBAR_POSITION else sidebar_position,
                asset_base_path=asset_base_path,
                media_relative_root=source_root,
                displayed_sidebar=displayed_sidebar,
            )
        )
    
    ui.console.print(f"Successfully generated MDX files at '{mdx_dir}'.")