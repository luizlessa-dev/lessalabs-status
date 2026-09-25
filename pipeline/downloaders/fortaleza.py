"""
Fonte: Fortaleza Dados Abertos — SEFIN
Dataset: ITBI Transações Imobiliárias (arquivo histórico acumulado)
URL: https://dados.fortaleza.ce.gov.br/dataset/dados_abertos_itbi_transacoes_imobiliarias
Formato: CSV único (encoding latin-1), coordenadas em UTM SIRGAS 2000
"""
import io
import re
import datetime
from datetime import date as date_
import requests
import pandas as pd

CKAN_BASE = "https://dados.fortaleza.ce.gov.br/api/3/action"
DATASET_ID = "dados_abertos_itbi_transacoes_imobiliarias"

DIRECT_CSV = (
    "https://dados.fortaleza.ce.gov.br/dataset/"
    "32608ed2-e4ad-4cd2-b7bc-deea35dd189f/resource/"
    "46324d49-9809-4d32-8e5c-b4b570f067ce/download/"
    "dados_abertos_itbi_transacoes_imobiliarias.csv"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# Fortaleza — UTM SIRGAS 2000 zona 24S (EPSG:31984)
_UTM_EPSG = "EPSG:31984"
_WGS84    = "EPSG:4326"


def _utm_to_wgs84(easting: float, northing: float):
    """Converte UTM SIRGAS 2000 (zona 24S) para lat/lng WGS84."""
    try:
        from pyproj import Transformer
        tf = Transformer.from_crs(_UTM_EPSG, _WGS84, always_xy=True)
        lng, lat = tf.transform(easting, northing)
        # Sanity check: Fortaleza fica em ~(-38.5, -3.7)
        if -40 < lng < -37 and -6 < lat < -2:
            return lng, lat
    except Exception:
        pass
    return None, None


def _parse_coord(s):
    """Extrai (easting, northing) de strings UTM comuns."""
    if not s or str(s).strip().lower() in ("nan", "none", ""):
        return None, None
    s = str(s).strip()
    # Tenta extrair dois números: "549123.45 9581234.56" ou com vírgula decimal
    nums = re.findall(r"[\d]+(?:[.,]\d+)?", s)
    if len(nums) >= 2:
        try:
            e = float(nums[0].replace(",", "."))
            n = float(nums[1].replace(",", "."))
            # UTM easting ~500k–600k, northing ~9.58M para Fortaleza
            if e > 1_000 and n > 1_000_000:
                return e, n
            # Pode já estar em WGS84 (lat/lng decimal)
            if -40 < e < -37 and -6 < n < -2:
                return None, None  # já é lat/lng, tratar separado
        except Exception:
            pass
    return None, None


def _parse_num(s) -> float | None:
    try:
        return float(str(s).replace(",", "."))
    except Exception:
        return None


def _parse_date(s) -> date_ | None:
    if not s or str(s).strip().lower() in ("nan", "none", ""):
        return None
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.datetime.strptime(s[:19], fmt).date()
        except Exception:
            pass
    return None


def _classify_type(s) -> str | None:
    s = str(s).lower() if s else ""
    if any(w in s for w in ["resid", "apart", "casa", "hab", "unifam"]):
        return "residential"
    if any(w in s for w in ["comer", "loja", "sala", "galpao", "industrial"]):
        return "commercial"
    if "terr" in s:
        return "land"
    return None


def _get_csv_url() -> str:
    """Tenta descobrir URL via CKAN; fallback para URL direta conhecida."""
    try:
        resp = requests.get(
            f"{CKAN_BASE}/package_show",
            params={"id": DATASET_ID},
            headers=HEADERS,
            timeout=20,
        )
        resp.raise_for_status()
        resources = resp.json().get("result", {}).get("resources", [])
        csv_resources = [r for r in resources if r.get("format", "").upper() == "CSV"]
        if csv_resources:
            return csv_resources[0]["url"]
    except Exception:
        pass
    return DIRECT_CSV


def download(year: int | None = None) -> pd.DataFrame:
    url = _get_csv_url()
    print(f"  [FOR] Baixando CSV de Fortaleza...")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=180)
        resp.raise_for_status()
    except Exception as exc:
        print(f"  [FOR] Erro ao baixar CSV: {exc}")
        return pd.DataFrame()

    raw = None
    for enc in ("latin-1", "utf-8", "iso-8859-1"):
        try:
            raw = pd.read_csv(
                io.StringIO(resp.content.decode(enc)),
                sep=";",
                low_memory=False,
                on_bad_lines="skip",
            )
            break
        except Exception:
            continue

    if raw is None or raw.empty:
        print("  [FOR] Falha ao parsear CSV.")
        return pd.DataFrame()

    # Normaliza nomes de colunas
    raw.columns = [c.strip().lower() for c in raw.columns]
    print(f"  [FOR] {len(raw):,} linhas brutas. Colunas: {list(raw.columns)[:10]}")

    return _normalize(raw, year)


