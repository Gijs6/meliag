from dotenv import load_dotenv

load_dotenv()

from flask import Flask

from routes.main import bp as main_bp
from routes.stations import bp as stations_bp
from routes.trips import bp as trips_bp
from utils.cache import init_db
from utils.filters import register_filters
from utils.ns_api import get_all_stations

app = Flask(__name__)

register_filters(app)
init_db()

app.register_blueprint(main_bp)
app.register_blueprint(stations_bp)
app.register_blueprint(trips_bp)


if __name__ == "__main__":
    print("\n---\nMeliag\n---\n")

    print("Initializing stations...")
    get_all_stations()

    print("Server starting...")
    app.run(debug=True)
