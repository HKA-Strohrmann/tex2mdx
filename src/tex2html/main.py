from pathlib import Path
import re
import subprocess
from dataclasses import dataclass
import typer


@dataclass
class LaTeXMLOutput:
    returncode: int
    log: str | None
    missing_packages: list[str]


LATEXML_PATHS = [
    "/opt/ar5iv-bindings/bindings",
    "/opt/ar5iv-bindings/supported_originals",
    "/test/chapters",
    "/test/media",
]
LATEXML_PRELOADS = ["ar5iv.sty"]
LATEXML_LOG_FILE = "_stdout.txt"
LATEXML_TIMEOUT_SEC = 540
LATEXML_MEM_LIMIT_BYTES = 6 * 1024**3
LATEXML_URL_BASE = "https://arxiv.org/static/browse/0.3.4"

def convert_latex_to_html(tex_file: str, output_filename: str, workdir: Path, output_dirname: str) -> LaTeXMLOutput:
    """Convert LaTeX file to HTML using LaTeXML."""
    output_path = f"{output_dirname}{output_filename}.html"
    log_path = f"{output_dirname}{LATEXML_LOG_FILE}"

    latexml_config = [
            "latexmlc.bat",
            "--whatsin=directory",
            "--pmml",
            "--mathtex",
            "--noinvisibletimes",
            "--format=html5",
            "--navigationtoc=context",
            "--splitat=chapter",
            f"--timeout={LATEXML_TIMEOUT_SEC}",
            f"--css={LATEXML_URL_BASE}/css/arxiv-html-papers-20260131.css",
            f"--javascript={LATEXML_URL_BASE}/js/arxiv-html-papers-20260131.js",
            # f"--source={workdir}",
            f"--log={log_path}",
            f"--dest={output_path}",
            f"{tex_file}"
        ]
    
    # for preload in LATEXML_PRELOADS:
        # latexml_config.append(f"--preload={preload}")
    # for path in LATEXML_PATHS:
    #     latexml_config.append(f"--path={path}")

    # print(latexml_config)

    try:
        result = subprocess.run(
            latexml_config,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            text=True,
            timeout=LATEXML_TIMEOUT_SEC + 5,
        )
        if result.returncode != 0:
            print(f"LaTeXML conversion failed with rc={result.returncode}")
        returncode = result.returncode
    except subprocess.TimeoutExpired:
        print(f"LaTeXML conversion timed out after {LATEXML_TIMEOUT_SEC} seconds")
        returncode = 1
    except Exception as e:
        print(f"LaTeXML conversion failed: {e}")
        returncode = 1

    return LaTeXMLOutput(
        missing_packages=list_missing_packages(Path(log_path)),
        log=None,
        returncode=returncode,
    )


MISSING_PACKAGE_PATTERN = re.compile(
    r"^Warning:missing_file:(\S+)\s(?:Can't\sfind\s(package|binding for class))?",
    flags=re.MULTILINE
)

def list_missing_packages(log_path: Path) -> list[str]:
    """Extract missing package names from LaTeXML log file."""
    packages = []
    if log_path.exists():
        with open(log_path) as f:
            for line in f:
                match = MISSING_PACKAGE_PATTERN.search(line)
                if match:
                    pkg = format_missing_dependency(match[1], match[2])
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


def run_cli_conversion(input_path: str, output_dir: str) -> LaTeXMLOutput:
    """Run LaTeX to HTML conversion from CLI."""
    tex_file = Path(input_path)
    
    if not tex_file.is_file() or tex_file.suffix != ".tex":
        raise FileNotFoundError(f"Input must be a .tex file: {input_path}")
    
    if not output_dir.endswith("/"):
        output_dir = f"{output_dir}/"
    
    return convert_latex_to_html(str(tex_file), tex_file.stem, tex_file, output_dir)


app = typer.Typer(help="CLI for LaTeX to HTML conversion")

@app.command()
def main(
    input: str = typer.Option(..., "--input", help="Path to a .tex file"),
    output: str = typer.Option("test/html/", "--output", help="Output directory"),
) -> int:
    """Convert a LaTeX file to HTML."""
    try:
        result = run_cli_conversion(input, output)
        typer.echo(f"returncode={result.returncode}")
        if result.missing_packages:
            typer.echo("missing packages:")
            for pkg in result.missing_packages:
                typer.echo(f"  - {pkg}")
        return result.returncode or 0
    except Exception as e:
        typer.echo(f"Error: {e}")
        return 2


if __name__ == "__main__":
    result = run_cli_conversion("test/combined.tex", "test/html/")