from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import requests

app = Flask(__name__)

# football-data.org API (ligas europeas)
FD_KEY = "3cf5da64049c4c2d8e3d7bb7305b8ca1"
FD_URL = "https://api.football-data.org/v4"
FD_HEADERS = {"X-Auth-Token": FD_KEY}

# RapidAPI (Liga Colombiana)
RAPID_KEY = "961f2c1250msh5870e4b2c146baep17b1b8jsnde8883f392fd"
RAPID_HOST = "free-api-live-football-data.p.rapidapi.com"
RAPID_HEADERS = {
    "x-rapidapi-key": RAPID_KEY,
    "x-rapidapi-host": RAPID_HOST
}

LIGAS_EU = {
    "premier":    {"id": 2021, "nombre": "Premier League",  "pais": "Inglaterra"},
    "laliga":     {"id": 2014, "nombre": "La Liga",          "pais": "Espana"},
    "seriea":     {"id": 2019, "nombre": "Serie A",          "pais": "Italia"},
    "bundesliga": {"id": 2002, "nombre": "Bundesliga",       "pais": "Alemania"},
    "champions":  {"id": 2001, "nombre": "Champions League", "pais": "Europa"},
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/partidos/<liga>")
def partidos(liga):
    try:
        if liga == "colombia":
            res = requests.get(
                "https://free-api-live-football-data.p.rapidapi.com/football-get-matches-by-league",
                headers=RAPID_HEADERS,
                params={"leagueId": "323"}
            )
            data = res.json()
            partidos_fmt = []
            if data.get("response") and data["response"].get("matches"):
                for m in data["response"]["matches"][:30]:
                    partidos_fmt.append({
                        "id": m.get("id", 0),
                        "utcDate": m.get("date", ""),
                        "status": m.get("status", "SCHEDULED"),
                        "homeTeam": {"name": m.get("homeTeam", {}).get("name", ""), "shortName": m.get("homeTeam", {}).get("shortName", ""), "crest": m.get("homeTeam", {}).get("logo", "")},
                        "awayTeam": {"name": m.get("awayTeam", {}).get("name", ""), "shortName": m.get("awayTeam", {}).get("shortName", ""), "crest": m.get("awayTeam", {}).get("logo", "")},
                        "score": {"fullTime": {"home": m.get("homeScore"), "away": m.get("awayScore")}}
                    })
            return jsonify({"matches": partidos_fmt})
        else:
            liga_id = LIGAS_EU.get(liga, LIGAS_EU["premier"])["id"]
            hace7 = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            en7 = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            res = requests.get(
                f"{FD_URL}/competitions/{liga_id}/matches?dateFrom={hace7}&dateTo={en7}",
                headers=FD_HEADERS
            )
            return jsonify(res.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tabla/<liga>")
def tabla(liga):
    try:
        if liga == "colombia":
            res = requests.get(
                "https://free-api-live-football-data.p.rapidapi.com/football-get-standing-all",
                headers=RAPID_HEADERS,
                params={"leagueId": "323"}
            )
            data = res.json()
            tabla_fmt = []
            if data.get("response") and data["response"].get("standings"):
                for i, e in enumerate(data["response"]["standings"]):
                    tabla_fmt.append({
                        "position": i + 1,
                        "team": {"name": e.get("team", {}).get("name", ""), "shortName": e.get("team", {}).get("shortName", ""), "crest": e.get("team", {}).get("logo", "")},
                        "playedGames": e.get("played", 0),
                        "won": e.get("won", 0),
                        "draw": e.get("draw", 0),
                        "lost": e.get("lost", 0),
                        "goalDifference": e.get("goalDifference", 0),
                        "points": e.get("points", 0)
                    })
            return jsonify({"standings": [{"table": tabla_fmt}]})
        else:
            liga_id = LIGAS_EU.get(liga, LIGAS_EU["premier"])["id"]
            res = requests.get(f"{FD_URL}/competitions/{liga_id}/standings", headers=FD_HEADERS)
            return jsonify(res.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/goleadores/<liga>")
def goleadores(liga):
    try:
        if liga == "colombia":
            res = requests.get(
                "https://free-api-live-football-data.p.rapidapi.com/football-get-top-scorers",
                headers=RAPID_HEADERS,
                params={"leagueId": "323"}
            )
            data = res.json()
            goles_fmt = []
            if data.get("response") and data["response"].get("scorers"):
                for g in data["response"]["scorers"][:15]:
                    goles_fmt.append({
                        "player": {"name": g.get("player", {}).get("name", "")},
                        "team": {"name": g.get("team", {}).get("name", "")},
                        "goals": g.get("goals", 0)
                    })
            return jsonify({"scorers": goles_fmt})
        else:
            liga_id = LIGAS_EU.get(liga, LIGAS_EU["premier"])["id"]
            res = requests.get(f"{FD_URL}/competitions/{liga_id}/scorers", headers=FD_HEADERS)
            return jsonify(res.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/prediccion", methods=["POST"])
def prediccion():
    try:
        data = request.json
        local = data.get("local", "Equipo Local")
        visita = data.get("visita", "Equipo Visita")
        pos_local = int(data.get("posLocal", 10))
        pos_visita = int(data.get("posVisita", 10))
        pj_local = int(data.get("pjLocal", 1)) or 1
        pj_visita = int(data.get("pjVisita", 1)) or 1
        gan_local = int(data.get("ganLocal", 0))
        gan_visita = int(data.get("ganVisita", 0))
        pts_local = int(data.get("ptsLocal", 0))
        pts_visita = int(data.get("ptsVisita", 0))
        gf_local = int(data.get("gfLocal", 0))
        gf_visita = int(data.get("gfVisita", 0))

        forma_local = (gan_local / pj_local) * 100
        forma_visita = (gan_visita / pj_visita) * 100
        fuerza_local = (forma_local * 0.5 + (20 - pos_local) * 2 + pts_local * 0.3 + gf_local * 0.2) * 1.15
        fuerza_visita = forma_visita * 0.5 + (20 - pos_visita) * 2 + pts_visita * 0.3 + gf_visita * 0.2

        total = fuerza_local + fuerza_visita + 20
        pct_local = round((fuerza_local / total) * 100)
        pct_visita = round((fuerza_visita / total) * 100)
        pct_empate = 100 - pct_local - pct_visita
        if pct_empate < 5:
            pct_empate = 10
            if pct_local > pct_visita: pct_local -= 5
            else: pct_visita -= 5

        gpp_local = round(gf_local / pj_local, 1) if pj_local > 0 else 1.0
        gpp_visita = round(gf_visita / pj_visita, 1) if pj_visita > 0 else 1.0
        marc_local = round(gpp_local * 0.9)
        marc_visita = round(gpp_visita * 0.75)

        if pct_local > pct_visita and pct_local > pct_empate:
            resultado = f"{local} gana"; emoji = "🏆"
        elif pct_visita > pct_local and pct_visita > pct_empate:
            resultado = f"{visita} gana"; emoji = "🏆"
        else:
            resultado = "Empate probable"; emoji = "🤝"

        return jsonify({"ok": True, "resultado": resultado, "emoji": emoji, "pct_local": pct_local, "pct_empate": pct_empate, "pct_visita": pct_visita, "marcador": f"{marc_local}-{marc_visita}", "razon": f"{local} (pos.{pos_local}) vs {visita} (pos.{pos_visita}). Ventaja local considerada."})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    print("GolColombia iniciado en http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
