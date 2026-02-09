
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, r"C:\careertrojan")

from fastapi import FastAPI
from services.backend_api.main import app

def count_endpoints():
    print(f"--- Live Endpoint Verification ---")
    
    total_routes = 0
    methods_count = 0
    
    routes_list = []

    for route in app.routes:
        if hasattr(route, "methods"):
            for method in route.methods:
                if method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    routes_list.append(f"{method} {route.path}")
                    methods_count += 1
            total_routes += 1
    
    # Sort for readability
    routes_list.sort()
    
    print(f"\nTotal Unique Routes: {total_routes}")
    print(f"Total HTTP Methods (Endpoints): {methods_count}")
    print(f"\n--- Endpoint List ---")
    for r in routes_list:
        print(r)

if __name__ == "__main__":
    try:
        count_endpoints()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error resolving endpoints: {e}")
