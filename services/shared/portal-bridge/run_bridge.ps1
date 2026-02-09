$env:PYTHONPATH = "C:\careertrojan"
& "C:\careertrojan\infra\python\python.exe" -m uvicorn services.portal_bridge.main:app --reload --port 8000
