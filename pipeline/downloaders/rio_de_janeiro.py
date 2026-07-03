"""
Fonte: data.rio — ArcGIS REST API
URL:   https://pgeo3.rio.rj.gov.br/arcgis/rest/services/Fazenda/ITBI/MapServer
Formatos: GeoJSON, CSV. Dados desde 2010.
Camadas:
  5 — Transações por Logradouro e Mês (Residenciais e Não-Residenciais)
"""
import requests
import pandas as pd

ARCGIS_BASE = (
    "https://pgeo3.rio.rj.gov.br/arcgis/rest/services/Fazenda/ITBI/MapServer/5/query"
)


def download(year: int | None = None, limit: int = 50_000) -> pd.DataFrame:
    where = f"ANO = {year}" if year else "1=1"
    params = {
        "where": where,
        "outFields": "*",
        "f": "json",
        "resultRecordCount": 1000,
        "returnGeometry": "false",
    }

    rows: list[dict] = []
    offset = 0

    while True:
        params["resultOffset"] = offset
        resp = requests.get(ARCGIS_BASE, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        features = data.get("features", [])
        rows.extend(f["attributes"] for f in features)

        if len(features) < 1000 or len(rows) >= limit:
            break
        offset += 1000

    df = pd.DataFrame(rows)
    return _normalize(df)


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip().upper() for c in df.columns]
    out = pd.DataFrame()

    logr_col = next((c for c in df.columns if "LOGR" in c and "NM" in c), None)
    bairro_col = next((c for c in df.columns if "BAIRRO" in c), None)

    out["address"] = (df.get(logr_col, pd.Series()).fillna("") + " — Rio de Janeiro RJ").str.strip()
    out["neighborhood"] = df.get(bairro_col, pd.Series()).str.title() if bairro_col else None

    valor_col = next((c for c in df.columns if "VALOR" in c or "VLR" in c), None)
    area_col  = next((c for c in df.columns if "AREA" in c or "M2" in c), None)

    out["value"] = pd.to_numeric(df.get(valor_col, pd.Series()), errors="coerce") if valor_col else None
    out["area_m2"] = pd.to_numeric(df.get(area_col, pd.Series()), errors="coerce") if area_col else None

    tipo_col = next((c for c in df.columns if "TIPO" in c or "USO" in c), None)
    if tipo_col:
        tipo = df[tipo_col].fillna("").str.lower()
        out["property_type"] = tipo.map(
            lambda t: "residential" if "resid" in t
                      else "commercial" if "comer" in t or "nao_resid" in t
                      else "land" if "terr" in t
                      else None
        )
    else:
        out["property_type"] = None

    ano_col = next((c for c in df.columns if c == "ANO" or c == "ANODTB"), None)
    mes_col = next((c for c in df.columns if c == "MES" or c == "MESDTB"), None)
    if ano_col and mes_col:
        out["transaction_date"] = pd.to_datetime(
            dict(year=df[ano_col], month=df[mes_col], day=1), errors="coerce"
        ).dt.date
    else:
        out["transaction_date"] = None

    out["source"] = "itbi_rj"
    out["external_id"] = df.get("OBJECTID", df.index).astype(str)
    out["raw_data"] = df.to_dict("records")

    return out.dropna(subset=["value", "transaction_date"])
