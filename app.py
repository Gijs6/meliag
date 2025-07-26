from flask import Flask, render_template, request

from datetime import datetime
from dotenv import load_dotenv
import requests
import os
import json


load_dotenv()

API_KEY = os.getenv("API_KEY")


app = Flask(__name__)


def fetch_ns_data(endpoint, station_code):
    url = f"https://gateway.apiportal.ns.nl/reisinformatie-api/api/v2/{endpoint}?uicCode={station_code}&lang=en"
    headers = {
        "Cache-Control": "no-cache",
        "Ocp-Apim-Subscription-Key": API_KEY,
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()


@app.template_filter("format_datetime")
def format_datetime(value, fmt="%Y-%m-%d %H:%M:%S"):
    if not value:
        return ""
    try:
        dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")
        return dt.strftime(fmt)
    except ValueError:
        return value


@app.template_filter("isoformat")
def isoformat(value, fmt="%Y-%m-%dT%H:%M:%S%z"):
    if not value:
        return None
    return datetime.strptime(value, fmt).isoformat()


@app.route("/")
def index():
    return "Meliag"


@app.route("/station-times/<station_code>")
def station_times(station_code):
    debug = request.args.get("debug") == "true"

    if debug:
        json_path = os.path.join(app.root_path, "data", "testdata.json")
        with open(json_path) as f:
            trains = json.load(f)
    else:
        arrival_data = fetch_ns_data("arrivals", station_code)
        departure_data = fetch_ns_data("departures", station_code)

        trains = {}

        for arrival in arrival_data.get("payload", {}).get("arrivals", []):
            number = arrival["product"]["number"]
            trains.setdefault(number, {"arrival": {}, "departure": {}})
            trains[number]["arrival"] = arrival

        for departure in departure_data.get("payload", {}).get("departures", []):
            number = departure["product"]["number"]
            trains.setdefault(number, {"arrival": {}, "departure": {}})
            trains[number]["departure"] = departure

        def average_actual_time(train):
            fmt = "%Y-%m-%dT%H:%M:%S%z"

            arrival = train.get("arrival", {}).get("actualDateTime")
            departure = train.get("departure", {}).get("actualDateTime")

            arrival_dt = datetime.strptime(arrival, fmt) if arrival else None
            departure_dt = datetime.strptime(departure, fmt) if departure else None

            if departure_dt:
                return departure_dt
            elif arrival_dt:
                return arrival_dt
            else:
                return datetime.max

        trains = dict(
            sorted(trains.items(), key=lambda item: average_actual_time(item[1]))
        )

    station_name_to_uic = load_uic_mapping()

    station_data_mapping = load_station_data_mapping()
    station_data = station_data_mapping.get(station_code)

    station_pictures_mapping = load_station_pictures_mapping()
    station_picture = station_pictures_mapping.get(station_code)

    return render_template(
        "station_times.html",
        trains=trains,
        station_name_to_uic=station_name_to_uic,
        station_data=station_data,
        station_picture=station_picture,
    )


def get_all_stations():
    url = "https://gateway.apiportal.ns.nl/nsapp-stations/v3?includeNonPlannableStations=false"
    headers = {
        "Cache-Control": "no-cache",
        "Ocp-Apim-Subscription-Key": API_KEY,
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = response.json()

    json_path = os.path.join(app.root_path, "data", "stations.json")
    with open(json_path, "w") as f:
        json.dump(data, f, indent=4)

    uic_mapping = {}
    for station in data.get("payload", []):
        names = station.get("names", {})
        uic = station.get("id", {}).get("uicCode")
        if not uic:
            continue
        for key in ("long", "medium", "short"):
            name = names.get(key)
            if name:
                uic_mapping[name.lower()] = uic
        for syn in names.get("synonyms", []):
            uic_mapping[syn.lower()] = uic

    with open(os.path.join(app.root_path, "data", "uic_mapping.json"), "w") as f:
        json.dump(uic_mapping, f, indent=4)

    station_data_mapping = {}
    for station in data.get("payload", []):
        uic = station.get("id", {}).get("uicCode")
        station_data_mapping[uic] = station

    with open(
        os.path.join(app.root_path, "data", "station_data_mapping.json"), "w"
    ) as f:
        json.dump(station_data_mapping, f, indent=4)


def load_uic_mapping():
    with open(os.path.join(app.root_path, "data", "uic_mapping.json")) as f:
        return json.load(f)


def load_station_data_mapping():
    with open(os.path.join(app.root_path, "data", "station_data_mapping.json")) as f:
        return json.load(f)


def load_station_pictures_mapping():
    with open(os.path.join(app.root_path, "station_images.json")) as f:
        return json.load(f)


if __name__ == "__main__":
    get_all_stations()
    print("Saved stations and UIC mapping.")
    app.run(debug=True)
