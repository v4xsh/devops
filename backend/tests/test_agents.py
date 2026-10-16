def test_list_agents_empty(client):
    resp = client.get("/api/agents")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_and_list_agent(client, agent):
    assert agent["name"] == "Test Agent"
    assert agent["team"] == "Tier 1"
    listed = client.get("/api/agents").json()
    assert [a["email"] for a in listed] == ["agent@deskflow.example.org"]


def test_create_agent_duplicate_email_conflict(client, agent):
    resp = client.post("/api/agents", json={"name": "Other", "email": "agent@deskflow.example.org"})
    assert resp.status_code == 409


def test_create_agent_invalid_email(client):
    resp = client.post("/api/agents", json={"name": "Bad", "email": "not-an-email"})
    assert resp.status_code == 422
