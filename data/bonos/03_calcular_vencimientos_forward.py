"""
03_calcular_vencimientos_forward.py — Calcula la serie temporal de vencimientos
de deuda soberana argentina en USD dentro de una ventana forward de 2 años.

Para cada mes t desde enero 2006 hasta hoy:
  → Suma todos los pagos de capital (amortización) de bonos USD activos
    que vencen en el intervalo [t, t + 24 meses]

Desagregación por:
  - tipo_tasa : fija | step_up | zero_coupon | variable | contingente
  - emisor    : tesoro | bcra | multilateral

Output: data/bonos/vencimientos_usd_2y_forward.csv

Ejecutar: python data/bonos/03_calcular_vencimientos_forward.py
"""
import pandas as pd
import json
import os

BONOS_DIR = os.path.dirname(os.path.abspath(__file__))


def clasificar_bono(bono):
    """Devuelve (tipo_tasa, emisor) a partir de los metadatos del bono."""
    era = bono.get("era", "")
    cupon = bono.get("cupon_info", "").lower()

    # ── tipo_tasa ─────────────────────────────────────────────────────────
    if "zero-coupon" in cupon or "zero coupon" in cupon:
        tipo_tasa = "zero_coupon"
    elif "variable" in cupon or "licitación" in cupon:
        tipo_tasa = "variable"
    elif "step-up" in cupon:
        tipo_tasa = "step_up"
    elif "contingente" in cupon or "pbi" in cupon:
        tipo_tasa = "contingente"
    else:
        tipo_tasa = "fija"

    # ── emisor ────────────────────────────────────────────────────────────
    if era in ("bopreal", "lebac_usd"):
        emisor = "bcra"
    elif era == "club_paris":
        emisor = "multilateral"
    else:
        emisor = "tesoro"

    return tipo_tasa, emisor


def generar_flujo_amortizacion(bono):
    """Genera DataFrame con columnas: fecha, amort_mm_usd, ticker, tipo_tasa, emisor."""
    monto = bono["monto_original_mm_usd"]
    tipo_tasa, emisor = clasificar_bono(bono)
    meta = {
        "ticker": bono["ticker"],
        "tipo_tasa": tipo_tasa,
        "emisor": emisor,
        "activo_desde": pd.Timestamp(bono["activo_desde"]),
        "activo_hasta": pd.Timestamp(bono["activo_hasta"]),
    }

    if bono.get("amortizacion_detalle"):
        rows = [
            {"fecha": pd.Timestamp(f), "amort_mm_usd": monto * pct / 100.0, **meta}
            for f, pct in bono["amortizacion_detalle"]
        ]

    elif bono.get("amortizacion_cuotas", 0) > 0:
        inicio = pd.Timestamp(bono["amortizacion_inicio"])
        n = bono["amortizacion_cuotas"]
        freq = "6MS" if bono.get("frecuencia_cupon") == "S" else "12MS"
        fechas = pd.date_range(inicio, periods=n, freq=freq)
        cuota = monto / n
        rows = [{"fecha": f, "amort_mm_usd": cuota, **meta} for f in fechas]

    else:
        rows = [{"fecha": pd.Timestamp(bono["fecha_vencimiento"]), "amort_mm_usd": monto, **meta}]

    return pd.DataFrame(rows)


def main():
    catalogo_path = os.path.join(BONOS_DIR, "catalogo_bonos_usd.json")
    if not os.path.exists(catalogo_path):
        print("Primero ejecutá: python data/bonos/02_catalogo_bonos_usd.py")
        return

    with open(catalogo_path, encoding="utf-8") as f:
        catalogo = json.load(f)

    print(f"Catálogo cargado: {len(catalogo)} bonos")

    # ── Generar todos los flujos ───────────────────────────────────────────
    flows = pd.concat(
        [generar_flujo_amortizacion(b) for b in catalogo], ignore_index=True
    )
    print(f"Flujos de amortización: {len(flows)}")
    print(f"  Monto total: USD {flows['amort_mm_usd'].sum():,.0f} MM")

    # ── Dimensiones de desagregación ──────────────────────────────────────
    tipos_tasa = sorted(flows["tipo_tasa"].unique())
    emisores   = sorted(flows["emisor"].unique())
    print(f"\nTipos de tasa presentes : {tipos_tasa}")
    print(f"Emisores presentes       : {emisores}")

    # ── Serie mensual ─────────────────────────────────────────────────────
    meses = pd.date_range("2006-01-01", pd.Timestamp.today(), freq="MS")
    resultados = []

    for t in meses:
        t_end = t + pd.DateOffset(years=2)

        # Flujos dentro de la ventana [t, t+24m] de bonos activos en t
        mask = (
            (flows["fecha"] >= t)
            & (flows["fecha"] < t_end)
            & (flows["activo_desde"] <= t)
            & (flows["activo_hasta"] >= t)
        )
        sub = flows.loc[mask]

        row = {
            "fecha": t,
            "vencimientos_usd_2y_mm": round(sub["amort_mm_usd"].sum(), 1),
            "n_bonos_activos": sub["ticker"].nunique(),
        }

        # Por tipo de tasa
        for tt in tipos_tasa:
            col = f"venc_{tt}_mm"
            row[col] = round(sub.loc[sub["tipo_tasa"] == tt, "amort_mm_usd"].sum(), 1)

        # Por emisor
        for em in emisores:
            col = f"venc_{em}_mm"
            row[col] = round(sub.loc[sub["emisor"] == em, "amort_mm_usd"].sum(), 1)

        resultados.append(row)

    df = pd.DataFrame(resultados).set_index("fecha")

    # ── Guardar ───────────────────────────────────────────────────────────
    output_path = os.path.join(BONOS_DIR, "vencimientos_usd_2y_forward.csv")
    df.to_csv(output_path)

    print(f"\nSerie guardada: {output_path}")
    print(f"  Periodo : {df.index.min().date()} al {df.index.max().date()}")
    print(f"  Obs.    : {len(df)}")

    # ── Resumen de columnas ───────────────────────────────────────────────
    print(f"\nColumnas generadas:")
    for c in df.columns:
        print(f"  {c}")

    print(f"\nÚltimos 12 meses:")
    pd.set_option("display.float_format", "{:,.1f}".format)
    pd.set_option("display.max_columns", 20)
    pd.set_option("display.width", 160)
    print(df.tail(12).to_string())

    print(f"\nEstadísticas descriptivas (total):")
    print(df["vencimientos_usd_2y_mm"].describe().round(1).to_string())


if __name__ == "__main__":
    main()
