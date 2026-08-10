"""
Fonte: Portal de Dados Abertos da PBH — dataset "itbi-relatorios"
URL:   https://ckan.pbh.gov.br/dataset/itbi-relatorios
Formato: CSVs mensais (novo formato desde 06/2024)
Colunas: Endereco, Bairro, Area Construida Adquirida, Valor Declarado,
         Descricao Tipo Ocupacao Unidade, Data Quitacao Transacao, ...
"""
import io
from datetime import date as date_
import requests
import pandas as pd

CKAN_BASE = "https://ckan.pbh.gov.br"
PACKAGE_API = f"{CKAN_BASE}/api/3/action/package_show"
DATASET_SLUG = "itbi-relatorios"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/csv,application/json",
    "Referer": "https://ckan.pbh.gov.br/",
}

MONTH_PT = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "março": 3,
    "abril": 4, "maio": 5, "junho": 6, "julho": 7,
    "agosto": 8, "setembro": 9, "outubro": 10,
    "novembro": 11, "dezembro": 12,
}


def _get_resources() -> list[dict]:
    resp = requests.get(
        PACKAGE_API, params={"id": DATASET_SLUG}, headers=HEADERS, timeout=30
    )
    resp.raise_for_status()
    return resp.json()["result"]["resources"]


def _read_csv(url: str) -> pd.DataFrame:
    resp = requests.get(url, headers=HEADERS, timeout=120)
    resp.raise_for_status()
    for enc in ("utf-8", "latin-1"):
        try:
            df = pd.read_csv(
                io.StringIO(resp.content.decode(enc)),
                sep=";",
                low_memory=False,
                on_bad_lines="skip",
            )
            df.columns = [c.strip() for c in df.columns]
            return df
        except Exception:
            continue
    raise RuntimeError(f"Não foi possível ler o CSV de {url}")


def download(year: int | None = None) -> pd.DataFrame:
    year = year or date_.today().year
    year_str = str(year)

    resources = _get_resources()

    # Somente CSVs mensais: "{year} - {Mês} - ITBI Relatórios"
    # Exclui o bulk histórico "01/2008 a 05/2024" que é enorme demais para carregar todo
    monthly = [
        r for r in resources
        if r.get("format", "").upper() == "CSV"
        and r.get("name", "").strip().startswith(year_str + " - ")
    ]

    if not monthly:
        print(f"  [BH] Nenhum recurso CSV encontrado para {year}.")
        return pd.DataFrame()

    # Normaliza cada arquivo individualmente para evitar concat de DataFrames brutos
    # com muitas colunas (workaround para segfault em Python 3.14 + numpy no macOS ARM)
    normalized: list[pd.DataFrame] = []
    offset = 0
    for r in sorted(monthly, key=lambda x: x["name"]):
        print(f"  [BH] {r['name']}...")
        try:
            raw = _read_csv(r["url"])
            name_lower = r["name"].lower()
            mes = next((v for k, v in MONTH_PT.items() if k in name_lower), 1)
            norm = _normalize(raw, year=year, mes=mes, index_offset=offset)
            offset += len(raw)
            normalized.append(norm)
            del raw
        except Exception as exc:
            print(f"  [BH] Erro em '{r['name']}': {exc}")

    if not normalized:
        return pd.DataFrame()

    return pd.concat(normalized, ignore_index=True)


def _parse_num(s) -> float | None:
    try:
        return float(str(s).replace(",", "."))
    except Exception:
        return None


def _parse_date(s, fallback: date_) -> date_:
    try:
        parts = str(s).strip().split("/")
        if len(parts) == 3:
            return date_(int(parts[2]), int(parts[1]), int(parts[0]))
    except Exception:
        pass
    return fallback


def _classify_type(t) -> str | None:
    t = str(t).lower() if t else ""
    if any(w in t for w in ["resid", "apart", "casa"]):
        return "residential"
    if any(w in t for w in ["comer", "loja", "sala"]):
        return "commercial"
    if "terr" in t:
        return "land"
    return None


def _normalize(
    df: pd.DataFrame,
    year: int = 0,
    mes: int = 1,
    index_offset: int = 0,
) -> pd.DataFrame:
    # Usa Python puro em vez de operações vetorizadas do numpy para evitar
    # segfault no Python 3.14 + numpy 2.x no macOS ARM
    area_col = (
        "Area Construida Adquirida"
        if "Area Construida Adquirida" in df.columns
        else "Area Adquirida Unidades Somadas"
    )
    has_date_col = "Data Quitacao Transacao" in df.columns
    has_id_col = "_id" in df.columns
    fallback = date_(year, mes, 1)

    def _col(name):
        return df[name].tolist() if name in df.columns else [None] * len(df)

    enderecos = _col("Endereco")
    bairros   = _col("Bairro")
    areas     = _col(area_col)
    values    = _col("Valor Declarado")
    tipos     = _col("Descricao Tipo Ocupacao Unidade")
    dates     = _col("Data Quitacao Transacao") if has_date_col else None
    ids       = _col("_id") if has_id_col else None

    rows = []
    for i in range(len(df)):
        val = _parse_num(values[i])
        if val is None:
            continue
        txdate = _parse_date(dates[i], fallback) if has_date_col else fallback
        if txdate is None:
            continue
        addr = str(enderecos[i]).strip().title() if enderecos[i] else ""
        ext_id = str(ids[i]) if has_id_col else f"{year}_{mes}_{i + index_offset}"
        rows.append({
            "address": addr,
            "neighborhood": str(bairros[i]).title() if bairros[i] else None,
            "area_m2": _parse_num(areas[i]),
            "value": val,
            "property_type": _classify_type(tipos[i]),
            "transaction_date": txdate,
            "source": "itbi_bh",
            "external_id": ext_id,
            "raw_data": None,
        })

    return pd.DataFrame(rows)
