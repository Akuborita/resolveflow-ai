"""Offline integration tests. They use an isolated temporary SQLite database."""
import sqlite3
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import auth
import database
import main

ORIGIN = "http://testserver"
LOGIN = "/auth/login"


@pytest.fixture
def api(tmp_path, monkeypatch):
    path = tmp_path / "testing.db"
    monkeypatch.setattr(database, "DB_PATH", path)
    monkeypatch.setattr(auth, "DB_PATH", path)
    with TestClient(main.app, base_url=ORIGIN) as client:
        with sqlite3.connect(path) as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("admin_test", auth.hasher.hash("Admin-Password-123"), "admin"),
            )
            conn.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("agent_test", auth.hasher.hash("Agent-Password-123"), "agent"),
            )
        yield client, path, monkeypatch


def sign_in(client, username="admin_test", password="Admin-Password-123"):
    return client.post(LOGIN, json={"username": username, "password": password}, headers={"Origin": ORIGIN})


def csrf(client):
    response = client.get("/auth/csrf")
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    return response.json()["csrf_token"]


def headers(token, origin=ORIGIN):
    return {"Origin": origin, "X-CSRF-Token": token}


def test_route_does_not_shadow_note_creation(api):
    paths = [(r.path, sorted(r.methods or [])) for r in main.app.routes]
    assert sum(path == "/tickets/{ticket_id}/notes" and "POST" in methods for path, methods in paths) == 1
    assert any(path == "/tickets/{ticket_id}" and "GET" in methods for path, methods in paths)


def test_origin_and_login(api):
    client, _, _ = api
    credentials = {"username": "admin_test", "password": "Admin-Password-123"}
    assert client.post(LOGIN, json=credentials, headers={"Origin": "https://other.example"}).status_code == 403
    assert client.post(LOGIN, json=credentials).status_code == 403
    assert client.post(LOGIN, json={**credentials, "password": "wrong"}, headers={"Origin": ORIGIN}).status_code == 401
    assert client.get("/auth/me").status_code == 401
    assert sign_in(client).status_code == 200
    assert client.get("/auth/me").json()["role"] == "admin"
    assert client.get("/dashboard").status_code == 200
    assert client.get("/auth/csrf").status_code == 200


def test_tickets_notes_and_csrf(api):
    client, _, monkeypatch = api
    assert sign_in(client).status_code == 200
    t = csrf(client)
    req = {"customer_name": "Test Person", "message": "My payment was charged twice"}
    path = "/tickets"
    assert client.post(path, json=req, headers={"Origin": ORIGIN}).status_code == 403
    assert client.post(path, json=req, headers=headers("incorrect")).status_code == 403
    assert client.post(path, json=req, headers=headers(t, "https://evil.example")).status_code == 403

    def fake_ai(request):
        return {"category": "Billing", "priority": "High", "assigned_department": "Billing Team",
                "classification_method": "Test stub", "status": "Awaiting Human Review"}

    monkeypatch.setattr(main, "classify_request_ai", fake_ai)
    response = client.post(path, json=req, headers=headers(t))
    assert response.status_code == 200, response.text
    ticket_id = response.json()["ticket_id"]
    assert client.get(f"/tickets/{ticket_id}").json()["message"] == req["message"]

    status_path = f"/tickets/{ticket_id}/status"
    assert client.patch(status_path, json={"status": "In Progress"}, headers={"Origin": ORIGIN}).status_code == 403
    assert client.patch(status_path, json={"status": "In Progress"}, headers=headers(t)).status_code == 200
    assert client.get(f"/tickets/{ticket_id}").json()["status"] == "In Progress"

    notes_path = f"/tickets/{ticket_id}/notes"
    assert client.post(notes_path, json={"note": "No token"}, headers={"Origin": ORIGIN}).status_code == 403
    assert client.post(notes_path, json={"note": "Bad token"}, headers=headers("bad")).status_code == 403
    assert client.post(notes_path, json={"note": "Wrong origin"}, headers=headers(t, "https://evil.example")).status_code == 403
    resp = client.post(notes_path, json={"note": "Persistent note"}, headers=headers(t))
    assert resp.status_code == 201, resp.text
    note_id = resp.json()["id"]
    read = client.get(notes_path)
    assert read.status_code == 200
    assert read.headers["cache-control"] == "no-store"
    assert len(read.json()["notes"]) == 1
    assert read.json()["notes"][0]["id"] == note_id
    assert read.json()["notes"][0]["note"] == "Persistent note"


def test_logout_and_session_expiration(api):
    client, _, _ = api
    assert client.get("/dashboard", follow_redirects=False).headers["location"] == "/login"
    assert sign_in(client).status_code == 200
    token = csrf(client)
    assert client.post("/auth/logout", headers={"Origin": ORIGIN}).status_code == 403
    assert client.post("/auth/logout", headers=headers(token)).status_code == 200
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/csrf").status_code == 401
    assert client.get("/dashboard", follow_redirects=False).status_code == 303


def test_agent_role_restrictions(api):
    client, _, _ = api
    assert sign_in(client, "agent_test", "Agent-Password-123").status_code == 200
    assert client.get("/admin/users").status_code == 403
    assert client.get("/tickets").status_code == 200
    assert sign_in(client, "admin_test", "Admin-Password-123").status_code == 200
    result = client.get("/admin/users")
    assert result.status_code == 200
    assert {u["role"] for u in result.json()["users"]} == {"admin", "agent"}
    assert all("password_hash" not in user for user in result.json()["users"])


def test_ai_classification_mocked_locally(api, monkeypatch):
    client, _, _ = api
    assert sign_in(client).status_code == 200
    token = csrf(client)

    def fake_post(*args, **kwargs):
        import httpx
        assert args[0] == "http://127.0.0.1:11434/api/chat"
        assert kwargs["json"]["model"] == "qwen3:1.7b"
        return httpx.Response(200, json={"message": {"content":
            '{"category":"Billing","priority":"Normal","explanation":"Looks like billing issue."}'
        }}, request=httpx.Request("POST", args[0]))

    monkeypatch.setattr(main.httpx, "post", fake_post)
    req = {"customer_name": "Test", "message": "My invoice has a problem"}
    assert client.post("/requests/classify-ai", json=req, headers={"Origin": ORIGIN}).status_code == 403
    result = client.post("/requests/classify-ai", json=req, headers=headers(token))
    assert result.status_code == 200, result.text
    assert result.json()["category"] == "Billing"
    basic = client.post("/requests/classify", json=req, headers=headers(token))
    assert basic.status_code == 200
    assert basic.json()["category"] == "Billing"


def test_ui_request_configuration(api):
    source = (Path(__file__).resolve().parents[1] / "frontend" / "index.html").read_text()
    assert 'fetch("/tickets", {\n                    method: "POST"' in source
    assert source.count('"X-CSRF-Token": await getCsrfToken()') >= 4
