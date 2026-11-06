$ErrorActionPreference = 'Stop'
$previousCondarc = $env:CONDARC
$previousCache = $env:CONDA_PKGS_DIRS
Push-Location $PSScriptRoot
try {
    $env:CONDARC = Join-Path $PSScriptRoot 'conda-config.yml'
    $env:CONDA_PKGS_DIRS = Join-Path $PSScriptRoot '.conda-pkgs'
    conda env create --prefix .\.conda --file environment.yml --yes
    if ($LASTEXITCODE -ne 0 -or !(Test-Path .\.conda\python.exe)) {
        throw 'Conda environment creation failed. See the output above.'
    }
    & .\.conda\python.exe -c 'import yt_dlp, bilibili_downloader'
    if ($LASTEXITCODE -ne 0) { throw 'Project dependencies are incomplete.' }
    Write-Host 'Ready. Run: conda run --no-capture-output --prefix .\.conda python download.py'
}
finally {
    $env:CONDARC = $previousCondarc
    $env:CONDA_PKGS_DIRS = $previousCache
    Pop-Location
}
