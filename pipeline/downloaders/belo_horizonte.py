"""
Fonte: Portal de Dados Abertos da PBH — dataset "itbi-relatorios"
URL:   https://ckan.pbh.gov.br/dataset/itbi-relatorios
Formato: CSVs mensais (novo formato desde 06/2024)
Colunas: Endereco, Bairro, Area Construida Adquirida, Valor Declarado,
         Descricao Tipo Ocupacao Unidade, Data Quitacao Transacao, ...
"""
import io
from datetime import date
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
    year = year or date.today().year
    year_str = str(year)

    resources = _get_resources()

    # Recursos mensais: "{year} - {Mês} - ITBI Relatórios"
    monthly = [
        r for r in resources
        if r.get("format", "").upper() == "CSV"
        and year_str in r.get("name", "")
        and "ITBI" in r.get("name", "")
    ]

    if not monthly:
        print(f"  [BH] Nenhum recurso CSV encontrado para {year}.")
        return pd.DataFrame()

    all_dfs: list[pd.DataFrame] = []
    for r in sorted(monthly, key=lambda x: x["name"]):
        print(f"  [BH] {r['name']}...")
        try:
            df = _read_csv(r["url"])
            # guarda mês para data de transação
            name_lower = r["name"].lower()
            df["_mes"] = next((v for k, v in MONTH_PT.items() if k in name_lower), 1)
            df["_ano"] = year
            all_dfs.append(df)
        except Exception as exc:
            print(f"  [BH] Erro em '{r['name']}': {exc}")

    if not all_dfs:
        return pd.DataFrame()

    return _normalize(pd.concat(all_dfs, ignore_index=True))


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()

    # Endereco já inclui bairro, CEP e cidade: perfeito para geocoding
    out["address"] = df.get("Endereco", pd.Series(dtype=str)).str.title().fillna("")
    out["neighborhood"] = df.get("Bairro", pd.Series(dtype=str)).str.title()

    area_col = (
        "Area Construida Adquirida"
        if "Area Construida Adquirida" in df.columns
        else "Area Adquirida Unidades Somadas"
    )
    out["area_m2"] = pd.to_numeric(
        df.get(area_col, pd.Series(dtype=str)).astype(str).str.replace(",", "."),
        errors="coerce",
    )

    out["value"] = pd.to_numeric(
        df.get("Valor Declarado", pd.Series(dtype=str)).astype(str).str.replace(",", "."),
        errors="coerce",
    )

    tipo = df.get("Descricao Tipo Ocupacao Unidade", pd.Series(dtype=str)).fillna("").str.lower()
    out["property_type"] = tipo.map(
        lambda t: "residential" if any(w in t for w in ["resid", "apart", "casa"])
                  else "commercial" if any(w in t for w in ["comer", "loja", "sala"])
                  else "land" if "terr" in t
                  else None
    )

    if "Data Quitacao Transacao" in df.columns:
        out["transaction_date"] = pd.to_datetime(
            df["Data Quitacao Transacao"], dayfirst=True, errors="coerce"
        ).dt.date
    else:
        out["transaction_date"] = pd.to_datetime(
            dict(year=df["_ano"], month=df["_mes"], day=1), errors="coerce"
        ).dt.date

    out["source"] = "itbi_bh"
    # external_id: usa _id do datastore se disponível, senão índice + mês/ano
    if "_id" in df.columns:
        out["external_id"] = df["_id"].astype(str)
    else:
        out["external_id"] = (
            df["_ano"].astype(str) + "_" + df["_mes"].astype(str)
            + "_" + df.index.astype(str)
        )
    out["raw_data"] = df.to_dict("records")

    return out.dropna(subset=["value", "transaction_date"])
