"""
Carrega transações normalizadas no PostgreSQL + PostGIS.
Usa upsert para evitar duplicatas (source + external_id).
"""
import json
import psycopg2
import psycopg2.extras
import pandas as pd
from tqdm import tqdm


def load_transactions(
    df: pd.DataFrame,
    city_id: int,
    conn: psycopg2.extensions.connection,
    coords: dict[str, tuple[float, float] | None],
    batch_size: int = 500,
) -> tuple[int, int]:
    cur = conn.cursor()
    inserted = skipped = 0

    records = df.to_dict("records")
    for i in tqdm(range(0, len(records), batch_size), desc="Loading"):
        batch = records[i : i + batch_size]
        values: list[tuple] = []

        for row in batch:
            addr = row.get("address", "")
            coords_pair = coords.get(addr)

            geom = None
            if coords_pair:
                lng, lat = coords_pair
                geom = f"SRID=4326;POINT({lng} {lat})"

            raw = row.get("raw_data")
            raw_json = json.dumps(raw, ensure_ascii=False, default=str) if raw else None

            values.append((
                city_id,
                addr,
                row.get("neighborhood"),
                row.get("zip_code"),
                row.get("value"),
                row.get("area_m2"),
                row.get("property_type"),
                row.get("transaction_date"),
                row.get("source"),
                str(row.get("external_id", "")),
                geom,
                raw_json,
            ))

        psycopg2.extras.execute_values(
            cur,
            """
            INSERT INTO transactions
              (city_id, address, neighborhood, zip_code, value, area_m2,
               property_type, transaction_date, source, external_id, geom, raw_data)
            VALUES %s
            ON CONFLICT (source, external_id) DO NOTHING
            """,
            values,
            template=(
                "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,"
                "ST_GeomFromEWKT(%s),"
                "%s::jsonb"
            ),
        )
        batch_ins = cur.rowcount if cur.rowcount >= 0 else 0
        inserted += batch_ins
        skipped  += len(batch) - batch_ins
        conn.commit()

    cur.close()
    return inserted, skipped
