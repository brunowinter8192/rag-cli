# INFRASTRUCTURE
import os
import subprocess
import sys
import time

import psycopg2
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv

load_dotenv()

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5433")
POSTGRES_USER = os.getenv("POSTGRES_USER", "rag")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "rag")
POSTGRES_DB = os.getenv("POSTGRES_DB", "rag")
# Docker container hosting Postgres — started automatically if the daemon/container is down.
PG_CONTAINER = os.getenv("RAG_PG_CONTAINER", "rag-postgres")


# AUTOSTART (OrbStack + container) — best-effort, triggered only on connection failure

# Quick probe: is Postgres accepting connections? Short timeout, no side effects.
def _postgres_reachable(timeout: int = 2) -> bool:
    try:
        c = psycopg2.connect(
            host=POSTGRES_HOST, port=POSTGRES_PORT, user=POSTGRES_USER,
            password=POSTGRES_PASSWORD, dbname=POSTGRES_DB, connect_timeout=timeout,
        )
        c.close()
        return True
    except psycopg2.OperationalError:
        return False


# Is the Docker (OrbStack) daemon up and responding?
def _docker_daemon_up() -> bool:
    try:
        return subprocess.run(
            ["docker", "info"], capture_output=True, timeout=5
        ).returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


# Best-effort heal: boot OrbStack daemon if down, start the Postgres container, wait for
# reachability. Returns True if Postgres is reachable afterwards. macOS only (`open -a OrbStack`).
def ensure_postgres_up() -> bool:
    if not _docker_daemon_up():
        print("[rag-cli] Postgres unreachable — booting OrbStack daemon...", file=sys.stderr)
        subprocess.run(["open", "-a", "OrbStack"], capture_output=True)
        deadline = time.time() + 60
        while time.time() < deadline:
            if _docker_daemon_up():
                break
            time.sleep(2)
        else:
            print("[rag-cli] OrbStack daemon did not come up within 60s.", file=sys.stderr)
            return False
    print(f"[rag-cli] starting container {PG_CONTAINER}...", file=sys.stderr)
    subprocess.run(["docker", "start", PG_CONTAINER], capture_output=True)
    deadline = time.time() + 30
    while time.time() < deadline:
        if _postgres_reachable():
            print("[rag-cli] Postgres reachable.", file=sys.stderr)
            return True
        time.sleep(1)
    print(f"[rag-cli] Postgres still unreachable after starting {PG_CONTAINER}.", file=sys.stderr)
    return False


# FUNCTIONS

# Get PostgreSQL connection.
# purpose controls statement_timeout + lock_timeout:
#   "read"  — short-lived queries (SELECT, progress checks)      10s / 5s
#   "write" — batch inserts, deletes                             120s / 10s
#   "ddl"   — schema creation, CREATE INDEX                     300s / 30s
def get_connection(purpose: str = "read", autocommit: bool = False):
    _timeouts = {
        "read":  {"stmt": 10_000,  "lock": 5_000},
        "write": {"stmt": 120_000, "lock": 10_000},
        "ddl":   {"stmt": 300_000, "lock": 30_000},
    }
    t = _timeouts.get(purpose, _timeouts["read"])
    options = f"-c statement_timeout={t['stmt']} -c lock_timeout={t['lock']}"
    params = dict(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        dbname=POSTGRES_DB,
        connect_timeout=5,
        options=options,
    )
    try:
        conn = psycopg2.connect(**params)
    except psycopg2.OperationalError:
        # Postgres down — attempt to boot OrbStack daemon + container, then retry once.
        ensure_postgres_up()
        conn = psycopg2.connect(**params)
    if autocommit:
        conn.autocommit = True
    register_vector(conn)
    return conn


# Validate that collection exists in database
def validate_collection(conn, collection: str):
    existing = [r['collection'] for r in query_collections(conn)]
    if collection not in existing:
        raise ValueError(f"Collection '{collection}' not found. Available: {', '.join(existing)}")


# Add document filter clause (LIKE if value contains %, else exact match).
# Returns new (where_clauses, where_params) lists — does not mutate arguments.
def add_document_filter(where_clauses: list, where_params: list, document: str) -> tuple[list, list]:
    clause = "document LIKE %s" if '%' in document else "document = %s"
    return where_clauses + [clause], where_params + [document]


# Add document exclude clause (NOT LIKE if value contains %, else != for exact match).
# Returns new (where_clauses, where_params) lists — does not mutate arguments.
def add_document_exclude(where_clauses: list, where_params: list, exclude: str) -> tuple[list, list]:
    clause = "document NOT LIKE %s" if '%' in exclude else "document != %s"
    return where_clauses + [clause], where_params + [exclude]


# Query all collections with chunk counts. filter: case-insensitive substring match on name.
def query_collections(conn, filter: str | None = None) -> list[dict]:
    where_clauses = []
    where_params = []
    if filter:
        where_clauses.append("collection ILIKE %s")
        where_params.append(f"%{filter}%")
    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT collection, COUNT(*) as chunk_count
            FROM documents
            {where_sql}
            GROUP BY collection
            ORDER BY collection
        """, where_params)
        rows = cur.fetchall()
    return [{"collection": row[0], "chunks": row[1]} for row in rows]


# Query all documents in a collection with chunk counts
def query_documents(conn, collection: str, document: str | None = None, filter: str | None = None, exclude: str | None = None) -> list[dict]:
    where_clauses = ["collection = %s"]
    where_params = [collection]
    if document:
        where_clauses, where_params = add_document_filter(where_clauses, where_params, document)
    if exclude:
        where_clauses, where_params = add_document_exclude(where_clauses, where_params, exclude)
    if filter:
        where_clauses.append("document ILIKE %s")
        where_params.append(f"%{filter}%")
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT document, COUNT(*) as chunk_count
            FROM documents
            WHERE {' AND '.join(where_clauses)}
            GROUP BY document
            ORDER BY document
        """, where_params)
        rows = cur.fetchall()
    return [{"document": row[0], "chunks": row[1]} for row in rows]


# Query indexing progress per document in a collection.
# Returns rows of {"document", "done", "total"} where:
#   done  = chunks currently in the documents table for this (collection, document)
#   total = expected chunk count (from the per-row total_chunks column)
# A document with done < total is in progress; done == total is fully indexed.
# Documents that haven't started indexing won't appear.
def query_progress(conn, collection: str) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT document,
                   COUNT(*)            AS done,
                   MAX(total_chunks)   AS total
            FROM documents
            WHERE collection = %s
            GROUP BY document
            ORDER BY document
            """,
            (collection,),
        )
        rows = cur.fetchall()
    return [{"document": row[0], "done": row[1], "total": row[2]} for row in rows]


# Fetch chunks for a contiguous range
def fetch_chunk_range(conn, collection: str, document: str, start_idx: int, end_idx: int) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT content, chunk_index
            FROM documents
            WHERE collection = %s AND document = %s
              AND chunk_index BETWEEN %s AND %s
            ORDER BY chunk_index
            """,
            (collection, document, start_idx, end_idx)
        )
        rows = cur.fetchall()
    return [{"content": row[0], "chunk_index": row[1]} for row in rows]
