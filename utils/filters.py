import string
from datetime import datetime


def normalize_name(name):
    return "".join(c for c in name.lower() if c.isalpha())


def format_name(name):
    return "".join(
        c for c in name if c.isalpha() or c == " " or c in string.punctuation
    ).strip()


def format_datetime(value, fmt="%Y-%m-%d %H:%M:%S"):
    if not value:
        return ""
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z").strftime(fmt)
    except ValueError:
        return value


def isoformat(value, fmt="%Y-%m-%dT%H:%M:%S%z"):
    if not value:
        return None
    return datetime.strptime(value, fmt).isoformat()


def parse_datetime(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        return None


def truncate_seconds(dt):
    if dt is None:
        return None
    return dt.replace(second=0, microsecond=0)


def calculate_delay_minutes(actual_time, planned_time):
    if not actual_time or not planned_time:
        return 0
    actual_dt = truncate_seconds(parse_datetime(actual_time))
    planned_dt = truncate_seconds(parse_datetime(planned_time))
    if not actual_dt or not planned_dt:
        return 0
    return round((actual_dt - planned_dt).total_seconds() / 60)


FILTERS = {
    "normalize_name": normalize_name,
    "format_name": format_name,
    "format_datetime": format_datetime,
    "isoformat": isoformat,
    "parse_datetime": parse_datetime,
    "truncate_seconds": truncate_seconds,
    "calculate_delay_minutes": calculate_delay_minutes,
}


def register_filters(app):
    for name, fn in FILTERS.items():
        app.template_filter(name)(fn)
