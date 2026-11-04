"""Point the app at a throwaway database and the offline analyzer before it is imported."""
import os
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest

_database = Path(tempfile.mkdtemp(prefix="acas-tests-")) / "test.db"

os.environ["USE_SQLITE_DEV"] = "false"
os.environ["DATABASE_URL"] = f"sqlite:///{_database.as_posix()}"
os.environ["FORCE_LOCAL"] = "true"
os.environ["OPENAI_API_KEY"] = ""
os.environ["ENVIRONMENT"] = "test"
os.environ.pop("SCRAPE_ALLOWED_HOSTS", None)
os.environ["EXPORT_DIR"] = tempfile.mkdtemp(prefix="acas-exports-")


@pytest.fixture()
def anon():
    """A client with no token. Server errors come back as 500 so tests can compare status codes."""
    from fastapi.testclient import TestClient

    from app.main import app

    # The context manager runs the startup hook, which creates the tables.
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture()
def register():
    """Register a new account and return its login response."""

    def _register(client, **fields):
        body = {"username": f"person_{uuid4().hex[:10]}", "password": "a-test-password", **fields}
        response = client.post("/auth/register", json=body)
        assert response.status_code == 200, response.text
        return response.json()

    return _register


@pytest.fixture()
def user_headers(anon, register):
    return {"Authorization": f"Bearer {register(anon)['access_token']}"}


@pytest.fixture()
def make_admin(anon):
    """Written straight to the database, because no public route can create an admin."""

    def _make_admin():
        from app.database.session import SessionLocal
        from app.models.user import User, UserRole
        from app.utils.security import create_access_token, hash_password

        db = SessionLocal()
        try:
            admin = User(
                username=f"admin_{uuid4().hex[:10]}",
                hashed_password=hash_password("a-test-password"),
                role=UserRole.admin,
            )
            db.add(admin)
            db.commit()
            return {"Authorization": f"Bearer {create_access_token({'sub': str(admin.id)})}"}
        finally:
            db.close()

    return _make_admin


@pytest.fixture()
def admin_headers(make_admin):
    return make_admin()
