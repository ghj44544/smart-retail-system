from typing import Dict

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.models.base import get_db
from app.schemas.ai import AIChatRequest, AIChatResponse, AISummaryResponse
from app.services.ai_service import answer_question, get_ai_summary, search_knowledge
from app.utils.jwt_utils import get_current_user
from app.utils.response_utils import success_response


router = APIRouter(prefix="/ai", tags=["AI 智能助手"])


@router.get("/summary", summary="AI 经营洞察摘要")
async def ai_summary(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
) -> Dict:
    data = get_ai_summary(db)
    return success_response(data=AISummaryResponse(**data).model_dump())


@router.post("/chat", summary="AI 问答助手")
async def ai_chat(
    request: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
) -> Dict:
    data = answer_question(db, request.question)
    return success_response(data=AIChatResponse(**data).model_dump())


@router.get("/knowledge", summary="AI 知识库检索")
async def ai_knowledge(
    q: str = Query(default="", max_length=100),
    current_user: Dict = Depends(get_current_user),
) -> Dict:
    return success_response(data={"items": search_knowledge(q)})
