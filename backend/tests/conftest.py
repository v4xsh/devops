"""Test fixtures.

Tests run against an in-memory SQLite database, never the real PostgreSQL
instance. Each test gets a fresh schema so tests stay independent.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.db import Base, get_db
from app.main import app


@pytest.fixture()
def engine():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def client(engine):
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def agent(client):
    resp = client.post("/api/agents", json={"name": "Test Agent", "email": "agent@example.com", "team": "Tier 1"})
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture()
def ticket(client, agent):
    resp = client.post(
        "/api/tickets",
        json={
            "title": "Printer on fire",
            "description": "Smoke coming out of tray 2",
            "priority": "urgent",
            "customer": "Initech",
            "assignee_id": agent["id"],
        },
    )
    assert resp.status_code == 201
    return resp.json()
