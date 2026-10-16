#!/usr/bin/env python3
"""Seed default analyst user into the PostgreSQL database."""

import os
import sys
from pathlib import Path
import psycopg
from backend.app.config import settings
from backend.app.security.passwords import hash_password


def seed_evaluation_user(db_url: str | None = None) -> None:
    target_url = db_url or settings.DATABASE_URL
    username = settings.EVAL_USERNAME
    pw_hash = settings.EVAL_PASSWORD_HASH

    # If the hash in settings looks like a plaintext password, hash it
    if not pw_hash.startswith("$2"):
        pw_hash = hash_password(pw_hash)

    print(f"[SeedUser] Seeding user '{username}' into database...")
    try:
        with psycopg.connect(target_url, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (username, password_hash, role)
                    VALUES (%s, %s, 'admin')
                    ON CONFLICT (username) DO UPDATE SET
                        password_hash = EXCLUDED.password_hash,
                        role = EXCLUDED.role;
                """, (username, pw_hash))
        print(f"[SeedUser] ✓ Successfully seeded user '{username}' (role: admin).")
    except psycopg.OperationalError as op_err:
        print(f"[SeedUser] Database connection error: {op_err}", file=sys.stderr)
        if settings.DATA_MODE == "mock":
            print("[SeedUser] (Ignored in mock mode - database is not required)", file=sys.stderr)
        else:
            sys.exit(1)


if __name__ == "__main__":
    seed_evaluation_user()
