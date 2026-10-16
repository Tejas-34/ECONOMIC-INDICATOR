import csv
import hashlib
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple
from backend.app.config import settings

SEED_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "seed"


def compute_file_sha256(filepath: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


async def load_seed_files_if_changed() -> Dict[str, int]:
    """Inspect curated seed CSV files, compare SHA-256 checksums, and ingest rows on change."""
    if settings.DATA_MODE == "mock":
        return {"loaded": 0, "status": "skipped_mock_mode"}

    from backend.app.db import fetch_all, execute_write, execute_many

    results = {}
    started_at = datetime.now(timezone.utc)
    total_rows = 0

    # Ensure source records exist
    source_records = [
        ("seed-budget", "Union Budget Expenditure Document", "external-curated", "https://www.indiabudget.gov.in", "Curated Central Government Revenue, Capital, and Total Expenditure"),
        ("seed-gst", "data.gov.in (Rajya Sabha)", "external", "https://data.gov.in", "Monthly and annual gross GST revenue collections"),
        ("data-gov-in", "data.gov.in (Rajya Sabha)", "external", "https://data.gov.in", "Gross GST Collection on all Supplies (Domestic + Imports)")
    ]
    for src in source_records:
        await execute_write("""
            INSERT INTO sources (id, name, type, url, notes)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                type = EXCLUDED.type,
                url = EXCLUDED.url;
        """, src)

    # 1. Process Government Expenditure Seed
    govt_file = SEED_DIR / "government_expenditure.csv"
    if govt_file.exists():
        checksum = compute_file_sha256(govt_file)
        existing = await fetch_all(
            "SELECT checksum FROM seed_files WHERE path = %s;",
            (str(govt_file),)
        )
        if not existing or existing[0]["checksum"] != checksum:
            rows_to_insert = []
            with open(govt_file, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    period = row["fiscal_year_label"].strip()
                    basis = row.get("basis", "actual").strip()
                    as_of_dt = date(int(row["fiscal_year_start"]), 3, 31)

                    # Total expenditure
                    rows_to_insert.append((
                        "government-expenditure", "total", period,
                        float(row["total_expenditure"]), "Rs lakh crore", basis, "seed-budget", as_of_dt
                    ))
                    # Capital expenditure
                    rows_to_insert.append((
                        "government-expenditure", "capital", period,
                        float(row["effective_capex"]), "Rs lakh crore", basis, "seed-budget", as_of_dt
                    ))
                    # Revenue expenditure
                    rows_to_insert.append((
                        "government-expenditure", "revenue", period,
                        float(row["revenue_expenditure"]), "Rs lakh crore", basis, "seed-budget", as_of_dt
                    ))

            if rows_to_insert:
                upsert_sql = """
                    INSERT INTO observations (indicator, series, period, value, unit, basis, source_id, as_of)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (indicator, series, period) DO UPDATE SET
                        value = EXCLUDED.value,
                        unit = EXCLUDED.unit,
                        basis = EXCLUDED.basis,
                        source_id = EXCLUDED.source_id,
                        as_of = EXCLUDED.as_of,
                        fetched_at = NOW();
                """
                await execute_many(upsert_sql, rows_to_insert)
                await execute_write("""
                    INSERT INTO seed_files (path, checksum, loaded_at)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (path) DO UPDATE SET
                        checksum = EXCLUDED.checksum,
                        loaded_at = NOW();
                """, (str(govt_file), checksum))
                total_rows += len(rows_to_insert)
                results["government_expenditure"] = len(rows_to_insert)

    # 2. Process GST Monthly Seed
    gst_file = SEED_DIR / "gst_monthly.csv"
    if gst_file.exists():
        checksum = compute_file_sha256(gst_file)
        existing = await fetch_all(
            "SELECT checksum FROM seed_files WHERE path = %s;",
            (str(gst_file),)
        )
        if not existing or existing[0]["checksum"] != checksum:
            rows_to_insert = []
            with open(gst_file, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    fy = row["fiscal_year"].strip()
                    as_of_dt = date(int(fy), 3, 31)

                    dom = float(row.get("domestic_lakh_cr", 0.0))
                    imp = float(row.get("imports_lakh_cr", 0.0))
                    gro = float(row.get("gross_collection_lakh_cr", 0.0))
                    avg = float(row.get("monthly_average_lakh_cr", 0.0))
                    yoy = float(row.get("yoy_growth_pct", 0.0))

                    rows_to_insert.append((
                        "gst", "domestic", fy,
                        dom, "Rs lakh crore", "actual", "data-gov-in", as_of_dt
                    ))
                    rows_to_insert.append((
                        "gst", "domestic_collection", fy,
                        dom, "Rs lakh crore", "actual", "data-gov-in", as_of_dt
                    ))
                    rows_to_insert.append((
                        "gst", "imports", fy,
                        imp, "Rs lakh crore", "actual", "data-gov-in", as_of_dt
                    ))
                    rows_to_insert.append((
                        "gst", "imports_collection", fy,
                        imp, "Rs lakh crore", "actual", "data-gov-in", as_of_dt
                    ))
                    rows_to_insert.append((
                        "gst", "gross_collection", fy,
                        gro, "Rs lakh crore", "actual", "data-gov-in", as_of_dt
                    ))
                    rows_to_insert.append((
                        "gst", "total_collection", fy,
                        gro, "Rs lakh crore", "actual", "data-gov-in", as_of_dt
                    ))
                    rows_to_insert.append((
                        "gst", "monthly_average", fy,
                        avg, "Rs lakh crore", "actual", "data-gov-in", as_of_dt
                    ))
                    rows_to_insert.append((
                        "gst", "yoy_growth", fy,
                        yoy, "%", "actual", "data-gov-in", as_of_dt
                    ))

            if rows_to_insert:
                upsert_sql = """
                    INSERT INTO observations (indicator, series, period, value, unit, basis, source_id, as_of)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (indicator, series, period) DO UPDATE SET
                        value = EXCLUDED.value,
                        unit = EXCLUDED.unit,
                        basis = EXCLUDED.basis,
                        source_id = EXCLUDED.source_id,
                        as_of = EXCLUDED.as_of,
                        fetched_at = NOW();
                """
                await execute_many(upsert_sql, rows_to_insert)
                await execute_write("""
                    INSERT INTO seed_files (path, checksum, loaded_at)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (path) DO UPDATE SET
                        checksum = EXCLUDED.checksum,
                        loaded_at = NOW();
                """, (str(gst_file), checksum))
                total_rows += len(rows_to_insert)
                results["gst_monthly"] = len(rows_to_insert)

    # Log execution in collector_runs
    finished_at = datetime.now(timezone.utc)
    await execute_write("""
        INSERT INTO collector_runs (job, started_at, finished_at, status, rows, error)
        VALUES ('seed_loader', %s, %s, 'success', %s, NULL);
    """, (started_at, finished_at, total_rows))

    return results
