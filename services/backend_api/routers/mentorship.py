"""
Mentorship API Routes - FastAPI Integration
Week 1 Implementation - November 15, 2025

REST API endpoints for mentorship portal:
- Mentor-user linking (anonymous)
- Notes management
- Requirement documents
- Invoicing and payments
- Mentor applications
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

# Import mentorship service
# Import mentorship service
from services.backend_api.services.mentorship_service import MentorshipService
from services.backend_api.db.connection import get_db as get_db_connection

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/mentorship/v1", tags=["mentorship"])

# ============================================================================
# PYDANTIC MODELS (Request/Response)
# ============================================================================

class CreateLinkRequest(BaseModel):
    user_id: str = Field(..., description="User ID")
    mentor_id: str = Field(..., description="Mentor ID")
    program_id: Optional[str] = Field(None, description="Program ID")

class CreateNoteRequest(BaseModel):
    link_id: str = Field(..., description="Mentorship link ID")
    mentor_id: str = Field(..., description="Mentor ID")
    note_content: str = Field(..., description="Note text")
    note_type: str = Field("session", description="Note type")
    note_title: Optional[str] = Field(None, description="Note title")
    is_shared_with_user: bool = Field(False, description="Share with user?")
    session_date: Optional[str] = Field(None, description="Session date (YYYY-MM-DD)")

class UpdateNoteRequest(BaseModel):
    note_content: Optional[str] = None
    note_title: Optional[str] = None
    is_shared_with_user: Optional[bool] = None

class CreateDocumentRequest(BaseModel):
    link_id: str
    mentor_id: str
    user_id: str
    document_content: str
    document_title: str = "Mentorship Requirement Document"

class SignDocumentRequest(BaseModel):
    signer_role: str = Field(..., description="'user' or 'mentor'")
    signature: str = Field(..., description="Digital signature")

class RejectDocumentRequest(BaseModel):
    rejection_reason: str

class CreateInvoiceRequest(BaseModel):
    link_id: str
    mentor_id: str
    user_id: str
    amount: float
    service_description: str

class MarkInvoicePaidRequest(BaseModel):
    stripe_payment_intent_id: str
    stripe_charge_id: str

class RaiseDisputeRequest(BaseModel):
    dispute_description: str

class MentorApplicationRequest(BaseModel):
    applicant_user_id: str
    email: str
    full_name: str
    application_data: Dict[str, Any]

class UpdateLinkStatusRequest(BaseModel):
    new_status: str = Field(..., description="active, paused, completed, cancelled")

# ============================================================================
# DEPENDENCY: GET MENTORSHIP SERVICE
# ============================================================================

from sqlalchemy.orm import Session
from services.backend_api.db.connection import get_db

def get_mentorship_service(db: Session = Depends(get_db)):
    """Dependency to get MentorshipService instance"""
    # MentorshipService uses raw DBAPI connection (cursor based)
    return MentorshipService(db.connection().connection)

# ============================================================================
# MENTOR-USER LINKING ENDPOINTS
# ============================================================================

@router.post("/links", status_code=status.HTTP_201_CREATED)
async def create_mentorship_link(
    request: CreateLinkRequest,
    service: MentorshipService = Depends(get_mentorship_service)
):
    """
    Create anonymous mentor-user link

    Returns link_id and anonymous_name (e.g. "Mentee #12345")
    """
    try:
        result = service.create_mentorship_link(
            user_id=request.user_id,
            mentor_id=request.mentor_id,
            program_id=request.program_id
        )
        return result
    except Exception as e:
        logger.error(f"Error creating mentorship link: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/links/mentor/{mentor_id}")
async def get_mentor_connections(
    mentor_id: str,
    status: Optional[str] = None,
    service: MentorshipService = Depends(get_mentorship_service)
):
    """
    Get all mentorship connections for a mentor

    Query params:
    - status: Filter by status (active, paused, completed)
    """
    try:
        connections = service.get_mentor_connections(mentor_id, status)
        return {"connections": connections}
    except Exception as e:
        logger.error(f"Error getting mentor connections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/links/user/{user_id}")
async def get_user_connections(
    user_id: str,
    status: Optional[str] = None,
    service: MentorshipService = Depends(get_mentorship_service)
):
    """
    Get all mentorship connections for a user
    """
    try:
        connections = service.get_user_connections(user_id, status)
        return {"connections": connections}
    except Exception as e:
        logger.error(f"Error getting user connections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/links/{link_id}/status")
async def update_link_status(
    link_id: str,
    request: UpdateLinkStatusRequest,
    service: MentorshipService = Depends(get_mentorship_service)
):
    """
    Update mentorship link status

    Status options: active, paused, completed, cancelled
    """
    try:
        success = service.update_link_status(link_id, request.new_status)
        return {"success": success, "link_id": link_id, "new_status": request.new_status}
    except Exception as e:
        logger.error(f"Error updating link status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# MENTOR NOTES ENDPOINTS
# ============================================================================

@router.post("/notes", status_code=status.HTTP_201_CREATED)
async def create_note(
    request: CreateNoteRequest,
    service: MentorshipService = Depends(get_mentorship_service)
):
    """
    Create mentor note for a mentorship
    """
    try:
        result = service.create_note(
            link_id=request.link_id,
            mentor_id=request.mentor_id,
            note_content=request.note_content,
            note_type=request.note_type,
            note_title=request.note_title,
            is_shared_with_user=request.is_shared_with_user,
            session_date=request.session_date
        )
        return result
    except Exception as e:
        logger.error(f"Error creating note: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notes/{link_id}")
async def get_notes_for_link(
    link_id: str,
    viewer_role: str = "mentor",
    service: MentorshipService = Depends(get_mentorship_service)
):
    """
    Get all notes for a mentorship link

    Query params:
    - viewer_role: 'mentor' or 'user' (users only see shared notes)
    """
    try:
        notes = service.get_notes_for_link(link_id, viewer_role)
        return {"notes": notes}
    except Exception as e:
        logger.error(f"Error getting notes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/notes/{note_id}")
async def update_note(
    note_id: int,
    request: UpdateNoteRequest,
    service: MentorshipService = Depends(get_mentorship_service)
):
    """
    Update existing note
    """
    try:
        success = service.update_note(
            note_id=note_id,
            note_content=request.note_content,
            note_title=request.note_title,
            is_shared_with_user=request.is_shared_with_user
        )
        return {"success": success, "note_id": note_id}
    except Exception as e:
        logger.error(f"Error updating note: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# REQUIREMENT DOCUMENTS ENDPOINTS
# ============================================================================

@router.post("/documents", status_code=status.HTTP_201_CREATED)
async def create_requirement_document(
    request: CreateDocumentRequest,
    service: MentorshipService = Depends(get_mentorship_service)
):
    """
    Create requirement document (AI-generated from session notes)
    """
    try:
        result = service.create_requirement_document(
            link_id=request.link_id,
            mentor_id=request.mentor_id,
            user_id=request.user_id,
            document_content=request.document_content,
            document_title=request.document_title
        )
        return result
    except Exception as e:
        logger.error(f"Error creating requirement document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{doc_id}")
async def get_requirement_document(
    doc_id: int,
    service: MentorshipService = Depends(get_mentorship_service)
):
    """
    Get requirement document by ID
    """
    try:
        document = service.get_requirement_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting requirement document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/{doc_id}/sign")
async def sign_document(
    doc_id: int,
    request: SignDocumentRequest,
    service: MentorshipService = Depends(get_mentorship_service)
):
    """
    Sign requirement document

    Body:
    - signer_role: 'user' or 'mentor'
    - signature: Digital signature / confirmation text
    """
    try:
        success = service.sign_document(
            doc_id=doc_id,
            signer_role=request.signer_role,
            signature=request.signature
        )
        return {"success": success, "doc_id": doc_id, "signer_role": request.signer_role}
    except Exception as e:
        logger.error(f"Error signing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/{doc_id}/reject")
async def reject_document(
    doc_id: int,
    request: RejectDocumentRequest,
    service: MentorshipService = Depends(get_mentorship_service)
):
    """
    Reject requirement document (needs revision)
    """
    try:
        success = service.reject_document(
            doc_id=doc_id,
            rejection_reason=request.rejection_reason
        )
        return {"success": success, "doc_id": doc_id}
    except Exception as e:
        logger.error(f"Error rejecting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# INVOICING & PAYMENTS ENDPOINTS
# ============================================================================

@router.post("/invoices", status_code=status.HTTP_201_CREATED)
async def create_invoice(
    request: CreateInvoiceRequest,
    service: MentorshipService = Depends(get_mentorship_service)
):
    """
    Create invoice for mentorship service

    Platform fee (20%) and mentor portion (80%) auto-calculated
    """
    try:
        result = service.create_invoice(
            link_id=request.link_id,
            mentor_id=request.mentor_id,
            user_id=request.user_id,
            amount=request.amount,
            service_description=request.service_description
        )
        return result
    except Exception as e:
        logger.error(f"Error creating invoice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/invoices/mentor/{mentor_id}")
async def get_mentor_invoices(
    mentor_id: str,
    status: Optional[str] = None,
    service: MentorshipService = Depends(get_mentorship_service)
):
    """
    Get all invoices for a mentor

    Query params:
    - status: Filter by status (pending, paid, held, released, disputed)
    """
    try:
        invoices = service.get_mentor_invoices(mentor_id, status)
        return {"invoices": invoices}
    except Exception as e:
        logger.error(f"Error getting mentor invoices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/invoices/{invoice_id}/mark-paid")
async def mark_invoice_paid(
    invoice_id: int,
    request: MarkInvoicePaidRequest,
    service: MentorshipService = Depends(get_mentorship_service)
):
    """
    Mark invoice as paid (user paid platform via Stripe)

    Funds now held by platform, awaiting completion confirmation
    """
    try:
        success = service.mark_invoice_paid(
            invoice_id=invoice_id,
            stripe_payment_intent_id=request.stripe_payment_intent_id,
            stripe_charge_id=request.stripe_charge_id
        )
        return {"success": success, "invoice_id": invoice_id, "status": "held"}
    except Exception as e:
        logger.error(f"Error marking invoice paid: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/invoices/{invoice_id}/service-delivered")
async def mark_service_delivered(
    invoice_id: int,
    mentor_id: str,
    service: MentorshipService = Depends(get_mentorship_service)
):
    """
    Mentor marks service as delivered

    Query params:
    - mentor_id: Mentor ID (for verification)
    """
    try:
        success = service.mark_service_delivered(invoice_id, mentor_id)
        return {"success": success, "invoice_id": invoice_id, "mentor_delivered": True}
    except Exception as e:
        logger.error(f"Error marking service delivered: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/invoices/{invoice_id}/confirm-completion")
async def confirm_service_completion(
    invoice_id: int,
    user_id: str,
    service: MentorshipService = Depends(get_mentorship_service)
):
    """
    User confirms satisfaction with service

    Query params:
    - user_id: User ID (for verification)

    If both parties confirmed, funds automatically released to mentor
    """
    try:
        success = service.confirm_service_completion(invoice_id, user_id)
        return {"success": success, "invoice_id": invoice_id, "user_confirmed": True}
    except Exception as e:
        logger.error(f"Error confirming service completion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/invoices/{invoice_id}/dispute")
async def raise_dispute(
    invoice_id: int,
    request: RaiseDisputeRequest,
    service: MentorshipService = Depends(get_mentorship_service)
):
    """
    Raise dispute on invoice (either party can do this)

    Triggers admin mediation workflow
    """
    try:
        success = service.raise_dispute(
            invoice_id=invoice_id,
            dispute_description=request.dispute_description
        )
        return {"success": success, "invoice_id": invoice_id, "status": "disputed"}
    except Exception as e:
        logger.error(f"Error raising dispute: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# MENTOR APPLICATIONS ENDPOINTS
# ============================================================================

@router.post("/applications", status_code=status.HTTP_201_CREATED)
async def submit_mentor_application(
    request: MentorApplicationRequest,
    service: MentorshipService = Depends(get_mentorship_service)
):
    """
    Submit mentor application

    Guardian review workflow triggered automatically
    """
    try:
        result = service.submit_mentor_application(
            applicant_user_id=request.applicant_user_id,
            email=request.email,
            full_name=request.full_name,
            application_data=request.application_data
        )
        return result
    except Exception as e:
        logger.error(f"Error submitting mentor application: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/applications/pending")
async def get_pending_applications(
    service: MentorshipService = Depends(get_mentorship_service)
):
    """
    Get all pending mentor applications for Guardian review

    Admin/Guardian access only
    """
    try:
        applications = service.get_pending_applications()
        return {"applications": applications}
    except Exception as e:
        logger.error(f"Error getting pending applications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/applications/{application_id}/approve")
async def approve_mentor_application(
    application_id: int,
    reviewer_admin_id: str,
    mentor_id: str,
    service: MentorshipService = Depends(get_mentorship_service)
):
    """
    Approve mentor application (Guardian action)

    Query params:
    - reviewer_admin_id: Guardian who approved
    - mentor_id: Assigned mentor ID
    """
    try:
        success = service.approve_mentor_application(
            application_id=application_id,
            reviewer_admin_id=reviewer_admin_id,
            mentor_id=mentor_id
        )
        return {"success": success, "application_id": application_id, "mentor_id": mentor_id}
    except Exception as e:
        logger.error(f"Error approving application: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "service": "mentorship"}
