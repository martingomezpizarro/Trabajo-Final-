"""
02_catalogo_bonos_usd.py — Catálogo maestro de bonos soberanos argentinos en USD
con cronogramas de amortización e intereses.

Cubre 3 eras:
  1. Post-restructuración 2005/2010 (Discount, Par, GDP Warrants)
  2. Emisiones 2016-2019 (nuevos Bonares y Globales post-holdout settlement)
  3. Post-restructuración 2020 (AL/GD Step-Up bonds)

Ejecutar: python data/bonos/02_catalogo_bonos_usd.py
"""
import pandas as pd
import numpy as np
from datetime import datetime
import os
import json

BONOS_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# CATÁLOGO DE BONOS — ESTRUCTURA
# ============================================================
# Cada bono tiene:
#   ticker: identificador corto
#   nombre: nombre completo
#   moneda: USD
#   fecha_emision: datetime
#   fecha_vencimiento: datetime
#   cupon_pct: tasa de cupón anual (puede ser step-up)
#   frecuencia_cupon: 'S' (semestral), 'A' (anual)
#   monto_original_mm_usd: monto emitido en millones de USD
#   amortizacion: lista de (fecha, pct_del_original) — cuotas de devolución de capital
#   era: '2005_restr', '2016_2019', '2020_restr'
#   activo_desde: fecha desde la que el bono existe
#   activo_hasta: fecha hasta la que el bono vence (o se reestructura)
#   notas: texto libre

bonos_catalogo = []

# ============================================================
# ERA 1: POST-RESTRUCTURACIÓN 2005/2010
# ============================================================

# --- Discount Bond (Ley NY - DICY) ---
# Emitido en canje 2005. Cupón step-up. Amortización bullet con amortizaciones parciales.
# Monto total emitido en la restructuración 2005+2010: ~USD 11,500 MM aprox (entre ambas leyes)
bonos_catalogo.append({
    'ticker': 'DICY',
    'nombre': 'Discount Bond USD (Ley NY)',
    'moneda': 'USD',
    'fecha_emision': '2005-06-02',
    'fecha_vencimiento': '2033-12-31',
    'cupon_info': 'Step-up: 3.97%(2005-08), 5.77%(2009-13), 8.28%(2014+)',
    'frecuencia_cupon': 'S',  # semestral (30 jun, 31 dic)
    'monto_original_mm_usd': 7700,  # aprox Ley NY
    'amortizacion_tipo': '20 cuotas semestrales iguales a partir de jun 2024',
    'amortizacion_inicio': '2024-06-30',
    'amortizacion_fin': '2033-12-31',
    'amortizacion_cuotas': 20,
    'era': '2005_restr',
    'activo_desde': '2005-06-02',
    'activo_hasta': '2020-09-04',  # Canjeado en restructuración 2020
    'notas': 'Canjeado por bonos GD/AL en sept 2020. 66.137% haircut sobre face value original.'
})

bonos_catalogo.append({
    'ticker': 'DICA',
    'nombre': 'Discount Bond USD (Ley Argentina)',
    'moneda': 'USD',
    'fecha_emision': '2005-06-02',
    'fecha_vencimiento': '2033-12-31',
    'cupon_info': 'Step-up: 3.97%(2005-08), 5.77%(2009-13), 8.28%(2014+)',
    'frecuencia_cupon': 'S',
    'monto_original_mm_usd': 3800,  # aprox Ley Arg
    'amortizacion_tipo': '20 cuotas semestrales iguales a partir de jun 2024',
    'amortizacion_inicio': '2024-06-30',
    'amortizacion_fin': '2033-12-31',
    'amortizacion_cuotas': 20,
    'era': '2005_restr',
    'activo_desde': '2005-06-02',
    'activo_hasta': '2020-09-04',
    'notas': 'Canjeado por bonos AL en sept 2020.'
})

# --- Par Bond (Ley NY - PARY) ---
bonos_catalogo.append({
    'ticker': 'PARY',
    'nombre': 'Par Bond USD (Ley NY)',
    'moneda': 'USD',
    'fecha_emision': '2005-06-02',
    'fecha_vencimiento': '2038-12-31',
    'cupon_info': 'Step-up gradual de 1.33% a 5.25%',
    'frecuencia_cupon': 'S',
    'monto_original_mm_usd': 8300,  # aprox ambas leyes juntas, pero este es NY
    'amortizacion_tipo': '20 cuotas semestrales iguales a partir de sept 2029',
    'amortizacion_inicio': '2029-09-30',
    'amortizacion_fin': '2038-12-31',
    'amortizacion_cuotas': 20,
    'era': '2005_restr',
    'activo_desde': '2005-06-02',
    'activo_hasta': '2020-09-04',
    'notas': 'Sin haircut sobre face value. Canjeado en 2020.'
})

bonos_catalogo.append({
    'ticker': 'PARA',
    'nombre': 'Par Bond USD (Ley Argentina)',
    'moneda': 'USD',
    'fecha_emision': '2005-06-02',
    'fecha_vencimiento': '2038-12-31',
    'cupon_info': 'Step-up gradual de 1.33% a 5.25%',
    'frecuencia_cupon': 'S',
    'monto_original_mm_usd': 4800,
    'amortizacion_tipo': '20 cuotas semestrales iguales a partir de sept 2029',
    'amortizacion_inicio': '2029-09-30',
    'amortizacion_fin': '2038-12-31',
    'amortizacion_cuotas': 20,
    'era': '2005_restr',
    'activo_desde': '2005-06-02',
    'activo_hasta': '2020-09-04',
    'notas': 'Sin haircut. Canjeado en 2020.'
})

