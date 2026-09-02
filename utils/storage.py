import json
import os

from utils.paths import DATA_DIR


def load_json(filename):
    path = os.path.join(DATA_DIR, filename)

    if not os.path.exists(path):
        return None

    with open(path) as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return None


def save_json(filename, data):
    path = os.path.join(DATA_DIR, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def load_uic_mapping():
    return load_json("uic_mapping.json") or {}


def load_station_data_mapping():
    return load_json("station_data_mapping.json") or {}


def load_station_pictures_mapping():
    return load_json("station_images.json") or {}
