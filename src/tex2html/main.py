from pathlib import Path
import shutil
import typer
from typing import Annotated

from . import ui
from .preprocess import replace_documentclass
from .latexml import convert_latex_to_html, LaTeXMLOutput


app = typer.Typer(help="CLI for LaTeX to HTML conversion")

import importlib.metadata
__version__ = importlib.metadata.version('tex2html')
def version_callback(value: bool):
    if value:
        print(f"Current Version: {__version__}")
        raise typer.Exit()

@app.command()
def main(
    input_file: Annotated[str, typer.Argument(help="Input LaTeX file")],
    output_file: Annotated[str, typer.Option("--output-file", help="Output file")] = "html/output.html",
    splitat: Annotated[str, typer.Option("--splitat", help="LaTeXML splitat option (e.g., 'chapter', 'section')")] = "chapter",
    version: Annotated[bool | None, typer.Option("--version", callback=version_callback, is_eager=True)] = None,
) -> typer.Exit:
    """Convert a LaTeX file to HTML."""    
    input_path = Path(input_file)
    if not input_path.exists() or not input_path.is_file() or input_path.suffix != ".tex":
        raise typer.BadParameter(f"Invalid input file '{input_path}'. Must be an existing .tex file.")
    
    output_path = Path(output_file)
    if output_path.suffix != ".html":
        raise typer.BadParameter(f"Output file '{output_path}' must have a .html extension.")
    
    output_dir = output_path.parent
    if output_dir.exists():
        shutil.rmtree(output_dir, ignore_errors=True)
        ui.console.print(f"Cleared output directory '{output_dir}'.")    
    output_dir.mkdir(parents=True, exist_ok=True)


    try:
        replace_documentclass(input_path)
        result = convert_latex_to_html(input_path, output_path, splitat)
        
        if result.is_fatal:
            return typer.Exit(code=result.returncode if result.returncode > 0 else 1)
            
        # Return 0 to the OS even if partial results exist, because the CLI "succeeded" 
        # at its task of generating an output.
        return typer.Exit(code=0)

    except Exception as e:
        ui.console.print(f"[bold red]Fatal Unexpected Error: {e}[/bold red]")
        return typer.Exit(code=2)