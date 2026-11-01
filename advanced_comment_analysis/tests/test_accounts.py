"""Registration cannot grant a role, and the first admin comes from a command on the server."""
import os
import secrets
import sqlite3
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest

PROJECT = Path(__file__).resolve().parent.parent


def run_tool(script, *args, **env):
    return subprocess.run(
        [sys.executable, str(PROJECT / "tools" / script), *args],
        cwd=PROJECT,
        env={**os.environ, "PYTHONIOENCODING": "utf-8", **env},
        capture_output=True,
        text=True,
        encoding="utf-8",
        stdin=subprocess.DEVNULL,
    )


def empty_production_database(tmp_path):
    path = tmp_path / "production.db"
    return path, {
        "ENVIRONMENT": "production",
        "JWT_SECRET_KEY": secrets.token_urlsafe(48),
        "USE_SQLITE_DEV": "false",
        "DATABASE_URL": f"sqlite:///{path.as_posix()}",
    }


@pytest.mark.parametrize("role", ["admin", "manager"])
def test_registration_cannot_set_a_role(anon, register, role):
    account = register(anon, role=role)
    headers = {"Authorization": f"Bearer {account['access_token']}"}

    assert account["role"] == "user"
    assert anon.get("/auth/me", headers=headers).json()["role"] == "user"
    assert anon.get("/admin/config", headers=headers).status_code == 403


def test_registration_schema_has_no_role_field():
    from app.schemas.auth import UserRegister

    assert "role" not in UserRegister.__fields__


def test_the_login_pages_do_not_offer_a_role():
    for page in ("login.html", "login_improved.html"):
        html = (PROJECT / "frontend" / page).read_text(encoding="utf-8")
        assert 'value="admin"' not in html and 'data-role="admin"' not in html, page


def test_a_password_bcrypt_cannot_hash_is_refused_cleanly(anon):
    too_long = "a" * 100
    assert anon.post("/auth/register", json={"username": f"p_{uuid4().hex[:10]}", "password": too_long}).status_code == 400
    assert anon.post("/auth/token", json={"username": "nobody", "password": too_long}).status_code == 401


def test_a_too_long_password_on_a_real_account_is_a_failed_login(anon, register):
    account = register(anon)
    response = anon.post("/auth/token", json={"username": account["username"], "password": "a" * 100})
    assert response.status_code == 401


def test_setup_command_creates_an_admin_who_can_log_in(anon):
    username = f"owner_{uuid4().hex[:10]}"
    password = secrets.token_urlsafe(18)

    result = run_tool("create_admin.py", "--username", username, ACAS_ADMIN_PASSWORD=password)
    assert result.returncode == 0, result.stderr
    assert password not in result.stdout + result.stderr

    login = anon.post("/auth/token", json={"username": username, "password": password})
    assert login.status_code == 200
    assert login.json()["role"] == "admin"
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert anon.get("/admin/config", headers=headers).status_code == 200


def test_setup_command_works_on_an_empty_production_database(tmp_path):
    path, env = empty_production_database(tmp_path)

    result = run_tool("create_admin.py", "--username", "owner", ACAS_ADMIN_PASSWORD=secrets.token_urlsafe(18), **env)
    assert result.returncode == 0, result.stderr

    rows = sqlite3.connect(path).execute("SELECT username, role FROM users").fetchall()
    assert rows == [("owner", "admin")]


def test_setup_command_refuses_a_short_password():
    username = f"owner_{uuid4().hex[:10]}"
    result = run_tool("create_admin.py", "--username", username, ACAS_ADMIN_PASSWORD="admin@123")
    assert result.returncode != 0
    assert "12" in result.stderr


def test_setup_command_will_not_touch_an_existing_account(anon, register):
    account = register(anon)
    result = run_tool("create_admin.py", "--username", account["username"], ACAS_ADMIN_PASSWORD=secrets.token_urlsafe(18))
    assert result.returncode != 0

    login = anon.post("/auth/token", json={"username": account["username"], "password": "a-test-password"})
    assert login.json()["role"] == "user"


def test_setup_command_does_not_accept_a_password_argument():
    # Arguments end up in shell history and process lists.
    result = run_tool("create_admin.py", "--username", "owner", "--password", "a-long-enough-password")
    assert result.returncode != 0


def test_demo_accounts_cannot_be_seeded_in_production(tmp_path):
    path, env = empty_production_database(tmp_path)

    result = run_tool("seed_users.py", **env)
    assert result.returncode != 0
    assert "create_admin.py" in result.stderr

    if path.exists():
        tables = sqlite3.connect(path).execute("SELECT name FROM sqlite_master WHERE name = 'users'").fetchall()
        assert not tables or not sqlite3.connect(path).execute("SELECT * FROM users").fetchall()
