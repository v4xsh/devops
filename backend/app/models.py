from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

TICKET_STATUSES = ("open", "in_progress", "resolved", "closed")
TICKET_PRIORITIES = ("low", "medium", "high", "urgent")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    team: Mapped[str] = mapped_column(String(80), nullable=False, default="Support")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    tickets: Mapped[list["Ticket"]] = relationship(back_populates="assignee")


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        CheckConstraint(f"status IN {TICKET_STATUSES}", name="ck_tickets_status"),
        CheckConstraint(f"priority IN {TICKET_PRIORITIES}", name="ck_tickets_priority"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open", index=True)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium", index=True)
    customer: Mapped[str] = mapped_column(String(160), nullable=False)
    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    assignee: Mapped[Agent | None] = relationship(back_populates="tickets", lazy="joined")

    @property
    def assignee_name(self) -> str | None:
        return self.assignee.name if self.assignee else None


class TicketEvent(Base):
    """Append-only activity log shown in the dashboard feed."""

    __tablename__ = "ticket_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    message: Mapped[str] = mapped_column(String(300), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
