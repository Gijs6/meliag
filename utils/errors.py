import json
import os
import sys
import threading
import traceback
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION_FILE = os.path.join(ROOT, "VERSION")
LIBRARY_MARKERS = ("site-packages", "dist-packages", "/lib/python")

_state = {"version": None, "user": None}


def _version(codename):
    build = "dev"
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE) as f:
            build = f.read().strip() or "dev"
    return f"{codename}-{build}"


def _frames(tb):
    frames = []
    for frame in traceback.extract_tb(tb):
        path = frame.filename
        in_app = path.startswith(ROOT) and not any(m in path for m in LIBRARY_MARKERS)
        if in_app:
            path = os.path.relpath(path, ROOT)
        frames.append(
            {
                "file": path,
                "line": frame.lineno,
                "func": frame.name,
                "code": (frame.line or "").strip(),
                "in_app": in_app,
            }
        )
    return frames


def _request_fields():
    try:
        from flask import has_request_context, request
    except ImportError:
        return {}
    if not has_request_context():
        return {}
    forwarded = request.headers.get("X-Forwarded-For", "")
    fields = {
        "kind": "request",
        "method": request.method,
        "host": request.host,
        "path": request.path,
        "query": request.query_string.decode("utf-8", "replace"),
        "status": 500,
        "ua": request.headers.get("User-Agent", ""),
        "ip": forwarded.split(",")[0].strip() or request.remote_addr,
        "request_id": request.headers.get("X-Request-ID"),
    }
    if _state["user"]:
        try:
            fields["user"] = _state["user"]()
        except Exception:
            fields["user"] = None
    return fields


def report(exc, kind="task", **extra):
    record = {
        "gauge": 1,
        "ts": datetime.now(timezone.utc).isoformat(),
        "version": _state["version"],
        "kind": kind,
        "exc_type": type(exc).__qualname__,
        "message": str(exc),
        "frames": _frames(exc.__traceback__),
        "traceback": "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        ),
    }
    record.update(_request_fields())
    record.update(extra)
    sys.stderr.write(json.dumps(record, default=str) + "\n")
    sys.stderr.flush()


def _thread_hook(args):
    if args.exc_type is SystemExit:
        return
    report(
        args.exc_value, kind="thread", thread=args.thread.name if args.thread else None
    )


def _process_hook(exc_type, exc, tb):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc, tb)
        return
    report(exc, kind="crash")


def register_errors(app=None, codename="app", user=None):
    _state["version"] = _version(codename)
    _state["user"] = user
    threading.excepthook = _thread_hook
    sys.excepthook = _process_hook
    if app is not None:

        def log_exception(exc_info):
            report(exc_info[1], kind="request")

        app.log_exception = log_exception
