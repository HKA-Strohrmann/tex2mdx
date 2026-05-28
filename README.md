# tex2html Conversion Tool

Converts your LaTeX documents to HTML via [LaTeXML](https://github.com/brucemiller/latexml).

The underlying invocation commands and custom CSS/JavaScript files are based on the [arXiv-view-as-html](https://github.com/arXiv/arxiv-view-as-html) pipeline. Check out their [official blog post](https://arxiv.org/html/2402.08954v1) for more details.

## Requirements

- [Python](https://www.python.org/downloads/) 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [LaTeX distribution](https://www.latex-project.org/get/), [MiKTeX](https://miktex.org/download) is recommended.
- [Ghostscript](https://www.ghostscript.com/releases/gsdnld.html): You probably want to install the 64bit GNU Affero General Public License version.
- [Perl](https://www.perl.org/get.html#win32): If you are on Windows, select strawberry perl.
- [ImageMagick](https://imagemagick.org/download/#gsc.tab=0): Please select a dynamic binary distribution (e.g., `ImageMagick-7.1.2-Q16-HDRI-x64-dll.exe`).
- [LaTeXML](https://math.nist.gov/~BMiller/LaTeXML/get.html)
- Optional: [Inkscape](https://inkscape.org/release/inkscape-1.4.2/windows/64-bit/msi/dl/) to compile SVG files to pdf.



### Manual Windows Setup

The ImageMagick has also be binded to your Perl installation. On Windows, there is an issue when ImageMagick is installed with a 64 channel bit mask, which requires a C++ compiler. To work around this issue, you will have to:

1. Ensure the following additional tasks are checked when installing the binary/exe file on Windows:
  
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

If you are on Windows, you can automate the tool installations using winget via PowerShell:

```powershell
winget install Python.Launcher astral-sh.uv StrawberryPerl.StrawberryPerl MiKTeX.MiKTeX Inkscape.Inkscape Microsoft.VisualStudio.2022.BuildTools
start "https://www.ghostscript.com/releases/gsdnld.html"
start "https://imagemagick.org/download/#gsc.tab=0"
write-warning "Please modify the file 'magick-baseconfig.h' file before continuing!"

cpanm --force Image::Magick
cpanm --force LaTeXML
```


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
git clone https://github.com/HKA-Strohrmann/tex2html.git
cd tex2html
uv sync
uv tool install . # makes tex2html available anywhere
```

## Usage

To convert a LaTeX file to HTML, run the following command:

```bash
tex2html "myfile.tex" --output-file "html/myfile.html"
start html/myfile.html # opens in default browser
```

A detailed list of options can be found by running:

```bash
tex2html --help
```

## Testing

To test changes locally, synchronize your test assets and run the parser:

```powershell
copy-item "C:\Users\Jax\Coding\Strohrmann-Lecture-Platform\doc2tex\test\skript\chapters" -destination "C:\Users\Jax\Coding\Strohrmann-Lecture-Platform\tex2html\test" -recurse -force
copy-item "C:\Users\Jax\Coding\Strohrmann-Lecture-Platform\doc2tex\test\skript\new media" -destination "C:\Users\Jax\Coding\Strohrmann-Lecture-Platform\tex2html\test" -recurse -force
copy-item "C:\Users\Jax\Coding\Strohrmann-Lecture-Platform\doc2tex\test\skript\combined.tex" -destination "C:\Users\Jax\Coding\Strohrmann-Lecture-Platform\tex2html\test" -recurse -force

cd test

uv run tex2html "combined.tex" --output-file "html/combined.html"
start html/combined.html
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
uv version --bump patch # select (in order of magnitude) major, minor, patch
($version = python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")

git commit -a -m "Prepared for release $version"
git push

git tag -a "v$version" -m "Release v$version"
git push --tags

uv tool install .
uv tool upgrade tex2html
```

## To Do

- --whatsout=fragment for embedding in other pages?
- --javascript=LaTeXML-maybeMathJax.js: The LaTeXML-maybeMathJax.js script loads MathJax for browsers without native MathML support, as a fallback rendering solution.
- babel does not work, figure captions will not render in german. maybe pin babel version to fix?
