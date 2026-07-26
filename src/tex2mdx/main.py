import os
import re
import stat
from pathlib import Path
import shutil
import typer
from typing import Annotated
import webbrowser
import subprocess


from tex2mdx import export, ui, latexml, html, mdx


app = typer.Typer(
    add_completion=False,   # dont list '--install-completion' command
    help="CLI for LaTeX to mdx conversion via LaTeXML HTML.",
)

import importlib.metadata
__version__ = importlib.metadata.version('tex2mdx')
def version_callback(value: bool):
    if value:
        print(f"Current Version: {__version__}")
        raise typer.Exit()


def _discover_tex_sources(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]

    excluded_parts = {"latex-template", "website", ".git", "build", "dist"}
    main_sources = [
        tex_file
        for tex_file in sorted(input_path.rglob("main.tex"))
        if not any(part in excluded_parts for part in tex_file.parts)
    ]

    if main_sources:
        return main_sources

    return [
        tex_file
        for tex_file in sorted(input_path.rglob("*.tex"))
        if not any(part in excluded_parts for part in tex_file.parts)
    ]


def _resolve_output_dir(input_path: Path, requested_output_dir: str) -> Path:
    if requested_output_dir != "tex2mdx":
        return Path(requested_output_dir)

    if input_path.is_dir():
        return input_path / "website" / "docs"

    return Path(requested_output_dir)


def _collect_languages_for_topic(repo_root: Path, topic: str) -> set[str]:
    topic_dir = repo_root / topic
    if not topic_dir.exists():
        return set()

    languages: set[str] = set()
    for child in topic_dir.iterdir():
        if child.is_dir() and (child / "main.tex").exists():
            languages.add(child.name)
    return languages


def _copy_topic_assets(repo_root: Path, static_root: Path) -> dict[str, list[Path]]:
    topics = {"apps": {".html"}, "notebooks": {".ipynb"}, "videos": {".mp4", ".webm", ".mov", ".m4v"}}
    copied_assets: dict[str, list[Path]] = {topic: [] for topic in topics}

    for topic, allowed_extensions in topics.items():
        source_dir = repo_root / topic
        target_dir = static_root / topic

        if target_dir.exists():
            shutil.rmtree(target_dir, onexc=_remove_readonly)

        if not source_dir.exists():
            continue

        for source_file in sorted(source_dir.rglob("*")):
            if not source_file.is_file() or source_file.suffix.lower() not in allowed_extensions:
                continue

            relative_path = source_file.relative_to(source_dir)
            target_file = target_dir / relative_path
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, target_file)
            copied_assets[topic].append(relative_path)

    return copied_assets


def _write_course_topic_docs(
    docs_root: Path,
    copied_assets: dict[str, list[Path]],
    lecture_languages: list[str],
    exercise_languages: list[str],
) -> None:
    sidebar_map = {
        "lecture": "lectureSidebar",
        "exercises": "exerciseSidebar",
        "apps": "appsSidebar",
        "videos": "videosSidebar",
        "notebooks": "notebooksSidebar",
    }

    def write_topic_page(topic: str, title: str, body_lines: list[str]) -> None:
        topic_dir = docs_root / topic
        topic_dir.mkdir(parents=True, exist_ok=True)
        page_content = "\n".join(
            [
                "---",
                f'title: "{title}"',
                f"displayed_sidebar: {sidebar_map[topic]}",
                "---",
                "",
                *body_lines,
                "",
            ]
        )
        (topic_dir / "index.mdx").write_text(page_content, encoding="utf-8")

    def extract_title(doc_path: Path) -> str:
        if not doc_path.exists():
            return doc_path.stem
        content = doc_path.read_text(encoding="utf-8")
        match = re.search(r'^title:\s*"([^"]+)"', content, flags=re.MULTILINE)
        return match.group(1) if match else doc_path.stem

    def chapter_sort_key(path: Path) -> int:
        chapter_match = re.fullmatch(r"Ch(\d+)", path.stem)
        if chapter_match:
            return int(chapter_match.group(1))
        return 10_000

    def build_topic_toc(topic: str, languages: list[str]) -> list[str]:
        lines: list[str] = ["## Table of contents", ""]
        for language in languages:
            topic_locale_dir = docs_root / topic / language
            if not topic_locale_dir.exists():
                continue

            lines.append(f"### {language.upper()}")
            lines.append(f"- [Overview](/docs/{topic}/{language}/)")

            chapter_docs = sorted(topic_locale_dir.glob("Ch*.mdx"), key=chapter_sort_key)
            for chapter_doc in chapter_docs:
                chapter_title = extract_title(chapter_doc)
                lines.append(f"- [{chapter_title}](/docs/{topic}/{language}/{chapter_doc.stem})")
            lines.append("")

        return lines if len(lines) > 2 else ["No content generated yet."]

    write_topic_page(
        "lecture",
        "Lecture",
        build_topic_toc("lecture", lecture_languages),
    )
    write_topic_page(
        "exercises",
        "Exercises",
        build_topic_toc("exercises", exercise_languages),
    )

    for topic, title in (("apps", "Apps"), ("videos", "Videos"), ("notebooks", "Notebooks")):
        files = copied_assets.get(topic, [])
        body_lines = [
            f"- [{relative_path.as_posix()}](/{topic}/{relative_path.as_posix()})"
            for relative_path in files
        ]
        write_topic_page(topic, title, body_lines if body_lines else [f"No {topic} content available yet."])