# --- Cupones PBI / GDP Warrants (TVPY / TVPA) ---
# Derivados emitidos en el canje 2005. Pagaban si el PBI real crecía por encima
# de un umbral. Generaron pagos significativos en USD 2006-2012.
# Pagos anuales el 15 de diciembre.
# Pagos acumulados estimados: ~USD 10,000 MM total entre 2006-2012
# El warrant dejó de triggear después de 2012 por la revisión del PBI base.
GDP_WARRANT_PAGOS = [
    (2006, 0),      # No triggerea aún
    (2007, 500),    # Primer pago
    (2008, 1200),   # Crecimiento fuerte
    (2009, 0),      # Recesión, no paga
    (2010, 2000),   # Rebote post-crisis
    (2011, 2500),   # Pico de pagos
    (2012, 1500),   # Último pago significativo
]
for yr, pago in GDP_WARRANT_PAGOS:
    if pago > 0:
        bonos_catalogo.append({
            'ticker': f'TVPY_{yr}',
            'nombre': f'GDP Warrant - Pago {yr}',
            'moneda': 'USD',
            'fecha_emision': '2005-06-02',
            'fecha_vencimiento': f'{yr}-12-15',
            'cupon_info': 'Pago contingente atado al crecimiento del PBI',
            'frecuencia_cupon': 'A',
            'monto_original_mm_usd': pago,
            'amortizacion_detalle': [(f'{yr}-12-15', 100.0)],
            'era': 'gdp_warrants',
            'activo_desde': f'{yr}-01-01',
            'activo_hasta': f'{yr}-12-15',
            'notas': f'Pago estimado del GDP Warrant en {yr}. TVPY (NY) + TVPA (AR) combinados.'
        })

# ============================================================
# ERA 0: BODEN — BONOS POST-CRISIS 2001
# ============================================================
# Los BODEN fueron la columna vertebral de la deuda argentina 2002-2015.
# Se usaron para compensar el corralón y la pesificación asimétrica.

# --- BODEN 2012 (RG12) ---
# El bono más importante de la poscrisis. 
# Pagado completamente en agosto 2012.
bonos_catalogo.append({
    'ticker': 'RG12',
    'nombre': 'BODEN 2012 (7% USD)',
    'moneda': 'USD',
    'fecha_emision': '2002-02-03',
    'fecha_vencimiento': '2012-08-03',
    'cupon_info': '7% anual',
    'frecuencia_cupon': 'S',
    'monto_original_mm_usd': 2000,
    'amortizacion_tipo': '10 cuotas semestrales iguales a partir de ago 2008',
    'amortizacion_inicio': '2008-02-03',
    'amortizacion_fin': '2012-08-03',
    'amortizacion_cuotas': 10,
    'era': 'boden',
    'activo_desde': '2002-02-03',
    'activo_hasta': '2012-08-03',
    'notas': 'Compensación corralón. Pagado en su totalidad ago-2012.'
})

# --- BODEN 2015 (RO15) ---
# Muy utilizado en el mercado minorista y para operaciones de dólar MEP.
bonos_catalogo.append({
    'ticker': 'RO15',
    'nombre': 'BODEN 2015 (7% USD)',
    'moneda': 'USD',
    'fecha_emision': '2005-04-03',
    'fecha_vencimiento': '2015-10-03',
    'cupon_info': '7% anual',
    'frecuencia_cupon': 'S',
    'monto_original_mm_usd': 6300,
    'amortizacion_tipo': 'Bullet',
    'amortizacion_inicio': '2015-10-03',
    'amortizacion_fin': '2015-10-03',
    'amortizacion_cuotas': 1,
    'era': 'boden',
    'activo_desde': '2005-04-03',
    'activo_hasta': '2015-10-03',
    'notas': 'Pagado en su totalidad oct-2015. Referencia del dólar MEP original.'
})

# --- Global 2017 / BODEN 2017 ---
# Emitido en el canje 2005 para compensar a ciertos acreedores
bonos_catalogo.append({
    'ticker': 'GJ17',
    'nombre': 'Global 2017 (7% USD)',
    'moneda': 'USD',
    'fecha_emision': '2005-06-02',
    'fecha_vencimiento': '2017-04-17',
    'cupon_info': '7% anual',
    'frecuencia_cupon': 'S',
    'monto_original_mm_usd': 3500,
    'amortizacion_tipo': 'Bullet',
    'amortizacion_inicio': '2017-04-17',
    'amortizacion_fin': '2017-04-17',
    'amortizacion_cuotas': 1,
    'era': '2005_restr',
    'activo_desde': '2005-06-02',
    'activo_hasta': '2017-04-17',
    'notas': 'Del canje 2005. Pagado normalmente a vencimiento abr-2017.'
})

# ============================================================
# ACUERDOS BILATERALES Y MULTILATERALES
# ============================================================

# --- Club de París (Acuerdo 2014) ---
# Acuerdo de mayo 2014 para regularizar ~USD 9,700 MM de deuda vieja.
# Pago en cuotas: pagos semestrales de may 2014 a may 2019 (aprox).
club_paris_pagos = [
    ('2014-07-15', 1150),   # Pago inicial
    ('2015-01-15', 600),    ('2015-07-15', 600),
    ('2016-01-15', 750),    ('2016-07-15', 750),
    ('2017-01-15', 1200),   ('2017-07-15', 1200),
    ('2018-01-15', 1000),   ('2018-07-15', 1000),
    ('2019-01-15', 725),    ('2019-07-15', 725),
]
for fecha, monto in club_paris_pagos:
    bonos_catalogo.append({
        'ticker': f'CLUB_PARIS_{fecha[:4]}_{fecha[5:7]}',
        'nombre': f'Club de París - Cuota {fecha}',
        'moneda': 'USD',
        'fecha_emision': '2014-05-29',
        'fecha_vencimiento': fecha,
        'cupon_info': '3% + intereses compensatorios',
        'frecuencia_cupon': 'S',
        'monto_original_mm_usd': monto,
        'amortizacion_detalle': [(fecha, 100.0)],
        'era': 'club_paris',
        'activo_desde': '2014-05-29',
        'activo_hasta': fecha,
        'notas': f'Acuerdo Club de París mayo 2014. ~USD 9,700 MM total restructurado.'
    })

