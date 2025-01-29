from flask import Flask, render_template, jsonify
from datetime import datetime
import pickle
import time
import threading
import requests


app = Flask(__name__)



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
            if (time.time() - dataDezeTrein["laatstBijgewerkt"]) > 300:
                ritnummersDataVernieuwen.append(item["treinNummer"])
        except KeyError:
            ritnummersDataVernieuwen.append(item["treinNummer"])


    thread = threading.Thread(target=dataVernieuwenVanRitnummers, args=(ritnummersDataVernieuwen,))
    thread.start()


    return jsonify(data2)




def dataVernieuwenVanRitnummers(ritnummerlijst):
    with open("ritnummers.pkl", "rb") as file:
        oudeData = pickle.load(file)

    itemsVerwijderen = []

    for ritnummer, itemdata in oudeData.items():
        if (time.time() - itemdata.get("laatstBijgewerkt", 0)) > 600 or itemdata.get("ritnummer", "N/A") in ritnummerlijst:
            itemsVerwijderen.append(itemdata.get("ritnummer", "N/A"))

    for item in itemsVerwijderen:
        if item in oudeData:
            del oudeData[str(item)]

    for ritnummer in ritnummerlijst:
        try:
            url = f"https://gateway.apiportal.ns.nl/virtual-train-api/v1/trein/{ritnummer}?features=drukte"

            headers = {
                "Cache-Control": "no-cache",
                "Ocp-Apim-Subscription-Key": api_key
            }

            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                return 500

            treindata = response.json()

            oudeData[str(ritnummer)] = ({
                "ritnummer": ritnummer,
                "laatstBijgewerkt": time.time(),
                "materieel": treindata.get("type", "N/A"),
                "vervoerder": treindata.get("vervoerder", "N/A"),
                "station": treindata.get("station", "N/A"),
                "spoor": treindata.get("spoor", "N/A"),
                "materieelNums": [deel.get("materieelnummer", "N/A") for deel in treindata.get("materieeldelen", [])],
                "afbeeldingen": [deel.get("afbeelding", "N/A") for deel in treindata.get("materieeldelen", [])]
            })

        except Exception as e:
           print(f"Errort {e}")

    with open("ritnummers.pkl", "wb") as file:
        pickle.dump(oudeData, file)





@app.route("/meliag/api/ritnummers")
def api_ritnums():
    with open("ritnummers.pkl", "rb") as file:
        return jsonify(pickle.load(file))






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

    alleRitnums = set(aankomstDataDict.keys()).union(vertrekDataDict.keys())

    volledigeData = []

    for ritnummer in alleRitnums:
        url = f"https://gateway.apiportal.ns.nl/virtual-train-api/v1/trein/{ritnummer}"

        headers = {
            "Cache-Control": "no-cache",
            "Ocp-Apim-Subscription-Key": api_key
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return 500

        treindata = response.json()




        aankomstDataItem = aankomstDataDict.get(ritnummer, {})
        vertrekDataItem = vertrekDataDict.get(ritnummer, {})


        geplande_aankomst = aankomstDataItem.get("plannedDateTime")
        echte_aankomst = aankomstDataItem.get("actualDateTime")
        geplande_vertrek = vertrekDataItem.get("plannedDateTime")
        echte_vertrek = vertrekDataItem.get("actualDateTime")

        geplande_aankomst_tijd = datetime.strptime(geplande_aankomst, "%Y-%m-%dT%H:%M:%S%z").strftime("%H:%M") if geplande_aankomst else "-"
        echte_aankomst_tijd = datetime.strptime(echte_aankomst, "%Y-%m-%dT%H:%M:%S%z").strftime("%H:%M") if echte_aankomst else "-"
        geplande_vertrek_tijd = datetime.strptime(geplande_vertrek, "%Y-%m-%dT%H:%M:%S%z").strftime("%H:%M") if geplande_vertrek else "-"
        echte_vertrek_tijd = datetime.strptime(echte_vertrek, "%Y-%m-%dT%H:%M:%S%z").strftime("%H:%M") if echte_vertrek else "-"



        try:
            if echte_aankomst and geplande_aankomst:
                vertraging_aankomst = round((datetime.strptime(echte_aankomst, "%Y-%m-%dT%H:%M:%S%z") - datetime.strptime(geplande_aankomst, "%Y-%m-%dT%H:%M:%S%z")).total_seconds() / 60)
            else:
                vertraging_aankomst = None
        except Exception as e:
            vertraging_aankomst = None


        try:
            if echte_vertrek and geplande_vertrek:
                vertraging_vertrek = round((datetime.strptime(echte_vertrek, "%Y-%m-%dT%H:%M:%S%z") - datetime.strptime(geplande_vertrek, "%Y-%m-%dT%H:%M:%S%z")).total_seconds() / 60)
            else:
                vertraging_vertrek = None
        except Exception as e:
            vertraging_vertrek = None


        materieellijst = []

        faciliteiten_iconen_dict = {
            "WIFI": "fa-solid fa-wifi",
            "TOILET": "fa-solid fa-toilet",
            "STILTE": "fa-solid fa-ear-deaf",
            "STROOM": "fa-solid fa-plug",
            "FIETS": "fa-solid fa-bicycle",
            "TOEGANKELIJK": "fa-solid fa-wheelchair"
        }



        for item in treindata.get("materieeldelen", []):
            faciliteiten_iconen = []
            for faciliteit in item.get("faciliteiten", []):
                faciliteiten_iconen.append(faciliteiten_iconen_dict.get(faciliteit.upper(),""))
            faciliteiten_iconen = sorted(faciliteiten_iconen)
            materieellijst.append({
                "matnum": item.get("materieelnummer", ""),
                "afb_url": item.get("afbeelding", ""),
                "mat": item.get("type", ""),
                "faciliteiten": item.get("faciliteiten", []),
                "faciliteiten_iconen": faciliteiten_iconen
            })




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

            "vervallen": vertrekDataItem.get("cancelled", False),
            "berichten": vertrekDataItem.get("messages", []),



            "materieel": treindata.get("type", "N/A"),
            "station": treindata.get("station", "N/A"),
            "spoor": treindata.get("spoor", "N/A"),
            "materieelNums": [deel.get("materieelnummer", "N/A") for deel in treindata.get("materieeldelen", [])],
            "afbeeldingen": [deel.get("afbeelding", "N/A") for deel in treindata.get("materieeldelen", [])],

            "matlijst": materieellijst,



        })


    volledigeData = sorted(volledigeData, key=lambda x: datetime.strptime(x["sort"], "%Y-%m-%dT%H:%M:%S%z"))


    return render_template("meliag/meliag_treintijden.html", data=volledigeData)














@app.errorhandler(404)
def not_found(e):
    return render_template("404.html", e=e), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html', e=e), 500



if __name__ == '__main__':
    app.run()

