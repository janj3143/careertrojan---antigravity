param(
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [Parameter(Mandatory=$true)][string]$FastApiJson,
  [Parameter(Mandatory=$true)][string]$ReactJson,
  [Parameter(Mandatory=$true)][string]$OutDir
)
& $PythonExe .\tools\join_endpoint_graph.py --fastapi $FastApiJson --react $ReactJson --out $OutDir