# ============================================================
# FMI — FONDO MONETARIO INTERNACIONAL
# ============================================================

# --- FMI Stand-By 2018 (SBA) ---
# Aprobado junio 2018. Total acordado: ~USD 57,000 MM (el más grande en la historia del FMI).
# Desembolsados efectivamente: ~USD 44,000 MM.
# Cancelado julio 2020. Refinanciado en EFF 2022 y luego en EFF 2025.
# Repagos originales del SBA 2018 empezaban en 2021.
# Bajo el EFF 2022 se extendieron los plazos.
# Los pagos efectivos de capital al FMI por el legado del SBA 2018:
FMI_2018_REPAGOS = [
    # Pagos trimestrales de capital (repurchases) al FMI
    # Estos son los pagos que Argentina efectivamente realizó o debe realizar.
    # Fuente: IMF Financial Statements, OPC
    ('2021-09-22', 1880),  # Primer repago de capital
    ('2021-12-22', 1880),
    ('2022-03-22', 2800),
    ('2022-06-22', 2800),  # A partir de aquí se refinancia con EFF 2022
    # Post-EFF 2022, los pagos se reestructuraron con plazos más largos
    # El grueso del repago se movió a 2026-2032
    ('2026-09-15', 583),   ('2026-12-15', 250),
    ('2027-03-15', 1500),  ('2027-06-15', 1500),
    ('2027-09-15', 1500),  ('2027-12-15', 1500),
    ('2028-03-15', 2000),  ('2028-06-15', 2000),
    ('2028-09-15', 2000),  ('2028-12-15', 2000),
    ('2029-03-15', 2500),  ('2029-06-15', 2500),
    ('2029-09-15', 2500),  ('2029-12-15', 2500),
    ('2030-03-15', 2000),  ('2030-06-15', 2000),
    ('2030-09-15', 1500),  ('2030-12-15', 1500),
    ('2031-03-15', 1000),  ('2031-06-15', 1000),
    ('2031-09-15', 500),   ('2031-12-15', 500),
]
for fecha, monto in FMI_2018_REPAGOS:
    bonos_catalogo.append({
        'ticker': f'FMI_SBA18_{fecha[:4]}_{fecha[5:7]}',
        'nombre': f'FMI SBA 2018 - Repago {fecha}',
        'moneda': 'USD',
        'fecha_emision': '2018-06-20',
        'fecha_vencimiento': fecha,
        'cupon_info': 'Tasa SDR + sobretasa (~4-5% efectivo)',
        'frecuencia_cupon': 'T',  # Trimestral
        'monto_original_mm_usd': monto,
        'amortizacion_detalle': [(fecha, 100.0)],
        'era': 'fmi',
        'activo_desde': '2018-06-20',
        'activo_hasta': fecha,
        'notas': f'Repago de capital al FMI (SBA 2018 → refinanciado EFF 2022). USD {monto} MM.'
    })

# --- FMI EFF 2025 (Facilidades Extendidas) ---
# Aprobado abril 2025. Total: USD 20,000 MM.
# Desembolso inicial: USD 12,000 MM (abril 2025).
# Revisiones trimestrales con desembolsos adicionales.
# Plazo de repago: 10 años desde cada desembolso.
# Gracia: 4.5 años para capital.
# Los repagos empiezan en ~2029-2030 y van hasta 2035.
FMI_2025_REPAGOS = [
    # El grueso del capital se devuelve 2030-2035
    # USD 20,000 MM distribuidos en ~20 cuotas semestrales
    ('2030-01-15', 1000),  ('2030-07-15', 1000),
    ('2031-01-15', 1500),  ('2031-07-15', 1500),
    ('2032-01-15', 2000),  ('2032-07-15', 2000),
    ('2033-01-15', 2000),  ('2033-07-15', 2000),
    ('2034-01-15', 2000),  ('2034-07-15', 2000),
    ('2035-01-15', 1500),  ('2035-07-15', 1500),
]
for fecha, monto in FMI_2025_REPAGOS:
    bonos_catalogo.append({
        'ticker': f'FMI_EFF25_{fecha[:4]}_{fecha[5:7]}',
        'nombre': f'FMI EFF 2025 - Repago {fecha}',
        'moneda': 'USD',
        'fecha_emision': '2025-04-11',
        'fecha_vencimiento': fecha,
        'cupon_info': 'Tasa SDR + sobretasa',
        'frecuencia_cupon': 'S',
        'monto_original_mm_usd': monto,
        'amortizacion_detalle': [(fecha, 100.0)],
        'era': 'fmi',
        'activo_desde': '2025-04-11',
        'activo_hasta': fecha,
        'notas': f'Repago de capital al FMI (EFF 2025, USD 20,000 MM total). Gracia 4.5 años.'
    })

# ============================================================
# ERA 2: EMISIONES POST-HOLDOUT SETTLEMENT (2016–2019)
# ============================================================

