"""
Fonte: dadosabertos.poa.br
Dataset: ITBI — exercícios 2020 a 2025
URL: https://dadosabertos.poa.br/dataset/itbi
Formato: CSV
"""
import io
from datetime import date as date_
import requests
import pandas as pd

CKAN_BASE = "https://dadosabertos.poa.br/api/3/action"
DATASET_ID = "itbi"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def _parse_num(s) -> float | None:
    try:
        return float(str(s).replace(",", "."))
    except Exception:
        return None


def _parse_date(s) -> date_ | None:
    if not s or str(s).strip().lower() in ("nan", "none", ""):
        return None
    s = str(s).strip()
    import datetime
    for fmt in ("%Y/%m/%d %H:%M:%S", "%Y/%m/%d", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except Exception:
            pass
    return None


def _normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza um DataFrame individual usando Python puro (evita segfault numpy 2.x)."""
    # Remove aspas simples literais que o portal de POA inclui nos nomes de colunas
    cols = [c.strip().lower().strip("'") for c in df.columns]
    df.columns = cols

    logr_col   = next((c for c in cols if c in ("logradouro", "endereco", "rua")), None)
    num_col    = next((c for c in cols if c in ("n_endereco", "numero", "num", "nro")), None)
    bairro_col = next((c for c in cols if "bairro" in c), None)
    val_col    = next((c for c in cols if c in ("base_de_calculo", "base_calculo", "valor", "valor_itbi", "vt")), None)
    area_col   = next((c for c in cols if c in ("area_constr_privativa", "area_constr_total", "area_total_terreno", "area", "area_imovel")), None)
    date_col   = next((c for c in cols if any(w in c for w in ("data", "competencia", "exercicio", "ano"))), None)

    def _col(name):
        return df[name].tolist() if name and name in df.columns else [None] * len(df)

    logrs  = _col(logr_col)
    nums   = _col(num_col)
    bairros = _col(bairro_col)
    vals   = _col(val_col)
    areas  = _col(area_col)
    dates  = _col(date_col)

    rows = []
    for i in range(len(df)):
        val = _parse_num(vals[i])
        if val is None:
            continue
        txdate = _parse_date(dates[i])
        if txdate is None:
            continue

        logr = str(logrs[i]).strip().title() if logrs[i] else ""
        num  = str(nums[i]).strip() if nums[i] else "S/N"
        addr = f"{logr}, {num} — Porto Alegre RS".strip(", ")

        rows.append({
            "address": addr,
            "neighborhood": str(bairros[i]).title() if bairros[i] else None,
            "area_m2": _parse_num(areas[i]),
            "value": val,
            "property_type": None,
            "transaction_date": txdate,
            "source": "itbi_poa",
            "external_id": str(i),
            "raw_data": None,
        })

    return pd.DataFrame(rows)


def download(year: int | None = None) -> pd.DataFrame:
    resp = requests.get(
        f"{CKAN_BASE}/package_show",
        params={"id": DATASET_ID},
        headers=HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    resources = resp.json()["result"]["resources"]

    target_year = str(year) if year else None

    normalized: list[pd.DataFrame] = []
    for r in resources:
        name = r.get("name", "")
        url  = r.get("url", "")
        if target_year and target_year not in name:
            continue
        if r.get("format", "").upper() != "CSV":
            continue

        print(f"  [POA] {name}...")
        try:
            csv_resp = requests.get(url, headers=HEADERS, timeout=120)
            csv_resp.raise_for_status()
            for enc in ("utf-8", "latin-1"):
                try:
                    raw = pd.read_csv(
                        io.StringIO(csv_resp.content.decode(enc)),
                        sep=";",
                        low_memory=False,
                        on_bad_lines="skip",
                    )
                    break
                except Exception:
                    continue
            norm = _normalize_df(raw)
            normalized.append(norm)
            del raw
        except Exception as exc:
            print(f"  [POA] Erro em '{name}': {exc}")

    if not normalized:
        return pd.DataFrame()

    result = pd.concat(normalized, ignore_index=True)
    # external_id único por fonte: usa índice global
    result["external_id"] = result.index.astype(str)
    return result
