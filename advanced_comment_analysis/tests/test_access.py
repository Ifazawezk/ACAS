"""Every route stays closed unless this file says otherwise."""
import re

from fastapi import APIRouter
from fastapi.routing import APIRoute

# Written out here on purpose, apart from app/utils/roles.py, so opening a route takes two edits.
PUBLIC_ROUTES = {
    ("POST", "/auth/register"),
    ("POST", "/auth/token"),
    ("GET", "/health"),
}

# Framework pages and static files. FastAPI dependencies do not run on these, so none may be private.
NON_API_ROUTES = {"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc", "/frontend"}

ADMIN_OUTSIDE_THE_ADMIN_PATHS = {
    ("POST", "/comments/bulk-action"),
    ("GET", "/comments/export/download"),
    ("GET", "/comments/activity/log"),
}


def app_routes():
    from app.main import app

    return app.routes


def every_api_route():
    for route in app_routes():
        if isinstance(route, APIRoute):
            for method in sorted(route.methods):
                yield method, route.path


def with_ids(path):
    return re.sub(r"\{[^}]+\}", "1", path)


def is_admin_route(method, path):
    return path.startswith("/admin") or (method, path) in ADMIN_OUTSIDE_THE_ADMIN_PATHS


def statuses(client, routes, headers=None):
    return {(method, path): client.request(method, with_ids(path), headers=headers).status_code for method, path in routes}


def test_routes_were_found():
    assert len(list(every_api_route())) > 40


def test_every_non_public_route_refuses_a_request_without_a_token(anon):
    closed = [route for route in every_api_route() if route not in PUBLIC_ROUTES]
    answered = {route: status for route, status in statuses(anon, closed).items() if status != 401}
    assert answered == {}


def test_every_non_public_route_refuses_a_bad_token(anon):
    closed = [route for route in every_api_route() if route not in PUBLIC_ROUTES]
    headers = {"Authorization": "Bearer not.a.token"}
    answered = {route: status for route, status in statuses(anon, closed, headers).items() if status != 401}
    assert answered == {}


def test_a_trailing_slash_does_not_get_around_the_rule(anon):
    closed = [route for route in every_api_route() if route not in PUBLIC_ROUTES]
    swapped = [(method, path[:-1] if path.endswith("/") else path + "/") for method, path in closed]
    # A slash that matches no route gives 404 or 405. Anything else must still be the 401.
    answered = {route: status for route, status in statuses(anon, swapped).items() if status not in (401, 404, 405)}
    assert answered == {}


def test_every_admin_route_refuses_a_normal_user(anon, user_headers):
    admin_routes = [route for route in every_api_route() if is_admin_route(*route)]
    answered = {route: status for route, status in statuses(anon, admin_routes, user_headers).items() if status != 403}
    assert answered == {}


def test_an_admin_is_let_through_on_every_route(anon, admin_headers):
    # The export route writes a file to /tmp, so it is left out to keep test runs clean.
    skip = PUBLIC_ROUTES | {("GET", "/comments/export/download")}
    routes = [route for route in every_api_route() if route not in skip]
    refused = {route: status for route, status in statuses(anon, routes, admin_headers).items() if status in (401, 403)}
    assert refused == {}


def test_a_normal_user_is_let_through_on_every_ordinary_route(anon, user_headers):
    routes = [route for route in every_api_route() if route not in PUBLIC_ROUTES and not is_admin_route(*route)]
    refused = {route: status for route, status in statuses(anon, routes, user_headers).items() if status in (401, 403)}
    assert refused == {}


def test_the_public_list_in_the_app_matches_this_file():
    from app.utils import roles

    assert roles.PUBLIC_ROUTES == PUBLIC_ROUTES


def test_nothing_is_served_outside_the_access_check():
    # A plain Route or Mount skips FastAPI dependencies, so each one has to be listed above.
    others = {route.path for route in app_routes() if not isinstance(route, APIRoute)}
    assert others == NON_API_ROUTES


def test_a_new_route_is_closed_without_any_extra_code(anon, user_headers, admin_headers):
    from app.main import app

    def endpoint():
        return {"ok": True}

    router = APIRouter()
    router.add_api_route("/brand-new-route", endpoint)
    router.add_api_route("/admin/brand-new-route", endpoint)
    before = list(app.router.routes)
    app.include_router(router)
    app.add_api_route("/brand-new-route-on-the-app", endpoint)
    try:
        assert anon.get("/brand-new-route").status_code == 401
        assert anon.get("/brand-new-route-on-the-app").status_code == 401
        assert anon.get("/brand-new-route", headers=user_headers).status_code == 200
        assert anon.get("/admin/brand-new-route").status_code == 401
        assert anon.get("/admin/brand-new-route", headers=user_headers).status_code == 403
        assert anon.get("/admin/brand-new-route", headers=admin_headers).status_code == 200
    finally:
        app.router.routes[:] = before


def test_rules_and_config_answer_nothing_without_a_token(anon):
    assert anon.post("/admin/rules", json={"pattern": "refund"}).status_code == 401
    assert anon.get("/admin/config").status_code == 401


def test_a_deactivated_account_loses_access_straight_away(anon, register):
    from app.database.session import SessionLocal
    from app.models.user import User

    account = register(anon)
    headers = {"Authorization": f"Bearer {account['access_token']}"}
    assert anon.get("/auth/me", headers=headers).status_code == 200

    db = SessionLocal()
    db.query(User).filter(User.id == account["user_id"]).update({"is_active": False})
    db.commit()
    db.close()

    assert anon.get("/auth/me", headers=headers).status_code == 401
    assert anon.get("/comments/", headers=headers).status_code == 401


def test_the_role_in_a_token_is_not_trusted(anon, register):
    # Only the signature is checked against the token. The role always comes from the database.
    from app.utils.security import create_access_token

    account = register(anon)
    token = create_access_token({"sub": str(account["user_id"]), "role": "admin"})
    assert anon.get("/admin/config", headers={"Authorization": f"Bearer {token}"}).status_code == 403
