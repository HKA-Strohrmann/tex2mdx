$ErrorActionPreference = "Continue"

$InstallDir = Join-Path $env:LOCALAPPDATA "Programs\tex2mdx"
$RepoDir = Join-Path $InstallDir "tex2mdx"

Write-Host "Creating installation directory '$InstallDir'" 
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

# install Dependencies using winget
Write-Host "Installing dependencies..." -ForegroundColor Cyan
$packages = @(
    "Git.Git"
    "Python.Launcher"
    "astral-sh.uv"
    "StrawberryPerl.StrawberryPerl"
    "MiKTeX.MiKTeX"
    "Inkscape.Inkscape"
    "Microsoft.VisualStudio.2022.BuildTools"
)
foreach ($pkg in $packages) {
    try {
        winget install --id $pkg --accept-package-agreements --accept-source-agreements
    }
    catch {
        Write-Warning "Failed to install $pkg"
    }
}

# Propt user to manually install packages
Write-Warning "Ghostscript and ImageMagick must be installed manually."
Start-Process "https://www.ghostscript.com/releases/gsdnld.html"
Start-Process "https://imagemagick.org/download/#gsc.tab=0"
do {
    $answer = Read-Host "Have you completed the Ghostscript and ImageMagick installation? (y/n)"
}
while ($answer -notmatch '^[Yy]$')

# Prompt user to manually configure ImageMagick
$magickConfig = Get-ChildItem `
    "C:\Program Files" `
    -Recurse `
    -Filter "magick-baseconfig.h" `
    -ErrorAction SilentlyContinue |
    Select-Object -First 1 -ExpandProperty FullName
Write-Warning "ImageMagick installation must be manually configured. See https://github.com/StrawberryPerl/Perl-Dist-Strawberry/issues/140#issuecomment-1756627785 for details."
if ($magickConfig) {
    Write-Warning "Please comment out the line containing: 'error ImageMagick was build with a 64 channel bit mask' in File: '$magickConfig'."
    Write-Warning "Opening the file in Notepad..."

    notepad $magickConfig
}
else {
    Write-Warning "Could not locate 'magick-baseconfig.h' automatically. Please locate the file in your ImageMagick installation directory and comment out the line containing: 'error ImageMagick was build with a 64 channel bit mask'."
}
do {
    $answer = Read-Host "Have you completed the ImageMagick configuration? (y/n)"
}
while ($answer -notmatch '^[Yy]$')

# Install Perl packages
Write-Host "Installing Perl packages..." -ForegroundColor Cyan
cpanm --force --notest Image::Magick
cpanm --force --notest LaTeXML

# Check Requirements
Write-Host "Validating installation..." -ForegroundColor Cyan
$checks = @(
    @{Name="Python";     Cmd="py --version"}
    @{Name="uv";         Cmd="uv --version"}
    @{Name="Ghostscript";Cmd="gswin64c.exe -version"}
    @{Name="ImageMagick";Cmd="magick --version"}
    @{Name="Perl";       Cmd="perl --version"}
    @{Name="latexmk";    Cmd="latexmk --version"}
    @{Name="LaTeXML";    Cmd="latexml --VERSION"}
    @{Name="Inkscape";   Cmd="inkscape --version"}
)
foreach ($check in $checks) {
    try {
        Invoke-Expression $check.Cmd | Out-Null
        Write-Host "[OK] $($check.Name)"
    }
    catch {
        Write-Warning "[FAILED] $($check.Name)"
    }
}

# Clone tex2mdx repository
Write-Host "Installing tex2mdx..." -ForegroundColor Cyan
if (-not (Test-Path $RepoDir)) {
    git clone https://github.com/HKA-Strohrmann/tex2mdx.git $RepoDir
}
else {
    git -C $RepoDir pull
}

# Install tex2mdx using uv
Push-Location $RepoDir
uv sync
uv tool install --force .
Pop-Location

# Finished Installation
Write-Host ""
Write-Host "Installation completed. You can now run:" -ForegroundColor Green
Write-Host "    tex2mdx --help" -ForegroundColor Green
