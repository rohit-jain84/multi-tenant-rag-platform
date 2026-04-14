import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EvalResult(Base):
    __tablename__ = "eval_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    strategy: Mapped[str] = mapped_column(String(50), nullable=False)  # hybrid, dense_only
    reranking_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    faithfulness: Mapped[float] = mapped_column(Float, nullable=True)
    answer_relevancy: Mapped[float] = mapped_column(Float, nullable=True)
    context_precision: Mapped[float] = mapped_column(Float, nullable=True)
    context_recall: Mapped[float] = mapped_column(Float, nullable=True)
    per_question_results: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
