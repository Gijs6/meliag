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


@app.template_filter("normalize_name")
def normalize_name(name):
    return ''.join(c for c in name.lower() if c.isalpha())

@app.template_filter("format_name")
def format_name(name):
    return ''.join(c for c in name if c.isalpha() or c == ' ').strip()

def get_all_stations():
    url = "https://gateway.apiportal.ns.nl/nsapp-stations/v3?includeNonPlannableStations=false"
    headers = {
        "Cache-Control": "no-cache",
        "Ocp-Apim-Subscription-Key": API_KEY,
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    payload = data.get("payload", [])

    save_path = os.path.join(app.root_path, "data")
    os.makedirs(save_path, exist_ok=True)

    with open(os.path.join(save_path, "stations.json"), "w") as f:
        json.dump(data, f, indent=4)

    uic_mapping = {}
    station_data_mapping = {}

    for station in payload:
        uic = station.get("id", {}).get("uicCode")
        if not uic:
            continue

        names = station.get("names", {})
        for key in ("long", "medium", "short"):
            name = names.get(key)
            if name:
                uic_mapping[normalize_name(name)] = uic

        for syn in names.get("synonyms", []):
            uic_mapping[normalize_name(syn)] = uic

        station_data_mapping[uic] = station

    with open(os.path.join(save_path, "uic_mapping.json"), "w") as f:
        json.dump(uic_mapping, f, indent=4)

    with open(os.path.join(save_path, "station_data_mapping.json"), "w") as f:
        json.dump(station_data_mapping, f, indent=4)


def load_json(path):
    with open(os.path.join(app.root_path, path)) as f:
        return json.load(f)


def load_uic_mapping():
    return load_json("data/uic_mapping.json")


def load_station_data_mapping():
    return load_json("data/station_data_mapping.json")


def load_station_pictures_mapping():
    return load_json("station_images.json")


@app.template_filter("format_datetime")
def format_datetime(value, fmt="%Y-%m-%d %H:%M:%S"):
    if not value:
        return ""
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z").strftime(fmt)
    except ValueError:
        return value


@app.template_filter("isoformat")
def isoformat(value, fmt="%Y-%m-%dT%H:%M:%S%z"):
    if not value:
        return None
    return datetime.strptime(value, fmt).isoformat()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/station-times/<station_code>")
def station_times(station_code):
    debug = request.args.get("debug") == "true"

    if debug:
        trains = load_json("data/testdata.json")
    else:
        arrivals = (
            fetch_ns_data("arrivals", station_code)
            .get("payload", {})
            .get("arrivals", [])
        )
        departures = (
            fetch_ns_data("departures", station_code)
            .get("payload", {})
            .get("departures", [])
        )

        trains = {}

        for arrival in arrivals:
            number = arrival["product"]["number"]
            trains.setdefault(number, {"arrival": {}, "departure": {}})
            trains[number]["arrival"] = arrival

        for departure in departures:
            number = departure["product"]["number"]
            trains.setdefault(number, {"arrival": {}, "departure": {}})
            trains[number]["departure"] = departure

        def actual_time(train):
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

        trains = dict(sorted(trains.items(), key=lambda item: actual_time(item[1])))

    return render_template(
        "station_times.html",
        trains=trains,
        station_name_to_uic=load_uic_mapping(),
        station_data=load_station_data_mapping().get(station_code),
        station_picture=load_station_pictures_mapping().get(station_code),
    )


@app.route("/station-search")
def station_search():
    stations = list(load_station_data_mapping().values())
    stations = sorted(stations, key=lambda s: s.get("names", {}).get("long", "").lower())
    return render_template("station_search.html", stations=stations)


if __name__ == "__main__":
    get_all_stations()
    print("Saved stations and UIC mapping.")
    app.run(debug=True)
