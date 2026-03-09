from typing import Literal

from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str
    companies: list[str] | None = None
    years: list[int] | None = None
    use_sub_questions: bool = False


class SourceDocument(BaseModel):
    filename: str
    page: int
    score: float
    text_snippet: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceDocument]


class IngestResponse(BaseModel):
    status: str
    documents_processed: int
    chunks_created: int


class FeedbackRequest(BaseModel):
    query_id: str
    rating: Literal["up", "down"]
    comment: str | None = None


class FeedbackResponse(BaseModel):
    status: str
    feedback_id: str
