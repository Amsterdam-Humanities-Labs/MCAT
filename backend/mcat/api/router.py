"""API route definitions."""

from api.handlers import health, project, processing, run, csv, tracking, dialog, auth

GET_ROUTES = {
    "/health": lambda _path: health.get_health(),
}

POST_ROUTES = {
    "/project/create": project.create,
    "/project/open": project.open_project,
    "/project/close": lambda body: project.close(),
    "/project/screenshots": project.set_screenshots,
    "/project/tracking-config": project.set_tracking_config,
    "/project/import-preview": project.preview_import,
    "/project/import-confirm": project.confirm_import,
    "/process/start": processing.start,
    "/process/pause": processing.pause,
    "/process/resume": processing.resume,
    "/run/abandon": run.abandon,
    "/run/changed-results": run.get_changed_results,
    "/run/results": run.get_results,
    "/csv/load": csv.load,
    "/csv/detect-url-column": csv.detect_url_column,
    "/tracking/start": tracking.start_tracking,
    "/tracking/stop": tracking.stop_tracking,
    "/tracking/status": tracking.get_tracking_status,
    "/dialog/open-file": dialog.open_file,
    "/dialog/open-folder": dialog.open_folder,
    "/dialog/open-external": dialog.open_external,
    "/auth/start-login": auth.start_login,
    "/auth/logout": auth.logout,
    "/auth/cookie-status": auth.cookie_status,
}
