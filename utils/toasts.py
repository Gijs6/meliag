import json

from flask import Response, redirect, request, session

TOAST_TYPES = {"success": "success", "warning": "warning", "error": "danger"}


def htmx_redirect(location):
    if request.headers.get("HX-Request") and not request.headers.get("HX-Boosted"):
        return Response(status=204, headers={"HX-Redirect": location})
    return redirect(location)


def toast_type(category):
    return TOAST_TYPES.get(category, "info")


def add_trigger(response, name, detail):
    current = response.headers.get("HX-Trigger")
    triggers = {}
    if current:
        try:
            triggers = json.loads(current)
        except ValueError:
            triggers = {event.strip(): None for event in current.split(",")}
    triggers[name] = detail
    response.headers["HX-Trigger"] = json.dumps(triggers)


def register_toasts(app):
    app.jinja_env.globals["toast_type"] = toast_type

    @app.after_request
    def flashes_to_toasts(response):
        if (
            not request.headers.get("HX-Request")
            or request.headers.get("HX-Boosted")
            or response.status_code in (204, 301, 302, 303, 307, 308)
            or "HX-Redirect" in response.headers
            or "HX-Refresh" in response.headers
            or "HX-Location" in response.headers
            or not session.get("_flashes")
        ):
            return response
        messages = [
            {
                "type": toast_type(category),
                "text": message["text"] if isinstance(message, dict) else message,
            }
            for category, message in session.pop("_flashes")
        ]
        add_trigger(response, "toast", {"messages": messages})
        return response
