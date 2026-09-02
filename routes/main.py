from flask import Blueprint, render_template

from utils.storage import load_station_data_mapping

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    stats = {"total_stations": len(load_station_data_mapping())}
    return render_template("index.jinja", stats=stats)
