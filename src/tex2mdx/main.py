from pathlib import Path
import shutil
import typer
from typing import Annotated
import webbrowser


from tex2mdx import ui, latexml, html, mdx


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

@app.command()
def main(
    input_file: Annotated[str, typer.Argument(help="Input LaTeX file")],
    output_folder: Annotated[str, typer.Option("--output-dir", help="Output folder")] = "output",
    splitat: Annotated[str, typer.Option("--splitat", help="LaTeXML splitat option (e.g., 'chapter', 'section')")] = "chapter",
    version: Annotated[bool | None, typer.Option("--version", help="Show version and exit", callback=version_callback, is_eager=True)] = None,
) -> typer.Exit:
    """Convert a LaTeX file to mdx."""    

    input_path = Path(input_file)
    if not input_path.exists() or not input_path.is_file() or input_path.suffix != ".tex":
        raise typer.BadParameter(f"File '{input_path}' must exist and be a .tex file.")
    
    output_dir = Path(output_folder)
    if output_dir.exists():
        shutil.rmtree(output_dir, ignore_errors=True)
        ui.console.print(f"Cleared output directory '{output_dir}'.")    
    output_dir.mkdir(parents=True, exist_ok=True)

    HTML_DIR = output_dir / "html"
    MDX_DIR = output_dir / "mdx"
    

    try:
        html_result: latexml.HTMLResult = latexml.build_html(input_path, HTML_DIR, splitat=splitat)

        html.process_html(html_result.chapter_files)

        mdx_result = mdx.build_mdx(html_result.chapter_files, mdx_directory=MDX_DIR)
        # process_mdx(mdx_result)
        
        # export_assets(mdx_result)

        ui.console.print(f"Opening html file '{html_result.output_file}' in web browser...")
        webbrowser.open(html_result.output_file.resolve().as_uri())


        return typer.Exit(code=0)
    

    except Exception as e:
        ui.console.print(f"[bold red]Fatal Unexpected Error: {e}[/bold red]")
        return typer.Exit(code=2)