# --- Bonar 2020 (AO20) ---
bonos_catalogo.append({
    'ticker': 'AO20',
    'nombre': 'Bonar 2020 (8.0%)',
    'moneda': 'USD',
    'fecha_emision': '2016-10-18',
    'fecha_vencimiento': '2020-10-18',
    'cupon_info': '8.0% anual',
    'frecuencia_cupon': 'S',
    'monto_original_mm_usd': 2750,
    'amortizacion_tipo': 'Bullet (100% al vencimiento)',
    'amortizacion_inicio': '2020-10-18',
    'amortizacion_fin': '2020-10-18',
    'amortizacion_cuotas': 1,
    'era': '2016_2019',
    'activo_desde': '2016-10-18',
    'activo_hasta': '2020-09-04',  # Canjeado en restructuración 2020
    'notas': 'Canjeado parcialmente en restructuración 2020.'
})

# --- Bonar 2024 (AY24) ---
bonos_catalogo.append({
    'ticker': 'AY24',
    'nombre': 'Bonar 2024 (8.75%)',
    'moneda': 'USD',
    'fecha_emision': '2017-05-11',
    'fecha_vencimiento': '2024-05-07',
    'cupon_info': '8.75% anual',
    'frecuencia_cupon': 'S',
    'monto_original_mm_usd': 3250,
    'amortizacion_tipo': 'Bullet',
    'amortizacion_inicio': '2024-05-07',
    'amortizacion_fin': '2024-05-07',
    'amortizacion_cuotas': 1,
    'era': '2016_2019',
    'activo_desde': '2017-05-11',
    'activo_hasta': '2020-09-04',
    'notas': 'Canjeado en restructuración 2020.'
})

# --- Argentina Century Bond 2117 (AC17) ---
bonos_catalogo.append({
    'ticker': 'AC17',
    'nombre': 'Century Bond 2117 (7.125%)',
    'moneda': 'USD',
    'fecha_emision': '2017-06-22',
    'fecha_vencimiento': '2117-07-06',
    'cupon_info': '7.125% anual',
    'frecuencia_cupon': 'S',
    'monto_original_mm_usd': 2750,
    'amortizacion_tipo': 'Bullet (100 años)',
    'amortizacion_inicio': '2117-07-06',
    'amortizacion_fin': '2117-07-06',
    'amortizacion_cuotas': 1,
    'era': '2016_2019',
    'activo_desde': '2017-06-22',
    'activo_hasta': '2020-09-04',
    'notas': 'El famoso bono a 100 años. Canjeado en 2020.'
})

# --- Global 2027 (A2E7 / GJ17) ---
bonos_catalogo.append({
    'ticker': 'A2E7',
    'nombre': 'Global 2027 (6.875%)',
    'moneda': 'USD',
    'fecha_emision': '2017-01-26',
    'fecha_vencimiento': '2027-01-26',
    'cupon_info': '6.875% anual',
    'frecuencia_cupon': 'S',
    'monto_original_mm_usd': 4500,
    'amortizacion_tipo': 'Bullet',
    'amortizacion_inicio': '2027-01-26',
    'amortizacion_fin': '2027-01-26',
    'amortizacion_cuotas': 1,
    'era': '2016_2019',
    'activo_desde': '2017-01-26',
    'activo_hasta': '2020-09-04',
    'notas': 'Canjeado en restructuración 2020.'
})

# --- Bonar 2025 (AA25) ---
bonos_catalogo.append({
    'ticker': 'AA25',
    'nombre': 'Bonar 2025 (5.625%)',
    'moneda': 'USD',
    'fecha_emision': '2016-04-22',
    'fecha_vencimiento': '2025-04-22',
    'cupon_info': '5.625% anual',
    'frecuencia_cupon': 'S',
    'monto_original_mm_usd': 1415,
    'amortizacion_tipo': 'Bullet',
    'amortizacion_inicio': '2025-04-22',
    'amortizacion_fin': '2025-04-22',
    'amortizacion_cuotas': 1,
    'era': '2016_2019',
    'activo_desde': '2016-04-22',
    'activo_hasta': '2020-09-04',
    'notas': 'Canjeado en restructuración 2020.'
})

# --- BONAR 2019 (AN19) — Pago Holdouts ---
bonos_catalogo.append({
    'ticker': 'AN19',
    'nombre': 'BONAR 2019 (6.875%) — Pago Holdouts',
    'moneda': 'USD',
    'fecha_emision': '2016-04-22',
    'fecha_vencimiento': '2019-04-18',
    'cupon_info': '6.875% anual',
    'frecuencia_cupon': 'S',
    'monto_original_mm_usd': 2750,
    'amortizacion_tipo': 'Bullet',
    'amortizacion_inicio': '2019-04-18',
    'amortizacion_fin': '2019-04-18',
    'amortizacion_cuotas': 1,
    'era': '2016_2019',
    'activo_desde': '2016-04-22',
    'activo_hasta': '2019-04-18',
    'notas': 'Emitido para pagar a fondos buitre (holdouts). Pagado a vencimiento.'
})

# --- Global 2021 (AA21) ---
bonos_catalogo.append({
    'ticker': 'AA21',
    'nombre': 'Global 2021 (6.875%)',
    'moneda': 'USD',
    'fecha_emision': '2016-04-22',
    'fecha_vencimiento': '2021-04-18',
    'cupon_info': '6.875% anual',
    'frecuencia_cupon': 'S',
    'monto_original_mm_usd': 2750,
    'amortizacion_tipo': 'Bullet',
    'amortizacion_inicio': '2021-04-18',
    'amortizacion_fin': '2021-04-18',
    'amortizacion_cuotas': 1,
    'era': '2016_2019',
    'activo_desde': '2016-04-22',
    'activo_hasta': '2020-09-04',
    'notas': 'Canjeado en restructuración 2020.'
})

