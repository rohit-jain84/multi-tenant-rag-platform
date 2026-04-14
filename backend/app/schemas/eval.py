import uuid
from datetime import datetime

from pydantic import BaseModel


class EvalRunRequest(BaseModel):
    strategy: str = "hybrid"  # "hybrid" or "dense_only"
    reranking_enabled: bool = True


class EvalResultResponse(BaseModel):
    id: uuid.UUID
    run_id: str
    strategy: str
    reranking_enabled: bool
    faithfulness: float | None
    answer_relevancy: float | None
    context_precision: float | None
    context_recall: float | None
    per_question_results: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EvalResultsListResponse(BaseModel):
    results: list[EvalResultResponse]
    total: int
