import requests
from flask import Blueprint, render_template

from utils.ns_api import fetch_journey

bp = Blueprint("trips", __name__)


@bp.route("/trip/<train_number>")
def trip_detail(train_number):
    try:
        journey = fetch_journey(train_number)
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            return (
                render_template(
                    "trip.jinja",
                    train_number=train_number,
                    stops=None,
                    notes=None,
                    error="No journey for this train today.",
                ),
                404,
            )
        return (
            render_template(
                "trip.jinja",
                train_number=train_number,
                stops=None,
                notes=None,
                error="Couldn't load this journey.",
            ),
            502,
        )
    except requests.exceptions.RequestException:
        return (
            render_template(
                "trip.jinja",
                train_number=train_number,
                stops=None,
                notes=None,
                error="Couldn't load this journey.",
            ),
            502,
        )

    payload = journey.get("payload") or {}
    stops = payload.get("stops") or []

    if not stops:
        return (
            render_template(
                "trip.jinja",
                train_number=train_number,
                stops=None,
                notes=None,
                error="No journey for this train today.",
            ),
            404,
        )

    return render_template(
        "trip.jinja",
        train_number=train_number,
        stops=stops,
        notes=payload.get("notes") or [],
        error=None,
    )
