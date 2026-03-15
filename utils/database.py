import sqlite3
import os

DB_PATH = "data/vega.db"

def get_connection():
    """Create and return a database connection."""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db():
    """Initialize all database tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link TEXT UNIQUE NOT NULL,
            title TEXT,
            source TEXT,
            region TEXT,
            level TEXT,
            category TEXT,
            location TEXT,
            actors TEXT,
            summary TEXT,
            image TEXT,
            published_date TEXT,
            detected_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sitreps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT,
            content TEXT,
            sources_used INTEGER,
            requested_by TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT,
            level TEXT,
            category TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("[VEGA] Database initialized.")

def article_exists(link: str) -> bool:
    """Check if an article has already been processed."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM articles WHERE link = ?", (link,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def save_article(data: dict):
    """Save a processed article to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO articles
            (link, title, source, region, level, category, location, actors, summary, image, published_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("link", ""),
            data.get("titulo", "") or data.get("title", ""),
            data.get("fuente", "") or data.get("source", ""),
            data.get("region", "Global"),
            data.get("level", "") or data.get("nivel", "MEDIUM"),
            data.get("category", "") or data.get("categoria", "Other"),
            data.get("precise_location", "") or data.get("ubicacion_precisa", ""),
            ", ".join(data.get("key_actors", []) or data.get("actores_principales", [])),
            data.get("resumen", "") or data.get("summary", ""),
            data.get("imagen", "") or data.get("image", ""),
            data.get("fecha", "") or data.get("date", "")
        ))
        conn.commit()
    except Exception as e:
        print(f"[VEGA] Error saving article: {e}")
    finally:
        conn.close()

def get_recent_articles(limit: int = 20, region: str = None, level: str = None):
    """Retrieve recent articles with optional filters."""
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM articles"
    params = []
    conditions = []

    if region:
        conditions.append("region = ?")
        params.append(region)
    if level:
        conditions.append("level = ?")
        params.append(level)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY detected_at DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_all_links() -> set:
    """Get all processed article links."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT link FROM articles")
    links = {row[0] for row in cursor.fetchall()}
    conn.close()
    return links

def save_event(type: str, description: str):
    """Log a system event to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO events (type, description) VALUES (?, ?)",
        (type, description)
    )
    conn.commit()
    conn.close()

def save_sitrep(topic: str, content: str, sources: int, author: str):
    """Save a generated SITREP to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sitreps (topic, content, sources_used, requested_by) VALUES (?, ?, ?, ?)",
        (topic, content, sources, author)
    )
    conn.commit()
    conn.close()

def get_stats():
    """Get system-wide statistics."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM articles")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT region, COUNT(*) as cnt FROM articles GROUP BY region ORDER BY cnt DESC")
    by_region = cursor.fetchall()

    cursor.execute("SELECT level, COUNT(*) as cnt FROM articles GROUP BY level ORDER BY cnt DESC")
    by_level = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) as total FROM sitreps")
    total_sitreps = cursor.fetchone()[0]

    conn.close()
    return {
        "total_articles": total,
        "by_region": [dict(r) for r in by_region],
        "by_level": [dict(r) for r in by_level],
        "total_sitreps": total_sitreps
    }