from dataclasses import dataclass
from pathlib import Path
import subprocess
import typer

import re
from pathlib import Path
from collections import Counter

IMG_SRC_RE = re.compile(r'src="([^"]+\.(?:png|jpg|jpeg|svg|gif))"')

from .format_logs import list_missing_packages, list_undefined_macros
from . import ui


# Configuration
LATEXML_TIMEOUT_SEC = 540

# Asset paths relative to this file
ASSETS_DIR = Path(__file__).parent / "assets"
CSS_PATH = ASSETS_DIR / "cleanup.css"


@dataclass
class HTMLResult:
    output_file: Path
    chapter_files: list[Path]
    media_files: list[Path]
    css_files: list[Path]
    js_files: list[Path]
    log_file: Path


def build_html(input_file: Path, output_dir: Path, splitat: str) -> HTMLResult:
    """Convert LaTeX file to HTML using LaTeXML."""
    output_file = output_dir / f"{input_file.stem}.html"

    log_path = output_file.with_suffix(".log").resolve()
    ui.console.print(f"LaTeXML logs are written to '{log_path}'.")

    # Build LaTeXML command
    latexml_config = [
        "latexmlc.bat",
        "--presentationmathml",
        "--mathtex",
        "--format=html5",
        "--graphicsmap=pdf.",
        f"--splitat={splitat}",
        f"--log={log_path}",
        f"--timeout={LATEXML_TIMEOUT_SEC}",
        f"--css={str(CSS_PATH.resolve())}",
        f"--dest={output_file.resolve()}",
    ]
    for binding in ASSETS_DIR.glob("*.sty.ltxml"):
        latexml_config.append(f"--preload={binding.resolve()}")
    latexml_config.append(str(input_file))

    ui.console.print(f"[dim]Command: {' '.join(latexml_config)}[/dim]")

    returncode = -1
    is_fatal = False

    with ui.console.status("[bold blue]Running LaTeXML conversion (this may take a while)...[/bold blue]"):
        try:
            result = subprocess.run(
                latexml_config,
                check=False,
                text=True,
                timeout=LATEXML_TIMEOUT_SEC + 5,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE, # Capture stdout so it doesn't bleed into the CLI
            )
            returncode = result.returncode
            if result.stderr:
                ui.console.print("[dim]Output: [/dim]")
                ui.console.print(f"[dim]{result.stderr.strip()}[/dim]")

            if returncode == 0:
                ui.console.print(f"Successfully written LaTeXML conversion to '{output_file}'.")
            else:
                ui.console.print(f"[bold red]LaTeXML encountered errors (Exit code {returncode})[/bold red]")
                is_fatal = True

        except subprocess.TimeoutExpired:
            ui.console.print(f"[bold red]LaTeXML conversion timed out after {LATEXML_TIMEOUT_SEC}s[/bold red]")
            is_fatal = True
        except FileNotFoundError:
            ui.console.print("[bold red]Could not find 'latexmlc.bat'. Is LaTeXML installed and in your PATH?[/bold red]")
            is_fatal = True
        except Exception as e:
            ui.console.print(f"[bold red]Unexpected execution error:[/bold red] {e}")
            is_fatal = True

    missing_packages = []
    undefined_macros = []
    # unresolved_errors = []
    
    if log_path.exists():
        missing_packages = list_missing_packages(log_path)
        if missing_packages:
            ui.console.print(f"[yellow]  Missing packages:[/yellow] {', '.join(missing_packages)}")
            
        undefined_macros = list_undefined_macros(log_path)
        if undefined_macros:
            ui.console.print(f"[yellow]  Undefined macros:[/yellow] {', '.join(undefined_macros)}")

        # unresolved_errors = list_unresolved_errors(log_path)
        # if unresolved_errors:
        #     ui.console.print(f"[yellow]  Unresolved errors:[/yellow] {', '.join(unresolved_errors)}")

    if is_fatal:
        typer.Exit(code=returncode if returncode > 0 else 1)

        
    return HTMLResult(
        output_file=output_file,
        chapter_files=sorted(output_dir.glob("Ch*.html")),  # TODO: is this sufficient, even for different splitat values?
        media_files=get_media_files(output_dir),
        css_files=sorted(output_dir.rglob("*.css")),
        js_files=sorted(output_dir.rglob("*.js")),
        log_file=log_path
    )


def get_media_files(output_dir: Path) -> list[Path]:
    IMAGE_EXTS = {
        ".png", ".jpg", ".jpeg", ".svg", ".gif",
        ".webp", ".bmp", ".tiff", ".ico", ".pdf"
    }

    files = []
    for p in output_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
            files.append(p)

    return sorted(files)
