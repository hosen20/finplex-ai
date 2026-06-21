from app.api.schemas.rag import (
    RagEvidenceResponse,
    RagSearchRequest,
    RagSearchResponse,
)
from app.application.services.rag_service import RagService
from app.database import get_db_session
from app.dependencies import get_current_user
from app.infrastructure.db.models.user_model import UserModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/search", response_model=RagSearchResponse)
def search_rag_evidence(
    payload: RagSearchRequest,
    current_user: UserModel = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> RagSearchResponse:
    """Search the signed-in user's tenant RAG evidence using pgvector."""

    service = RagService(session)
    results = service.search(
        tenant_id=current_user.tenant_id,
        query=payload.query,
        limit=payload.limit,
    )
    return RagSearchResponse(
        tenant_id=current_user.tenant_id,
        query=payload.query,
        results=[
            RagEvidenceResponse(
                chunk_id=result.chunk_id,
                document_id=result.document_id,
                document_title=result.document_title,
                source_type=result.source_type,
                content=result.content,
                score=result.score,
            )
            for result in results
        ],
    )
