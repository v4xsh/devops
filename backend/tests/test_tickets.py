import pytest


def test_list_tickets_empty(client):
    resp = client.get("/api/tickets")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_ticket(client, ticket, agent):
    assert ticket["id"] > 0
    assert ticket["status"] == "open"
    assert ticket["priority"] == "urgent"
    assert ticket["assignee_id"] == agent["id"]
    assert ticket["assignee_name"] == "Test Agent"
    assert ticket["created_at"] and ticket["updated_at"]


def test_create_ticket_defaults(client):
    resp = client.post("/api/tickets", json={"title": "Need help", "customer": "Globex"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "open"
    assert body["priority"] == "medium"
    assert body["assignee_id"] is None


def test_get_ticket(client, ticket):
    resp = client.get(f"/api/tickets/{ticket['id']}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Printer on fire"


def test_get_ticket_404(client):
    resp = client.get("/api/tickets/9999")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"]


def test_update_ticket(client, ticket):
    resp = client.put(f"/api/tickets/{ticket['id']}", json={"status": "in_progress", "priority": "high"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "in_progress"
    assert body["priority"] == "high"
    assert body["title"] == ticket["title"]


def test_update_ticket_unassign(client, ticket):
    resp = client.put(f"/api/tickets/{ticket['id']}", json={"assignee_id": None})
    assert resp.status_code == 200
    assert resp.json()["assignee_id"] is None


def test_update_ticket_404(client):
    resp = client.put("/api/tickets/9999", json={"status": "closed"})
    assert resp.status_code == 404


def test_delete_ticket(client, ticket):
    resp = client.delete(f"/api/tickets/{ticket['id']}")
    assert resp.status_code == 204
    assert client.get(f"/api/tickets/{ticket['id']}").status_code == 404


def test_delete_ticket_404(client):
    assert client.delete("/api/tickets/9999").status_code == 404


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "x", "customer": "Acme"},  # title too short
        {"title": "Valid title"},  # customer missing
        {"title": "Valid title", "customer": "Acme", "status": "pending"},
        {"title": "Valid title", "customer": "Acme", "priority": "critical"},
    ],
)
def test_create_ticket_validation_errors(client, payload):
    assert client.post("/api/tickets", json=payload).status_code == 422


def test_create_ticket_unknown_assignee(client):
    resp = client.post("/api/tickets", json={"title": "Valid title", "customer": "Acme", "assignee_id": 42})
    assert resp.status_code == 422


def test_update_ticket_invalid_status(client, ticket):
    resp = client.put(f"/api/tickets/{ticket['id']}", json={"status": "done"})
    assert resp.status_code == 422


def test_filter_tickets(client, ticket):
    client.post("/api/tickets", json={"title": "Low prio question", "customer": "Hooli", "priority": "low"})
    assert len(client.get("/api/tickets").json()) == 2
    urgent = client.get("/api/tickets", params={"priority": "urgent"}).json()
    assert [t["id"] for t in urgent] == [ticket["id"]]
    assert client.get("/api/tickets", params={"status": "closed"}).json() == []
    found = client.get("/api/tickets", params={"q": "hooli"}).json()
    assert len(found) == 1 and found[0]["customer"] == "Hooli"


def test_stats(client, ticket):
    client.post("/api/tickets", json={"title": "Second ticket", "customer": "Hooli", "priority": "low"})
    client.put(f"/api/tickets/{ticket['id']}", json={"status": "resolved"})
    resp = client.get("/api/tickets/stats")
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["total"] == 2
    assert stats["by_status"] == {"open": 1, "in_progress": 0, "resolved": 1, "closed": 0}
    assert stats["by_priority"]["urgent"] == 1
    assert stats["by_priority"]["low"] == 1
    assert stats["open_urgent"] == 0
    assert stats["unassigned"] == 1
    assert stats["resolution_rate"] == 50.0


def test_stats_empty(client):
    stats = client.get("/api/tickets/stats").json()
    assert stats["total"] == 0
    assert stats["resolution_rate"] == 0.0


def test_activity_feed(client, ticket):
    client.put(f"/api/tickets/{ticket['id']}", json={"status": "in_progress"})
    client.delete(f"/api/tickets/{ticket['id']}")
    events = client.get("/api/activity").json()
    assert [e["action"] for e in events][:3] == ["deleted", "status", "created"]