def _sync_course_docs_and_static(repo_root: Path, docs_root: Path, static_root: Path) -> None:
    copied_assets = _copy_topic_assets(repo_root, static_root)
    lecture_languages = sorted(_collect_languages_for_topic(repo_root, "lecture"))
    exercise_languages = sorted(_collect_languages_for_topic(repo_root, "exercises"))
    _write_course_topic_docs(docs_root, copied_assets, lecture_languages, exercise_languages)

@app.command()
def main(
    input_file: Annotated[str, typer.Argument(help="Input LaTeX file or repo root")],
    output_folder: Annotated[str, typer.Option("--output-dir", help="Output folder")] = "tex2mdx",
    media_folder: Annotated[str | None, typer.Option("--media-dir", help="Media directory")] = None,
    new_media_path: Annotated[str | None, typer.Option("--new-media-path", help="New media path")] = "/eit/digitale-signalverarbeitung/latex-assets",
    splitat: Annotated[str, typer.Option("--splitat", help="LaTeXML splitat option (e.g., 'chapter', 'section')")] = "chapter",
    open_preview: Annotated[bool, typer.Option("--open-preview/--no-open-preview", help="Open generated HTML preview in browser")] = False,
    version: Annotated[bool | None, typer.Option("--version", help="Show version and exit", callback=version_callback, is_eager=True)] = None,
) -> typer.Exit:
    """Convert LaTeX sources to MDX."""    

    input_path = Path(input_file)
    if not input_path.exists():
        raise typer.BadParameter(f"Path '{input_path}' must exist.")

    if input_path.is_file() and input_path.suffix != ".tex":
        raise typer.BadParameter(f"File '{input_path}' must be a .tex file.")
    
    output_dir = _resolve_output_dir(input_path, output_folder)
    if output_dir.exists():
        shutil.rmtree(output_dir, onexc=_remove_readonly)
        ui.console.print(f"Cleared output directory '{output_dir}'.")    
    output_dir.mkdir(parents=True, exist_ok=True)

    media_dir = Path(media_folder) if media_folder else None
    if media_dir and not media_dir.exists():
        raise typer.BadParameter(f"Media directory '{media_dir}' does not exist.")

    if input_path.is_dir():
        asset_dir = input_path / "website" / "static" / "latex-assets"
        static_root = input_path / "website" / "static"
        html_root = output_dir.parent / ".tex2mdx-html"
        asset_base_path = "/latex-assets"
    else:
        asset_dir = output_dir
        static_root = output_dir
        html_root = output_dir / "html"
        asset_base_path = new_media_path or "/eit/digitale-signalverarbeitung/latex-assets"

    if asset_dir.exists():
        shutil.rmtree(asset_dir, onexc=_remove_readonly)
    asset_dir.mkdir(parents=True, exist_ok=True)

    if html_root.exists():
        shutil.rmtree(html_root, onexc=_remove_readonly)

    sources = _discover_tex_sources(input_path)
    if not sources:
        raise typer.BadParameter(f"No LaTeX sources found under '{input_path}'.")

    try:
        opened_preview = False

        for source_file in sources:
            if input_path.is_dir():
                source_relative_dir = source_file.relative_to(input_path).parent
                html_output_dir = html_root / source_relative_dir
                mdx_output_dir = output_dir / source_relative_dir
                chapter_sources = sorted((source_file.parent / "chapters").glob("*.tex"))
                topic = source_relative_dir.parts[0] if source_relative_dir.parts else ""
                displayed_sidebar = {
                    "lecture": "lectureSidebar",
                    "exercises": "exerciseSidebar",
                }.get(topic)
            else:
                html_output_dir = html_root
                mdx_output_dir = output_dir / "mdx"
                chapter_sources = []
                displayed_sidebar = None

            html_result: latexml.HTMLResult = latexml.build_html(source_file, html_output_dir, splitat=splitat)
            html_files = [html_result.output_file, *html_result.chapter_files]
            source_texs: list[Path | None] = [source_file]
            if chapter_sources:
                source_texs.extend(chapter_sources[: len(html_result.chapter_files)])
            while len(source_texs) < len(html_files):
                source_texs.append(None)
            html.process_html(html_files, source_texs=source_texs)

            if open_preview and not opened_preview:
                ui.console.print(f"Opening html file in web browser...")
                webbrowser.open(html_result.output_file.resolve().as_uri())
                opened_preview = True

            mdx.build_mdx(
                [html_result.output_file, *html_result.chapter_files],
                mdx_dir=mdx_output_dir,
                source_root=html_output_dir,
                asset_base_path=asset_base_path,
                displayed_sidebar=displayed_sidebar,
            )

            export.export_assets(
                asset_dir,
                media_dir,
                html_result.media_files,
                html_result.css_files,
                html_result.js_files,
                source_root=html_output_dir,
                page_dirs=[html_output_dir, mdx_output_dir],
            )

        if input_path.is_dir():
            _sync_course_docs_and_static(input_path, output_dir, static_root)

        return typer.Exit(code=0)
    

    except Exception as e:
        ui.console.print(f"[bold red]Fatal Unexpected Error: {e}[/bold red]")
        return typer.Exit(code=2)


