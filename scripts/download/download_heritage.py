"""
Heritage Foundation — Index of Economic Freedom.
Scrapea la página 'all-country-scores' para localizar el último XLS
y también baja ediciones históricas.
"""
from __future__ import annotations

import re
from pathlib import Path

from curl_cffi import requests as cr

OUT = Path(__file__).resolve().parents[2] / "data" / "raw" / "heritage"
OUT.mkdir(parents=True, exist_ok=True)

INDEX_URL = "https://www.heritage.org/index/pages/all-country-scores"
HIST_TEMPLATE = "https://static.heritage.org/index/data/{year}/{year}_indexofeconomicfreedom_data.xlsx"


def fetch(url: str, dest: Path) -> bool:
    try:
        r = cr.get(url, impersonate="chrome120", timeout=60)
    except Exception as e:
        print(f"  ERROR {url}: {e}")
        return False
    if r.status_code == 200 and len(r.content) > 1000:
        dest.write_bytes(r.content)
        print(f"  ok {len(r.content)/1024:.0f} KB -> {dest.name}")
        return True
    print(f"  HTTP {r.status_code}, {len(r.content)} bytes -> {url}")
    return False


def main() -> None:
    # Edición actual (link obtenido del HTML)
    print(f"[Heritage] Consultando {INDEX_URL}")
    r = cr.get(INDEX_URL, impersonate="chrome120", timeout=30)
    links = re.findall(r'https?://[^\s"\'<>]+?\.(?:xls|xlsx|csv)', r.text)
    for link in set(links):
        name = link.rsplit("/", 1)[-1]
        fetch(link, OUT / name)

    # Ediciones históricas: pre-2024 .xls, 2024+ .xlsx
    for year in range(2010, 2027):
        for ext in ("xlsx", "xls"):
            dest = OUT / f"{year}_indexofeconomicfreedom_data.{ext}"
            if dest.exists():
                break
            url = f"https://static.heritage.org/index/data/{year}/{year}_indexofeconomicfreedom_data.{ext}"
            print(f"[Heritage {year} .{ext}]")
            if fetch(url, dest):
                break

    files = sorted(OUT.glob("*_indexofeconomicfreedom_data.xlsx"))
    print(f"\n{len(files)} archivos en {OUT}")


if __name__ == "__main__":
    main()
