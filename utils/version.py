import os

VERSION_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "VERSION")


def register_version(app, codename):
    build = "dev"
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE) as f:
            build = f.read().strip()

    @app.context_processor
    def inject_version():
        return {"APP_VERSION": f"{codename}-{'dev' if app.debug else build}"}
