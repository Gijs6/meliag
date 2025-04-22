from flask import Flask, render_template, jsonify
from datetime import datetime, timedelta
import pickle
import time
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("api_key")

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
    # This function is ran (externally) every day
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


with open('afkoNaarVolledig.json', 'r', encoding='utf-8') as file:
    abbreviationToFull = json.load(file)


@app.route("/meliag/treintijden/<station>")
def meliag_train_times(station):
    url = f"https://gateway.apiportal.ns.nl/reisinformatie-api/api/v2/arrivals?station={station}"

    headers = {
        "Cache-Control": "no-cache",
        "Ocp-Apim-Subscription-Key": api_key
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return 500

    arrivalData = response.json()

    url = f"https://gateway.apiportal.ns.nl/reisinformatie-api/api/v2/departures?station={station}"

    headers = {
        "Cache-Control": "no-cache",
        "Ocp-Apim-Subscription-Key": api_key
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return 500

    departureData = response.json()

    arrivalDataDict = {item.get("product", {})["number"]: item for item in arrivalData["payload"]["arrivals"]}
    departureDataDict = {item.get("product", {})["number"]: item for item in departureData["payload"]["departures"]}

    allTripNumbersInArrivalAndDeparture = set(arrivalDataDict.keys()).union(departureDataDict.keys())

    tripNumbersToFetch = []

    with open("ritnummers.pkl", "rb") as file:
        tripNumberData = pickle.load(file)

    tripNumbersInData = tripNumberData.keys()

    for tripNumber in allTripNumbersInArrivalAndDeparture:
        if tripNumber not in tripNumbersInData:
            tripNumbersToFetch.append(tripNumber)

    if tripNumbersToFetch:
        tripNumberData = update_train_data(tripNumbersToFetch)

    fullData = []

    for tripNumber in allTripNumbersInArrivalAndDeparture:
        arrivalItem = arrivalDataDict.get(tripNumber, {})
        departureItem = departureDataDict.get(tripNumber, {})

        plannedArrival = arrivalItem.get("plannedDateTime")
        actualArrival = arrivalItem.get("actualDateTime")
        plannedDeparture = departureItem.get("plannedDateTime")
        actualDeparture = departureItem.get("actualDateTime")

        plannedArrivalTime = datetime.strptime(plannedArrival, "%Y-%m-%dT%H:%M:%S%z").strftime("%H:%M") if plannedArrival else "-"
        actualArrivalTime = datetime.strptime(actualArrival, "%Y-%m-%dT%H:%M:%S%z").strftime("%H:%M") if actualArrival else "-"
        plannedDepartureTime = datetime.strptime(plannedDeparture, "%Y-%m-%dT%H:%M:%S%z").strftime("%H:%M") if plannedDeparture else "-"
        actualDepartureTime = datetime.strptime(actualDeparture, "%Y-%m-%dT%H:%M:%S%z").strftime("%H:%M") if actualDeparture else "-"

        try:
            if actualArrival and plannedArrival:
                delayArrival = round((datetime.strptime(actualArrival, "%Y-%m-%dT%H:%M:%S%z") - datetime.strptime(plannedArrival, "%Y-%m-%dT%H:%M:%S%z")).total_seconds() / 60)
            else:
                delayArrival = None
        except:
            delayArrival = None

        try:
            if actualDeparture and plannedDeparture:
                delayDeparture = round((datetime.strptime(actualDeparture, "%Y-%m-%dT%H:%M:%S%z") - datetime.strptime(plannedDeparture, "%Y-%m-%dT%H:%M:%S%z")).total_seconds() / 60)
            else:
                delayDeparture = None
        except:
            delayDeparture = None

        messagesDict = {}

        for msg in departureItem.get("messages", []) + arrivalItem.get("messages", []):
            text, style = msg["message"], msg["style"]

            if text in messagesDict:
                if style == "WARNING" or messagesDict[text] != "WARNING":
                    messagesDict[text] = "WARNING"
            else:
                messagesDict[text] = style

        messages = [{"message": msg, "style": style} for msg, style in messagesDict.items()]

        fullData.append({
            "ritnummer": tripNumber,
            "stationVan": arrivalItem.get("origin", ""),
            "stationNaar": departureItem.get("direction", ""),

            "geplandeAankomstTijd": plannedArrivalTime,
            "echteAankomstTijd": actualArrivalTime,
            "geplandeVertrekTijd": plannedDepartureTime,
            "echteVertrekTijd": actualDepartureTime,
            "vertragingAankomst": delayArrival,
            "vertragingVertrek": delayDeparture,

            "sort": departureItem.get("actualDateTime", arrivalItem.get("actualDateTime", "")),

            "geplandAankomstSpoor": arrivalItem.get("plannedTrack", ""),
            "echtAankomstSpoor": arrivalItem.get("actualTrack", ""),
            "geplandVertrekSpoor": departureItem.get("plannedTrack", ""),
            "echtVertrekSpoor": departureItem.get("actualTrack", ""),

            "afkoCat": departureItem.get("product", {}).get("categoryCode",arrivalItem.get("product", {}).get("categoryCode", "")),
            "kleineCat": departureItem.get("product", {}).get("longCategoryName", arrivalItem.get("product", {}).get("longCategoryName", "")),
            "groteCat": departureItem.get("product", {}).get("shortCategoryName",arrivalItem.get("product", {}).get("shortCategoryName", "")),
            "operator": departureItem.get("product", {}).get("operatorName",arrivalItem.get("product", {}).get("operatorName", "")),
            "stationsOnRoute": [station["mediumName"] for station in departureItem.get("routeStations", [])],

            "aankomstStatus": arrivalItem.get("arrivalStatus", ""),
            "vertrekStatus": departureItem.get("departureStatus", ""),

            "vervallen": (departureItem.get("cancelled", False) or arrivalItem.get("cancelled", False)),
            "berichten": messages,

            "matData": tripNumberData.get(str(tripNumber), {})
        })

    fullData = sorted(fullData, key=lambda x: datetime.strptime(x["sort"], "%Y-%m-%dT%H:%M:%S%z"))

    fullStationName = abbreviationToFull.get(station.capitalize(), "NIET BESCHIKBAAR")

    return render_template("meliag/meliag_treintijden.html", data=fullData, volledigestationsnaam=fullStationName)


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html", e=e), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html', e=e), 500


if __name__ == '__main__':
    app.run(port=9000)
