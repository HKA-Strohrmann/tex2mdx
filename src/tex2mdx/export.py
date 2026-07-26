from pathlib import Path
import shutil
import stat


def _ensure_writable(path: Path) -> None:
    if path.exists():
        path.chmod(stat.S_IWRITE | stat.S_IREAD)


def _copy_file_if_needed(source_path: Path, target_path: Path) -> None:
    if source_path.resolve() == target_path.resolve():
        return
    _ensure_writable(target_path)
    shutil.copy2(source_path, target_path)


def export_assets(
    asset_dir: Path,
    media_dir: Path | None,
    media_files: list[Path],
    css_files: list[Path],
    js_files: list[Path],
    source_root: Path | None = None,
    page_dirs: list[Path] | None = None,
) -> None:
    """Export LaTeXML assets to the specified directory."""
    MEDIA_PATH = asset_dir / "media"
    CSS_PATH = asset_dir / "css"
    JS_PATH = asset_dir / "js"

    # TODO: handle file already exists. overwrite!

    # Copy media files
    MEDIA_PATH.mkdir(parents=True, exist_ok=True)
    if media_dir:
        shutil.copytree(media_dir, MEDIA_PATH, dirs_exist_ok=True)
    elif media_files:
        for media_file in media_files:
            if source_root is None:
                target_path = MEDIA_PATH / media_file.name
            else:
                media_path = media_file.relative_to(source_root)
                if media_path.parts and media_path.parts[0] == "media":
                    relative_media_path = Path(*media_path.parts[1:]) if len(media_path.parts) > 1 else Path(media_path.name)
                    target_path = MEDIA_PATH / relative_media_path
                else:
                    target_path = MEDIA_PATH / media_path.name

            target_path.parent.mkdir(parents=True, exist_ok=True)
            _copy_file_if_needed(media_file, target_path)

    if page_dirs and media_files:
        for page_dir in page_dirs:
            for media_file in media_files:
                if source_root is None:
                    target_path = page_dir / "media" / media_file.name
                else:
                    media_path = media_file.relative_to(source_root)
                    if media_path.parts and media_path.parts[0] == "media":
                        relative_media_path = Path(*media_path.parts[1:]) if len(media_path.parts) > 1 else Path(media_path.name)
                        target_path = page_dir / "media" / relative_media_path
                    else:
                        target_path = page_dir / "media" / media_path.name

                target_path.parent.mkdir(parents=True, exist_ok=True)
                _copy_file_if_needed(media_file, target_path)

    # Copy CSS files
    CSS_PATH.mkdir(parents=True, exist_ok=True)
    for css_file in css_files:
        target_css_file = CSS_PATH / css_file.name
        _copy_file_if_needed(css_file, target_css_file)

    # Copy JS files
    JS_PATH.mkdir(parents=True, exist_ok=True)
    for js_file in js_files:
        target_js_file = JS_PATH / js_file.name
        _copy_file_if_needed(js_file, target_js_file)