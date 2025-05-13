import sqlite3

TAGS_DB_PATH = "tags.db"
DB_PATH = "../DBTestes.db"

def update_tags():
    # Conecta no banco tags.db
    conn_tags = sqlite3.connect(TAGS_DB_PATH)
    cursor_tags = conn_tags.cursor()
    cursor_tags.execute("SELECT tag_epc FROM tags")
    tag_epcs = [row[0] for row in cursor_tags.fetchall()]
    conn_tags.close()

    # Conecta no banco Cronos.db
    conn_cronos = sqlite3.connect(DB_PATH)
    cursor_cronos = conn_cronos.cursor()
    cursor_cronos.execute("SELECT PlacaId FROM Placas")
    placa_ids = [row[0] for row in cursor_cronos.fetchall()]

    # Associa na ordem: tag_epc -> Placas.id
    for tag, placa_id in zip(tag_epcs, placa_ids):
        cursor_cronos.execute("UPDATE Placas SET Tag = ? WHERE PlacaId = ?", (tag, placa_id))

    # Salva e fecha
    conn_cronos.commit()
    conn_cronos.close()

update_tags()