from flask import Flask, render_template, jsonify
from datetime import datetime, timedelta
import requests

app = Flask(__name__)

API_KEY = "3cf5da64049c4c2d8e3d7bb7305b8ca1"
API_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": API_KEY}

LIGAS = {
    "premier":    {"id": 2021, "nombre": "Premier League",  "pais": "Inglaterra"},
    "laliga":     {"id": 2014, "nombre": "La Liga",          "pais": "España"},
    "seriea":     {"id": 2019, "nombre": "Serie A",          "pais": "Italia"},
    "bundesliga": {"id": 2002, "nombre": "Bundesliga",       "pais": "Alemania"},
    "champions":  {"id": 2001, "nombre": "Champions League", "pais": "Europa"},
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/ligas")
def ligas():
    return jsonify(LIGAS)

@app.route("/api/partidos/<liga>")
def partidos(liga):
    try:
        liga_id = LIGAS.get(liga, LIGAS["premier"])["id"]
        hoy = datetime.now().strftime("%Y-%m-%d")
        hace7 = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        en7 = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        res = requests.get(
            f"{API_URL}/competitions/{liga_id}/matches?dateFrom={hace7}&dateTo={en7}",
            headers=HEADERS
        )
        return jsonify(res.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tabla/<liga>")
def tabla(liga):
    try:
        liga_id = LIGAS.get(liga, LIGAS["premier"])["id"]
        res = requests.get(
            f"{API_URL}/competitions/{liga_id}/standings",
            headers=HEADERS
        )
        return jsonify(res.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/goleadores/<liga>")
def goleadores(liga):
    try:
        liga_id = LIGAS.get(liga, LIGAS["premier"])["id"]
        res = requests.get(
            f"{API_URL}/competitions/{liga_id}/scorers",
            headers=HEADERS
        )
        return jsonify(res.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("GolColombia iniciado en http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
