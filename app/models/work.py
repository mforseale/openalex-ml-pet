from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Work(Base):
    __tablename__ = "works"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    openalex_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    publication_year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    publication_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    cited_by_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    doi: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )