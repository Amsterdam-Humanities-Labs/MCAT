"""API route definitions."""

from api.handlers import health, project, processing, run, csv, results, tracking


def get_routes():
    """Return GET route mappings."""
    return {
        "/health": lambda _path: health.get_health(),
        "/run/interrupted": lambda _path: run.get_interrupted(),
        "/results/combined": lambda _path: results.get_combined(),
    }


def post_routes():
    """Return POST route mappings."""
    return {
        "/project/create": project.create,
        "/project/open": project.open_project,
        "/project/close": lambda body: project.close(),
        "/project/import-preview": project.preview_import,
        "/project/import-confirm": project.confirm_import,
        "/process/start": processing.start,
        "/process/pause": processing.pause,
        "/process/resume": processing.resume,
        "/process/cancel": processing.cancel,
        "/run/resume": run.resume_run,
        "/run/abandon": run.abandon,
        "/csv/load": csv.load,
        "/csv/detect-url-column": csv.detect_url_column,
        "/tracking/start": tracking.start_tracking,
        "/tracking/stop": tracking.stop_tracking,
        "/tracking/status": tracking.get_tracking_status,
        "/results/run": results.get_run_results,
    }
