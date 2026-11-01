"""Holes that were open before, with checks that closing them did not break normal use."""
import re
from pathlib import Path
from uuid import uuid4

import pytest
import requests

PROJECT = Path(__file__).resolve().parent.parent
ANGRY = "This is the worst service I have ever had, I hate it and I want a refund now."


def post_comment(client, headers, content=ANGRY):
    response = client.post("/comments/", json={"content": f"{content} {uuid4().hex}"}, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def bulk(client, headers, action, *ids, **params):
    return client.post("/comments/bulk-action", params={"action": action, "comment_ids": list(ids), **params}, headers=headers)


# --- API configs ---

def test_an_api_config_can_be_saved_on_a_fresh_database(anon, admin_headers):
    name = f"config-{uuid4().hex[:10]}"
    key = "sk-" + uuid4().hex * 2

    created = anon.post("/admin/api-configs", json={"name": name, "provider": "OpenAI", "api_key": key}, headers=admin_headers)
    assert created.status_code == 200, created.text
    assert key not in created.text

    listed = anon.get("/admin/api-configs", headers=admin_headers)
    assert name in listed.text
    assert key not in listed.text


# --- Bulk actions ---

def test_bulk_delete_needs_a_token(anon, user_headers):
    comment = post_comment(anon, user_headers)
    assert bulk(anon, None, "delete", comment["id"]).status_code == 401
    assert anon.get(f"/comments/{comment['id']}", headers=user_headers).status_code == 200


def test_bulk_delete_needs_an_admin(anon, user_headers):
    comment = post_comment(anon, user_headers)
    assert bulk(anon, user_headers, "delete", comment["id"]).status_code == 403
    assert anon.get(f"/comments/{comment['id']}", headers=user_headers).status_code == 200


def test_bulk_delete_removes_a_comment_with_its_ticket_and_favorites(anon, user_headers, admin_headers):
    from app.database.session import SessionLocal
    from app.models.activity_log import Favorite
    from app.models.ticket import Ticket

    comment = post_comment(anon, user_headers)
    assert comment["ticket"], "this comment should have opened a ticket"
    assert anon.post(f"/comments/{comment['id']}/favorite", headers=user_headers).status_code == 200

    response = bulk(anon, admin_headers, "delete", comment["id"])
    assert response.status_code == 200, response.text
    assert response.json()["affected_count"] == 1
    assert anon.get(f"/comments/{comment['id']}", headers=admin_headers).status_code == 404

    db = SessionLocal()
    assert db.query(Ticket).filter(Ticket.comment_id == comment["id"]).count() == 0
    assert db.query(Favorite).filter(Favorite.comment_id == comment["id"]).count() == 0
    db.close()


def test_the_other_bulk_actions_work_for_an_admin(anon, user_headers, admin_headers):
    calm = post_comment(anon, user_headers, "Thank you, a lovely product")
    assert bulk(anon, admin_headers, "tag", calm["id"]).status_code == 200
    response = bulk(anon, admin_headers, "assign_priority", calm["id"], priority="High")
    assert response.status_code == 200, response.text
    assert anon.get(f"/comments/{calm['id']}", headers=admin_headers).json()["priority"] == "High"

    angry = post_comment(anon, user_headers)
    assert bulk(anon, admin_headers, "create_tickets", angry["id"]).status_code == 200


# --- CSV upload ---

@pytest.fixture()
def upload_folder(tmp_path, monkeypatch):
    """Run in a scratch folder and keep the file, which the background job would otherwise delete."""
    seen = []
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("app.services.csv_service.process_csv_file", lambda path, source: seen.append(path))
    return tmp_path, seen


@pytest.mark.parametrize("filename", ["../victim.csv", "..\\victim.csv", "tmp/../../victim.csv"])
def test_an_upload_cannot_write_outside_the_tmp_folder(anon, user_headers, upload_folder, filename):
    folder, seen = upload_folder
    victim = folder / "victim.csv"
    victim.write_text("do not overwrite me", encoding="utf-8")

    response = anon.post(
        "/comments/upload",
        files={"file": (filename, b"content\nhello there\n", "text/csv")},
        headers=user_headers,
    )

    assert response.status_code == 200, response.text
    assert victim.read_text(encoding="utf-8") == "do not overwrite me"
    assert Path(seen[0]).resolve().parent == (folder / "tmp").resolve()


def test_an_upload_returns_only_the_plain_file_name(anon, user_headers, upload_folder):
    response = anon.post(
        "/comments/upload",
        files={"file": ("../../some/place/report.csv", b"content\nhello there\n", "text/csv")},
        headers=user_headers,
    )
    assert response.json()["filename"] == "report.csv"


def test_a_normal_upload_is_still_processed_and_cleaned_up(anon, user_headers, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    text = f"The app keeps crashing {uuid4().hex}"
    csv = f"content\n{text}\n".encode()

    response = anon.post("/comments/upload", files={"file": ("comments.csv", csv, "text/csv")}, headers=user_headers)

    assert response.status_code == 200, response.text
    found = anon.get("/comments/", params={"search": text}, headers=user_headers).json()
    assert [c["content"] for c in found] == [text]
    assert list((tmp_path / "tmp").iterdir()) == []


# --- URL scraping ---

def scrape(client, headers, monkeypatch, *comments):
    page = "<html><body>" + "".join(f"<p>{text}</p>" for text in comments) + "</body></html>"
    monkeypatch.setattr("app.api.ai.fetch_url_content", lambda url: page)
    url = f"https://shop.example/reviews/{uuid4().hex}"
    response = client.post("/ai/scrape-url", json={"url": url}, headers=headers)
    assert response.status_code == 200, response.text
    saved = client.get("/comments/", params={"source": f"web_scrape:{url}"}, headers=headers).json()
    return response.json(), saved


def test_scraped_comments_are_really_analysed(anon, user_headers, monkeypatch):
    body, saved = scrape(anon, user_headers, monkeypatch, ANGRY, "Thank you, this is a great and lovely product.")

    assert body["success"] and body["saved_count"] == len(saved) == 2
    angry = next(c for c in saved if "worst service" in c["content"])
    assert angry["emotion"] != "neutral"
    assert angry["confidence"] > 0
    assert angry["priority"] in ("High", "Critical")
    assert angry["ticket"] is not None


def test_a_scraped_comment_that_cannot_be_analysed_is_not_saved(anon, user_headers, monkeypatch):
    monkeypatch.setattr("app.api.ai.analyze_text", lambda text: None)
    body, saved = scrape(anon, user_headers, monkeypatch, ANGRY)

    assert body["comments_count"] == 1
    assert body["saved_count"] == 0
    assert saved == []


def response_with(status, location=None, body="<html>page</html>"):
    response = requests.models.Response()
    response.status_code = status
    response._content = body.encode()
    response.encoding = "utf-8"
    if location:
        response.headers["location"] = location
    return response


@pytest.fixture()
def network(monkeypatch):
    """A fake network. Names resolve as listed here and each fetch is recorded."""
    addresses = {
        "shop.example": "93.184.216.34",
        "localhost": "127.0.0.1",
        "metadata.example": "169.254.169.254",
        "intranet.example": "10.0.0.5",
    }
    fetched = []
    responses = {}

    def getaddrinfo(host, *args, **kwargs):
        return [(2, 1, 6, "", (addresses.get(host, host), 0))]

    def get(url, **kwargs):
        fetched.append(url)
        return responses.get(url, response_with(200))

    monkeypatch.setattr("socket.getaddrinfo", getaddrinfo)
    monkeypatch.setattr("app.services.web_scraper.requests.get", get)
    return fetched, responses


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:8000/admin/config",
        "http://localhost/",
        "127.0.0.1",
        "http://[::1]/",
        "http://[::ffff:127.0.0.1]/",
        "http://10.0.0.5/",
        "http://192.168.1.1/",
        "http://169.254.169.254/latest/meta-data/",
        "http://metadata.example/",
        "http://intranet.example/",
    ],
)
def test_the_scraper_will_not_fetch_private_addresses(network, url):
    from app.services.web_scraper import fetch_url_content

    fetched, _ = network
    assert fetch_url_content(url) is None
    assert fetched == []


