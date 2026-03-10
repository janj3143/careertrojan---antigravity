from __future__ import annotations

from fastapi import APIRouter, Depends

from services.backend_api.routers import admin as admin_v1

router = APIRouter(prefix="/api/admin", tags=["admin-legacy"])


@router.get("/integrations/status")
def integrations_status_legacy(_: bool = Depends(admin_v1.require_admin)):
    return admin_v1.integrations_status(_)


@router.post("/integrations/sendgrid/configure")
def configure_sendgrid_legacy(payload: dict, _: bool = Depends(admin_v1.require_admin)):
    return admin_v1.configure_sendgrid(payload, _)


@router.post("/integrations/klaviyo/configure")
def configure_klaviyo_legacy(payload: dict, _: bool = Depends(admin_v1.require_admin)):
    return admin_v1.configure_klaviyo(payload, _)


@router.post("/email/send_test")
def send_test_email_legacy(payload: dict, _: bool = Depends(admin_v1.require_admin)):
    return admin_v1.send_test_email(payload, _)


@router.post("/email/send_bulk")
def send_bulk_email_legacy(payload: dict, _: bool = Depends(admin_v1.require_admin)):
    return admin_v1.send_bulk_email(payload, _)
