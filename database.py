import sqlite3

DB_PATH = 'data/ocr_results.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS resultados (
            job_id TEXT PRIMARY KEY,
            nombre TEXT,
            codigo_estudiante TEXT,
            carrera TEXT,
            institucion TEXT,
            status TEXT,
            processed_at TEXT,
            raw_text TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_result_to_db(data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO resultados (
            job_id, nombre, codigo_estudiante, carrera, institucion,
            status, processed_at, raw_text
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('job_id'),
        data.get('nombre'),
        data.get('codigo_estudiante'),
        data.get('carrera'),
        data.get('institucion'),
        data.get('status'),
        data.get('processed_at'),
        data.get('raw_text')
    ))
    conn.commit()
    conn.close()
