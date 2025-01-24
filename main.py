from flask import Flask, render_template

app = Flask(__name__)



@app.route("/meliag")
def meliag_home():
    return render_template("meliag/meliag_home.html")


@app.route("/meliag/kaart")
def meliag_kaart():
    return render_template("meliag/kaart.html")


@app.route("/meliag/colofon")
def meliag_colofon():
    return render_template("meliag/colofon.html")





@app.errorhandler(404)
def not_found(e):
    return render_template("404.html", e=e), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html', e=e), 500



if __name__ == '__main__':
    app.run()