# --- Global 2022 (AA22) ---
bonos_catalogo.append({
    'ticker': 'AA22',
    'nombre': 'Global 2022 (5.875%)',
    'moneda': 'USD',
    'fecha_emision': '2017-01-26',
    'fecha_vencimiento': '2022-01-11',
    'cupon_info': '5.875% anual',
    'frecuencia_cupon': 'S',
    'monto_original_mm_usd': 3250,
    'amortizacion_tipo': 'Bullet',
    'amortizacion_inicio': '2022-01-11',
    'amortizacion_fin': '2022-01-11',
    'amortizacion_cuotas': 1,
    'era': '2016_2019',
    'activo_desde': '2017-01-26',
    'activo_hasta': '2020-09-04',
    'notas': 'Canjeado en restructuración 2020.'
})

# --- Global 2023 (AA23) ---
bonos_catalogo.append({
    'ticker': 'AA23',
    'nombre': 'Global 2023 (7.50%)',
    'moneda': 'USD',
    'fecha_emision': '2018-06-28',
    'fecha_vencimiento': '2023-12-28',
    'cupon_info': '7.50% anual',
    'frecuencia_cupon': 'S',
    'monto_original_mm_usd': 1500,
    'amortizacion_tipo': 'Bullet',
    'amortizacion_inicio': '2023-12-28',
    'amortizacion_fin': '2023-12-28',
    'amortizacion_cuotas': 1,
    'era': '2016_2019',
    'activo_desde': '2018-06-28',
    'activo_hasta': '2020-09-04',
    'notas': 'Canjeado en restructuración 2020.'
})

# --- Global 2036 (AA36) ---
bonos_catalogo.append({
    'ticker': 'AA36',
    'nombre': 'Global 2036 (7.125%)',
    'moneda': 'USD',
    'fecha_emision': '2017-07-06',
    'fecha_vencimiento': '2036-07-06',
    'cupon_info': '7.125% anual',
    'frecuencia_cupon': 'S',
    'monto_original_mm_usd': 2500,
    'amortizacion_tipo': 'Bullet',
    'amortizacion_inicio': '2036-07-06',
    'amortizacion_fin': '2036-07-06',
    'amortizacion_cuotas': 1,
    'era': '2016_2019',
    'activo_desde': '2017-07-06',
    'activo_hasta': '2020-09-04',
    'notas': 'Canjeado en restructuración 2020.'
})

# --- Global 2046 (AA46) — NO confundir con GD46 del canje 2020 ---
bonos_catalogo.append({
    'ticker': 'AA46',
    'nombre': 'Global 2046 (7.625%) — Era Macri',
    'moneda': 'USD',
    'fecha_emision': '2016-04-22',
    'fecha_vencimiento': '2046-04-22',
    'cupon_info': '7.625% anual',
    'frecuencia_cupon': 'S',
    'monto_original_mm_usd': 6500,
    'amortizacion_tipo': 'Bullet',
    'amortizacion_inicio': '2046-04-22',
    'amortizacion_fin': '2046-04-22',
    'amortizacion_cuotas': 1,
    'era': '2016_2019',
    'activo_desde': '2016-04-22',
    'activo_hasta': '2020-09-04',
    'notas': 'NO confundir con GD46 (canje 2020). Canjeado en 2020.'
})

# --- Global 2048 (AA48) ---
bonos_catalogo.append({
    'ticker': 'AA48',
    'nombre': 'Global 2048 (6.875%)',
    'moneda': 'USD',
    'fecha_emision': '2018-01-11',
    'fecha_vencimiento': '2048-01-11',
    'cupon_info': '6.875% anual',
    'frecuencia_cupon': 'S',
    'monto_original_mm_usd': 1750,
    'amortizacion_tipo': 'Bullet',
    'amortizacion_inicio': '2048-01-11',
    'amortizacion_fin': '2048-01-11',
    'amortizacion_cuotas': 1,
    'era': '2016_2019',
    'activo_desde': '2018-01-11',
    'activo_hasta': '2020-09-04',
    'notas': 'Canjeado en restructuración 2020.'
})

# ============================================================
# ERA 3: POST-RESTRUCTURACIÓN 2020 (BONOS STEP-UP)
# ============================================================
# Emitidos el 4 de septiembre de 2020.
# Pagan intereses semestrales el 9-ene y 9-jul.
# El cupón va aumentando (step-up).
# Amortización en múltiples cuotas.

# --- GD29 / AL29 ---
gd29_amort = [
    # (fecha, pct_del_residual_original)
    ('2025-07-09', 4.0), ('2026-01-09', 4.0), ('2026-07-09', 8.0),
    ('2027-01-09', 8.0), ('2027-07-09', 16.0), ('2028-01-09', 16.0),
    ('2028-07-09', 16.0), ('2029-01-09', 16.0), ('2029-07-09', 12.0),
]
for ticker, ley, monto in [('GD29','NY',4450), ('AL29','AR',1600)]:
    bonos_catalogo.append({
        'ticker': ticker,
        'nombre': f'Step-Up 2029 (Ley {"NY" if ley=="NY" else "Argentina"})',
        'moneda': 'USD',
        'fecha_emision': '2020-09-04',
        'fecha_vencimiento': '2029-07-09',
        'cupon_info': 'Step-up: 0.125%(2020-21), 1%(2021-23), 2.5%(2023-24), 3.5%(2024-25), 4.5%(2025-26), 4.75%(2026-27), 5%(2027-28), 1%(2028-29)',
        'frecuencia_cupon': 'S',
        'monto_original_mm_usd': monto,
        'amortizacion_detalle': gd29_amort,
        'era': '2020_restr',
        'activo_desde': '2020-09-04',
        'activo_hasta': '2029-07-09',
        'notas': f'Ley {ley}. Primer pago de capital jul 2025.'
    })

