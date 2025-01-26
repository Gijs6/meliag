from flask import Flask, render_template, jsonify
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



@app.errorhandler(404)
def not_found(e):
    return render_template("404.html", e=e), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html', e=e), 500



if __name__ == '__main__':
    app.run()

