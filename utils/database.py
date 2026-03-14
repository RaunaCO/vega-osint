import sqlite3
import os
from datetime import datetime

DB_PATH = "data/vega.db"

def get_connection():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Tabla de artículos vistos (reemplaza vistos.json)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articulos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link TEXT UNIQUE NOT NULL,
            titulo TEXT,
            fuente TEXT,
            region TEXT,
            nivel TEXT,
            categoria TEXT,
            ubicacion TEXT,
            actores TEXT,
            resumen TEXT,
            imagen TEXT,
            fecha_publicacion TEXT,
            fecha_detectado TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabla de eventos/logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT,
            descripcion TEXT,
            fecha TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabla de SITREPs generados
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sitreps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tema TEXT,
            contenido TEXT,
            fuentes_usadas INTEGER,
            solicitado_por TEXT,
            fecha TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabla de estadísticas por región
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS estadisticas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT,
            nivel TEXT,
            categoria TEXT,
            fecha TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("[VEGA] Base de datos inicializada.")

def articulo_existe(link: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM articulos WHERE link = ?", (link,))
    existe = cursor.fetchone() is not None
    conn.close()
    return existe

def guardar_articulo(datos: dict):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO articulos
            (link, titulo, fuente, region, nivel, categoria, ubicacion, actores, resumen, imagen, fecha_publicacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datos.get("link", ""),
            datos.get("titulo", ""),
            datos.get("fuente", ""),
            datos.get("region", "Global"),
            datos.get("nivel", "MEDIO"),
            datos.get("categoria", "Otro"),
            datos.get("ubicacion_precisa", ""),
            ", ".join(datos.get("actores_principales", [])),
            datos.get("resumen", ""),
            datos.get("imagen", ""),
            datos.get("fecha", "")
        ))
        conn.commit()
    except Exception as e:
        print(f"[VEGA] Error guardando artículo: {e}")
    finally:
        conn.close()

def obtener_articulos_recientes(limite: int = 20, region: str = None, nivel: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM articulos"
    params = []
    condiciones = []

    if region:
        condiciones.append("region = ?")
        params.append(region)
    if nivel:
        condiciones.append("nivel = ?")
        params.append(nivel)
    if condiciones:
        query += " WHERE " + " AND ".join(condiciones)

    query += " ORDER BY fecha_detectado DESC LIMIT ?"
    params.append(limite)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def obtener_todos_los_links() -> set:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT link FROM articulos")
    links = {row[0] for row in cursor.fetchall()}
    conn.close()
    return links

def guardar_evento(tipo: str, descripcion: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO eventos (tipo, descripcion) VALUES (?, ?)",
        (tipo, descripcion)
    )
    conn.commit()
    conn.close()

def guardar_sitrep(tema: str, contenido: str, fuentes: int, autor: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sitreps (tema, contenido, fuentes_usadas, solicitado_por) VALUES (?, ?, ?, ?)",
        (tema, contenido, fuentes, autor)
    )
    conn.commit()
    conn.close()

def obtener_estadisticas():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM articulos")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT region, COUNT(*) as cnt FROM articulos GROUP BY region ORDER BY cnt DESC")
    por_region = cursor.fetchall()

    cursor.execute("SELECT nivel, COUNT(*) as cnt FROM articulos GROUP BY nivel ORDER BY cnt DESC")
    por_nivel = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) as total FROM sitreps")
    total_sitreps = cursor.fetchone()[0]

    conn.close()
    return {
        "total_articulos": total,
        "por_region": [dict(r) for r in por_region],
        "por_nivel": [dict(r) for r in por_nivel],
        "total_sitreps": total_sitreps
    }