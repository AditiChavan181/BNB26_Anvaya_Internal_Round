from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    content_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    model: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    model_identifier: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    model_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    tool: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    issuer: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    validation_state: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    c2pa_found: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    has_provenance_chain: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    actions: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    ingredients: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    validation_results: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    blockchain_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="NOT_ANCHORED",
    )

    blockchain_tx_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )