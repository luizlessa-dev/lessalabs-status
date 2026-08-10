"""
Fonte: data.rio — ArcGIS REST API
URL:   https://pgeo3.rio.rj.gov.br/arcgis/rest/services/Fazenda/ITBI/MapServer
Formatos: GeoJSON, CSV. Dados desde 2010.
Camadas:
  5 — Transações por Logradouro e Mês (Residenciais e Não-Residenciais)
"""
from datetime import date as date_
import requests
import pandas as pd

ARCGIS_BASE = (
    "https://pgeo3.rio.rj.gov.br/arcgis/rest/services/Fazenda/ITBI/MapServer/5/query"
)


def _parse_num(s) -> float | None:
    try:
        return float(str(s).replace(",", "."))
    except Exception:
        return None


def _classify_type(t) -> str | None:
    t = str(t).lower() if t else ""
    if "resid" in t:
        return "residential"
    if "comer" in t or "nao_resid" in t or "não_resid" in t:
        return "commercial"
    if "terr" in t:
        return "land"
    return None


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

    if not rows:
        return pd.DataFrame()

    return _normalize(rows)


def _normalize(rows: list[dict]) -> pd.DataFrame:
    # Usa Python puro em vez de operações vetorizadas do numpy para evitar
    # segfault no Python 3.14 + numpy 2.x no macOS ARM
    if not rows:
        return pd.DataFrame()

    # Descobre colunas a partir do primeiro registro
    sample_keys = [k.strip().upper() for k in rows[0].keys()]

    logr_col   = next((k for k in sample_keys if "LOGR" in k and "NM" in k), None)
    bairro_col = next((k for k in sample_keys if "BAIRRO" in k), None)
    valor_col  = next((k for k in sample_keys if "VALOR" in k or "VLR" in k), None)
    area_col   = next((k for k in sample_keys if "AREA" in k or "M2" in k), None)
    tipo_col   = next((k for k in sample_keys if "TIPO" in k or "USO" in k), None)
    ano_col    = next((k for k in sample_keys if k in ("ANO", "ANODTB")), None)
    mes_col    = next((k for k in sample_keys if k in ("MES", "MESDTB")), None)
    id_col     = next((k for k in sample_keys if k == "OBJECTID"), None)

    result = []
    for i, raw in enumerate(rows):
        # normaliza chaves para maiúsculo
        row = {k.strip().upper(): v for k, v in raw.items()}

        val = _parse_num(row.get(valor_col)) if valor_col else None
        if val is None:
            continue

        txdate = None
        if ano_col and mes_col:
            try:
                ano = int(row.get(ano_col, 0))
                mes = int(row.get(mes_col, 0))
                if 1 <= mes <= 12 and ano > 1900:
                    txdate = date_(ano, mes, 1)
            except Exception:
                pass
        if txdate is None:
            continue

        logr = str(row.get(logr_col, "")).strip().title() if logr_col else ""
        addr = f"{logr} — Rio de Janeiro RJ".strip(" —")

        result.append({
            "address": addr,
            "neighborhood": str(row.get(bairro_col, "")).strip().title() if bairro_col else None,
            "area_m2": _parse_num(row.get(area_col)) if area_col else None,
            "value": val,
            "property_type": _classify_type(row.get(tipo_col)) if tipo_col else None,
            "transaction_date": txdate,
            "source": "itbi_rj",
            "external_id": str(row.get(id_col, i)) if id_col else str(i),
            "raw_data": None,
        })

    return pd.DataFrame(result)
