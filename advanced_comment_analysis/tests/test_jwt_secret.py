"""No token is ever signed with a value anyone can read in this repo."""
import os
import secrets
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from jose import jwt

PROJECT = Path(__file__).resolve().parent.parent
PUBLISHED_DEFAULT = "supersecretjwtkey"


def start_app(**env):
    """Import the app the way uvicorn does, in a new process with its own settings."""
    return subprocess.run(
        [sys.executable, "-c", "import app.main"],
        cwd=PROJECT,
        env={**os.environ, **env},
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("secret", ["", PUBLISHED_DEFAULT, "change-me", "too-short"])
def test_production_refuses_to_start_without_a_real_secret(secret):
    result = start_app(ENVIRONMENT="production", JWT_SECRET_KEY=secret)
    assert result.returncode != 0
    assert "JWT_SECRET_KEY" in result.stderr


@pytest.mark.parametrize("environment", ["staging", "prod", " Production "])
def test_anything_not_marked_as_development_counts_as_production(environment):
    result = start_app(ENVIRONMENT=environment, JWT_SECRET_KEY="")
    assert result.returncode != 0


def test_production_starts_with_a_real_secret():
    result = start_app(ENVIRONMENT="production", JWT_SECRET_KEY=secrets.token_urlsafe(48))
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("environment", ["development", "dev", "local", "test", ""])
def test_development_starts_with_no_setup(environment):
    result = start_app(ENVIRONMENT=environment, JWT_SECRET_KEY="")
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("secret", ["", PUBLISHED_DEFAULT, "change-me"])
def test_development_replaces_a_weak_secret_with_a_random_one(monkeypatch, secret):
    from app.utils import security

    monkeypatch.setenv("JWT_SECRET_KEY", secret)
    monkeypatch.setenv("ENVIRONMENT", "development")
    first, second = security.load_jwt_secret(), security.load_jwt_secret()

    assert first != second
    assert len(first) >= 32
    assert secret not in (first, second)


def test_a_real_secret_is_used_as_given(monkeypatch):
    from app.utils import security

    real = secrets.token_urlsafe(48)
    monkeypatch.setenv("JWT_SECRET_KEY", real)
    assert security.load_jwt_secret() == real


def test_a_token_forged_with_the_published_default_is_refused(anon, register):
    account = register(anon)
    claims = {"sub": str(account["user_id"]), "exp": datetime.utcnow() + timedelta(minutes=5)}
    forged = jwt.encode(claims, PUBLISHED_DEFAULT, algorithm="HS256")
    assert anon.get("/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401
