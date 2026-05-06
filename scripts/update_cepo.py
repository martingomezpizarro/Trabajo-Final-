import pandas as pd

csv_path = r"c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\processed\dummy_cepo.csv"

print(f"Cargando {csv_path}...")
df = pd.read_csv(csv_path)
df['fecha'] = pd.to_datetime(df['fecha'])

# Definir fechas críticas
fecha_inicio_extension = pd.to_datetime("2024-12-16")
fecha_salida_nueva = pd.to_datetime("2025-04-13")

print(f"Extendiendo cepo desde {fecha_inicio_extension.date()} hasta antes de {fecha_salida_nueva.date()}...")

# 1. Extender el cepo (valor 1) para el periodo solicitado
df.loc[(df['fecha'] >= fecha_inicio_extension) & (df['fecha'] < fecha_salida_nueva), 'dummy_cepo'] = 1

# 2. Asegurar que a partir de la nueva fecha de salida sea 0
df.loc[df['fecha'] >= fecha_salida_nueva, 'dummy_cepo'] = 0

# Guardar cambios
print("Guardando cambios...")
df.to_csv(csv_path, index=False)

print("Verificando resultados...")
# Mostrar filas alrededor del 16-12-2024
print("\nAlrededor del 16-12-2024 (debería ser 1):")
print(df[(df['fecha'] >= "2024-12-12") & (df['fecha'] <= "2024-12-20")])

# Mostrar filas alrededor del 13-04-2025
print("\nAlrededor del 13-04-2025 (debería cambiar de 1 a 0):")
print(df[(df['fecha'] >= "2025-04-10") & (df['fecha'] <= "2025-04-16")])
