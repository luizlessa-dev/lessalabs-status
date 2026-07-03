"""
Fonte: Secretaria Municipal da Fazenda de São Paulo
URL:   https://prefeitura.sp.gov.br/web/fazenda/w/acesso_a_informacao/31501
Formato: CSV, atualização mensal
Campos:  ANODTB, MESDTB, NRLOGR, DSLOGR, NRCONTR, NMCOMPLM, NMBAIRRO,
         VLUTIL, VLOUTROS, VLTOTAL, NUGEO (geocódigo SQL)
"""
import io
from datetime import date
import requests
import pandas as pd


BASE_URL = (
    "https://dados.prefeitura.sp.gov.br/dataset/"
    "3cdbd99f-b534-450a-8b39-04b22cc5bcc2/resource/"
    "4c9a5b91-3c52-4e7e-9d1a-37a6a8c4b4fc/download/"
    "transacoes_imobiliarias_{year}.csv"
)

DTYPE_MAP = {
    "NRLOGR":  str,
    "DSLOGR":  str,
    "NRCONTR": str,
    "NMCOMPLM": str,
    "NMBAIRRO": str,
    "NUGEO":   str,
}


def download(year: int | None = None) -> pd.DataFrame:
    year = year or date.today().year
    url = BASE_URL.format(year=year)

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