def test_the_scraper_will_not_follow_a_redirect_to_a_private_address(network):
    from app.services.web_scraper import fetch_url_content

    fetched, responses = network
    responses["http://shop.example/"] = response_with(302, "http://169.254.169.254/latest/meta-data/")

    assert fetch_url_content("http://shop.example/") is None
    assert fetched == ["http://shop.example/"]


def test_the_scraper_still_fetches_public_pages_and_follows_redirects(network):
    from app.services.web_scraper import fetch_url_content

    fetched, responses = network
    responses["http://shop.example/old"] = response_with(301, "/new")
    responses["http://shop.example/new"] = response_with(200, body="<p>real page</p>")

    assert fetch_url_content("http://shop.example/old") == "<p>real page</p>"
    assert fetched == ["http://shop.example/old", "http://shop.example/new"]


def test_a_private_host_can_be_allowed_on_purpose(network, monkeypatch):
    from app.services.web_scraper import fetch_url_content

    monkeypatch.setenv("SCRAPE_ALLOWED_HOSTS", "intranet.example")
    assert fetch_url_content("http://intranet.example/") == "<html>page</html>"
    assert fetch_url_content("http://10.0.0.5/") is None


# --- Health check ---

def test_health_never_calls_the_paid_api(anon, monkeypatch):
    calls = []
    monkeypatch.setattr("app.services.ai_service.call_openai", lambda *args, **kwargs: calls.append(args))

    assert anon.get("/health").json()["status"] == "ok"
    assert calls == []


# --- CORS ---

def test_other_sites_are_not_offered_credentials(anon):
    response = anon.options(
        "/auth/me",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert response.headers.get("access-control-allow-credentials") != "true"


# --- Stored script in the dashboards ---

UNTRUSTED_FIELDS = re.compile(
    r"\b(?:c|comment|t|r|rule|m|log|api_config|item)\??\."
    r"(?:content|source|customer_name|emotion|intent|title|pattern|author|name|provider|model_name"
    r"|description|action_type|resource_type|suggested_response)\b|\bt\.(?:status|priority)\b"
)


@pytest.mark.parametrize("page", sorted(path.name for path in (PROJECT / "frontend").glob("*.html")))
def test_pages_escape_what_users_can_write(page):
    # Tokens live in localStorage, so a script in a comment could steal an admin's login.
    html = (PROJECT / "frontend" / page).read_text(encoding="utf-8")
    expressions = re.findall(r"\$\{([^{}]*)\}", html)
    unescaped = [
        expression
        for expression in expressions
        if UNTRUSTED_FIELDS.search(expression) and "escapeHtml(" not in expression and ".length" not in expression
    ]
    assert unescaped == []
