from pathlib import Path
import shutil


def export_assets(output_dir: Path, media_dir: Path | None, css_files: list[Path], js_files: list[Path], ) -> None:
    """Export assets (images, media files) to the specified asset base path."""

    MEDIA_PATH = output_dir / "media"
    CSS_PATH = output_dir / "css"
    JS_PATH = output_dir / "js"

    # Copy media files
    MEDIA_PATH.mkdir(parents=True, exist_ok=True)
    if media_dir:
        shutil.copytree(media_dir, MEDIA_PATH, dirs_exist_ok=True)

    # Copy CSS files
    CSS_PATH.mkdir(parents=True, exist_ok=True)
    for css_file in css_files:
        shutil.move(css_file, CSS_PATH)

    # Copy JS files
    JS_PATH.mkdir(parents=True, exist_ok=True)
    for js_file in js_files:
        shutil.move(js_file, JS_PATH)