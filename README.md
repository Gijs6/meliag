# Meliag

A simple Flask app that shows real-time Dutch train information using the NS API.

Shows arrival and departure times, delays, platform changes, and route information for any Dutch train station.

I am really proud of this project, because the code is just very very clean.

## Installation and usage

You'll need an NS API key first. Get one from the [NS API portal](https://apiportal.ns.nl/) and put it in a `.env` file:

```
NS_API_KEY=your_api_key_here
```

Then just:

```bash
pip install -r requirements.txt
python app.py
```

Visit any station by going to `/station/{station_code}`. Note that the station codes **not** the 3-letter codes NS uses, like `asd` for Amsterdam Centraal or `ut` for Utrecht Centraal, but the **UIC**-codes of the stations.

That's about it. Simple train times, no fancy stuff :D
