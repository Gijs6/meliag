import os

import requests

from utils import cache
from utils.filters import normalize_name
from utils.storage import save_json


def fetch_ns_data(endpoint):
    url = f"https://gateway.apiportal.ns.nl{endpoint}"
    headers = {
        "Cache-Control": "no-cache",
        "Ocp-Apim-Subscription-Key": os.getenv("NS_API_KEY"),
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def fetch_train_stock(train_number):
    cached = cache.get_train_stock(train_number)
    if cached is not None:
        return cached

    data = fetch_ns_data(f"/virtual-train-api/v1/trein/{train_number}")
    cache.set_train_stock(train_number, data)
    return data


def fetch_journey(train_number):
    return fetch_ns_data(
        f"/reisinformatie-api/api/v2/journey?train={train_number}&lang=en&omitCrowdForecast=true"
    )


def fetch_arrivals(station_code):
    return (
        fetch_ns_data(
            f"/reisinformatie-api/api/v2/arrivals?uicCode={station_code}&lang=en"
        )
        .get("payload", {})
        .get("arrivals", [])
    )


def fetch_departures(station_code):
    return (
        fetch_ns_data(
            f"/reisinformatie-api/api/v2/departures?uicCode={station_code}&lang=en"
        )
        .get("payload", {})
        .get("departures", [])
    )


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
