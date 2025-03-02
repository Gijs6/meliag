from flask import Flask, render_template, jsonify
from datetime import datetime, timedelta
import pickle
import time
import requests
import json

app = Flask(__name__)


@app.route("/meliag")
def meliag_home():
    return render_template("meliag/meliag_home.html")


@app.route("/meliag/kaart")
def meliag_map():
    return render_template("meliag/meliag_kaart.html")


@app.route("/meliag/colofon")
def meliag_colophon():
    return render_template("meliag/meliag_colofon.html")


@app.route("/meliag/api/pos")
def api_position():
    url = "https://gateway.apiportal.ns.nl/virtual-train-api/vehicle?lat=0&lng=0"
    headers = {
        "Cache-Control": "no-cache",
        "Ocp-Apim-Subscription-Key": api_key
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return 500

    data = response.json()
    processed_data = []

    for item in data["payload"]["treinen"]:
        processed_data.append({
            "ritNum": item.get("treinNummer", "N/A"),
            "lat": item.get("lat", "N/A"),
            "lon": item.get("lng", "N/A"),
            "snelheid": item.get("snelheid", "N/A"),
            "treinSoort": item.get("type", "N/A"),
        })

    return jsonify(processed_data)


def refresh_all_train_numbers():
    # This function is ran (externally) every hour
    url = "https://gateway.apiportal.ns.nl/virtual-train-api/vehicle?lat=0&lng=0"
    headers = {
        "Cache-Control": "no-cache",
        "Ocp-Apim-Subscription-Key": api_key
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return 500

    data = response.json()
    train_numbers = [item.get("treinNummer", "0000") for item in data["payload"]["treinen"]]
    update_train_data(train_numbers)


def update_train_data(train_numbers):
    with open("ritnummers.pkl", "rb") as file:
        data = pickle.load(file)

    facility_icons = {
        "WIFI": "fa-solid fa-wifi",
        "TOILET": "fa-solid fa-toilet",
        "STILTE": "fa-solid fa-ear-deaf",
        "STROOM": "fa-solid fa-plug",
        "FIETS": "fa-solid fa-bicycle",
        "TOEGANKELIJK": "fa-solid fa-wheelchair"
    }

    material_replacements = {
        "ELOC TR25": "TRAXX",
        "SW7-25KV_2+7": "ICR",
        "ELOC VECT": "VECTRON",
        "Flirt 3 FFF": "Flirt 3",
        "Flirt 4 FFF": "Flirt 4"
    }

    for train_number in train_numbers:
        url = f"https://gateway.apiportal.ns.nl/virtual-train-api/v1/trein/{train_number}?features=drukte"
        headers = {
            "Cache-Control": "no-cache",
            "Ocp-Apim-Subscription-Key": api_key
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return 500

        train_data = response.json()
        material_list = []

        for item in train_data.get("materieeldelen", []):
            icons = sorted([facility_icons.get(facility.upper(), "") for facility in item.get("faciliteiten", [])])
            material_list.append({
                "matnum": item.get("materieelnummer", ""),
                "afb_url": item.get("afbeelding", ""),
                "mat": material_replacements.get(item.get("type", ""), item.get("type", "")),
                "faciliteiten": item.get("faciliteiten", []),
                "faciliteiten_iconen": icons
            })

        data[str(train_number)] = {
            "dataRetrieved": time.time(),
            "materieel": train_data.get("type", "N/A"),
            "station": train_data.get("station", "N/A"),
            "spoor": train_data.get("spoor", "N/A"),
            "materieelNums": [deel.get("materieelnummer", "N/A") for deel in train_data.get("materieeldelen", [])],
            "afbeeldingen": [deel.get("afbeelding", "N/A") for deel in train_data.get("materieeldelen", [])],
            "matlijst": material_list,
        }

    with open("ritnummers.pkl", "wb") as file:
        pickle.dump(data, file)

    return data


def clean_train_number_data():
    with open("ritnummers.pkl", "rb") as file:
        data = pickle.load(file)

    yesterday = datetime.now() - timedelta(days=1)
    timestamp_yesterday = int(datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59).timestamp())

    new_data = {k: v for k, v in data.items() if v.get("dataRetrieved", 0) > timestamp_yesterday}

    with open("ritnummers.pkl", "wb") as file:
        pickle.dump(new_data, file)


@app.route("/meliag/api/ritnummers")
def api_train_numbers():
    with open("ritnummers.pkl", "rb") as file:
        return jsonify(pickle.load(file))


@app.route("/meliag/treintijden")
def meliag_timetable_search():
    with open("stationslijst.pkl", "rb") as file:
        station_list = pickle.load(file)
    return render_template("meliag/meliag_treintijden_zoeken.html", stationslijst=station_list)


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html", e=e), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html', e=e), 500


if __name__ == '__main__':
    app.run()
