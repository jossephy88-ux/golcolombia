from flask import Flask, render_template, jsonify, request, session, redirect
from datetime import datetime, timedelta
import requests
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "golcolombia2026"

# football-data.org API (ligas europeas)
FD_KEY = "3cf5da64049c4c2d8e3d7bb7305b8ca1"
FD_URL = "https://api.football-data.org/v4"
FD_HEADERS = {"X-Auth-Token": FD_KEY}

LIGAS_EU = {
    "premier":    {"id": 2021, "nombre": "Premier League"},
    "laliga":     {"id": 2014, "nombre": "La Liga"},
    "seriea":     {"id": 2019, "nombre": "Serie A"},
    "bundesliga": {"id": 2002, "nombre": "Bundesliga"},
    "champions":  {"id": 2001, "nombre": "Champions League"},
}

DB = "golcolombia.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS partidos_col (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT, hora TEXT,
            local TEXT, visita TEXT,
            goles_local INTEGER DEFAULT 0,
            goles_visita INTEGER DEFAULT 0,
            estado TEXT DEFAULT 'programado',
            jornada INTEGER DEFAULT 1,
            creado TEXT
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS tabla_col (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pos INTEGER, equipo TEXT, pj INTEGER,
            gan INTEGER, emp INTEGER, per INTEGER,
            gf INTEGER, gc INTEGER, pts INTEGER
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT, password TEXT
        )""")
        db.execute("INSERT OR IGNORE INTO admin (usuario, password) VALUES ('admin', 'gol2026')")

        # Tabla inicial Liga BetPlay 2026
        equipos = [
            (1,"Atletico Nacional",5,4,1,0,10,3,13),
            (2,"America de Cali",5,3,1,1,8,5,10),
            (3,"Millonarios",5,3,0,2,7,6,9),
            (4,"Junior",5,2,2,1,6,4,8),
            (5,"Deportivo Cali",5,2,2,1,5,5,8),
            (6,"Santa Fe",5,2,1,2,5,6,7),
            (7,"Once Caldas",5,2,1,2,4,5,7),
            (8,"Deportes Tolima",5,1,3,1,4,4,6),
            (9,"Envigado",5,1,2,2,3,5,5),
            (10,"Peñarol",5,1,1,3,3,7,4),
        ]
        for e in equipos:
            existing = db.execute("SELECT id FROM tabla_col WHERE equipo=?", (e[1],)).fetchone()
            if not existing:
                db.execute("INSERT INTO tabla_col (pos,equipo,pj,gan,emp,per,gf,gc,pts) VALUES (?,?,?,?,?,?,?,?,?)", e)

        # Partidos iniciales
        partidos_ini = [
            ("2026-04-20","15:30","Atletico Nacional","America de Cali",None,None,"programado",18),
            ("2026-04-20","17:45","Junior","Millonarios",None,None,"programado",18),
            ("2026-04-19","15:30","Santa Fe","Once Caldas",1,0,"finalizado",17),
            ("2026-04-19","17:45","Deportivo Cali","Deportes Tolima",2,1,"finalizado",17),
        ]
        for p in partidos_ini:
            existing = db.execute("SELECT id FROM partidos_col WHERE local=? AND fecha=?", (p[2], p[0])).fetchone()
            if not existing:
                db.execute("INSERT INTO partidos_col (fecha,hora,local,visita,goles_local,goles_visita,estado,jornada,creado) VALUES (?,?,?,?,?,?,?,?,?)",
                    (p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[7],datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

init_db()

# ── RUTAS PUBLICAS ──

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/partidos/colombia")
def partidos_colombia():
    with get_db() as db:
        rows = db.execute("SELECT * FROM partidos_col ORDER BY fecha DESC, hora ASC LIMIT 30").fetchall()
    partidos = []
    for p in rows:
        partidos.append({
            "id": p["id"],
            "utcDate": f"{p['fecha']}T{p['hora']}:00",
            "status": "FINISHED" if p["estado"] == "finalizado" else "LIVE" if p["estado"] == "en vivo" else "SCHEDULED",
            "jornada": p["jornada"],
            "homeTeam": {"name": p["local"], "shortName": p["local"], "crest": ""},
            "awayTeam": {"name": p["visita"], "shortName": p["visita"], "crest": ""},
            "score": {"fullTime": {"home": p["goles_local"], "away": p["goles_visita"]}}
        })
    return jsonify({"matches": partidos})

@app.route("/api/tabla/colombia")
def tabla_colombia():
    with get_db() as db:
        rows = db.execute("SELECT * FROM tabla_col ORDER BY pts DESC, gf DESC").fetchall()
    tabla = []
    for i, e in enumerate(rows):
        tabla.append({
            "position": i + 1,
            "team": {"name": e["equipo"], "shortName": e["equipo"], "crest": ""},
            "playedGames": e["pj"],
            "won": e["gan"],
            "draw": e["emp"],
            "lost": e["per"],
            "goalsFor": e["gf"],
            "goalDifference": e["gf"] - e["gc"],
            "points": e["pts"]
        })
    return jsonify({"standings": [{"table": tabla}]})

@app.route("/api/goleadores/colombia")
def goleadores_colombia():
    return jsonify({"scorers": []})

@app.route("/api/partidos/<liga>")
def partidos_eu(liga):
    try:
        liga_id = LIGAS_EU.get(liga, LIGAS_EU["premier"])["id"]
        hace7 = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        en7 = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        res = requests.get(f"{FD_URL}/competitions/{liga_id}/matches?dateFrom={hace7}&dateTo={en7}", headers=FD_HEADERS)
        return jsonify(res.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tabla/<liga>")
def tabla_eu(liga):
    try:
        liga_id = LIGAS_EU.get(liga, LIGAS_EU["premier"])["id"]
        res = requests.get(f"{FD_URL}/competitions/{liga_id}/standings", headers=FD_HEADERS)
        return jsonify(res.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/goleadores/<liga>")
def goleadores_eu(liga):
    try:
        liga_id = LIGAS_EU.get(liga, LIGAS_EU["premier"])["id"]
        res = requests.get(f"{FD_URL}/competitions/{liga_id}/scorers", headers=FD_HEADERS)
        return jsonify(res.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/prediccion", methods=["POST"])
def prediccion():
    try:
        data = request.json
        local = data.get("local","Local")
        visita = data.get("visita","Visita")
        pos_local = int(data.get("posLocal",10))
        pos_visita = int(data.get("posVisita",10))
        pj_local = int(data.get("pjLocal",1)) or 1
        pj_visita = int(data.get("pjVisita",1)) or 1
        gan_local = int(data.get("ganLocal",0))
        gan_visita = int(data.get("ganVisita",0))
        pts_local = int(data.get("ptsLocal",0))
        pts_visita = int(data.get("ptsVisita",0))
        gf_local = int(data.get("gfLocal",0))
        gf_visita = int(data.get("gfVisita",0))

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

        return jsonify({"ok":True,"resultado":resultado,"emoji":emoji,"pct_local":pct_local,"pct_empate":pct_empate,"pct_visita":pct_visita,"marcador":f"{marc_local}-{marc_visita}","razon":f"{local} (pos.{pos_local}) vs {visita} (pos.{pos_visita}). Ventaja local considerada."})
    except Exception as e:
        return jsonify({"ok":False,"error":str(e)}), 500

# ── ADMIN COLOMBIA ──

@app.route("/admin/colombia", methods=["GET","POST"])
def admin_colombia():
    if request.method == "POST" and "usuario" in request.form:
        usuario = request.form.get("usuario","")
        password = request.form.get("password","")
        with get_db() as db:
            user = db.execute("SELECT * FROM admin WHERE usuario=? AND password=?", (usuario, password)).fetchone()
        if user:
            session["admin"] = usuario
        else:
            return render_template("admin_colombia.html", error="Usuario o contrasena incorrecta", logueado=False, partidos=[], tabla=[])

    if "admin" not in session:
        return render_template("admin_colombia.html", error=None, logueado=False, partidos=[], tabla=[])

    with get_db() as db:
        partidos = db.execute("SELECT * FROM partidos_col ORDER BY fecha DESC, hora ASC").fetchall()
        tabla = db.execute("SELECT * FROM tabla_col ORDER BY pts DESC").fetchall()
    return render_template("admin_colombia.html", error=None, logueado=True, partidos=partidos, tabla=tabla)

@app.route("/admin/colombia/partido", methods=["POST"])
def agregar_partido():
    if "admin" not in session: return jsonify({"ok":False}), 401
    data = request.json
    with get_db() as db:
        db.execute("INSERT INTO partidos_col (fecha,hora,local,visita,goles_local,goles_visita,estado,jornada,creado) VALUES (?,?,?,?,?,?,?,?,?)",
            (data["fecha"],data["hora"],data["local"],data["visita"],
             data.get("goles_local"),data.get("goles_visita"),
             data.get("estado","programado"),data.get("jornada",1),
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    return jsonify({"ok":True})

@app.route("/admin/colombia/partido/<int:pid>", methods=["PUT"])
def actualizar_partido(pid):
    if "admin" not in session: return jsonify({"ok":False}), 401
    data = request.json
    with get_db() as db:
        db.execute("UPDATE partidos_col SET goles_local=?, goles_visita=?, estado=? WHERE id=?",
            (data.get("goles_local"), data.get("goles_visita"), data.get("estado"), pid))
    return jsonify({"ok":True})

@app.route("/admin/colombia/tabla/<int:tid>", methods=["PUT"])
def actualizar_tabla(tid):
    if "admin" not in session: return jsonify({"ok":False}), 401
    data = request.json
    with get_db() as db:
        db.execute("UPDATE tabla_col SET pj=?,gan=?,emp=?,per=?,gf=?,gc=?,pts=? WHERE id=?",
            (data["pj"],data["gan"],data["emp"],data["per"],data["gf"],data["gc"],data["pts"],tid))
    return jsonify({"ok":True})

@app.route("/admin/colombia/logout")
def admin_logout():
    session.clear()
    return redirect("/admin/colombia")

if __name__ == "__main__":
    print("GolColombia iniciado en http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
