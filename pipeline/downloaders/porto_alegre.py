"""
Fonte: dadosabertos.poa.br
Dataset: ITBI — exercícios 2020 a 2025
URL: https://dadosabertos.poa.br/dataset/itbi
Formato: CSV
"""
import io
import requests
import pandas as pd

CKAN_BASE = "https://dadosabertos.poa.br/api/3/action"
DATASET_ID = "itbi"


def download(year: int | None = None) -> pd.DataFrame:
    resp = requests.get(
        f"{CKAN_BASE}/package_show",
        params={"id": DATASET_ID},
        timeout=30,
    )
    resp.raise_for_status()
    resources = resp.json()["result"]["resources"]

    target_year = str(year) if year else None
    frames: list[pd.DataFrame] = []

    for r in resources:
        name = r.get("name", "")
        if target_year and target_year not in name:
            continue
        if not r.get("url", "").endswith(".csv"):
            continue
        csv_resp = requests.get(r["url"], timeout=120)
        csv_resp.raise_for_status()
        df = pd.read_csv(io.StringIO(csv_resp.text), sep=";", encoding="latin-1", low_memory=False)
        frames.append(df)

    if not frames:
        return pd.DataFrame()

    raw = pd.concat(frames, ignore_index=True)
    return _normalize(raw)


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip().lower() for c in df.columns]
    out = pd.DataFrame()

    logr = df.get("logradouro", df.get("endereco", pd.Series())).fillna("").str.title()
    num  = df.get("numero", pd.Series()).fillna("S/N").astype(str)
    out["address"] = (logr + ", " + num + " — Porto Alegre RS").str.strip(", ")
    out["neighborhood"] = df.get("bairro", pd.Series()).str.title()
    out["value"] = pd.to_numeric(
        df.get("base_calculo", df.get("valor", pd.Series()))
          .astype(str).str.replace(",", "."),
        errors="coerce",
    )
    out["area_m2"] = pd.to_numeric(
        df.get("area", df.get("area_imovel", pd.Series()))
          .astype(str).str.replace(",", "."),
        errors="coerce",
    )
    out["property_type"] = None

    data_col = next(
        (c for c in df.columns if "data" in c or "competencia" in c or "ano" in c), None
    )
    out["transaction_date"] = pd.to_datetime(df.get(data_col, pd.Series()), errors="coerce").dt.date if data_col else None
    out["source"] = "itbi_poa"
    out["external_id"] = df.index.astype(str)
    out["raw_data"] = df.to_dict("records")

    return out.dropna(subset=["value", "transaction_date"])
