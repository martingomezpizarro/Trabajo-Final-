"""
Descarga datasets públicos de datos.gob.ar (CKAN API).
Cubre INDEC (IPC, EMAE, ICA, BP), Mecon, BCRA espejados.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT_INDEC = ROOT / "data" / "raw" / "indec"
OUT_MECON = ROOT / "data" / "raw" / "mecon"
OUT_INDEC.mkdir(parents=True, exist_ok=True)
OUT_MECON.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (research; academic)"}

# (package_id, carpeta_destino, prefijo_archivos)
PACKAGES = [
    # INDEC
    ("sspm-indice-precios-al-consumidor-nacional-ipc-base-diciembre-2016", OUT_INDEC, "ipc_nacional"),
    ("sspm-ipc-nacional-tasas-variacion-mensual-por-categorias-base-dic-2016", OUT_INDEC, "ipc_variaciones"),
    ("sspm-estimador-mensual-actividad-economica-emae-base-2004", OUT_INDEC, "emae"),
    ("sspm-estimador-mensual-actividad-economica-emae-apertura-sectorial-base-2004", OUT_INDEC, "emae_sectorial"),
    ("sspm-intercambio-comercial-argentino", OUT_INDEC, "ica"),
    ("sspm-saldo-comercial-por-paises-regiones-fob-cif", OUT_INDEC, "saldo_comercial_paises"),
    ("sspm-balance-pagos-mbp6", OUT_INDEC, "balance_pagos"),
    ("sspm-cuenta-corriente-balance-pagos-flujos-monetarios", OUT_INDEC, "cuenta_corriente"),
    ("sspm-producto-interno-bruto-dolares-producto-interno-bruto-per-capita-poblacion", OUT_INDEC, "pbi_usd_pc"),
    ("sspm-indicadores-oferta-demanda-global-precios-constantes-2004-trimestral", OUT_INDEC, "pbi_oferta_demanda"),
    # Mecon / Fiscal / Deuda (nombres correctos 2025/2026)
    ("sspm-titulos-publicos-deuda", OUT_MECON, "deuda_titulos"),
    ("sspm-deuda-externa-bruta-por-sector-residente", OUT_MECON, "deuda_externa_bruta"),
    ("sspm-deuda-externa-privada---bcra", OUT_MECON, "deuda_externa_privada"),
    ("sspm-informe-mensual-ingresos-gastos-sector-publico-nacional-no-financiero-imig", OUT_MECON, "imig_spnf"),
    ("sspm-esquema-ahorro---inversion---financiamiento-sector-publico-nacional-base-caja", OUT_MECON, "aif_spn"),
    ("sspm-esquema-ahorro---inversion---financiamiento-tesoro-nacional-base-caja", OUT_MECON, "aif_tesoro"),
    ("sspm-esquema-ahorro---inversion---financiamiento-administracion-publica-nacional-base-caja", OUT_MECON, "aif_apn"),
    ("sspm-cuenta-aif---base-devengado-sector-publico-argentino", OUT_MECON, "aif_devengado"),
    ("sspm-recursos-tributarios-totales-por-tributo", OUT_MECON, "recursos_tributarios"),
    ("sspm-principales-subgrupos-recaudacion-tributaria", OUT_MECON, "recaudacion_subgrupos"),
]


def get_package(pkg_id: str) -> dict | None:
    url = f"https://datos.gob.ar/api/3/action/package_show?id={pkg_id}"
    r = requests.get(url, headers=HEADERS, timeout=60)
    if r.status_code != 200:
        print(f"  ! pkg {pkg_id} HTTP {r.status_code}")
        return None
    d = r.json()
    if not d.get("success"):
        print(f"  ! pkg {pkg_id} not found")
        return None
    return d["result"]


def download_resource(url: str, dest: Path) -> bool:
    try:
        r = requests.get(url, headers=HEADERS, timeout=120)
    except Exception as e:
        print(f"  ERR {url}: {e}")
        return False
    if r.status_code != 200 or len(r.content) < 50:
        print(f"  HTTP {r.status_code} ({len(r.content)}b) {url}")
        return False
    dest.write_bytes(r.content)
    return True


def slugify(s: str) -> str:
    import re
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")[:60]


def main() -> None:
    summary = []
    for pkg_id, out_dir, prefix in PACKAGES:
        print(f"\n[DGA] {pkg_id}")
        meta = get_package(pkg_id)
        if meta is None:
            continue
        for res in meta.get("resources", []):
            fmt = (res.get("format") or "").upper()
            if fmt not in ("CSV", "XLS", "XLSX", "JSON"):
                continue
            name = res.get("name", "")
            ext = fmt.lower()
            fname = f"{prefix}_{slugify(name)}.{ext}"
            dest = out_dir / fname
            if download_resource(res["url"], dest):
                size_kb = dest.stat().st_size / 1024
                print(f"  ok {fmt} {size_kb:6.0f} KB -> {fname}")
                summary.append({
                    "package": pkg_id, "resource": name, "format": fmt,
                    "path": str(dest.relative_to(ROOT)), "size_kb": round(size_kb, 1),
                })

    pd.DataFrame(summary).to_csv(ROOT / "data" / "raw" / "_datos_gob_index.csv", index=False)
    print(f"\n{len(summary)} recursos descargados")


if __name__ == "__main__":
    main()
