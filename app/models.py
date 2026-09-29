from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )

    agent_runs: Mapped[list["AgentRun"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id"),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    conversation: Mapped["Conversation"] = relationship(
        back_populates="messages",
    )


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="running",
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    conversation: Mapped["Conversation"] = relationship(
        back_populates="agent_runs",
    )

    tool_calls: Mapped[list["ToolCall"]] = relationship(
        back_populates="agent_run",
        cascade="all, delete-orphan",
    )


class ToolCall(Base):
    __tablename__ = "tool_calls"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    agent_run_id: Mapped[int] = mapped_column(
        ForeignKey("agent_runs.id"),
        nullable=False,
    )

    tool_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    arguments: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    result: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    agent_run: Mapped["AgentRun"] = relationship(
        back_populates="tool_calls",
    )
