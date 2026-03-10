"""Central marker documentation for test-layer intent."""

MARKERS = {
    "unit": "Unit tests (no external deps)",
    "integration": "Integration tests (may need DB/Redis)",
    "e2e": "End-to-end tests (full stack)",
    "smoke": "Fast boot/runtime checks",
    "regression": "Guards for previously identified defects",
    "contract": "API/schema contract checks",
    "load": "Performance/load checks",
}
