from datetime import datetime, timezone

from utils.filters import parse_datetime

MESSAGE_PRIORITY = {"WARNING": 1, "INFO": 2}


def merge_arrivals_departures(arrivals, departures):
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
        arrival_dt = parse_datetime(train.get("arrival", {}).get("actualDateTime"))
        departure_dt = parse_datetime(train.get("departure", {}).get("actualDateTime"))
        return departure_dt or arrival_dt or datetime.max.replace(tzinfo=timezone.utc)

    return dict(sorted(trains.items(), key=lambda item: actual_time(item[1])))


def merged_messages(train):
    messages = list((train.get("arrival") or {}).get("messages") or []) + list(
        (train.get("departure") or {}).get("messages") or []
    )

    unique = {}
    for message in messages:
        text = message["message"]
        priority = MESSAGE_PRIORITY.get(message["style"], 999)
        if text not in unique or priority < MESSAGE_PRIORITY.get(
            unique[text]["style"], 999
        ):
            unique[text] = message

    result = list(unique.values())

    arrival = train.get("arrival") or {}
    departure = train.get("departure") or {}
    if (
        arrival
        and departure
        and arrival.get("actualTrack") != departure.get("actualTrack")
    ):
        result.append(
            {
                "style": "WARNING",
                "message": "Arrives and departs from different platforms",
            }
        )

    return result
