from flask import Flask, render_template, request

from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import string
import requests
import os
import json
import atexit
import signal
import sys


load_dotenv()
NS_API_KEY = os.getenv("NS_API_KEY")
OWM_API_KEY = os.getenv("OWM_API_KEY")


app = Flask(__name__)

train_stock_cache = {}


DATA_FILE_PATH = os.path.join(app.root_path, "data")
os.makedirs(DATA_FILE_PATH, exist_ok=True)


def load_json(file):
    path = os.path.join(DATA_FILE_PATH, file)

    if os.path.exists(path):
        with open(path) as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return None

    return None


def save_json(file, data):
    path = os.path.join(DATA_FILE_PATH, file)

    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def load_cache():
    global train_stock_cache
    cached_data = load_json("train_stock_cache.json")
    if cached_data:
        train_stock_cache = cached_data
        print(f"Cache loaded: {len(train_stock_cache)} train entries")
    else:
        print("No cache found, starting empty")
        train_stock_cache = {}


def save_cache():
    save_json("train_stock_cache.json", train_stock_cache)
    print(f"Cache saved: {len(train_stock_cache)} entries")


def load_uic_mapping():
    return load_json("uic_mapping.json")


def load_station_data_mapping():
    return load_json("station_data_mapping.json")


def load_station_pictures_mapping():
    return load_json("station_images.json")


def fetch_ns_data(endpoint):
    url = f"https://gateway.apiportal.ns.nl{endpoint}"
    headers = {
        "Cache-Control": "no-cache",
        "Ocp-Apim-Subscription-Key": NS_API_KEY,
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def is_cache_valid(cached_time):
    now = datetime.now()
    cache_date = cached_time.date()
    current_date = now.date()

    if cache_date != current_date:
        return False

    time_diff = now - cached_time
    return time_diff < timedelta(hours=3)


def fetch_train_stock(ritnummer):
    cache_key = str(ritnummer)

    if cache_key in train_stock_cache:
        cache = train_stock_cache[cache_key]
        cached_time = datetime.fromisoformat(cache["time"])
        cached_data = cache["data"]
        if is_cache_valid(cached_time):
            return cached_data

    data = fetch_ns_data(f"/virtual-train-api/v1/trein/{ritnummer}")

    train_stock_cache[cache_key] = {"time": datetime.now().isoformat(), "data": data}

    return data


def get_all_stations():
    data = fetch_ns_data(
        "/nsapp-stations/v3?includeNonPlannableStations=false&countryCodes=nl"
    )
    payload = data.get("payload", [])

    save_json("stations.json", data)

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

    save_json("uic_mapping.json", uic_mapping)

    save_json("station_data_mapping.json", station_data_mapping)


@app.template_filter("normalize_name")
def normalize_name(name):
    return "".join(c for c in name.lower() if c.isalpha())


@app.template_filter("format_name")
def format_name(name):
    return "".join(
        c for c in name if c.isalpha() or c == " " or c in string.punctuation
    ).strip()


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


@app.template_filter("parse_datetime")
def parse_datetime(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        return None


@app.template_filter("truncate_seconds")
def truncate_seconds(dt):
    if dt is None:
        return None
    return dt.replace(second=0, microsecond=0)


@app.template_filter("calculate_delay_minutes")
def calculate_delay_minutes(actual_time, planned_time):
    if not actual_time or not planned_time:
        return 0
    actual_dt = parse_datetime(actual_time)
    planned_dt = parse_datetime(planned_time)
    if not actual_dt or not planned_dt:
        return 0
    actual_truncated = truncate_seconds(actual_dt)
    planned_truncated = truncate_seconds(planned_dt)
    if not actual_truncated or not planned_truncated:
        return 0
    return round((actual_truncated - planned_truncated).total_seconds() / 60)


@app.route("/")
def index():
    station_data = load_station_data_mapping()

    stats = {"total_stations": len(station_data)}

    return render_template("index.html", stats=stats)


@app.route("/station-search")
def station_search():
    stations = list(load_station_data_mapping().values())
    stations = sorted(
        stations, key=lambda s: s.get("names", {}).get("long", "").lower()
    )
    return render_template("station_search.html", stations=stations)


@app.route("/api/train-stock/<train_number>")
def train_stock_api(train_number):
    try:
        stock_data = fetch_train_stock(train_number)
        if stock_data and stock_data.get("materieeldelen"):
            parts_count = len(stock_data.get("materieeldelen", []))
            print(f"Train {train_number}: {parts_count} parts")
            html = render_template("train_stock.html", stock=stock_data)
            return {"success": True, "html": html}
        else:
            print(f"Train {train_number}: no composition data")
            return {
                "success": False,
                "html": '<div class="train-stock-error">Train composition not available</div>',
            }
    except requests.exceptions.RequestException as e:
        print(f"Train {train_number}: fetch failed - {str(e)}")
        return {
            "success": False,
            "html": '<div class="train-stock-error">Failed to load train composition</div>',
        }


@app.route("/station-times/<station_code>")
def station_times(station_code):
    debug = request.args.get("debug") == "true"

    station_data = load_station_data_mapping().get(station_code)

    station_name = (
        station_data.get("names", {}).get("long", station_code)
        if station_data
        else station_code
    )

    lat = station_data["location"]["lat"]
    lon = station_data["location"]["lng"]

    weather_resp = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OWM_API_KEY}&lang=en&units=metric"
    )
    weather_resp.raise_for_status()
    weather_data = weather_resp.json()

    if debug:
        trains = load_json("data/testdata.json")
        print(f"Debug mode: {station_name}")
    else:
        arrivals = (
            fetch_ns_data(
                f"/reisinformatie-api/api/v2/arrivals?uicCode={station_code}&lang=en"
            )
            .get("payload", {})
            .get("arrivals", [])
        )
        departures = (
            fetch_ns_data(
                f"/reisinformatie-api/api/v2/departures?uicCode={station_code}&lang=en"
            )
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
                return datetime.max.replace(tzinfo=timezone.utc)

        trains = dict(sorted(trains.items(), key=lambda item: actual_time(item[1])))
        print(f"{station_name}: {len(arrivals)} arrivals, {len(departures)} departures")

    return render_template(
        "station_times.html",
        trains=trains,
        station_name_to_uic=load_uic_mapping(),
        station_data=station_data,
        station_picture=load_station_pictures_mapping().get(station_code),
        weather_data=weather_data,
    )


def signal_handler(_sig, _frame):
    print("Shutting down...")
    save_cache()
    print("Shutdown complete")
    sys.exit(0)


if __name__ == "__main__":
    print("\n---\nMeliag\n---\n")

    print("Initializing stations...")
    get_all_stations()

    print("Loading cache...")
    load_cache()

    signal.signal(signal.SIGINT, signal_handler)
    atexit.register(save_cache)

    print("Server starting...")

    app.run(debug=True)
