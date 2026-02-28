<#
.SYNOPSIS
    Sets up a J-drive-only runtime toolchain for CareerTrojan.

.DESCRIPTION
    - Uses J:\Python311\python.exe as the authoritative Python runtime.
    - Creates project-local virtual environment at .venv-j.
    - Installs runtime or full Python dependencies into .venv-j.
    - Installs Node.js to J:\nodej (portable folder) if missing.
    - Generates .env.j-drive.generated with J:/L: runtime paths.

.EXAMPLE
    .\scripts\setup_j_runtime.ps1 -FullDeps -InstallPytest
#>

param(
    [string]$NodeVersion = "25.4.0",
    [string]$DockerCliVersion = "29.2.1",
    [switch]$SkipNodeInstall,
    [switch]$InstallDockerCli,
    [switch]$SkipPipInstall,
    [switch]$FullDeps,
    [switch]$InstallPytest
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$PythonRoot = "J:\Python311"
$PythonExe = Join-Path $PythonRoot "python.exe"
$VenvDir = Join-Path $ProjectRoot ".venv-j"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$NodeRoot = "J:\nodej"
$NodeExe = Join-Path $NodeRoot "node.exe"
$NodeNpm = Join-Path $NodeRoot "npm.cmd"
$DockerRoot = "J:\docker-cli"
$DockerExe = Join-Path $DockerRoot "docker.exe"
$RuntimeReq = Join-Path $ProjectRoot "requirements.runtime.txt"
$FullReq = Join-Path $ProjectRoot "requirements.txt"
$EnvGenerated = Join-Path $ProjectRoot ".env.j-drive.generated"

Write-Host "=== CareerTrojan J-Drive Runtime Setup ===" -ForegroundColor Cyan
Write-Host "Project Root: $ProjectRoot" -ForegroundColor Yellow

if (-not (Test-Path $PythonExe)) {
    throw "J-drive Python missing: $PythonExe"
}

Write-Host "[1/5] Python runtime..." -ForegroundColor Cyan
Write-Host "Using: $PythonExe" -ForegroundColor Green

Write-Host "[2/5] Virtual environment (.venv-j)..." -ForegroundColor Cyan
if (-not (Test-Path $VenvPython)) {
    & $PythonExe -m venv $VenvDir
}
if (-not (Test-Path $VenvPython)) {
    throw "Failed to create venv at $VenvDir"
}
Write-Host "Ready: $VenvPython" -ForegroundColor Green

if (-not $SkipPipInstall) {
    Write-Host "[3/5] Installing Python packages..." -ForegroundColor Cyan
    & $VenvPython -m pip install --upgrade pip

    if ($FullDeps) {
        & $VenvPython -m pip install -r $FullReq
        Write-Host "Installed full requirements from requirements.txt" -ForegroundColor Green
    } else {
        & $VenvPython -m pip install -r $RuntimeReq
        Write-Host "Installed runtime requirements from requirements.runtime.txt" -ForegroundColor Green
    }

    if ($InstallPytest) {
        & $VenvPython -m pip install pytest
        Write-Host "Installed pytest" -ForegroundColor Green
    }
} else {
    Write-Host "[3/5] Skipped pip install." -ForegroundColor Yellow
}

if (-not $SkipNodeInstall) {
    Write-Host "[4/5] Node.js on J: ..." -ForegroundColor Cyan
    if (-not (Test-Path $NodeExe)) {
        $zipName = "node-v$NodeVersion-win-x64.zip"
        $downloadUrl = "https://nodejs.org/dist/v$NodeVersion/$zipName"
        $tmpZip = Join-Path $env:TEMP $zipName
        $tmpExtractRoot = Join-Path $env:TEMP "node-install-$NodeVersion"
        $expandedFolder = Join-Path $tmpExtractRoot "node-v$NodeVersion-win-x64"

        if (Test-Path $tmpZip) { Remove-Item $tmpZip -Force }
        if (Test-Path $tmpExtractRoot) { Remove-Item $tmpExtractRoot -Recurse -Force }

        Write-Host "Downloading $downloadUrl" -ForegroundColor Gray
        Invoke-WebRequest -Uri $downloadUrl -OutFile $tmpZip
        Expand-Archive -Path $tmpZip -DestinationPath $tmpExtractRoot -Force

        if (Test-Path $NodeRoot) { Remove-Item $NodeRoot -Recurse -Force }
        Move-Item -Path $expandedFolder -Destination $NodeRoot

        Remove-Item $tmpZip -Force
        Remove-Item $tmpExtractRoot -Recurse -Force
    }

    if (-not (Test-Path $NodeExe)) {
        throw "Node install failed at $NodeRoot"
    }

    $nodeVer = & $NodeExe --version
    $npmVer = & $NodeNpm --version
    Write-Host "Node: $nodeVer" -ForegroundColor Green
    Write-Host "NPM:  $npmVer" -ForegroundColor Green
} else {
    Write-Host "[4/5] Skipped Node.js install." -ForegroundColor Yellow
}

if ($InstallDockerCli) {
    Write-Host "[4b/5] Docker CLI on J: ..." -ForegroundColor Cyan
    if (-not (Test-Path $DockerExe)) {
        $zipName = "docker-$DockerCliVersion.zip"
        $downloadUrl = "https://download.docker.com/win/static/stable/x86_64/$zipName"
        $tmpZip = Join-Path $env:TEMP $zipName
        $tmpExtractRoot = Join-Path $env:TEMP "docker-cli-$DockerCliVersion"
        $dockerFolder = Join-Path $tmpExtractRoot "docker"

        if (Test-Path $tmpZip) { Remove-Item $tmpZip -Force }
        if (Test-Path $tmpExtractRoot) { Remove-Item $tmpExtractRoot -Recurse -Force }

        Write-Host "Downloading $downloadUrl" -ForegroundColor Gray
        Invoke-WebRequest -Uri $downloadUrl -OutFile $tmpZip
        Expand-Archive -Path $tmpZip -DestinationPath $tmpExtractRoot -Force

        if (Test-Path $DockerRoot) { Remove-Item $DockerRoot -Recurse -Force }
        New-Item -ItemType Directory -Path $DockerRoot -Force | Out-Null
        Get-ChildItem -Path $dockerFolder | ForEach-Object {
            Copy-Item -Path $_.FullName -Destination $DockerRoot -Recurse -Force
        }

        Remove-Item $tmpZip -Force
        Remove-Item $tmpExtractRoot -Recurse -Force
    }

    if (-not (Test-Path $DockerExe)) {
        throw "Docker CLI install failed at $DockerRoot"
    }
    $dockerVer = & $DockerExe --version
    Write-Host "$dockerVer" -ForegroundColor Green
} else {
    Write-Host "[4b/5] Docker CLI install not requested (-InstallDockerCli)." -ForegroundColor Yellow
}

Write-Host "[5/5] Generating J-drive env template..." -ForegroundColor Cyan
$envContent = @(
    "# Auto-generated by scripts/setup_j_runtime.ps1",
    "CAREERTROJAN_APP_ROOT=$ProjectRoot",
    "CAREERTROJAN_DATA_ROOT=L:\Codec-Antigravity Data set",
    "CAREERTROJAN_AI_DATA=L:\Codec-Antigravity Data set\ai_data_final",
    "CAREERTROJAN_PARSER_ROOT=L:\Codec-Antigravity Data set\automated_parser",
    "CAREERTROJAN_USER_DATA=L:\Codec-Antigravity Data set\USER DATA",
    "CAREERTROJAN_USER_DATA_MIRROR=E:\CareerTrojan\USER_DATA_COPY",
    "CAREERTROJAN_PYTHON_BIN=$VenvPython",
    "CAREERTROJAN_NODE_BIN=$NodeExe",
    "CAREERTROJAN_DOCKER_BIN=$DockerExe"
)
$envContent | Set-Content -Path $EnvGenerated -Encoding UTF8
Write-Host "Generated: $EnvGenerated" -ForegroundColor Green

Write-Host ""
Write-Host "J-drive runtime setup complete." -ForegroundColor Cyan
Write-Host "Use this Python for runtime/tests:" -ForegroundColor Gray
Write-Host "  $VenvPython" -ForegroundColor White
Write-Host "Use this Node runtime:" -ForegroundColor Gray
Write-Host "  $NodeExe" -ForegroundColor White
