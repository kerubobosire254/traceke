"""
core/database.py
-----------------
All data storage for TraceKE.

SQLite  → stores readable data: names, ages, dates, locations, status
ChromaDB → stores face embedding vectors for similarity search

They link via case_id. ChromaDB finds the closest face vectors;
SQLite provides everything else about the case.
"""

import sqlite3
import chromadb
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "traceke.db")
CHROMA_PATH = os.path.join(BASE_DIR, "data", "chroma_store")
PHOTOS_PATH = os.path.join(BASE_DIR, "data", "photos")

# ChromaDB persistent client — saves to disk between sessions
_chroma = chromadb.PersistentClient(path=CHROMA_PATH)

def _get_collection():
    """
    Gets or creates the face collection, automatically handling dimension
    mismatches. If the stored collection expects 128 dimensions (old DeepFace)
    but we now produce 512 (facenet-pytorch), we delete and recreate it.
    This runs once at startup and fixes the collection silently.
    """
    collection = _chroma.get_or_create_collection(
        name="traceke_faces",
        metadata={"hnsw:space": "cosine"}
    )

    # check if existing collection has wrong dimensions by testing with a dummy
    if collection.count() > 0:
        try:
            sample = collection.get(limit=1, include=["embeddings"])
            if sample and sample["embeddings"] is not None and len(sample["embeddings"]) > 0 and len(sample["embeddings"][0]) != 512:
                print(f"TraceKE: dimension mismatch detected "
                      f"({len(sample['embeddings'][0])} vs 512). "
                      f"Resetting collection...")
                _chroma.delete_collection("traceke_faces")

                # also wipe SQLite so IDs stay in sync
                import sqlite3 as _sq
                if os.path.exists(DB_PATH):
                    conn = _sq.connect(DB_PATH)
                    conn.execute("DELETE FROM missing_persons")
                    conn.execute("DELETE FROM found_persons")
                    conn.execute("DELETE FROM match_log")
                    conn.execute("DELETE FROM tips")
                    conn.commit()
                    conn.close()

                collection = _chroma.get_or_create_collection(
                    name="traceke_faces",
                    metadata={"hnsw:space": "cosine"}
                )
                print("TraceKE: collection reset to 512 dimensions. App will reseed.")
        except Exception as e:
            # if anything goes wrong just recreate cleanly
            print(f"TraceKE: collection check failed ({e}), recreating.")
            try:
                _chroma.delete_collection("traceke_faces")
            except Exception:
                pass
            collection = _chroma.get_or_create_collection(
                name="traceke_faces",
                metadata={"hnsw:space": "cosine"}
            )

    return collection

