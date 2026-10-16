from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Agent
from app.schemas import AgentCreate, AgentRead

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("", response_model=list[AgentRead])
def list_agents(db: Session = Depends(get_db)):
    return db.scalars(select(Agent).order_by(Agent.name)).all()


@router.post("", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
def create_agent(payload: AgentCreate, db: Session = Depends(get_db)):
    if db.scalar(select(Agent).where(Agent.email == payload.email)):
        raise HTTPException(status_code=409, detail="An agent with this email already exists")
    agent = Agent(**payload.model_dump())
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent
