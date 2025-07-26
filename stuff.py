import requests
import json
import os

# Load stations.json
with open(os.path.join("data", "stations.json")) as f:
    stations = json.load(f)["payload"]

def search_commons_image(station_name):
    search_url = "https://commons.wikimedia.org/w/api.php"
    search_params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": f"{station_name} station",
        "srnamespace": 6,
        "srlimit": 1
    }
    r = requests.get(search_url, params=search_params)
    data = r.json()

    if not data.get("query", {}).get("search"):
        return None

    file_title = data["query"]["search"][0]["title"]

    image_params = {
        "action": "query",
        "format": "json",
        "titles": file_title,
        "prop": "imageinfo",
        "iiprop": "url|size",
        "iiurlwidth": 2560
    }

    r = requests.get(search_url, params=image_params)
    image_data = r.json()

    pages = image_data.get("query", {}).get("pages", {})
    for page in pages.values():
        if "imageinfo" in page:
            return page["imageinfo"][0]["url"]

    return None

# Final mapping: uicCode → image URL
uic_to_url = {}

for station in stations:
    uic = station["id"]["uicCode"]
    name = station["names"]["long"]
    url = search_commons_image(name)
    if url:
        print(f"{uic} ({name}): {url}")
        uic_to_url[uic] = url
    else:
        print(f"{uic} ({name}): No image found")

# Save mapping
with open("station_images.json", "w") as f:
    json.dump(uic_to_url, f, indent=2)
