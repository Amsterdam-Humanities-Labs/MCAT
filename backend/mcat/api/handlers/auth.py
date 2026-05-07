"""Authentication handlers for platform login."""

from api.context import app_context
from api.handlers.project import _build_project_dict
from cookies.cookie_store import CookieStore
from services.login_service import LoginService

_login_service: LoginService | None = None


def _get_login_service() -> LoginService:
    global _login_service
    project = app_context.current_project
    if not project:
        raise ValueError("No project open")
    if _login_service is None:
        _login_service = LoginService(CookieStore(project.project_path))
    return _login_service


def start_login(body: dict) -> dict:
    service = _get_login_service()
    project = app_context.current_project
    return service.start_login(project.platform)


def check_login(body: dict) -> dict:
    service = _get_login_service()
    return service.check_login()


def complete_login(body: dict) -> dict:
    service = _get_login_service()
    return service.complete_login()


def cancel_login(body: dict) -> dict:
    service = _get_login_service()
    return service.cancel_login()


def logout(body: dict) -> dict:
    project = app_context.current_project
    if not project:
        return {"success": False, "error": "No project open"}
    store = CookieStore(project.project_path)
    store.delete_cookies(project.platform)
    return {"success": True, "project": _build_project_dict()}
