from app.db import get_db
from app.main import app


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["service"] == "deskflow-backend"
    assert "Vansh Dobhal" in body["author"]


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_ready_when_database_ok(client):
    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


def test_ready_returns_503_when_database_down(client):
    class BrokenSession:
        def execute(self, *args, **kwargs):
            raise RuntimeError("connection refused")

    def broken_db():
        yield BrokenSession()

    app.dependency_overrides[get_db] = broken_db
    resp = client.get("/ready")
    assert resp.status_code == 503
    assert resp.json()["status"] == "not_ready"


def test_metrics_exposed(client):
    client.get("/health")
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "http_requests_total" in resp.text


def test_openapi_docs(client):
    assert client.get("/docs").status_code == 200
    spec = client.get("/api/openapi.json").json()
    assert "/api/tickets" in spec["paths"]
    assert "Vansh Dobhal" in spec["info"]["title"]
