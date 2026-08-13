"""
Carrega transações normalizadas no PostgreSQL + PostGIS.
Usa upsert para evitar duplicatas (source + external_id).
"""
import json
import psycopg
import pandas as pd
from tqdm import tqdm


def load_transactions(
    df: pd.DataFrame,
    city_id: int,
    conn: psycopg.Connection,
    coords: dict[str, tuple[float, float] | None],
    batch_size: int = 500,
) -> tuple[int, int]:
    inserted = skipped = 0

    # Extract columns as plain Python lists to avoid numpy/segfault issues
    col = lambda name: df[name].tolist() if name in df.columns else [None] * len(df)
    addresses      = col("address")
    neighborhoods  = col("neighborhood")
    zip_codes      = col("zip_code")
    values_        = col("value")
    areas          = col("area_m2")
    ptypes         = col("property_type")
    dates          = col("transaction_date")
    sources        = col("source")
    ext_ids        = col("external_id")

    n = len(df)
    for i in tqdm(range(0, n, batch_size), desc="Loading"):
        end = min(i + batch_size, n)
        batch_values: list[tuple] = []

        for j in range(i, end):
            addr = addresses[j] or ""
            coords_pair = coords.get(addr)

            geom = None
            if coords_pair:
                lng, lat = coords_pair
                geom = f"SRID=4326;POINT({lng} {lat})"

            batch_values.append((
                city_id,
                addr,
                neighborhoods[j],
                zip_codes[j],
                values_[j],
                areas[j],
                ptypes[j],
                dates[j],
                sources[j],
                str(ext_ids[j]) if ext_ids[j] is not None else str(j),
                geom,
                None,  # raw_data always None to avoid JSON serialisation issues
            ))

        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO transactions
                  (city_id, address, neighborhood, zip_code, value, area_m2,
                   property_type, transaction_date, source, external_id, geom, raw_data)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                        ST_GeomFromEWKT(%s),
                        %s::jsonb)
                ON CONFLICT (source, external_id) DO NOTHING
                """,
                batch_values,
            )
            batch_ins = cur.rowcount if cur.rowcount >= 0 else len(batch_values)
            inserted += batch_ins
            skipped  += (end - i) - batch_ins
        conn.commit()

    return inserted, skipped
