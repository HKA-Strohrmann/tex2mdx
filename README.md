# Tex 2 HTML

This tools converts LaTeX source files to HTML using LaTeXML. The process if forked from arvix.

## Install

- download image magic dynamic binary
- ![image magick install](image.png)
- install perl
- cpanm Image::Magick#
- cpanm LaTeXML

```
cpanm Image::Magick --force
git clone
cd tex2html
uv sync

uv tool install . # available anywhere as tex2html

```

## Usage

## Test

```bash
copy-item "C:\Users\Jax\Coding\Strohrmann-Lecture-Platform\doc2tex\test\skript\chapters" -destination "C:\Users\Jax\Coding\Strohrmann-Lecture-Platform\tex2html\test" -recurse -force
copy-item "C:\Users\Jax\Coding\Strohrmann-Lecture-Platform\doc2tex\test\skript\new media" -destination "C:\Users\Jax\Coding\Strohrmann-Lecture-Platform\tex2html\test" -recurse -force
copy-item "C:\Users\Jax\Coding\Strohrmann-Lecture-Platform\doc2tex\test\skript\combined.tex" -destination "C:\Users\Jax\Coding\Strohrmann-Lecture-Platform\tex2html\test" -recurse -force

cd test
uv run tex2html "test.tex" --output-file "html/test.html"

uv run tex2html "combined.tex" --output-file "html/combined.html"
```

Test latex compilation in pdftex and lualatex:
```bash
latexmk -C --outdir="_build" && latexmk -pdf -interaction=nonstopmode -synctex=1 -file-line-error --shell-escape --outdir="_build" combined.tex
latexmk -C --outdir="_build" && latexmk -lualatex -pdf -interaction=nonstopmode -synctex=1 -file-line-error --shell-escape --outdir="_build" combined.tex
```

## update version and make available

on project root

```
uv version # current version
uv version --bump patch # select (in order of magnitude) major, minor, patch
($version = python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")

git commit -a -m "Prepared for release $version"
git push

git tag -a "v$version" -m "Release v$version"
git push --tags

uv tool install .
```


then, on a different file path you can use

```
uv tool upgrade tex2html
tex2html "combined.tex" --output-file "html/combined.html"
```



## To Do

- Replace scrbook with book. KOMA is not supported by LaTeXML.
- create binding for awesomefont5
- --whatsout=fragment for embedding in other pages?
- create binding to supress tcolorbox errors
- --javascript=LaTeXML-maybeMathJax.js: The LaTeXML-maybeMathJax.js script loads MathJax for browsers without native MathML support, as a fallback rendering solution.
- babel does not work, figure captions will not render in german. maybe pin babel version to fix?
- scrbook is not supported, currently is replaced by book. but scrbook offers more featuress, maybe find a new way.





DefMacro('\tcb@tikz@option@hook','\relax');
DefMacro('\tcb@use@autoparskip','\relax');
DefMacro('\tcb@split@state','\relax');
DefMacro('\tcb@lrtoggle','\relax');
DefMacro('\tcb@setbb@toggle','\relax');
DefMacro('\tcb@height@adjust','\relax');
DefMacro('\tcb@apply@graph@patches','\relax');
DefMacro('\kvtcb@width','\relax');
DefMacro('\kvtcb@phantom','\relax');
DefMacro('\kvtcb@right@rule','\relax');
DefMacro('\kvtcb@geonodes','\relax');
DefMacro('\kvtcb@boxsep','\relax');
