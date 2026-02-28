from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.backend_api.models.spider_covey import SpiderProfile, CoveyActionLens
from services.backend_api.services.covey_builder import (
    build_covey_action_lens,
    load_action_library_from_json,
)

router = APIRouter(prefix="/api/lenses/v1", tags=["lenses"])

ACTION_LIBRARY_PATH = Path(__file__).resolve().parents[1] / "data" / "action_library.json"


class BuildSpiderRequest(BaseModel):
    user_id: str
    resume_id: str
    job_family: str
    cohort: Dict[str, Any] = Field(default_factory=dict)


class BuildCoveyRequest(BaseModel):
    spider: SpiderProfile
    options: Dict[str, Any] = Field(default_factory=dict)


class BuildCompositeRequest(BaseModel):
    spider: SpiderProfile
    options: Dict[str, Any] = Field(default_factory=dict)


class CompositeResponse(BaseModel):
    spider: SpiderProfile
    covey: CoveyActionLens


@router.post("/spider", response_model=SpiderProfile)
async def build_spider(req: BuildSpiderRequest) -> SpiderProfile:
    raise HTTPException(
        status_code=501,
        detail="Spider builder not implemented yet. Use /api/lenses/v1/covey with a SpiderProfile payload.",
    )


@router.post("/covey", response_model=CoveyActionLens)
async def build_covey(req: BuildCoveyRequest) -> CoveyActionLens:
    templates = load_action_library_from_json(ACTION_LIBRARY_PATH)
    if not templates:
        raise HTTPException(status_code=500, detail="Action library is empty or missing")

    options = req.options or {}
    split_x = float(options.get("split_x", 50))
    split_y = float(options.get("split_y", 50))
    top_n = int(options.get("top_n", 30))

    return build_covey_action_lens(
        spider=req.spider,
        action_templates=templates,
        split_x=split_x,
        split_y=split_y,
        top_n=top_n,
    )


@router.post("/composite", response_model=CompositeResponse)
async def build_composite(req: BuildCompositeRequest) -> CompositeResponse:
    templates = load_action_library_from_json(ACTION_LIBRARY_PATH)
    if not templates:
        raise HTTPException(status_code=500, detail="Action library is empty or missing")

    options = req.options or {}
    covey = build_covey_action_lens(
        spider=req.spider,
        action_templates=templates,
        split_x=float(options.get("split_x", 50)),
        split_y=float(options.get("split_y", 50)),
        top_n=int(options.get("top_n", 30)),
    )
    return CompositeResponse(spider=req.spider, covey=covey)
