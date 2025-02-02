from flask import Flask, render_template, jsonify
from datetime import datetime
from threading import Thread, Lock
import pickle
import time
import requests
import json

app = Flask(__name__)


ritnummer_thread = None
ritnummer_lock = Lock()


@app.route("/meliag")
def meliag_home():
    return render_template("meliag/meliag_home.html")


@app.route("/meliag/kaart")
def meliag_kaart():
    return render_template("meliag/meliag_kaart.html")


@app.route("/meliag/colofon")
def meliag_colofon():
    return render_template("meliag/meliag_colofon.html")


@app.route("/meliag/api/pos")
def api_pos():
    url = "https://gateway.apiportal.ns.nl/virtual-train-api/vehicle?lat=0&lng=0"
    headers = {
        "Cache-Control": "no-cache",
        "Ocp-Apim-Subscription-Key": api_key
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return 500

    data = response.json()

    data2 = []

    with open("ritnummers.pkl", "rb") as file:
        ritnummerData = pickle.load(file)

    ritnummersDataVernieuwen = []

    for item in data["payload"]["treinen"]:
        data2.append({
            "ritNum": item.get("treinNummer", "N/A"),
            "lat": item.get("lat", "N/A"),
            "lon": item.get("lng", "N/A"),
            "snelheid": item.get("snelheid", "N/A"),
            "treinSoort": item.get("type", "N/A"),
        })

        try:
            dataDezeTrein = ritnummerData[str(item["treinNummer"])]
            if (time.time() - dataDezeTrein["dataOpgehaald"]) > 300:
                ritnummersDataVernieuwen.append(item["treinNummer"])
        except KeyError:
            ritnummersDataVernieuwen.append(item["treinNummer"])

    global ritnummer_thread
    with ritnummer_lock:
        if ritnummer_thread is None or not ritnummer_thread.is_alive():
            ritnummer_thread = Thread(target=dataVernieuwenVanRitnummers, args=(ritnummersDataVernieuwen,))
            ritnummer_thread.daemon = True
            ritnummer_thread.start()

    return jsonify(data2)

def dataVernieuwenVanRitnummers(ritnummerlijst):
    with open("ritnummers.pkl", "rb") as file:
        data = pickle.load(file)

    faciliteiten_iconen_dict = {
        "WIFI": "fa-solid fa-wifi",
        "TOILET": "fa-solid fa-toilet",
        "STILTE": "fa-solid fa-ear-deaf",
        "STROOM": "fa-solid fa-plug",
        "FIETS": "fa-solid fa-bicycle",
        "TOEGANKELIJK": "fa-solid fa-wheelchair"
    }

    matvervang = {
        "ELOC TR25": "TRAXX",
        "SW7-25KV_2+7": "ICR",
        "ELOC VECT": "VECTRON",
        "Flirt 3 FFF": "Flirt 3",
        "Flirt 4 FFF": "Flirt 4"
    }

    for ritnummer in ritnummerlijst:
        url = f"https://gateway.apiportal.ns.nl/virtual-train-api/v1/trein/{ritnummer}?features=drukte"

        headers = {
            "Cache-Control": "no-cache",
            "Ocp-Apim-Subscription-Key": api_key
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return 500

        treindata = response.json()

        materieellijst = []

        for item in treindata.get("materieeldelen", []):
            faciliteiten_iconen = []
            for faciliteit in item.get("faciliteiten", []):
                faciliteiten_iconen.append(faciliteiten_iconen_dict.get(faciliteit.upper(), ""))
            faciliteiten_iconen = sorted(faciliteiten_iconen)
            materieellijst.append({
                "matnum": item.get("materieelnummer", ""),
                "afb_url": item.get("afbeelding", ""),
                "mat": matvervang.get(item.get("type", ""), item.get("type", "")),
                "faciliteiten": item.get("faciliteiten", []),
                "faciliteiten_iconen": faciliteiten_iconen
            })

        data[str(ritnummer)] = ({
            "dataOpgehaald": time.time(),
            "materieel": treindata.get("type", "N/A"),
            "station": treindata.get("station", "N/A"),
            "spoor": treindata.get("spoor", "N/A"),
            "materieelNums": [deel.get("materieelnummer", "N/A") for deel in treindata.get("materieeldelen", [])],
            "afbeeldingen": [deel.get("afbeelding", "N/A") for deel in treindata.get("materieeldelen", [])],
            "matlijst": materieellijst,
        })

    with open("ritnummers.pkl", "wb") as file:
        pickle.dump(data, file)


@app.route("/meliag/api/ritnummers")
def api_ritnums():
    with open("ritnummers.pkl", "rb") as file:
        return jsonify(pickle.load(file))


@app.route("/meliag/treintijden")
def meliag_treintijden_zoeken():
    with open("stationslijst.pkl", "rb") as bestand:
        data = pickle.load(bestand)

    return render_template("meliag/meliag_treintijden_zoeken.html", stationslijst=data)


with open('stations.json', 'r', encoding='utf-8') as file:
    afkoNaarVolledig = json.load(file)


@app.route("/meliag/treintijden/<station>")
def meliag_treintijden(station):
    url = f"https://gateway.apiportal.ns.nl/reisinformatie-api/api/v2/arrivals?station={station}"

    headers = {
        "Cache-Control": "no-cache",
        "Ocp-Apim-Subscription-Key": api_key
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return 500

    aankomstData = response.json()

    url = f"https://gateway.apiportal.ns.nl/reisinformatie-api/api/v2/departures?station={station}"

    headers = {
        "Cache-Control": "no-cache",
        "Ocp-Apim-Subscription-Key": api_key
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return 500

    vertrekData = response.json()

    aankomstDataDict = {item.get("product", {})["number"]: item for item in aankomstData["payload"]["arrivals"]}
    vertrekDataDict = {item.get("product", {})["number"]: item for item in vertrekData["payload"]["departures"]}

    alleRitnumsInVertrekEnAankomst = set(aankomstDataDict.keys()).union(vertrekDataDict.keys())

    alleRitnummersWaaranDeDataMoetWordenBijgewerkt = []

    ritNumDataDIRECTOPHALEN = []

    with open("ritnummers.pkl", "rb") as file:
        ritnumData = pickle.load(file)

    ritNumsInRitnumData = ritnumData.keys()

    for ritnum in alleRitnumsInVertrekEnAankomst:
        if ritnum not in ritNumsInRitnumData:
            ritNumDataDIRECTOPHALEN.append(ritnum)
        elif (ritnumData[ritnum].get("dataOpgehaald", time.time() - 3600) - time.time()) > 600:
            alleRitnummersWaaranDeDataMoetWordenBijgewerkt.append(ritnum)

    if alleRitnummersWaaranDeDataMoetWordenBijgewerkt:
        thread = Thread(target=dataVernieuwenVanRitnummers, args=(alleRitnummersWaaranDeDataMoetWordenBijgewerkt,))
        thread.start()

    if ritNumDataDIRECTOPHALEN:
        dataVernieuwenVanRitnummers(ritNumDataDIRECTOPHALEN)

        with open("ritnummers.pkl", "rb") as file:
            ritnumData = pickle.load(file)

    volledigeData = []

    for ritnummer in alleRitnumsInVertrekEnAankomst:

        aankomstDataItem = aankomstDataDict.get(ritnummer, {})
        vertrekDataItem = vertrekDataDict.get(ritnummer, {})

        geplande_aankomst = aankomstDataItem.get("plannedDateTime")
        echte_aankomst = aankomstDataItem.get("actualDateTime")
        geplande_vertrek = vertrekDataItem.get("plannedDateTime")
        echte_vertrek = vertrekDataItem.get("actualDateTime")

        geplande_aankomst_tijd = datetime.strptime(geplande_aankomst, "%Y-%m-%dT%H:%M:%S%z").strftime(
            "%H:%M") if geplande_aankomst else "-"
        echte_aankomst_tijd = datetime.strptime(echte_aankomst, "%Y-%m-%dT%H:%M:%S%z").strftime(
            "%H:%M") if echte_aankomst else "-"
        geplande_vertrek_tijd = datetime.strptime(geplande_vertrek, "%Y-%m-%dT%H:%M:%S%z").strftime(
            "%H:%M") if geplande_vertrek else "-"
        echte_vertrek_tijd = datetime.strptime(echte_vertrek, "%Y-%m-%dT%H:%M:%S%z").strftime(
            "%H:%M") if echte_vertrek else "-"

        try:
            if echte_aankomst and geplande_aankomst:
                vertraging_aankomst = round((datetime.strptime(echte_aankomst,
                                                               "%Y-%m-%dT%H:%M:%S%z") - datetime.strptime(
                    geplande_aankomst, "%Y-%m-%dT%H:%M:%S%z")).total_seconds() / 60)
            else:
                vertraging_aankomst = None
        except:
            vertraging_aankomst = None

        try:
            if echte_vertrek and geplande_vertrek:
                vertraging_vertrek = round((datetime.strptime(echte_vertrek, "%Y-%m-%dT%H:%M:%S%z") - datetime.strptime(
                    geplande_vertrek, "%Y-%m-%dT%H:%M:%S%z")).total_seconds() / 60)
            else:
                vertraging_vertrek = None
        except:
            vertraging_vertrek = None

        berichtenDict = {}

        for bericht in vertrekDataItem.get("messages", []) + aankomstDataItem.get("messages", []):
            text, style = bericht["message"], bericht["style"]

            if text in berichtenDict:
                if style == "WARNING" or berichtenDict[text] != "WARNING":
                    berichtenDict[text] = "WARNING"
            else:
                berichtenDict[text] = style

        berichten = [{"message": bericht, "style": style} for bericht, style in berichtenDict.items()]

        volledigeData.append({
            "ritnummer": ritnummer,
            "stationVan": aankomstDataItem.get("origin", ""),
            "stationNaar": vertrekDataItem.get("direction", ""),

            "geplandeAankomstTijd": geplande_aankomst_tijd,
            "echteAankomstTijd": echte_aankomst_tijd,
            "geplandeVertrekTijd": geplande_vertrek_tijd,
            "echteVertrekTijd": echte_vertrek_tijd,
            "vertragingAankomst": vertraging_aankomst,
            "vertragingVertrek": vertraging_vertrek,

            "sort": vertrekDataItem.get("actualDateTime", aankomstDataItem.get("actualDateTime", "")),

            "geplandAankomstSpoor": aankomstDataItem.get("plannedTrack", ""),
            "echtAankomstSpoor": aankomstDataItem.get("actualTrack", ""),
            "geplandVertrekSpoor": vertrekDataItem.get("plannedTrack", ""),
            "echtVertrekSpoor": vertrekDataItem.get("actualTrack", ""),

            "afkoCat": vertrekDataItem.get("product", {}).get("categoryCode", aankomstDataItem.get("product", {}).get("categoryCode", "")),
            "kleineCat": vertrekDataItem.get("product", {}).get("longCategoryName", aankomstDataItem.get("product", {}).get("longCategoryName", "")),
            "groteCat": vertrekDataItem.get("product", {}).get("shortCategoryName", aankomstDataItem.get("product", {}).get("shortCategoryName", "")),
            "operator": vertrekDataItem.get("product", {}).get("operatorName", aankomstDataItem.get("product", {}).get("operatorName", "")),

            "stationsOpDeRoute": [station["mediumName"] for station in vertrekDataItem.get("routeStations", [])],

            "aankomstStatus": aankomstDataItem.get("arrivalStatus", ""),
            "vertrekStatus": vertrekDataItem.get("departureStatus", ""),

            "vervallen": (vertrekDataItem.get("cancelled", False) or aankomstDataItem.get("cancelled", False)),
            "berichten": berichten,

            "matData": ritnumData.get(str(ritnummer), {})

        })

    volledigeData = sorted(volledigeData, key=lambda x: datetime.strptime(x["sort"], "%Y-%m-%dT%H:%M:%S%z"))

    stationvolledig = afkoNaarVolledig.get(station.capitalize(), "NIET BESCHIKBAAR")

    return render_template("meliag/meliag_treintijden.html", data=volledigeData, volledigestationsnaam=stationvolledig)


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html", e=e), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html', e=e), 500


if __name__ == '__main__':
    app.run()
