import re
import subprocess
from pathlib import Path

from bs4 import BeautifulSoup
from flask import current_app

from ...domain.conversion import ConversionPayload, LaTeXMLOutput
from ..files import get_file_manager

MISSING_PACKAGE_RE = re.compile(
    r"^Warning:missing_file:(\S+)\s(?:Can't\sfind\s(package|binding for class))?", flags=re.MULTILINE
)


def format_missing_dependency(name: str, message_fragment: str) -> str | None:
    if name.endswith((".sty", ".cls")):
        return name
    # Ignore some common low-level issues, this report focuses on the high-level latexml requirements
    elif name.endswith((".css", ".js", ".tex", ".ltx", ".def")):
        return None
    else:
        ext = "cls" if message_fragment == "binding for class" else "sty"
        return f"{name}.{ext}"


def list_missing_packages(latexml_log: str) -> list[str]:
    matches = MISSING_PACKAGE_RE.findall(latexml_log)
    return list(filter(None, map(lambda match: format_missing_dependency(match[0], match[1]), matches)))


def latexml(payload: ConversionPayload, workdir: Path) -> LaTeXMLOutput:
    LATEXML_URL_BASE = current_app.config["LATEXML_URL_BASE"]

    output_path = f"{get_file_manager().latexml_output_dir_name(payload)}{payload.name}.html"

    latexml_config = [
        "latexmlc",
        "--preload=[nobibtex,nobreakuntex,localrawstyles,mathlexemes,magnify=1.2,zoomout=1.2,tokenlimit=249999999,iflimit=3599999,absorblimit=1299999,pushbacklimit=599999]latexml.sty",
        "--preload=ar5iv.sty",
        "--path=/opt/ar5iv-bindings/bindings",
        "--path=/opt/ar5iv-bindings/supported_originals",
        "--pmml",
        "--mathtex",
        "--noinvisibletimes",
        "--timeout=600",
        "--nodefaultresources",
        "--format=html5",
        "--css=https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css",
        f"--css={LATEXML_URL_BASE}/css/ar5iv.0.8.2.min.css",
        f"--css={LATEXML_URL_BASE}/css/ar5iv-fonts.0.8.2.min.css",
        f"--css={LATEXML_URL_BASE}/css/latexml_styles.0.8.2.css",
        "--javascript=https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js",
        "--javascript=https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.3.3/html2canvas.min.js",
        f"--javascript={LATEXML_URL_BASE}/js/addons_new.js",
        f"--javascript={LATEXML_URL_BASE}/js/feedbackOverlay.js",
        "--navigationtoc=context",
        "--whatsin=directory",
        f"--source={workdir}",
        f"--dest={output_path}",
    ]

    completed_process = subprocess.run(
        latexml_config, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True, text=True, timeout=500
    )

    return LaTeXMLOutput(
        output=completed_process.stdout, missing_packages=list_missing_packages(completed_process.stdout)
    )


def insert_base_tag(idv: str, html_file_path: str) -> None:
    """Insert the base tag into the html so we can use the /html/arxiv_id url."""
    base_html = f'<base href="/html/{idv}/">'

    with open(html_file_path, "r+") as html:
        soup = BeautifulSoup(html.read(), "html.parser")
        if soup.head:
            soup.head.append(BeautifulSoup(base_html, "html.parser"))
            html.truncate(0)
            html.seek(0)
            html.write(str(soup))


def replace_relative_anchors(absolute_base: str, html_file_path: str) -> None:
    """Replace all the relative anchor tags with absolute anchors."""
    # Note: If this causes bugs, use a SAX parser to do this more accurately
    # while still not needing to completely rebuild the DOM in memory with bs4
    ANCHOR_REGEX = re.compile(r'href="#')
    with open(html_file_path, "r+") as html:
        new_text = re.sub(ANCHOR_REGEX, f'href="{absolute_base}#', html.read())
        html.truncate(0)
        html.seek(0)
        html.write(new_text)
