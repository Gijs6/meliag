import requests
from flask import Blueprint, render_template, request

from utils.filters import normalize_name
from utils.ns_api import fetch_arrivals, fetch_departures, fetch_train_stock
from utils.storage import (
    load_json,
    load_station_data_mapping,
    load_station_pictures_mapping,
    load_uic_mapping,
)
from utils.trains import merge_arrivals_departures, merged_messages

bp = Blueprint("stations", __name__)


def station_matches(station, query):
    if not query:
        return True

    needle = normalize_name(query)
    name = normalize_name(station.get("names", {}).get("long", ""))
    if needle in name:
        return True

    return query in str(station.get("id", {}).get("uicCode", ""))


@bp.route("/station-search")
def station_search():
    query = request.args.get("q", "").strip()

    stations = sorted(
        load_station_data_mapping().values(),
        key=lambda s: s.get("names", {}).get("long", "").lower(),
    )
    stations = [s for s in stations if station_matches(s, query)]

    is_htmx = request.headers.get("HX-Request") == "true"
    template = "search_results.jinja" if is_htmx else "search.jinja"
    return render_template(template, stations=stations, query=query)


@bp.route("/api/train-stock/<train_number>")
def train_stock_api(train_number):
    try:
        stock_data = fetch_train_stock(train_number)
    except requests.exceptions.RequestException as e:
        print(f"Train {train_number}: fetch failed - {e}")
        return render_template(
            "train_stock.jinja", stock=None, error="Couldn't load composition"
        )

    if not stock_data or not stock_data.get("materieeldelen"):
        return render_template(
            "train_stock.jinja", stock=None, error="No composition available"
        )

    return render_template("train_stock.jinja", stock=stock_data, error=None)


@bp.route("/station-page/<station_code>")
def station_page(station_code):
    debug = request.args.get("debug") == "true"

    station_data = load_station_data_mapping().get(station_code)
    station_name = (
        station_data.get("names", {}).get("long", station_code)
        if station_data
        else station_code
    )

    if debug:
        trains = load_json("testdata.json") or {}
        print(f"Debug mode: {station_name}")
    else:
        trains = merge_arrivals_departures(
            fetch_arrivals(station_code), fetch_departures(station_code)
        )

    for train in trains.values():
        train["messages"] = merged_messages(train)

    return render_template(
        "station_page.jinja",
        trains=trains,
        station_name=station_name,
        station_name_to_uic=load_uic_mapping(),
        station_data=station_data,
        station_picture=load_station_pictures_mapping().get(station_code),
    )
