"""
Fonte: Secretaria Municipal da Fazenda de São Paulo
API:   https://dados.prefeitura.sp.gov.br/api/3/action/package_show?id=<dataset_id>
Formato: CSV, atualização mensal
Campos:  ANODTB, MESDTB, NRLOGR, DSLOGR, NRCONTR, NMCOMPLM, NMBAIRRO,
         VLUTIL, VLOUTROS, VLTOTAL, NUGEO (geocódigo SQL)
"""
import io
from datetime import date
import requests
import pandas as pd

CKAN_API = "https://dados.prefeitura.sp.gov.br/api/3/action/package_show"
DATASET_ID = "3cdbd99f-b534-450a-8b39-04b22cc5bcc2"

DTYPE_MAP = {
    "NRLOGR":  str,
    "DSLOGR":  str,
    "NRCONTR": str,
    "NMCOMPLM": str,
    "NMBAIRRO": str,
    "NUGEO":   str,
}


def _find_csv_url(year: int) -> str:
    """Descobre a URL do CSV via API CKAN para evitar dependência de resource_id fixo."""
    resp = requests.get(CKAN_API, params={"id": DATASET_ID}, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if not data.get("success"):
        raise RuntimeError(f"CKAN API retornou erro: {data.get('error')}")

    resources = data["result"]["resources"]
    year_str = str(year)

    # Prioriza recursos cujo nome/URL contenha o ano
    for r in resources:
        url = r.get("url", "")
        name = r.get("name", "")
        if year_str in url or year_str in name:
            return url

    # Fallback: retorna o recurso CSV mais recente disponível
    csv_resources = [r for r in resources if r.get("format", "").upper() == "CSV"]
    if csv_resources:
        return csv_resources[-1]["url"]

    raise RuntimeError(f"Nenhum recurso CSV encontrado para o ano {year} no dataset SP.")


def download(year: int | None = None) -> pd.DataFrame:
    year = year or date.today().year
    url = _find_csv_url(year)
    print(f"  [SP] Baixando de: {url}")

    resp = requests.get(url, timeout=120)
    resp.raise_for_status()

    df = pd.read_csv(
        io.StringIO(resp.text),
        sep=";",
        encoding="latin-1",
        dtype=DTYPE_MAP,
        low_memory=False,
    )
    df.columns = [c.strip().upper() for c in df.columns]

    return _normalize(df, year)


def _normalize(df: pd.DataFrame, year: int) -> pd.DataFrame:
    out = pd.DataFrame()
    out["address"] = (
        df["DSLOGR"].fillna("") + ", "
        + df["NRLOGR"].fillna("S/N")
        + " — São Paulo SP"
    ).str.strip(", ")
    out["neighborhood"] = df["NMBAIRRO"].str.title()
    out["value"] = pd.to_numeric(df["VLTOTAL"].astype(str).str.replace(",", "."), errors="coerce")
    out["area_m2"] = None  # SP não disponibiliza área no CSV público
    out["property_type"] = None
    out["transaction_date"] = pd.to_datetime(
        dict(year=year, month=df["MESDTB"], day=1), errors="coerce"
    ).dt.date
    out["source"] = "itbi_sp"
    out["external_id"] = df["NUGEO"].astype(str) + "_" + df["MESDTB"].astype(str) + "_" + str(year)
    out["raw_data"] = df.to_dict("records")

    return out.dropna(subset=["value", "transaction_date"])
