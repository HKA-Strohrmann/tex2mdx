from pathlib import Path
import re
import subprocess
import logging
from dataclasses import dataclass
from abc import ABC, abstractmethod
import sys
import typer


@dataclass
class LaTeXMLOutput:
    returncode: int
    log: str | None
    missing_packages: list[str]

@dataclass
class ConversionPayload(ABC):
    identifier: int
    single_file: bool | None

    @property
    @abstractmethod
    def name(self) -> str: ...




LATEXML_PATHS = [
    "/opt/ar5iv-bindings/bindings",
    "/opt/ar5iv-bindings/supported_originals",
    "/test/chapters",
    "/test/media",
]
LATEXML_PRELOADS = ["ar5iv.sty"]
LATEXML_LOG_FILE = "__stdout.txt"
LATEXML_TIMEOUT_SEC = 540
LATEXML_MEM_LIMIT_BYTES = 6 * 1024**3
LATEXML_URL_BASE = "https://arxiv.org/static/browse/0.3.4"

def convert_latex_to_html(file, payload: ConversionPayload, workdir: Path, output_dirname: str) -> LaTeXMLOutput:

    # output_dirname = get_file_manager().latexml_output_dir_name(payload)
    output_path = f"{output_dirname}{payload.name}.html"
    log_path = f"{output_dirname}{LATEXML_LOG_FILE}"

    # print(f"Converting {file} to HTML with LaTeXML, output will be at {output_path}", file=sys.stderr)

    latexml_config = [
            "latexmlc.bat",
            "--whatsin=directory",
            "--pmml",
            "--mathtex",
            "--noinvisibletimes",
            "--format=html5",
            "--navigationtoc=context",
            "--splitat=chapter"
            f"--timeout={LATEXML_TIMEOUT_SEC}",
            f"--css={LATEXML_URL_BASE}/css/arxiv-html-papers-20260131.css",
            f"--javascript={LATEXML_URL_BASE}/js/arxiv-html-papers-20260131.js",
            # f"--source={workdir}",
            f"--log={log_path}",
            f"--dest={output_path}",
            f"{file}"
        ]
    
    # for preload in LATEXML_PRELOADS:
        # latexml_config.append(f"--preload={preload}")
    # for path in LATEXML_PATHS:
    #     latexml_config.append(f"--path={path}")

    # print(latexml_config)

    try:
        completed_process = subprocess.run(
            latexml_config,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            text=True,
            timeout=LATEXML_TIMEOUT_SEC + 5,
        )
        returncode = completed_process.returncode
        if returncode != 0:
            logging.error(
                f"LaTeXML conversion failed rc={returncode} "
                f"(mem_limit={LATEXML_MEM_LIMIT_BYTES}) for {payload.identifier}"
            )
    except subprocess.TimeoutExpired as e:
        logging.warning(f"LaTeXML conversion timed out after {e.timeout} seconds")
        returncode = 1
    except Exception as e:
        logging.warning(f"LaTeXML conversion failed with error {e}")
        returncode = 1
    # Note: latexml will write the full conversion log at the path specified by `--log=[path]`,
    # so we can keep the current __stdout.txt convention for now by copying the deposited log.
    return LaTeXMLOutput(
        missing_packages=list_missing_packages(Path(log_path)),
        log=None,  # use the file from --log
        returncode=returncode,
    )


MISSING_PACKAGE_RE = re.compile(
    r"^Warning:missing_file:(\S+)\s(?:Can't\sfind\s(package|binding for class))?", flags=re.MULTILINE
)
def list_missing_packages(latexml_log_path: Path) -> list[str]:
    matches = []
    if latexml_log_path.exists():
        with open(latexml_log_path) as latexml_log_stream:
            for line in latexml_log_stream:
                match = re.search(MISSING_PACKAGE_RE, line)
                if match:
                    matches.append(match)
    return list(filter(None, map(lambda match: format_missing_dependency(match[1], match[2]), matches)))


def format_missing_dependency(name: str, message_fragment: str) -> str | None:
    if name.endswith((".sty", ".cls")):
        return name
    # Ignore some common low-level issues, this report focuses on the high-level latexml requirements
    elif name.endswith((".css", ".js", ".tex", ".ltx", ".def")):
        return None
    else:
        ext = "cls" if message_fragment == "binding for class" else "sty"
        return f"{name}.{ext}"


ANCHOR_REGEX = re.compile(r'\b(href|src|data)\s*=\s*"(?![/#])(?!http)(?!data:)', re.IGNORECASE)
def add_prefix_to_relative_links(prefix: str, html_file_path: str) -> None:
    """Add a given prefix to all relative links in an HTML file."""
    with open(html_file_path, "r+") as html:
        new_text = re.sub(ANCHOR_REGEX, rf'\1="{prefix}/', html.read())
        html.truncate(0)
        html.seek(0)
        html.write(new_text)


class _CLIPayload(ConversionPayload):
    def __init__(self, identifier: int, single_file: bool | None, name: str):
        self.identifier = identifier
        self.single_file = single_file
        self._name = name

    @property
    def name(self) -> str:
        return self._name


def run_cli_conversion(input_path: str, output_dirname: str) -> LaTeXMLOutput:
    p = Path(input_path)
    if p.is_dir():
        raise ValueError(f"Directory input not supported in CLI mode, expected a .tex file but got: {input_path}")
    tex = p
    if not tex.exists():
        raise FileNotFoundError(f"Input tex file not found: {tex}")
    payload = _CLIPayload(identifier=0, single_file=True, name=tex.stem)
    workdir = tex
    if not output_dirname.endswith("/"):
        output_dirname = f"{output_dirname}/"
    return convert_latex_to_html(input_path, payload, workdir, output_dirname)


app = typer.Typer(help="CLI for LaTeXML conversion (test only)")
@app.command()
def main(
    input: str = typer.Option(..., "--input", help="Path to a .tex file"),
    output: str = typer.Option("test/html/", "--output", help="Output directory prefix (will be used as-is)")
) -> int:
    try:
        result = run_cli_conversion(input, output)
        typer.echo(f"returncode={result.returncode}")
        if result.missing_packages:
            typer.echo("missing packages:")
            for pkg in result.missing_packages:
                typer.echo(f" - {pkg}")
        return result.returncode or 0
    except Exception as e:
        typer.echo(f"Conversion failed: {e}")
        return 2


if __name__ == "__main__":
    # raise SystemExit(app())
    result = run_cli_conversion("test/combined.tex", "test/html/")