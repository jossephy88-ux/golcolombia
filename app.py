from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

API_KEY = "3cf5da64049c4c2d8e3d7bb7305b8c a1"
API_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": API_KEY.replace(" ", "")}

# ID de la Liga BetPlay Colombia
LIGA_ID = 2021

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/partidos")
def partidos():
    try:
        res = requests.get(f"{API_URL}/competitions/{LIGA_ID}/matches?status=SCHEDULED,LIVE,FINISHED", headers=HEADERS)
        data = res.json()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tabla")
def tabla():
    try:
        res = requests.get(f"{API_URL}/competitions/{LIGA_ID}/standings", headers=HEADERS)
        data = res.json()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/goleadores")
def goleadores():
    try:
        res = requests.get(f"{API_URL}/competitions/{LIGA_ID}/scorers", headers=HEADERS)
        data = res.json()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("GolColombia iniciado en http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
