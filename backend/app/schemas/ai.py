from typing import Dict, List

from pydantic import BaseModel, Field


class AIChatRequest(BaseModel):
    question: str = Field(default="", max_length=500)


class AIInsight(BaseModel):
    type: str
    title: str
    content: str
    priority: str


class AIProductRankItem(BaseModel):
    id: int
    name: str
    stock: int
    sales_count: int
    sold_qty: int
    revenue: float


class AISummaryResponse(BaseModel):
    metrics: Dict
    segments: Dict[str, int]
    top_products: List[AIProductRankItem]
    insights: List[AIInsight]


class AIKnowledgeItem(BaseModel):
    id: str
    title: str
    keywords: List[str]
    summary: str
    suggestions: List[str]


class AIChatResponse(BaseModel):
    answer: str
    suggestions: List[str]
    sources: List[str]
    related_knowledge: List[AIKnowledgeItem]