def _normalize(df: pd.DataFrame, year: int | None) -> pd.DataFrame:
    col = lambda name: df[name].tolist() if name in df.columns else [None] * len(df)

    logr_col  = next((c for c in df.columns if "logradouro" in c or c == "endereco" or c == "rua"), None)
    num_col   = next((c for c in df.columns if c in ("numero", "num", "nro", "nr")), None)
    bairro_col = next((c for c in df.columns if "bairro" in c), None)
    cep_col   = next((c for c in df.columns if "cep" in c), None)
    val_col   = next((c for c in df.columns if c in ("base_calculo", "base_de_calculo", "valor_transacao", "vt")), None)
    area_terr = next((c for c in df.columns if "area_terreno" in c), None)
    area_constr = next((c for c in df.columns if "area_construida" in c or "area_constr" in c), None)
    uso_col   = next((c for c in df.columns if "descricao_uso" in c or "uso" in c or "tipo" in c), None)
    date_col  = next((c for c in df.columns if "data_transacao" in c or "data" in c), None)
    coord_col = next((c for c in df.columns if "coordenada" in c or "coord" in c), None)
    ins_col   = next((c for c in df.columns if "inscricao" in c or "sql" in c or "numero_declaracao" in c), None)

    logrs   = col(logr_col)
    nums    = col(num_col)
    bairros = col(bairro_col)
    ceps    = col(cep_col)
    vals    = col(val_col)
    areas_t = col(area_terr)
    areas_c = col(area_constr)
    usos    = col(uso_col)
    dates   = col(date_col)
    coords  = col(coord_col)
    ins_ids = col(ins_col)

    rows = []
    for i in range(len(df)):
        val = _parse_num(vals[i])
        if val is None or val <= 0:
            continue
        txdate = _parse_date(dates[i])
        if txdate is None:
            continue
        if year and txdate.year != year:
            continue

        logr = str(logrs[i]).strip().title() if logrs[i] else ""
        num  = str(nums[i]).strip() if nums[i] else "S/N"
        addr = f"{logr}, {num} — Fortaleza CE".strip(", ")

        # Área: preferir construída, fallback para terreno
        area = _parse_num(areas_c[i]) or _parse_num(areas_t[i])

        # Coordenadas UTM → WGS84
        lng, lat = None, None
        if coord_col:
            e, n = _parse_coord(coords[i])
            if e and n:
                lng, lat = _utm_to_wgs84(e, n)

        cep = str(ceps[i]).strip() if ceps[i] and str(ceps[i]).strip() not in ("nan", "None") else None
        ext_id = str(ins_ids[i]).strip() if ins_ids[i] and str(ins_ids[i]).strip() not in ("nan", "None") else f"for_{i}"

        rows.append({
            "address":          addr,
            "neighborhood":     str(bairros[i]).title() if bairros[i] and str(bairros[i]) not in ("nan", "None") else None,
            "zip_code":         cep,
            "area_m2":          area,
            "value":            val,
            "property_type":    _classify_type(usos[i]),
            "transaction_date": txdate,
            "source":           "itbi_fortaleza",
            "external_id":      ext_id,
            "lat":              lat,
            "lng":              lng,
        })

    return pd.DataFrame(rows)
