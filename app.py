from flask import Flask, render_template, jsonify, request

app = Flask(__name__)


@app.route("/")
def hello():
    return render_template("main/home.html")


@app.route("/admin")
def adminHome():
    return render_template("dashboard/HomeDash.html")


@app.route("/kelolaproduk")
def kelolaProduk():
    return render_template("dashboard/kelolaProduk.html")


if __name__ == "__main__":
    app.run("0.0.0.0", port=8000, debug=True)
