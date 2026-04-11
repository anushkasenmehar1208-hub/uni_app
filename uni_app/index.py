"""Compatibility shim for Reflex app discovery.

Keep a single canonical app definition in `uni_app.uni_app`.
"""

from .uni_app import AppState, app

__all__ = ["app", "AppState"]
