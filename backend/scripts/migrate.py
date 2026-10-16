#!/usr/bin/env python3
"""Numbered SQL migration runner for PostgreSQL.

Applies pending migrations in alphanumeric order inside transactions.
Tracks applied versions in the `schema_migrations` table.
"""

import os
import sys
from pathlib import Path
import psycopg

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def get_db_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        # Try loading from backend/.env
        env_path = Path(__file__).resolve().parent.parent / ".env"
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.strip().startswith("DATABASE_URL="):
                        url = line.strip().split("=", 1)[1].strip()
                        break
    return url or "postgresql://postgres:postgres@localhost:5432/economic_indicators"


def run_migrations(db_url: str | None = None) -> None:
    target_url = db_url or get_db_url()
    print(f"[Migrate] Connecting to database...")

    try:
        with psycopg.connect(target_url, autocommit=False) as conn:
            with conn.cursor() as cur:
                # Ensure migration tracker exists
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version VARCHAR(64) PRIMARY KEY,
                        applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                """)
                cur.execute("SELECT version FROM schema_migrations;")
                applied = {row[0] for row in cur.fetchall()}

            # Discover and order migration files
            migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
            if not migration_files:
                print(f"[Migrate] No migration files found in {MIGRATIONS_DIR}")
                return

            pending_count = 0
            for sql_file in migration_files:
                version = sql_file.name
                if version in applied:
                    continue

                print(f"[Migrate] Applying {version}...")
                with open(sql_file, "r", encoding="utf-8") as f:
                    sql_content = f.read()

                try:
                    with conn.transaction():
                        with conn.cursor() as cur:
                            cur.execute(sql_content)
                            cur.execute(
                                "INSERT INTO schema_migrations (version) VALUES (%s);",
                                (version,)
                            )
                    print(f"[Migrate] ✓ Applied {version}")
                    pending_count += 1
                except Exception as ex:
                    print(f"[Migrate] ✗ Error applying {version}: {ex}", file=sys.stderr)
                    conn.rollback()
                    raise

            if pending_count == 0:
                print("[Migrate] Database schema is already up to date. Zero pending migrations.")
            else:
                print(f"[Migrate] Successfully applied {pending_count} migrations.")

    except psycopg.OperationalError as op_err:
        print(f"[Migrate] Database connection error: {op_err}", file=sys.stderr)
        print("[Migrate] Tip: Ensure PostgreSQL is running or verify DATABASE_URL in .env", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run_migrations()
