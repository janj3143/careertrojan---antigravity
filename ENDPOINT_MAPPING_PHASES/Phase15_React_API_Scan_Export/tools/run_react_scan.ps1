param(
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [Parameter(Mandatory=$true)][string]$ReactSrcRoot,
  [string]$OutDir = ".\exports"
)
& $PythonExe .\tools\react_api_scan.py --root $ReactSrcRoot --out $OutDir
