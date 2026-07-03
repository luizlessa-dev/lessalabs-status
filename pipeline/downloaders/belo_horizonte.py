"""
Fonte: Portal de Dados Abertos da PBH (ckan.pbh.gov.br)
Formato: CSV, desde 2008, atualização mensal
Campos: ano, mes, valor_declarado, area_construida, tipo_padrao,
        tipo_logradouro, nome_logradouro, numero, complemento, bairro
"""
import io
import requests
import pandas as pd

CKAN_API = "https://ckan.pbh.gov.br/api/3/action/datastore_search"
RESOURCE_ID = "8b73b834-f7c0-4abd-b8c8-185a9bfb30f1"


def download(year: int | None = None, limit: int = 100_000) -> pd.DataFrame:
    rows: list[dict] = []
    offset = 0
    filters = f'{{"ano": {year}}}' if year else None

    while True:
        params: dict = {"resource_id": RESOURCE_ID, "limit": 1000, "offset": offset}
        if filters:
            params["filters"] = filters

        resp = requests.get(CKAN_API, params=params, timeout=60)
        resp.raise_for_status()
        result = resp.json()["result"]
        batch = result.get("records", [])
        rows.extend(batch)

        if len(rows) >= limit or len(batch) < 1000:
            break
        offset += 1000

    df = pd.DataFrame(rows)
    return _normalize(df)


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip().lower() for c in df.columns]
    out = pd.DataFrame()

    logr = (
        df.get("tipo_logradouro", "").fillna("").str.title() + " "
        + df.get("nome_logradouro", "").fillna("").str.title() + ", "
        + df.get("numero", "").fillna("S/N").astype(str)
        + " — Belo Horizonte MG"
    )
    out["address"] = logr.str.strip()
    out["neighborhood"] = df.get("bairro", pd.Series()).str.title()
    out["value"] = pd.to_numeric(
        df.get("valor_declarado", df.get("valor_fiscal", pd.Series()))
          .astype(str).str.replace(",", "."),
        errors="coerce",
    )
    out["area_m2"] = pd.to_numeric(
        df.get("area_construida", pd.Series()).astype(str).str.replace(",", "."),
        errors="coerce",
    )

    tipo = df.get("tipo_padrao", "").fillna("").str.lower()
    out["property_type"] = tipo.map(
        lambda t: "residential" if "resid" in t
                  else "commercial" if "comer" in t
                  else "land" if "terr" in t
                  else None
    )

    out["transaction_date"] = pd.to_datetime(
        dict(year=df["ano"], month=df["mes"], day=1), errors="coerce"
    ).dt.date
    out["source"] = "itbi_bh"
    out["external_id"] = df.get("_id", pd.Series()).astype(str)
    out["raw_data"] = df.to_dict("records")

    return out.dropna(subset=["value", "transaction_date"])
