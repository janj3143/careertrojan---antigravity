from fastapi import APIRouter, Query

from services.backend_api.services.glossary_service import load_collocation_glossary

router = APIRouter(prefix="/api/ontology/v1", tags=["ontology"])


def _build_entries(payload: dict) -> list:
    entries = []
    for item in payload.get("bigrams", []):
        if isinstance(item, dict):
            entries.append({
                "phrase": item.get("phrase"),
                "count": item.get("count", 0),
                "pmi": item.get("pmi", 0.0),
                "type": "bigram",
            })
    for item in payload.get("trigrams", []):
        if isinstance(item, dict):
            entries.append({
                "phrase": item.get("phrase"),
                "count": item.get("count", 0),
                "pmi": item.get("pmi", 0.0),
                "type": "trigram",
            })
    return [e for e in entries if e.get("phrase")]


@router.get("/phrases")
def list_phrases(
    limit: int = Query(200, ge=1, le=5000),
    q: str | None = Query(None, min_length=1),
):
    payload = load_collocation_glossary()
    entries = _build_entries(payload)

    if q:
        needle = q.lower()
        entries = [e for e in entries if needle in e["phrase"].lower()]

    return {
        "ok": True,
        "count": len(entries),
        "items": entries[:limit],
        "generated_at": payload.get("generated_at"),
    }


@router.get("/phrases/summary")
def phrases_summary():
    payload = load_collocation_glossary()
    entries = _build_entries(payload)
    return {
        "ok": True,
        "count": len(entries),
        "generated_at": payload.get("generated_at"),
        "sources": payload.get("source_counts", {}),
    }
