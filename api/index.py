from flask import Flask, request, jsonify
import sqlite3
import os

DB = "inventario.db"

# Slots fixos
SLOTS_FIXOS = [
    "capacete", "armadura", "botas", "luvas",
    "anel1", "anel2", "colar", "capa"
]
# +30 espaços livres
for i in range(1, 31):
    SLOTS_FIXOS.append(f"slot{i}")

app = Flask(__name__)

def init_db():
    """Cria o banco e inicializa slots vazios."""
    with sqlite3.connect(DB) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS inventario (
                id INTEGER PRIMARY KEY,
                slot TEXT NOT NULL,
                item TEXT
            )
        """)
        # Verifica se já tem dados
        cur.execute("SELECT COUNT(*) FROM inventario")
        count = cur.fetchone()[0]
        if count == 0:
            for slot in SLOTS_FIXOS:
                cur.execute("INSERT INTO inventario (slot, item) VALUES (?, ?)", (slot, None))
        conn.commit()

@app.route("/inventario", methods=["GET"])
def get_inventario():
    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT slot, item FROM inventario")
        rows = cur.fetchall()
        data = {row["slot"]: row["item"] for row in rows}
        return jsonify(data)

@app.route("/add_item", methods=["POST"])
def add_item():
    data = request.json
    item = data.get("item")
    if not item:
        return jsonify({"erro": "Informe o item"}), 400

    with sqlite3.connect(DB) as conn:
        cur = conn.cursor()
        # Procura primeira vaga livre (slot com item NULL)
        cur.execute("SELECT id, slot FROM inventario WHERE item IS NULL ORDER BY id LIMIT 1")
        vaga = cur.fetchone()
        if not vaga:
            return jsonify({"erro": "Inventário cheio"}), 400
        cur.execute("UPDATE inventario SET item=? WHERE id=?", (item, vaga[0]))
        conn.commit()
        return jsonify({"mensagem": f"{item} adicionado no slot {vaga[1]}"})

@app.route("/equip_item", methods=["POST"])
def equip_item():
    data = request.json
    slot = data.get("slot")
    item = data.get("item")
    if not slot or not item:
        return jsonify({"erro": "Informe slot e item"}), 400

    with sqlite3.connect(DB) as conn:
        cur = conn.cursor()
        # Coloca no slot fixo
        cur.execute("UPDATE inventario SET item=? WHERE slot=?", (item, slot))
        conn.commit()
        return jsonify({"mensagem": f"{item} equipado no slot {slot}"})

if __name__ == "__main__":
    if not os.path.exists(DB):
        init_db()
    else:
        # Garante que estrutura existe
        init_db()
    app.run(debug=True)
