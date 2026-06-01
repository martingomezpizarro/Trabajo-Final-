"""
Gráficos de validación para Resultado Fiscal Estructural.
Genera Fig5_replicada.png para inspeccionar visualmente el output.
"""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "Variables Finales" / "resultado_fiscal_estructural.csv"
OUT = ROOT / "outputs" / "graficos"
OUT.mkdir(parents=True, exist_ok=True)


def main():
    df = pd.read_csv(DATA, parse_dates=["fecha"], index_col="fecha")

    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

    # 1. Superávit primario observado vs estructural
    ax = axes[0]
    ax.plot(df.index, df["SP_oficial_pctPIB"], label="SP oficial (MECON)", color="black", linewidth=1.5)
    ax.plot(df.index, df["SCA_pctPIB"], label="SCA (cíclicamente ajustado)", color="tab:blue", linestyle="--")
    ax.plot(df.index, df["SE_pctPIB"], label="SE (estructural, ajuste TI)", color="tab:red")
    ax.axhline(0, color="grey", linewidth=0.5)
    ax.set_title("Resultado Fiscal Estructural — Argentina 2006Q1-2025Q4")
    ax.set_ylabel("% del PIB nominal")
    ax.legend(loc="lower left", fontsize=9)
    ax.grid(alpha=0.3)

    # 2. Brecha del producto
    ax = axes[1]
    colors = ["tab:green" if v >= 0 else "tab:orange" for v in df["GAP"]]
    ax.bar(df.index, df["GAP"] * 100, color=colors, width=80, alpha=0.7)
    ax.axhline(0, color="grey", linewidth=0.5)
    ax.set_title("Brecha del Producto (GAP = (Y-Y*)/Y*)")
    ax.set_ylabel("%")
    ax.grid(alpha=0.3)

    # 3. TI vs TI*
    ax = axes[2]
    ax.plot(df.index, df["TI"], label="TI (observado)", color="tab:purple")
    ax.plot(df.index, df["TI_star"], label="TI* (largo plazo, MA10y centrado)", color="tab:brown", linestyle="--")
    ax.set_title("Términos de Intercambio — observado vs largo plazo")
    ax.set_ylabel("Índice base 2004=100")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    plt.tight_layout()
    out_path = OUT / "resultado_fiscal_estructural.png"
    plt.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"[OK] Guardado: {out_path.relative_to(ROOT)}")

    # Tabla anual para inspección
    annual = df[["SP_oficial_pctPIB", "SP_pctPIB", "SCA_pctPIB", "SE_pctPIB", "GAP"]].resample("YE").mean()
    annual["GAP_pct"] = annual["GAP"] * 100
    annual_path = OUT / "tabla_anual_se.csv"
    annual[["SP_oficial_pctPIB", "SP_pctPIB", "SCA_pctPIB", "SE_pctPIB", "GAP_pct"]].round(2).to_csv(annual_path)
    print(f"[OK] Guardado: {annual_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