faces = _get_collection()


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Creates all tables if they don't already exist. Safe to call on every startup."""
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS missing_persons (
            id               TEXT PRIMARY KEY,
            name             TEXT NOT NULL,
            age              INTEGER,
            sex              TEXT,
            height_cm        INTEGER,
            last_seen        TEXT,
            clothing         TEXT,
            marks            TEXT,
            date_reported    TEXT,
            reporter_contact TEXT,
            photo_paths      TEXT,
            photo_quality    TEXT,
            status           TEXT DEFAULT 'Open',
            date_created     TEXT,
            notes            TEXT,
            is_demo          INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS found_persons (
            id               TEXT PRIMARY KEY,
            approx_age       INTEGER,
            sex              TEXT,
            location_found   TEXT,
            date_found       TEXT,
            institution      TEXT,
            contact          TEXT,
            photo_path       TEXT,
            photo_quality    TEXT,
            notes            TEXT,
            date_created     TEXT,
            is_demo          INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS match_log (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            missing_id       TEXT,
            found_id         TEXT,
            face_score       REAL,
            age_score        REAL,
            gender_score     REAL,
            final_score      REAL,
            location_flag    TEXT,
            status           TEXT DEFAULT 'Pending',
            reviewer_notes   TEXT,
            timestamp        TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS tips (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            photo_path       TEXT,
            location         TEXT,
            description      TEXT,
            contact          TEXT,
            status           TEXT DEFAULT 'Unreviewed',
            timestamp        TEXT
        )
    """)

    conn.commit()
    conn.close()


def _next_id(prefix: str, table: str) -> str:
    conn = get_conn()
    c = conn.cursor()
    c.execute(f"SELECT COUNT(*) FROM {table}")
    n = c.fetchone()[0] + 1
    conn.close()
    return f"{prefix}-{datetime.now().year}-{str(n).zfill(4)}"


def save_missing_person(data: dict, embedding: list, photo_paths: list, is_demo: bool = False) -> str:
    case_id = _next_id("MP", "missing_persons")

    conn = get_conn()
    conn.cursor().execute("""
        INSERT INTO missing_persons
        (id,name,age,sex,height_cm,last_seen,clothing,marks,date_reported,
         reporter_contact,photo_paths,photo_quality,date_created,notes,is_demo)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        case_id, data.get("name"), data.get("age"), data.get("sex"),
        data.get("height_cm"), data.get("last_seen"), data.get("clothing"),
        data.get("marks"), data.get("date_reported"), data.get("reporter_contact"),
        ",".join(photo_paths), data.get("photo_quality", "high"),
        datetime.now().isoformat(), data.get("notes", ""), int(is_demo)
    ))
    conn.commit()
    conn.close()

    faces.add(
        ids=[case_id],
        embeddings=[embedding],
        metadatas=[{
            "name": data.get("name", ""),
            "age": str(data.get("age", "")),
            "sex": data.get("sex", ""),
            "type": "missing"
        }]
    )
    return case_id


def save_found_person(data: dict, embedding: list, photo_path: str, is_demo: bool = False) -> str:
    found_id = _next_id("FP", "found_persons")

    conn = get_conn()
    conn.cursor().execute("""
        INSERT INTO found_persons
        (id,approx_age,sex,location_found,date_found,institution,
         contact,photo_path,photo_quality,notes,date_created,is_demo)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        found_id, data.get("approx_age"), data.get("sex"),
        data.get("location_found"), data.get("date_found"),
        data.get("institution"), data.get("contact"),
        photo_path, data.get("photo_quality", "high"),
        data.get("notes", ""), datetime.now().isoformat(), int(is_demo)
    ))
    conn.commit()
    conn.close()

    faces.add(
        ids=[found_id],
        embeddings=[embedding],
        metadatas=[{
            "approx_age": str(data.get("approx_age", "")),
            "sex": data.get("sex", ""),
            "location": data.get("location_found", ""),
            "type": "found"
        }]
    )
    return found_id


def search_matches(query_embedding: list, top_k: int = 5) -> list:
    total = faces.count()
    if total == 0:
        return []

    results = faces.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, total),
        include=["metadatas", "distances"]
    )

    matches = []
    for i, case_id in enumerate(results["ids"][0]):
        distance = results["distances"][0][i]
        similarity = round((1 - distance) * 100, 1)
        meta = results["metadatas"][0][i]
        matches.append({
            "case_id": case_id,
            "similarity": similarity,
            "metadata": meta,
            "type": meta.get("type", "unknown")
        })
    return matches


def get_missing_person(case_id: str) -> dict:
    conn = get_conn()
    row = conn.cursor().execute(
        "SELECT * FROM missing_persons WHERE id=?", (case_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_found_person(found_id: str) -> dict:
    conn = get_conn()
    row = conn.cursor().execute(
        "SELECT * FROM found_persons WHERE id=?", (found_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_missing_persons(status: str = None) -> list:
    conn = get_conn()
    if status:
        rows = conn.cursor().execute(
            "SELECT * FROM missing_persons WHERE status=? ORDER BY date_created DESC", (status,)
        ).fetchall()
    else:
        rows = conn.cursor().execute(
            "SELECT * FROM missing_persons ORDER BY date_created DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_case_status(case_id: str, new_status: str):
    conn = get_conn()
    conn.cursor().execute(
        "UPDATE missing_persons SET status=? WHERE id=?", (new_status, case_id)
    )
    conn.commit()
    conn.close()


def log_match(missing_id: str, found_id: str, scores: dict):
    conn = get_conn()
    conn.cursor().execute("""
        INSERT INTO match_log
        (missing_id,found_id,face_score,age_score,gender_score,
         final_score,location_flag,timestamp)
        VALUES (?,?,?,?,?,?,?,?)
    """, (
        missing_id, found_id,
        scores.get("face_score"), scores.get("age_score"),
        scores.get("gender_score"), scores.get("final_score"),
        scores.get("location_context", {}).get("flag", ""),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()


def get_match_log() -> list:
    conn = get_conn()
    rows = conn.cursor().execute(
        "SELECT * FROM match_log ORDER BY timestamp DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_tip(data: dict) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO tips (photo_path,location,description,contact,timestamp)
        VALUES (?,?,?,?,?)
    """, (
        data.get("photo_path"), data.get("location"),
        data.get("description"), data.get("contact", "Anonymous"),
        datetime.now().isoformat()
    ))
    tip_id = cur.lastrowid
    conn.commit()
    conn.close()
    return tip_id


def get_dashboard_stats() -> dict:
    conn = get_conn()
    c = conn.cursor()
    stats = {
        "total": c.execute("SELECT COUNT(*) FROM missing_persons").fetchone()[0],
        "open": c.execute("SELECT COUNT(*) FROM missing_persons WHERE status='Open'").fetchone()[0],
        "resolved": c.execute("SELECT COUNT(*) FROM missing_persons WHERE status='Resolved'").fetchone()[0],
        "matches": c.execute("SELECT COUNT(*) FROM match_log").fetchone()[0],
        "tips": c.execute("SELECT COUNT(*) FROM tips").fetchone()[0],
    }
    conn.close()
    return stats


def is_db_empty() -> bool:
    """Returns True if no cases have been registered yet. Used to trigger demo seeding."""
    conn = get_conn()
    count = conn.cursor().execute("SELECT COUNT(*) FROM missing_persons").fetchone()[0]
    conn.close()
    return count == 0