def _remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)



@app.command()
def check(
    input_file: Annotated[str, typer.Argument(help="Input tex file")],
    build_dir: Annotated[str, typer.Option("--build-dir", help="Directory to store build files.")] = "build",
) -> None:
    """Checks if a LaTeX file compiles with pdftex, lualatex, and latexml."""
    input_path = Path(input_file)
    if not input_path.exists():
        raise typer.BadParameter(f"Input file not found: {input_path}")
    
    common_flags = [
        f"--outdir={build_dir}", 
        "-interaction=nonstopmode", 
        "-synctex=1", 
        "-file-line-error", 
        "--shell-escape",
        "-pdf"
    ]

    tasks = {
        # "pdftex": ["latexmk"] + common_flags + [str(input_path.resolve())],
        "lualatex": ["latexmk", "-lualatex"] + common_flags + [str(input_path.resolve())],
    }

    # ui.console.print(f"Checking compatibility for: [bold cyan]{input_path.resolve()}[/bold cyan]")

    for engine, cmd in tasks.items():
        ui.console.print(f"\n--- Running [bold]{engine}[/bold] ---")

        cleanup_cmd = ["latexmk", "-C", f"--outdir={build_dir}", str(input_path.resolve())]
        subprocess.run(cleanup_cmd, capture_output=True)

        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=False
            )

            if result.returncode == 0:
                ui.console.print(f"[bold green]✓ {engine} compilation successful.[/bold green]")
            else:
                ui.console.print(f"[bold red]✗ {engine} compilation failed.[/bold red]")
                ui.console.print(f"[dim]Error output:\n{result.stderr.strip()}[/dim]")
                
        except FileNotFoundError:
            ui.console.print(f"[bold yellow]! {engine} not found. Is it installed in your PATH?[/bold yellow]")
        except Exception as e:
            ui.console.print(f"[bold red]Error running {engine}: {e}[/bold red]")