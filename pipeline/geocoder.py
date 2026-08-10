"""
Geocodifica endereços usando Nominatim (OSM).
Cache no banco para evitar chamadas repetidas.
"""
import time
import hashlib
import requests
import psycopg
from psycopg.rows import dict_row
from config import DATABASE_URL, NOMINATIM_USER_AGENT

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def _cache_key(address: str) -> str:
    return hashlib.sha256(address.lower().encode()).hexdigest()[:16]


def _fetch_coords(address: str) -> tuple[float, float] | None:
    resp = requests.get(
        NOMINATIM_URL,
        params={"q": address, "format": "json", "limit": 1, "countrycodes": "br"},
        headers={"User-Agent": NOMINATIM_USER_AGENT},
        timeout=10,
    )
    resp.raise_for_status()
    results = resp.json()
    if not results:
        return None
    r = results[0]
    return float(r["lon"]), float(r["lat"])


def geocode_batch(
    addresses: list[str],
    conn: psycopg.Connection,
    delay: float = 1.1,
) -> dict[str, tuple[float, float] | None]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS geocode_cache (
              key   TEXT PRIMARY KEY,
              address TEXT,
              lng   DOUBLE PRECISION,
              lat   DOUBLE PRECISION,
              found BOOLEAN
            )
            """
        )
        conn.commit()

        result: dict[str, tuple[float, float] | None] = {}

        keys = [_cache_key(a) for a in addresses]
        if keys:
            cur.execute(
                "SELECT key, lng, lat, found FROM geocode_cache WHERE key = ANY(%s)",
                (keys,),
            )
            cached = {row["key"]: row for row in cur.fetchall()}
        else:
            cached = {}

        to_fetch: list[str] = []
        for addr in addresses:
            k = _cache_key(addr)
            if k in cached:
                row = cached[k]
                result[addr] = (row["lng"], row["lat"]) if row["found"] else None
            else:
                to_fetch.append(addr)

        for addr in to_fetch:
            coords = _fetch_coords(addr)
            k = _cache_key(addr)
            if coords:
                cur.execute(
                    "INSERT INTO geocode_cache (key, address, lng, lat, found) VALUES (%s,%s,%s,%s,true) ON CONFLICT (key) DO NOTHING",
                    (k, addr, coords[0], coords[1]),
                )
            else:
                cur.execute(
                    "INSERT INTO geocode_cache (key, address, lng, lat, found) VALUES (%s,%s,NULL,NULL,false) ON CONFLICT (key) DO NOTHING",
                    (k, addr),
                )
            conn.commit()
            result[addr] = coords
            time.sleep(delay)

    return result
