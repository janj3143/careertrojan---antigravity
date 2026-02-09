# Shared Router
from fastapi import APIRouter

router = APIRouter(
    prefix="/api/shared/v1",
    tags=["shared"],
    responses={404: {"description": "Not found"}},
)

@router.get("/health")
async def health_check():
    return {"status": "ok"}