# --- GD30 / AL30 ---
gd30_amort = [
    ('2024-07-09', 0.4), ('2025-01-09', 0.8), ('2025-07-09', 0.8),
    ('2026-01-09', 4.0), ('2026-07-09', 4.0), ('2027-01-09', 8.0),
    ('2027-07-09', 8.0), ('2028-01-09', 12.0), ('2028-07-09', 12.0),
    ('2029-01-09', 12.0), ('2029-07-09', 12.0), ('2030-01-09', 12.0),
    ('2030-07-09', 14.0),
]
for ticker, ley, monto in [('GD30','NY',8850), ('AL30','AR',3200)]:
    bonos_catalogo.append({
        'ticker': ticker,
        'nombre': f'Step-Up 2030 (Ley {"NY" if ley=="NY" else "Argentina"})',
        'moneda': 'USD',
        'fecha_emision': '2020-09-04',
        'fecha_vencimiento': '2030-07-09',
        'cupon_info': 'Step-up: 0.125%(2020-21), 0.5%(2021-23), 1.75%(2023-24), 2.5%(2024-26), 3.875%(2026-28), 5%(2028-29), 0.75%(2029-30)',
        'frecuencia_cupon': 'S',
        'monto_original_mm_usd': monto,
        'amortizacion_detalle': gd30_amort,
        'era': '2020_restr',
        'activo_desde': '2020-09-04',
        'activo_hasta': '2030-07-09',
        'notas': f'Ley {ley}. El bono más líquido de referencia.'
    })

# --- GD35 / AL35 ---
gd35_amort = [
    ('2031-01-09', 5.0), ('2031-07-09', 5.0), ('2032-01-09', 5.0),
    ('2032-07-09', 5.0), ('2033-01-09', 10.0), ('2033-07-09', 10.0),
    ('2034-01-09', 10.0), ('2034-07-09', 10.0), ('2035-01-09', 20.0),
    ('2035-07-09', 20.0),
]
for ticker, ley, monto in [('GD35','NY',4200), ('AL35','AR',2800)]:
    bonos_catalogo.append({
        'ticker': ticker,
        'nombre': f'Step-Up 2035 (Ley {"NY" if ley=="NY" else "Argentina"})',
        'moneda': 'USD',
        'fecha_emision': '2020-09-04',
        'fecha_vencimiento': '2035-07-09',
        'cupon_info': 'Step-up: 0.125%(2020-23), 3.625%(2023-25), 4.125%(2025-30), 4.75%(2030-32), 5%(2032-35)',
        'frecuencia_cupon': 'S',
        'monto_original_mm_usd': monto,
        'amortizacion_detalle': gd35_amort,
        'era': '2020_restr',
        'activo_desde': '2020-09-04',
        'activo_hasta': '2035-07-09',
        'notas': f'Ley {ley}.'
    })

# --- GD38 ---
gd38_amort = [
    ('2031-01-09', 5.0), ('2031-07-09', 5.0), ('2032-01-09', 5.0),
    ('2032-07-09', 5.0), ('2033-01-09', 5.0), ('2033-07-09', 5.0),
    ('2034-01-09', 5.0), ('2034-07-09', 5.0), ('2035-01-09', 5.0),
    ('2035-07-09', 5.0), ('2036-01-09', 5.0), ('2036-07-09', 5.0),
    ('2037-01-09', 10.0), ('2037-07-09', 10.0),
    ('2038-01-09', 10.0), ('2038-07-09', 10.0),
]
bonos_catalogo.append({
    'ticker': 'GD38',
    'nombre': 'Step-Up 2038 (Ley NY)',
    'moneda': 'USD',
    'fecha_emision': '2020-09-04',
    'fecha_vencimiento': '2038-07-09',
    'cupon_info': 'Step-up: 0.125%(2020-23), 3.5%(2023-25), 4.875%(2025-30), 5%(2030-35), 5.25%(2035-38)',
    'frecuencia_cupon': 'S',
    'monto_original_mm_usd': 3200,
    'amortizacion_detalle': gd38_amort,
    'era': '2020_restr',
    'activo_desde': '2020-09-04',
    'activo_hasta': '2038-07-09',
    'notas': 'Solo Ley NY.'
})

# --- GD41 / AL41 ---
gd41_amort = [
    ('2033-01-09', 4.55), ('2033-07-09', 4.55), ('2034-01-09', 4.55),
    ('2034-07-09', 4.55), ('2035-01-09', 4.55), ('2035-07-09', 4.55),
    ('2036-01-09', 4.55), ('2036-07-09', 4.55), ('2037-01-09', 4.55),
    ('2037-07-09', 4.55), ('2038-01-09', 4.55), ('2038-07-09', 4.55),
    ('2039-01-09', 4.55), ('2039-07-09', 4.55), ('2040-01-09', 4.55),
    ('2040-07-09', 4.55), ('2041-01-09', 4.55), ('2041-07-09', 4.55),
]
for ticker, ley, monto in [('GD41','NY',5000), ('AL41','AR',1600)]:
    bonos_catalogo.append({
        'ticker': ticker,
        'nombre': f'Step-Up 2041 (Ley {"NY" if ley=="NY" else "Argentina"})',
        'moneda': 'USD',
        'fecha_emision': '2020-09-04',
        'fecha_vencimiento': '2041-07-09',
        'cupon_info': 'Step-up: 0.125%(2020-23), 1%(2023), 1.5%(2024), 3.5%(2025-30), 4.875%(2030-33), 5%(2033-38), 5.25%(2038-41)',
        'frecuencia_cupon': 'S',
        'monto_original_mm_usd': monto,
        'amortizacion_detalle': gd41_amort,
        'era': '2020_restr',
        'activo_desde': '2020-09-04',
        'activo_hasta': '2041-07-09',
        'notas': f'Ley {ley}.'
    })

