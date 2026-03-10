import json
from services.backend_api.main import app
rows=[]
for route in app.routes:
    path=getattr(route,"path",None); methods=sorted(list(getattr(route,"methods",[]) or [])); name=getattr(route,"name",None)
    if path: rows.append({"path":path,"methods":methods,"name":name})
rows=sorted(rows,key=lambda x:(x["path"], ",".join(x["methods"])))
json.dump(rows, open("route_snapshot.json","w",encoding="utf-8"), indent=2)
print(f"saved {len(rows)} routes")


