# INFRASTRUCTURE
import os
import subprocess
import sys
import time

import psycopg2
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv

load_dotenv()

POSTGRES_HOST = os.environ["POSTGRES_HOST"]
POSTGRES_PORT = os.environ["POSTGRES_PORT"]
POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
POSTGRES_DB = os.environ["POSTGRES_DB"]
PG_CONTAINER = os.getenv("RAG_PG_CONTAINER", "rag-postgres")


# FUNCTIONS

def probe_postgres(timeout: int = 2) -> str | None:
    try:
        c = psycopg2.connect(
            host=POSTGRES_HOST, port=POSTGRES_PORT, user=POSTGRES_USER,
            password=POSTGRES_PASSWORD, dbname=POSTGRES_DB, connect_timeout=timeout,
        )
        c.close()
        return None
    except psycopg2.OperationalError as exc:
        return str(exc)


def _docker_daemon_up() -> bool:
    try:
        return subprocess.run(
            ["docker", "info"], capture_output=True, timeout=5
        ).returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


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
        if probe_postgres() is None:
            print("[rag-cli] Postgres reachable.", file=sys.stderr)
            return True
        time.sleep(1)
    print(f"[rag-cli] Postgres still unreachable after starting {PG_CONTAINER}.", file=sys.stderr)
    return False


def get_connection(purpose: str = "read", autocommit: bool = False):
    _timeouts = {
        "read":  {"stmt": 10_000,  "lock": 5_000},
        "write": {"stmt": 120_000, "lock": 10_000},
        "ddl":   {"stmt": 300_000, "lock": 30_000},
    }
    t = _timeouts[purpose]
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
    except psycopg2.OperationalError as exc:
        if not ensure_postgres_up():
            raise RuntimeError("Postgres unreachable and could not be started (see messages above)") from exc
        conn = psycopg2.connect(**params)
    if autocommit:
        conn.autocommit = True
    register_vector(conn)
    return conn


def validate_collection(conn, collection: str):
    existing = [r['collection'] for r in query_collections(conn)]
    if collection not in existing:
        raise ValueError(f"Collection '{collection}' not found. Available: {', '.join(existing)}")


def add_document_filter(where_clauses: list, where_params: list, document: str) -> tuple[list, list]:
    clause = "document LIKE %s" if '%' in document else "document = %s"
    return where_clauses + [clause], where_params + [document]


def add_document_exclude(where_clauses: list, where_params: list, exclude: str) -> tuple[list, list]:
    clause = "document NOT LIKE %s" if '%' in exclude else "document != %s"
    return where_clauses + [clause], where_params + [exclude]


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
