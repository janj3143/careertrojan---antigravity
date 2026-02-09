import sys, traceback
try:
    from services.backend_api.main import app
    print("OK: app loaded")
    print(f"Routes: {len(app.routes)}")
except Exception as e:
    traceback.print_exc()
    sys.exit(1)
