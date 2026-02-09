
import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request

from services.backend_api.routers.auth import get_current_user

router = APIRouter(prefix="/api/mapping/v1", tags=["mapping"])

# Adjust path to where data/visual_registry.json lives relative to this file
# This file is in services/backend_api/routers/
# Registry is in services/backend_api/data/
BASE_DIR = Path(__file__).resolve().parents[1]
REGISTRY_PATH = BASE_DIR / "data" / "visual_registry.json"

def load_registry():
    if not REGISTRY_PATH.exists():
        return []
    with REGISTRY_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)["visuals"]

@router.get("/registry")
def registry(user = Depends(get_current_user)):
    return {"visuals": load_registry()}

@router.get("/endpoints")
def endpoints(request: Request, user = Depends(get_current_user)):
    """
    Returns a DYNAMIC list of all registered FastAPI endpoints.
    """
    rows = []
    for route in request.app.routes:
        if hasattr(route, "methods"):
            for method in route.methods:
                if method in ["GET", "POST", "PUT", "DELETE"]:
                    rows.append({
                        "portal": "backend_api",
                        "route": route.path,
                        "page": "API",
                        "visual": "Endpoint",
                        "component": "Backend",
                        "method": method,
                        "endpoint": route.path,
                        "service": "careertrojan-backend",
                        "status": "live",
                        "auth": "jwt" if "auth" in route.path or "user" in route.path else "public"
                    })
    
    # Sort by path
    rows.sort(key=lambda x: x["endpoint"])
    return {"rows": rows}

@router.get("/graph")
def graph(user = Depends(get_current_user)):
    visuals = load_registry()
    nodes=[]; edges=[]
    def add_node(_id,label,_type,**meta): nodes.append({"data":{"id":_id,"label":label,"type":_type,**meta}})
    def add_edge(_id,s,t,label): edges.append({"data":{"id":_id,"source":s,"target":t,"label":label}})

    for p in ["user_portal","admin_portal","mentor_portal"]:
        add_node(f"portal:{p}", p, "portal")

    add_node("page:user:/insights/visuals","VisualisationsHub (/insights/visuals)","page", portal="user_portal", route="/insights/visuals")
    add_edge("edge:user->hub","portal:user_portal","page:user:/insights/visuals","contains")

    for v in visuals:
        vid=f"vis:{v['id']}"
        add_node(vid, v["title"], "visual", component=v["react_component"], category=v.get("category"))
        add_edge(f"edge:hub->{vid}","page:user:/insights/visuals",vid,"uses")
        for i,ep in enumerate(v.get("required_endpoints",[]),start=1):
            eid=f"ep:{ep['method']}:{ep['path']}"
            add_node(eid, f"{ep['method']} {ep['path']}", "endpoint")
            add_edge(f"edge:{vid}->{eid}:{i}", vid, eid, "requires")

    return {"nodes": nodes, "edges": edges}
