import json
from backend.app.main import app
with open("openapi.snapshot.json","w",encoding="utf-8") as f: json.dump(app.openapi(), f, indent=2)
print("saved openapi.snapshot.json")
