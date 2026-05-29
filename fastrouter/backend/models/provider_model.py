from datetime import datetime

from sqlalchemy import String, Integer, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class ProviderModel(Base):
    __tablename__ = "provider_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    api_base: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