# --- GD46 ---
gd46_amort = [
    # 40 cuotas semestrales iguales (2.5% c/u) desde ene 2028 hasta jul 2046
]
for i in range(40):
    yr = 2028 + i // 2
    month = 1 if i % 2 == 0 else 7
    gd46_amort.append((f'{yr}-{month:02d}-09', 2.5))

bonos_catalogo.append({
    'ticker': 'GD46',
    'nombre': 'Step-Up 2046 (Ley NY)',
    'moneda': 'USD',
    'fecha_emision': '2020-09-04',
    'fecha_vencimiento': '2046-07-09',
    'cupon_info': 'Step-up: 0.125%(2020-23), 1.0%(2023-28), 4.25%(2028-36), 4.875%(2036-41), 5.0%(2041-46)',
    'frecuencia_cupon': 'S',
    'monto_original_mm_usd': 2900,
    'amortizacion_detalle': gd46_amort,
    'era': '2020_restr',
    'activo_desde': '2020-09-04',
    'activo_hasta': '2046-07-09',
    'notas': 'Solo Ley NY. El de mayor plazo del canje 2020.'
})

# ============================================================
# ERA 2b: LETRAS DEL TESORO EN USD (LETES) — 2016–2019
# ============================================================
# Las LETES eran bonos zero-coupon de corto plazo (3, 6, 9, 12 meses)
# emitidos semanalmente. Es imposible modelar cada emisión individual.
# Se usa el STOCK OUTSTANDING promedio trimestral como proxy.
# Dado que son <12 meses, SIEMPRE caen dentro de la ventana forward de 2 años.
#
# Stock estimado (MM USD) por trimestre (fuente: Sec. Finanzas, OPC):
LETES_STOCK_TRIMESTRAL = {
    # Año 2016 — Inicio gradual
    '2016-Q2': 500,  '2016-Q3': 1500, '2016-Q4': 3000,
    # Año 2017 — Crecimiento fuerte
    '2017-Q1': 4000, '2017-Q2': 5500, '2017-Q3': 7000, '2017-Q4': 8500,
    # Año 2018 — Pico y colapso (crisis cambiaria)
    '2018-Q1': 10000, '2018-Q2': 12000, '2018-Q3': 8000, '2018-Q4': 5000,
    # Año 2019 — Reducción post-crisis y reperfilamiento
    '2019-Q1': 4000, '2019-Q2': 3500, '2019-Q3': 2000, '2019-Q4': 500,
    # A partir de 2020 ya no se emiten LETES USD
}

# Modelamos las LETES como un "bono rolling" trimestral que vence dentro del trimestre.
# Para cada trimestre con stock > 0, creamos una entrada que vence 6 meses después.
for quarter, stock in LETES_STOCK_TRIMESTRAL.items():
    yr = int(quarter.split('-')[0])
    q = int(quarter.split('-')[1][1])
    # Fecha inicio del trimestre
    month_start = (q - 1) * 3 + 1
    fecha_inicio = f'{yr}-{month_start:02d}-01'
    # Vencimiento promedio: 6 meses después (mix de 3-12 meses)
    m_end = month_start + 6
    yr_end = yr
    if m_end > 12:
        m_end -= 12
        yr_end += 1
    fecha_venc = f'{yr_end}-{m_end:02d}-15'
    
    bonos_catalogo.append({
        'ticker': f'LETES_{quarter}',
        'nombre': f'Letras del Tesoro USD (Stock {quarter})',
        'moneda': 'USD',
        'fecha_emision': fecha_inicio,
        'fecha_vencimiento': fecha_venc,
        'cupon_info': 'Zero-coupon (se emiten con descuento)',
        'frecuencia_cupon': 'N/A',
        'monto_original_mm_usd': stock,
        'amortizacion_detalle': [(fecha_venc, 100.0)],
        'era': 'letes_usd',
        'activo_desde': fecha_inicio,
        'activo_hasta': fecha_venc,
        'notas': f'Stock promedio de LETES USD durante {quarter}. Proxy aggregate rolling.'
    })

# ============================================================
# ERA 4: BOPREAL — BONOS DEL BCRA EN USD (2024+)
# ============================================================
# Emitidos por el BCRA (no el Tesoro) para regularizar deuda comercial.
# Denominados en USD, pagos en USD.

# --- BOPREAL Serie 1 (BPO27) ---
# Dividido en 4 sub-series (1A, 1B, 1C, 1D) a partir de mar 2024
# Monto total emitido: ~USD 5,000 MM
# Amortización: 2 cuotas iguales en abril y octubre 2027
bonos_catalogo.append({
    'ticker': 'BPO27',
    'nombre': 'BOPREAL Serie 1 (2027)',
    'moneda': 'USD',
    'fecha_emision': '2024-01-25',
    'fecha_vencimiento': '2027-10-31',
    'cupon_info': '5% anual',
    'frecuencia_cupon': 'S',
    'monto_original_mm_usd': 5000,
    'amortizacion_detalle': [
        ('2027-04-30', 50.0),
        ('2027-10-31', 50.0),
    ],
    'era': 'bopreal',
    'activo_desde': '2024-01-25',
    'activo_hasta': '2027-10-31',
    'notas': 'BCRA. Para importadores. Sub-series 1A/1B/1C/1D. Usos fiscales especiales.'
})

