from datetime import datetime
from typing import Any

from sqlalchemy import String, Integer, Boolean, DateTime, Float, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class ProviderConfig(Base):
    __tablename__ = "provider_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model_pattern: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    weight: Mapped[int] = mapped_column(Integer, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    circuit_breaker_status: Mapped[str] = mapped_column(String(20), default="closed")
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    last_failure_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    settings: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
