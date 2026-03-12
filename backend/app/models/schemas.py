from typing import Literal

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    companies: list[str] | None = Field(default=None, max_length=10)
    years: list[int] | None = Field(default=None, max_length=10)
    doc_types: list[str] | None = Field(default=None, max_length=10)
    use_sub_questions: bool = True


class SourceDocument(BaseModel):
    filename: str
    page: int
    score: float
    text_snippet: str
    source_type: str = "document"


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceDocument]
    query_id: str = ""


class IngestRequest(BaseModel):
    force: bool = False


class IngestResponse(BaseModel):
    status: str
    documents_processed: int
    chunks_created: int
    existing_chunks: int = 0


class FeedbackRequest(BaseModel):
    query_id: str
    rating: Literal["up", "down"]
    comment: str | None = None


class FeedbackResponse(BaseModel):
    status: str
    feedback_id: str


class FeedbackStatsResponse(BaseModel):
    total_queries: int
    positive_percentage: float
    negative_percentage: float


class FeedbackRecord(BaseModel):
    feedback_id: str
    query_id: str
    rating: str
    comment: str | None = None
    created_at: str
