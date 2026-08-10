"""
Fonte: data.rio — ArcGIS REST API
URL:   https://pgeo3.rio.rj.gov.br/arcgis/rest/services/Fazenda/ITBI/MapServer/0
Dados: agregados por bairro/mês (médias de valor e área por uso)
Campos: bairro, uso, ano_transação, mês_transação, total_transações,
        média_valor_transação, média_área_construída
"""
from datetime import date as date_
import requests
import pandas as pd

ARCGIS_BASE = (
    "https://pgeo3.rio.rj.gov.br/arcgis/rest/services/Fazenda/ITBI/MapServer/0/query"
)

FIELD_ANO = "ano_transação"
FIELD_MES = "mês_transação"
FIELD_VALOR = "média_valor_transação"
FIELD_AREA = "média_área_construída"
FIELD_BAIRRO = "bairro"
FIELD_USO = "uso"
FIELD_ID = "objectid"


def _parse_num(s) -> float | None:
    try:
        return float(str(s).replace(",", "."))
    except Exception:
        return None


def _classify_type(t) -> str | None:
    t = str(t).lower() if t else ""
    if "resid" in t:
        return "residential"
    if "nao" in t or "não" in t or "comer" in t:
        return "commercial"
    if "terr" in t:
        return "land"
    return None


def download(year: int | None = None, limit: int = 50_000) -> pd.DataFrame:
    # ArcGIS não aceita bem caracteres especiais no WHERE; busca tudo e filtra em Python
    params = {
        "where": "1=1",
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
        if data.get("error"):
            print(f"  [RJ] Erro ArcGIS: {data['error']}")
            break
        features = data.get("features", [])
        rows.extend(f["attributes"] for f in features)

        if len(features) < 1000 or len(rows) >= limit:
            break
        offset += 1000

    if not rows:
        return pd.DataFrame()

    # Filtra por ano em Python
    if year:
        rows = [r for r in rows if r.get(FIELD_ANO) == year]

    return _normalize(rows)


def _normalize(rows: list[dict]) -> pd.DataFrame:
    result = []
    for i, row in enumerate(rows):
        val = _parse_num(row.get(FIELD_VALOR))
        if val is None:
            continue

        try:
            ano = int(row.get(FIELD_ANO, 0))
            mes = int(row.get(FIELD_MES, 0))
            if not (1 <= mes <= 12 and ano > 1900):
                continue
            txdate = date_(ano, mes, 1)
        except Exception:
            continue

        bairro = str(row.get(FIELD_BAIRRO, "")).strip().title()
        uso = row.get(FIELD_USO, "")
        addr = f"{bairro} — Rio de Janeiro RJ" if bairro else "Rio de Janeiro RJ"
        ext_id = str(row.get(FIELD_ID, i))

        result.append({
            "address": addr,
            "neighborhood": bairro or None,
            "area_m2": _parse_num(row.get(FIELD_AREA)),
            "value": val,
            "property_type": _classify_type(uso),
            "transaction_date": txdate,
            "source": "itbi_rj",
            "external_id": ext_id,
            "raw_data": None,
        })

    return pd.DataFrame(result)
