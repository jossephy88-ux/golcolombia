from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

API_KEY = "3cf5da64049c4c2d8e3d7bb7305b8c a1"
API_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": API_KEY.replace(" ", "")}

# ID de la Liga BetPlay Colombia
LIGAS = {
    "premier": {"id": 2021, "nombre": "Premier League", "pais": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    "laliga": {"id": 2014, "nombre": "La Liga", "pais": "🇪🇸"},
    "seriea": {"id": 2019, "nombre": "Serie A", "pais": "🇮🇹"},
    "bundesliga": {"id": 2002, "nombre": "Bundesliga", "pais": "🇩🇪"},
    "champions": {"id": 2001, "nombre": "Champions League", "pais": "🇪🇺"},
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/partidos/<liga>")
def partidos(liga):
    try:
        liga_id = LIGAS.get(liga, LIGAS["premier"])["id"]
        res = requests.get(f"{API_URL}/competitions/{liga_id}/matches?status=SCHEDULED,LIVE,FINISHED", headers=HEADERS)
        return jsonify(res.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tabla/<liga>")
def tabla(liga):
    try:
        liga_id = LIGAS.get(liga, LIGAS["premier"])["id"]
        res = requests.get(f"{API_URL}/competitions/{liga_id}/standings", headers=HEADERS)
        return jsonify(res.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/goleadores/<liga>")
def goleadores(liga):
    try:
        liga_id = LIGAS.get(liga, LIGAS["premier"])["id"]
        res = requests.get(f"{API_URL}/competitions/{liga_id}/scorers", headers=HEADERS)
        return jsonify(res.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/ligas")
def ligas():
    return jsonify(LIGAS)