"""
Pipeline principal. Uso:
  python run.py --city sao-paulo --year 2024
  python run.py --all --year 2024
  python run.py --all  # usa o ano corrente
"""
import argparse
import sys
from datetime import date
import psycopg2
from config import DATABASE_URL, CITIES
from downloaders import DOWNLOADERS
from geocoder import geocode_batch
from loader import load_transactions


def run(city_slug: str, year: int) -> None:
    cfg = CITIES[city_slug]
    downloader = DOWNLOADERS[cfg["downloader"]]

    print(f"[{city_slug}] Downloading {year}...")
    df = downloader(year=year)
    if df.empty:
        print(f"[{city_slug}] No data returned.")
        return
    print(f"[{city_slug}] {len(df):,} records fetched.")

    conn = psycopg2.connect(DATABASE_URL)

    print(f"[{city_slug}] Geocoding {df['address'].nunique():,} unique addresses...")
    unique_addresses = df["address"].dropna().unique().tolist()
    coords = geocode_batch(unique_addresses, conn)
    geocoded = sum(1 for v in coords.values() if v is not None)
    print(f"[{city_slug}] Geocoded {geocoded}/{len(unique_addresses)} addresses.")

    ins, skip = load_transactions(df, cfg["db_id"], conn, coords)
    print(f"[{city_slug}] Inserted {ins:,} | Skipped {skip:,} (duplicates)")

    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", choices=list(CITIES.keys()))
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--year", type=int, default=date.today().year)
    args = parser.parse_args()

    if not args.city and not args.all:
        parser.print_help()
        sys.exit(1)

    targets = list(CITIES.keys()) if args.all else [args.city]
    for slug in targets:
        try:
            run(slug, args.year)
        except Exception as exc:
            print(f"[{slug}] ERROR: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
