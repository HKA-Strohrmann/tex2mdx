# tex2mdx Conversion Tool

Converts your LaTeX documents to HTML via [LaTeXML](https://github.com/brucemiller/latexml). THe files are then post-processed to the [MDX format](https://mdxjs.com/) and styled with custom CSS. The resulting files can be used in the web application [Strohrmann Lecture Platform](https://github.com/HKA-Strohrmann/strohrmann-lecture-platform).

The underlying invocation commands and custom CSS/JavaScript files are based on the [arXiv-view-as-html](https://github.com/arXiv/arxiv-view-as-html) pipeline. Check out their [official blog post](https://arxiv.org/html/2402.08954v1) for more details.

## Requirements

- [Python](https://www.python.org/downloads/) 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [LaTeX distribution](https://www.latex-project.org/get/): [MiKTeX](https://miktex.org/download) is recommended for Windows.
- [Ghostscript](https://www.ghostscript.com/releases/gsdnld.html): You probably want to install the 64bit GNU Affero General Public License version.
- [Perl](https://www.perl.org/get.html#win32): If you are on Windows, select Strawberry Perl.
- [ImageMagick](https://imagemagick.org/download/#gsc.tab=0): Please select a dynamic binary distribution (e.g., `ImageMagick-7.x.x-Q16-HDRI-x64-dll.exe`).
- [LaTeXML](https://math.nist.gov/~BMiller/LaTeXML/get.html)
- Optional: [Inkscape](https://inkscape.org/release/inkscape-1.4.2/windows/64-bit/msi/dl/) to compile SVG files to pdf.



### Manual Windows Setup

The ImageMagick has to be binded to your Perl installation. On Windows, there is an issue when ImageMagick is installed via Perl. To work around this issue, you will have to:

1. Download ImageMagick from their website. Ensure the following additional tasks are checked when installing the binary/exe file on Windows:
  
    ![install options for image magick](<docs/ImageMagick install.png>)

2. Manually disable the error message in `magick-baseconfig.h` (e.g.: `C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\include\MagickCore\magick-baseconfig.h`): 
    ```c
    #if MAGICKCORE_CHANNEL_MASK_DEPTH == 64
     #  if !defined(__cplusplus) && !defined(c_plusplus)
    -#    error ImageMagick was build with a 64 channel bit mask and that requires a C++ compiler
    +// #    error ImageMagick was build with a 64 channel bit mask and that requires a C++ compiler
     #  endif
    #endif
    ```
    See this [issue](https://github.com/StrawberryPerl/Perl-Dist-Strawberry/issues/140#issuecomment-1756627785) for more details.
3. Now you can install the ImageMagick perl binding via cpanm:
    ```bash
    cpanm --force Image::Magick
    ```

### Automated Windows Setup

If you are on Windows, you can automate the installations of the requirements and `tex2mdx` using [WinGet](https://learn.microsoft.com/de-de/windows/package-manager/winget/) via this [sctipt file](scripts/setup.ps1).


### Confirm Requirements

Please make sure all tools are part of your system PATH for easy command line access. Test by confirming the ouput of:

```bash
python --version
uv --version
gswin64c.exe -version
magick --version
perl --version
latexmk --version
latexml --VERSION
inkscape --version
```

## Install

Uv handles python dependencies, virtual environments and script execution. To install the project, run the following commands:

```bash
git clone https://github.com/HKA-Strohrmann/tex2mdx.git
cd tex2mdx
uv sync
uv tool install . # makes tex2mdx available anywhere
```

## Usage

To convert a LaTeX file to HTML, run the following command:

```bash
tex2mdx "myfile.tex" --output-file "html/myfile.html"
start "html/myfile.html" # opens in default browser
```

A detailed list of options can be found by running:

```bash
tex2mdx --help
```

## Testing

To test changes locally, synchronize your test assets and run the parser:

```powershell
cd test

uv run tex2mdx "combined.tex" --output-dir "output" --media-dir "new_media"
```

### Test LaTeX compilation

Test latex compilation in pdftex and lualatex:

```bash
latexmk -C --outdir="_build" && latexmk -pdf -interaction=nonstopmode -synctex=1 -file-line-error --shell-escape --outdir="_build" combined.tex
latexmk -C --outdir="_build" && latexmk -lualatex -pdf -interaction=nonstopmode -synctex=1 -file-line-error --shell-escape --outdir="_build" combined.tex
```

## Update Version

To make the global version use an updated version of this package, run the following commands on project root:

```bash
uv version # current version
uv version --bump patch # select either major, minor or patch
($version = python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")

git commit -a -m "Prepared for release $version"
git push

git tag -a "v$version" -m "Release v$version"
git push --tags

uv tool install .
uv tool upgrade tex2mdx
```

## To Do

- --whatsout=fragment for embedding in other pages?
- --javascript=LaTeXML-maybeMathJax.js: The LaTeXML-maybeMathJax.js script loads MathJax for browsers without native MathML support, as a fallback rendering solution.
- babel does not work, figure captions will not render in german. maybe pin babel version to fix?
- dont wipe the full html folder every run, only the affected files. 
- update module to explicitly export mdx files. html files are a temp resource and can be used for quick validation.
- why no right hand side navigation bar for sections?

Why is this part of the arvix codebase?

```python
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
```