# --- BOPREAL Serie 2 (BPJ25) ---
# Vencimiento junio 2025
# Amortización: 12 cuotas mensuales (jul 2024 a jun 2025)
bpo2_amort = []
for m in range(12):
    yr = 2024 + (7 + m - 1) // 12
    month = ((7 + m - 1) % 12) + 1
    bpo2_amort.append((f'{yr}-{month:02d}-15', 100.0 / 12))

bonos_catalogo.append({
    'ticker': 'BPJ25',
    'nombre': 'BOPREAL Serie 2 (2025)',
    'moneda': 'USD',
    'fecha_emision': '2024-02-05',
    'fecha_vencimiento': '2025-06-15',
    'cupon_info': '0% (zero coupon)',
    'frecuencia_cupon': 'N/A',
    'monto_original_mm_usd': 2000,
    'amortizacion_detalle': bpo2_amort,
    'era': 'bopreal',
    'activo_desde': '2024-02-05',
    'activo_hasta': '2025-06-15',
    'notas': 'BCRA. 12 cuotas mensuales. Zero-coupon.'
})

# --- BOPREAL Serie 3 (BPY26) ---
# Vencimiento mayo 2026
# Amortización: 3 cuotas trimestrales (nov 2025, feb 2026, may 2026)
bonos_catalogo.append({
    'ticker': 'BPY26',
    'nombre': 'BOPREAL Serie 3 (2026)',
    'moneda': 'USD',
    'fecha_emision': '2024-02-19',
    'fecha_vencimiento': '2026-05-31',
    'cupon_info': '3% anual',
    'frecuencia_cupon': 'S',
    'monto_original_mm_usd': 3000,
    'amortizacion_detalle': [
        ('2025-11-30', 33.33),
        ('2026-02-28', 33.33),
        ('2026-05-31', 33.34),
    ],
    'era': 'bopreal',
    'activo_desde': '2024-02-19',
    'activo_hasta': '2026-05-31',
    'notas': 'BCRA. 3 cuotas trimestrales.'
})

# --- BOPREAL Serie 4 (BPO28) ---
# Anunciado abril 2025. Pago único octubre 2028.
bonos_catalogo.append({
    'ticker': 'BPO28',
    'nombre': 'BOPREAL Serie 4 (2028)',
    'moneda': 'USD',
    'fecha_emision': '2025-04-15',
    'fecha_vencimiento': '2028-10-31',
    'cupon_info': 'TBD',
    'frecuencia_cupon': 'S',
    'monto_original_mm_usd': 3000,  # estimado
    'amortizacion_detalle': [
        ('2028-10-31', 100.0),
    ],
    'era': 'bopreal',
    'activo_desde': '2025-04-15',
    'activo_hasta': '2028-10-31',
    'notas': 'BCRA. Bullet. Para deuda acumulada hasta dic 2024.'
})

# ============================================================
# ERA HISTÓRICA: LEBAC USD del BCRA (2006–2017)
# ============================================================
# Las LEBACs en dólares fueron emitidas por el BCRA hasta ~2017.
# Eran de corto plazo (30-365 días). Stock variable.
# Se modelan como stock promedio anual, similar a las LETES.
LEBAC_USD_STOCK_ANUAL = {
    2006: 1500, 2007: 2000, 2008: 2500, 2009: 2000,
    2010: 1500, 2011: 1200, 2012: 1000, 2013: 800,
    2014: 600,  2015: 500,  2016: 300,  2017: 100,
}

for yr, stock in LEBAC_USD_STOCK_ANUAL.items():
    if stock > 0:
        bonos_catalogo.append({
            'ticker': f'LEBAC_USD_{yr}',
            'nombre': f'LEBAC USD (Stock promedio {yr})',
            'moneda': 'USD',
            'fecha_emision': f'{yr}-01-01',
            'fecha_vencimiento': f'{yr}-12-31',
            'cupon_info': 'Variable (licitación)',
            'frecuencia_cupon': 'N/A',
            'monto_original_mm_usd': stock,
            'amortizacion_detalle': [(f'{yr}-12-31', 100.0)],
            'era': 'lebac_usd',
            'activo_desde': f'{yr}-01-01',
            'activo_hasta': f'{yr}-12-31',
            'notas': f'Stock promedio de LEBAC USD durante {yr}. Proxy anual.'
        })

# ============================================================
# GUARDAR CATÁLOGO
# ============================================================
# Guardamos el catálogo como JSON para uso posterior
output_path = os.path.join(BONOS_DIR, "catalogo_bonos_usd.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(bonos_catalogo, f, indent=2, ensure_ascii=False, default=str)
print(f"✅ Catálogo guardado: {output_path}")
print(f"   Total bonos: {len(bonos_catalogo)}")

# También como CSV resumen
resumen = pd.DataFrame([{
    'ticker': b['ticker'],
    'nombre': b['nombre'],
    'emision': b['fecha_emision'],
    'vencimiento': b['fecha_vencimiento'],
    'monto_mm_usd': b['monto_original_mm_usd'],
    'era': b['era'],
    'activo_desde': b['activo_desde'],
    'activo_hasta': b['activo_hasta'],
} for b in bonos_catalogo])
resumen.to_csv(os.path.join(BONOS_DIR, "catalogo_bonos_resumen.csv"), index=False)
print(f"✅ Resumen CSV guardado: catalogo_bonos_resumen.csv")
print(resumen.to_string(index=False))
