"""Authentication handlers for platform login."""

from api.context import app_context, log_buffer
from api.serializers import build_project_dict, publish_project
from cookies.cookie_store import CookieStore
from services.login_service import LoginService

_login_service: LoginService | None = None
_login_project_path: str | None = None


def _get_login_service() -> LoginService:
    global _login_service, _login_project_path
    project = app_context.current_project
    if not project:
        raise ValueError("No project open")
    project_path = str(project.project_path)
    if _login_service is None or _login_project_path != project_path:
        _login_service = LoginService(
            CookieStore(project.project_path),
            log_callback=log_buffer.add,
            on_login=publish_project,
        )
        _login_project_path = project_path
    return _login_service


def start_login(body: dict) -> dict:
    service = _get_login_service()
    project = app_context.current_project
    if not project:
        return {"success": False, "error": "No project open"}
    return service.start_login(project.platform)


def logout(body: dict) -> dict:
    project = app_context.current_project
    if not project:
        return {"success": False, "error": "No project open"}
    store = CookieStore(project.project_path)
    store.delete_cookies(project.platform)
    return {"success": True, "project": build_project_dict()}


def cookie_status(body: dict) -> dict:
    project = app_context.current_project
    if not project:
        return {"has_cookies": False}
    store = CookieStore(project.project_path)
    info = store.get_cookie_info(project.platform)
    return {
        "has_cookies": info is not None,
        "username": info["username"] if info else "",
        "captured_at": info["captured_at"] if info else None,
    }
