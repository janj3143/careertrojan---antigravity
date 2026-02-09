param(
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [Parameter(Mandatory=$true)][string]$AppImport,
  [string]$OutDir = ".\exports"
)
& $PythonExe .\tools\fastapi_introspect_routes.py --app-import $AppImport --out $OutDir
