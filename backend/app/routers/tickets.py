from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import TICKET_PRIORITIES, TICKET_STATUSES, Agent, Ticket, TicketEvent
from app.schemas import ActivityRead, Priority, Status, TicketCreate, TicketRead, TicketStats, TicketUpdate

router = APIRouter(prefix="/api", tags=["tickets"])


def _get_ticket_or_404(db: Session, ticket_id: int) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return ticket


def _check_assignee(db: Session, assignee_id: int | None) -> None:
    if assignee_id is not None and db.get(Agent, assignee_id) is None:
        raise HTTPException(status_code=422, detail=f"Agent {assignee_id} does not exist")


def _log(db: Session, ticket_id: int, action: str, message: str) -> None:
    db.add(TicketEvent(ticket_id=ticket_id, action=action, message=message[:300]))


@router.get("/tickets", response_model=list[TicketRead])
def list_tickets(
    db: Session = Depends(get_db),
    status_: Status | None = Query(default=None, alias="status"),
    priority: Priority | None = None,
    assignee_id: int | None = None,
    q: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=100, ge=1, le=500),
):
    stmt = select(Ticket)
    if status_:
        stmt = stmt.where(Ticket.status == status_)
    if priority:
        stmt = stmt.where(Ticket.priority == priority)
    if assignee_id is not None:
        stmt = stmt.where(Ticket.assignee_id == assignee_id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Ticket.title.ilike(like), Ticket.customer.ilike(like)))
    stmt = stmt.order_by(Ticket.updated_at.desc(), Ticket.id.desc()).limit(limit)
    return db.scalars(stmt).unique().all()


@router.get("/tickets/stats", response_model=TicketStats)
def ticket_stats(db: Session = Depends(get_db)):
    by_status = {s: 0 for s in TICKET_STATUSES}
    for value, count in db.execute(select(Ticket.status, func.count()).group_by(Ticket.status)):
        by_status[value] = count
    by_priority = {p: 0 for p in TICKET_PRIORITIES}
    for value, count in db.execute(select(Ticket.priority, func.count()).group_by(Ticket.priority)):
        by_priority[value] = count

    total = sum(by_status.values())
    open_urgent = db.scalar(
        select(func.count()).where(Ticket.priority == "urgent", Ticket.status.in_(("open", "in_progress")))
    )
    unassigned = db.scalar(
        select(func.count()).where(Ticket.assignee_id.is_(None), Ticket.status.in_(("open", "in_progress")))
    )
    done = by_status["resolved"] + by_status["closed"]
    return TicketStats(
        total=total,
        by_status=by_status,
        by_priority=by_priority,
        open_urgent=open_urgent or 0,
        unassigned=unassigned or 0,
        resolution_rate=round(done / total * 100, 1) if total else 0.0,
    )


@router.get("/activity", response_model=list[ActivityRead])
def recent_activity(db: Session = Depends(get_db), limit: int = Query(default=15, ge=1, le=100)):
    stmt = select(TicketEvent).order_by(TicketEvent.created_at.desc(), TicketEvent.id.desc()).limit(limit)
    return db.scalars(stmt).all()


@router.post("/tickets", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    _check_assignee(db, payload.assignee_id)
    ticket = Ticket(**payload.model_dump())
    db.add(ticket)
    db.flush()
    _log(db, ticket.id, "created", f"#{ticket.id} opened by {ticket.customer}: {ticket.title}")
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("/tickets/{ticket_id}", response_model=TicketRead)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    return _get_ticket_or_404(db, ticket_id)


@router.put("/tickets/{ticket_id}", response_model=TicketRead)
def update_ticket(ticket_id: int, payload: TicketUpdate, db: Session = Depends(get_db)):
    ticket = _get_ticket_or_404(db, ticket_id)
    changes = payload.model_dump(exclude_unset=True)
    if "assignee_id" in changes:
        _check_assignee(db, changes["assignee_id"])
    old_status = ticket.status
    for field, value in changes.items():
        setattr(ticket, field, value)
    if "status" in changes and changes["status"] != old_status:
        _log(db, ticket.id, "status", f"#{ticket.id} moved {old_status} -> {ticket.status}")
    elif changes:
        _log(db, ticket.id, "updated", f"#{ticket.id} updated ({', '.join(sorted(changes))})")
    db.commit()
    db.refresh(ticket)
    return ticket


@router.delete("/tickets/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = _get_ticket_or_404(db, ticket_id)
    _log(db, ticket.id, "deleted", f"#{ticket.id} deleted: {ticket.title}")
    db.delete(ticket)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
