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
    with open("map.pkl", "rb") as file:
        data = pickle.load(file)

    last_updated = data.get("last_updated", 0)
    current_time = time.time()

    if current_time - last_updated > 120:
        threading.Thread(target=api_update_pos).start()

    return jsonify(data.get("data",[]))






def api_update_pos():
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

    for item in data["payload"]["treinen"]:
        url = f"https://gateway.apiportal.ns.nl/virtual-train-api/v1/trein/{item['treinNummer']}?features=drukte"
        headers = {
            "Cache-Control": "no-cache",
            "Ocp-Apim-Subscription-Key": api_key
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return 500

        treindata = response.json()

        data2.append({
            "ritNum": item.get("treinNummer", "N/A"),
            "lat": item.get("lat", "N/A"),
            "lon": item.get("lng", "N/A"),
            "snelheid": item.get("snelheid", "N/A"),
            "treinSoort": item.get("type", "N/A"),
            "materieel": treindata.get("type", "N/A"),
            "vervoerder": treindata.get("vervoerder", "N/A"),
            "station": treindata.get("station", "N/A"),
            "spoor": treindata.get("spoor", "N/A"),
            "materieelNums": [deel.get("materieelnummer", "N/A") for deel in treindata.get("materieeldelen", [])],
            "afbeeldingen": [deel.get("afbeelding", "N/A") for deel in treindata.get("materieeldelen", [])]
        })


    datastuff = {
        "last_updated": time.time(),
        "data": data2
    }


    with open("map.pkl", "wb") as file:
            pickle.dump(datastuff, file)




@app.errorhandler(404)
def not_found(e):
    return render_template("404.html", e=e), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html', e=e), 500



if __name__ == '__main__':
    app.run()

