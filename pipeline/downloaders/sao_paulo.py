"""
Fonte: Secretaria Municipal da Fazenda de São Paulo
Dataset: "Dados das Transações Imobiliárias com recolhimento de ITBI"
URL: https://prefeitura.sp.gov.br/web/fazenda/w/acesso_a_informacao/31501
Biblioteca: dadosimob (PyPI) — scraping automático das URLs instáveis da SF/SP
"""
import datetime
from datetime import date as date_
import pandas as pd


def _parse_num(s) -> float | None:
    try:
        return float(str(s).replace(",", "."))
    except Exception:
        return None


def _parse_date(s) -> date_ | None:
    if not s or str(s).strip().lower() in ("nan", "none", "nat", ""):
        return None
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.datetime.strptime(s[:10], fmt).date()
        except Exception:
            pass
    return None


def _classify_type(s) -> str | None:
    s = str(s).lower() if s else ""
    if any(w in s for w in ["resid", "apart", "casa", "hab"]):
        return "residential"
    if any(w in s for w in ["comer", "loja", "sala", "escrit", "office"]):
        return "commercial"
    if "terr" in s:
        return "land"
    return None


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    col = lambda name: df[name].tolist() if name in df.columns else [None] * len(df)

    logradouros = col("logradouro")
    numeros     = col("numero")
    bairros     = col("bairro")
    ceps        = col("cep")
    valores     = col("valor_transacao")
    areas       = col("area_construida_m2")
    usos        = col("descricao_uso")
    datas       = col("data_transacao")
    sqls        = col("sql")

    rows = []
    for i in range(len(df)):
        val = _parse_num(valores[i])
        if val is None or val <= 0:
            continue
        txdate = _parse_date(datas[i])
        if txdate is None:
            continue

        logr = str(logradouros[i]).strip().title() if logradouros[i] else ""
        num  = str(numeros[i]).strip() if numeros[i] else "S/N"
        addr = f"{logr}, {num} — São Paulo SP".strip(", ")

        cep = str(ceps[i]).strip() if ceps[i] and str(ceps[i]).strip() not in ("nan", "None") else None

        rows.append({
            "address":          addr,
            "neighborhood":     str(bairros[i]).title() if bairros[i] and str(bairros[i]) not in ("nan", "None") else None,
            "zip_code":         cep,
            "area_m2":          _parse_num(areas[i]),
            "value":            val,
            "property_type":    _classify_type(usos[i]),
            "transaction_date": txdate,
            "source":           "itbi_sp",
            "external_id":      f"{sqls[i]}_{txdate}",
        })

    return pd.DataFrame(rows)


def download(year: int | None = None) -> pd.DataFrame:
    try:
        from dadosimob.itbi import sp as sp_itbi
    except ImportError:
        print("  [SP] ERRO: instale dadosimob → pip install dadosimob")
        return pd.DataFrame()

    year = year or date_.today().year
    print(f"  [SP] Baixando {year} via dadosimob...")

    try:
        raw = sp_itbi.load(years=[year])
    except Exception as exc:
        print(f"  [SP] Erro ao carregar via dadosimob: {exc}")
        return pd.DataFrame()

    if raw is None or raw.empty:
        print(f"  [SP] Nenhum dado retornado para {year}.")
        return pd.DataFrame()

    print(f"  [SP] {len(raw):,} linhas brutas — normalizando...")
    return _normalize(raw)
