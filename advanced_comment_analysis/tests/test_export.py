"""Exports are saved in a data folder, open in Excel, and only the admin who made one can download it."""
import codecs
import json
from pathlib import Path
from uuid import uuid4

import pytest

PROJECT = Path(__file__).resolve().parent.parent
ARABIC = "الخدمة سيئة جدا ولم يرد علي أحد"


def add_comment(client, headers):
    text = f"{ARABIC} {uuid4().hex}"
    assert client.post("/comments/", json={"content": text}, headers=headers).status_code == 200
    return text


def export(client, headers, **params):
    response = client.get("/comments/export/download", params=params, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def test_a_csv_export_of_arabic_comments_opens_in_excel(anon, user_headers, admin_headers):
    text = add_comment(anon, user_headers)

    download = anon.get(export(anon, admin_headers)["url"], headers=admin_headers)

    assert download.status_code == 200, download.text
    assert download.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in download.headers["content-disposition"]
    # Excel reads a CSV as the local code page unless it starts with a UTF-8 byte order mark.
    assert download.content.startswith(codecs.BOM_UTF8)
    assert text in download.content.decode("utf-8-sig")


def test_a_json_export_can_be_downloaded(anon, user_headers, admin_headers):
    text = add_comment(anon, user_headers)

    download = anon.get(export(anon, admin_headers, format="json")["url"], headers=admin_headers)

    assert download.status_code == 200, download.text
    assert text in [c["content"] for c in json.loads(download.content.decode("utf-8"))]


def test_an_export_with_no_comments_still_gives_a_file(anon, admin_headers):
    result = export(anon, admin_headers, emotion=f"none-{uuid4().hex}")

    download = anon.get(result["url"], headers=admin_headers)

    assert result["count"] == 0
    assert download.status_code == 200
    assert download.content.decode("utf-8-sig").startswith("id,")


def test_exports_are_written_to_the_export_folder(anon, admin_headers, tmp_path, monkeypatch):
    monkeypatch.setenv("EXPORT_DIR", str(tmp_path))

    result = export(anon, admin_headers)

    assert [path.name for path in tmp_path.rglob("*") if path.is_file()] == [result["filename"]]


def test_the_export_folder_defaults_to_the_project_data_folder(monkeypatch):
    from app.api.comments import export_dir

    monkeypatch.delenv("EXPORT_DIR", raising=False)
    assert export_dir() == PROJECT / "data" / "exports"
    monkeypatch.setenv("EXPORT_DIR", "somewhere/else")
    assert export_dir() == PROJECT / "somewhere" / "else"


def test_only_the_admin_who_made_an_export_can_download_it(anon, admin_headers, make_admin, user_headers):
    url = export(anon, admin_headers)["url"]

    assert anon.get(url).status_code == 401
    assert anon.get(url, headers=user_headers).status_code == 403
    assert anon.get(url, headers=make_admin()).status_code == 404
    assert anon.get(url, headers=admin_headers).status_code == 200


@pytest.mark.parametrize("name", ["..%2F..%2Fdev.db", "..\..\data\dev.db", "notes.txt", "comments_export.csv"])
def test_a_download_cannot_reach_other_files(anon, admin_headers, name):
    assert anon.get(f"/comments/export/files/{name}", headers=admin_headers).status_code == 404


def test_an_export_is_logged(anon, admin_headers):
    export(anon, admin_headers, format="json")

    me = anon.get("/auth/me", headers=admin_headers).json()["id"]
    logs = anon.get("/admin/activity-log", params={"user_id": me}, headers=admin_headers).json()
    assert [(e["action"], e["resource_type"]) for e in logs] == [("export", "comment")]
