"""The activity log, templates and favorites used to answer 500 on every call."""
from uuid import uuid4

ANGRY = "This is the worst service I have ever had, I hate it and I want a refund now."


def post_comment(client, headers):
    response = client.post("/comments/", json={"content": f"{ANGRY} {uuid4().hex}"}, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def my_id(client, headers):
    return client.get("/auth/me", headers=headers).json()["id"]


# --- Activity log ---

def test_the_activity_log_can_be_read(anon, admin_headers):
    for path in ("/admin/activity-log", "/admin/activity-log/stats"):
        response = anon.get(path, headers=admin_headers)
        assert response.status_code == 200, response.text


def test_an_admin_can_add_an_entry_and_it_names_them(anon, admin_headers):
    note = f"checked the rules {uuid4().hex}"
    response = anon.post(
        "/admin/activity-log/log",
        json={"action": "update", "resource_type": "rule", "details": note},
        headers=admin_headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["user_id"] == my_id(anon, admin_headers)

    logs = anon.get("/admin/activity-log", params={"action": "update"}, headers=admin_headers).json()
    assert note in [entry["details"] for entry in logs]


def test_changes_are_written_to_the_log(anon, admin_headers, user_headers):
    comment = post_comment(anon, user_headers)
    anon.post("/comments/bulk-action", params={"action": "assign_priority", "comment_ids": [comment["id"]], "priority": "High"}, headers=admin_headers)
    anon.post("/admin/templates", json={"name": f"t-{uuid4().hex[:8]}", "content": "Sorry about that."}, headers=admin_headers)
    anon.post("/admin/rules", json={"pattern": f"refund-{uuid4().hex[:8]}"}, headers=admin_headers)
    anon.post(f"/tickets/{comment['ticket']['id']}/close", headers=user_headers)

    admin_logs = anon.get("/admin/activity-log", params={"user_id": my_id(anon, admin_headers)}, headers=admin_headers).json()
    assert {(e["action"], e["resource_type"]) for e in admin_logs} == {("bulk", "comment"), ("create", "template"), ("create", "rule")}

    user_logs = anon.get("/admin/activity-log", params={"user_id": my_id(anon, user_headers)}, headers=admin_headers).json()
    assert [(e["action"], e["resource_type"], e["resource_id"]) for e in user_logs] == [("update", "ticket", comment["ticket"]["id"])]

    stats = anon.get("/admin/activity-log/stats", headers=admin_headers).json()
    assert stats["total_logs"] >= 4
    assert stats["by_action"]["create"] >= 2


def test_clearing_old_entries_keeps_recent_ones_and_is_logged(anon, admin_headers):
    anon.post("/admin/activity-log/log", json={"action": "update", "resource_type": "rule"}, headers=admin_headers)
    before = anon.get("/admin/activity-log/stats", headers=admin_headers).json()["total_logs"]

    response = anon.delete("/admin/activity-log/old", params={"days": 30}, headers=admin_headers)

    assert response.status_code == 200, response.text
    assert response.json()["deleted"] == 0
    assert anon.get("/admin/activity-log/stats", headers=admin_headers).json()["total_logs"] == before + 1


# --- Templates ---

def test_a_template_can_be_saved_read_used_and_deleted(anon, admin_headers):
    name = f"apology-{uuid4().hex[:8]}"
    created = anon.post("/admin/templates", json={"name": name, "content": "Sorry, we are on it."}, headers=admin_headers)
    assert created.status_code == 200, created.text
    template = created.json()
    assert template["created_at"]

    assert anon.get(f"/admin/templates/{template['id']}", headers=admin_headers).json()["name"] == name
    assert name in [t["name"] for t in anon.get("/admin/templates", headers=admin_headers).json()]

    updated = anon.put(
        f"/admin/templates/{template['id']}",
        json={"name": name, "content": "Sorry, it is fixed now.", "category": "apology"},
        headers=admin_headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["category"] == "apology"

    assert anon.post(f"/admin/templates/{template['id']}/use", headers=admin_headers).json()["usage_count"] == 1
    assert anon.delete(f"/admin/templates/{template['id']}", headers=admin_headers).status_code == 200
    assert anon.get(f"/admin/templates/{template['id']}", headers=admin_headers).status_code == 404


def test_a_template_belongs_to_the_admin_who_made_it(anon, admin_headers):
    from app.database.session import SessionLocal
    from app.models.template import ResponseTemplate

    created = anon.post("/admin/templates", json={"name": "mine", "content": "Hello"}, headers=admin_headers).json()
    db = SessionLocal()
    try:
        assert db.get(ResponseTemplate, created["id"]).user_id == my_id(anon, admin_headers)
    finally:
        db.close()


# --- Favorites ---

def test_favorites_are_listed_for_their_owner_only(anon, user_headers, register):
    comment = post_comment(anon, user_headers)
    assert anon.post(f"/comments/{comment['id']}/favorite", headers=user_headers).status_code == 200

    mine = anon.get("/comments/favorites/list", headers=user_headers)
    assert mine.status_code == 200, mine.text
    assert [c["id"] for c in mine.json()] == [comment["id"]]

    someone_else = {"Authorization": f"Bearer {register(anon)['access_token']}"}
    assert anon.get("/comments/favorites/list", headers=someone_else).json() == []
