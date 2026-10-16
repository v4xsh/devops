from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Status = Literal["open", "in_progress", "resolved", "closed"]
Priority = Literal["low", "medium", "high", "urgent"]


class AgentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    team: str = Field(default="Support", min_length=2, max_length=80)


class AgentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    team: str
    created_at: datetime


class TicketBase(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(default="", max_length=5000)
    status: Status = "open"
    priority: Priority = "medium"
    customer: str = Field(min_length=2, max_length=160)
    assignee_id: int | None = None


class TicketCreate(TicketBase):
    pass


class TicketUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    status: Status | None = None
    priority: Priority | None = None
    customer: str | None = Field(default=None, min_length=2, max_length=160)
    assignee_id: int | None = None


class TicketRead(TicketBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assignee_name: str | None = None
    created_at: datetime
    updated_at: datetime


class TicketStats(BaseModel):
    total: int
    by_status: dict[str, int]
    by_priority: dict[str, int]
    open_urgent: int
    unassigned: int
    resolution_rate: float


class ActivityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    action: str
    message: str
    created_at: datetime
