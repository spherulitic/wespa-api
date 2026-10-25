"""Helpers for accessing the Flask-Caching instance."""

from __future__ import annotations

from flask import current_app


def get_cache():
    """Return the configured Flask-Caching instance, if caching is enabled.

    Flask-Caching stores a mapping of Cache instance -> backend in
    ``app.extensions["cache"]``, so the extension value itself is not the
    cache object.
    """
    extension = current_app.extensions.get("cache")
    if isinstance(extension, dict):
        for candidate in extension:
            if hasattr(candidate, "get") and hasattr(candidate, "set"):
                return candidate
    if hasattr(extension, "get") and hasattr(extension, "set"):
        return extension
    return None
