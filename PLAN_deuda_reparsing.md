# Plan: Re-parsear saldo_deuda y vencimientos con detalle ARS/USD

## Problema
- La info de saldo_deuda.csv y vencimientos_2y.csv no distingue ARS vs USD
- Los archivos fuente SÍ tienen ese detalle
- Estructura según el usuario:
  - saldo_deuda_unificado.xlsx hoja A.1: fila 9 (1-indexed) = fechas de los trimestres, col A = categorías
  - vencimientos_2y_nuevo.xlsx hoja "Por Tipo y Moneda": fila 6 (1-indexed) = fechas, col A = tipos desagregados por moneda

## Paso 1: Re-parsear saldo_deuda_unificado.xlsx

Hoja: A.1
- Fila 9 (idx=8): cabecera con fechas MM/YYYY en columnas
- Fila 10 (idx=9): DEUDA BRUTA TOTAL
- Fila 11 (idx=10): I. DEUDA EN SITUACION DE PAGO NORMAL
- Fila 12 (idx=11): TITULOS PUBLICOS
- Fila 13 (idx=12): BONOS
- Fila 14 (idx=13): LETRAS (total letras)
- Fila 15 (idx=14): LETRAS DEL TESORO
- Fila 16 (idx=15): LETRAS EN GARANTIA
- Fila 17 (idx=16): PRESTAMOS
- Fila 18 (idx=17): PRESTAMOS GARANTIZADOS
- Fila 19 (idx=18): ORGANISMOS INTERNACIONALES
- Fila 20 (idx=19): BCIE
- Fila 21 (idx=20): BEI
- Fila 22 (idx=21): BID
- Fila 23 (idx=22): BIRF
- Fila 24 (idx=23): CAF
- Fila 25 (idx=24): FIDA
- Fila 26 (idx=25): FMI
- Fila 27 (idx=26): FONPLATA
- Fila 28 (idx=27): OFID
- Fila 29 (idx=28): ORGANISMOS OFICIALES
- Fila 30 (idx=29): BILATERALES
- Fila 31 (idx=30): CLUB DE PARIS
- Fila 32 (idx=31): BANCA COMERCIAL
- Fila 33 (idx=32): PAGARES DEL TESORO
- Fila 34 (idx=33): ANTICIPOS BCRA
- Fila 35 (idx=34): AVALES
- Fila 36 (idx=35): II. DEUDA EN SITUACION DE PAGO DIFERIDO
- Fila 37 (idx=36): III. DEUDA ELEGIBLE PENDIENTE DE REESTRUCTURACION

NOTA: Todo en millones de USD. No hay desglose por moneda en este archivo.
Guardar como saldo_deuda.csv con todos los instrumentos disponibles.

## Paso 2: Re-parsear vencimientos_2y_nuevo.xlsx hoja "Por Tipo y Moneda"

Hoja: Por Tipo y Moneda
- Fila 6 (idx=5): cabecera = "Tipo de Deuda / Moneda" en col 0, fechas MM/YYYY en el resto
- Col A (idx=0): labels con estructura:
  INSTRUMENTO
    Moneda Local
    Moneda Extranjera
  (repetido para cada instrumento)

Instrumentos a extraer (cada uno tiene total + local + extranjera):
- TOTAL (fila 6): total=6, local=7, ext=8
- ANTICIPOS BCRA (fila 9): total=9, local=10, ext=11
- BANCA COMERCIAL (fila 15): total=15, local=16, ext=17
- BID (fila 24): total=24, local=25, ext=26
- BILATERALES (fila 27): total=27, local=28, ext=29
- BIRF (fila 30): total=30, local=31, ext=32
- BONOS (fila 36): total=36, local=37, ext=38
- CAF (fila 39): total=39, local=40, ext=41
- CLUB DE PARIS (fila 42): total=42, local=43, ext=44
- FMI (fila 54): total=54, local=55, ext=56
- LETRAS DEL TESORO (fila 60): total=60, local=61, ext=62

Todos los índices están en 0-based. Guardar como vencimientos_2y.csv.

IMPORTANTE: La col de FMI tiene ~58% NaN porque Argentina no tenía deuda con el FMI en
2007-2018. Eso es CORRECTO, no un error.

## Paso 3: Verificar parsing correcto

Revisar que:
- Fechas van de 06/2007 a 12/2025 (71 trimestres)
- No hay duplicados de fechas
- FMI muestra NaN pre-2018 y valores en 2018-2025
- ANTICIPOS BCRA tiene solo local (ext=NaN siempre)
- BID, BIRF, CAF, FMI, Bilaterales: local=NaN siempre (son todos moneda extranjera)

## Paso 4: Actualizar CATALOG en visualizador_template.html

Sección SALDO DE DEUDA BRUTA - agregar instrumentos faltantes:
- deuda_letras_del_tesoro (row 14)
- deuda_letras_garantia (row 15) -- si tiene datos relevantes
- deuda_prestamos_garantizados (row 17)
- deuda_bcie (row 19)
- deuda_bei (row 20)
- deuda_fida (row 24) -- probablemente todo cero
- deuda_fonplata (row 26)
- deuda_ofid (row 27)
- deuda_banca_com (row 31) -- actualmente como deuda_banca_com
- deuda_pagares (row 32)

Sección VENCIMIENTOS A 2 AÑOS - ya está correcta excepto que falta verificar
que los column names del CATALOG coincidan con los del CSV.

## Paso 5: Regenerar

python notebooks/generar_visualizador.py

## Estado actual

- vencimientos_2y.csv: RE-PARSEADO, tiene local/ext breakdown ✓
- saldo_deuda.csv: original, sin ARS/USD (porque el fuente solo tiene USD)
- CATALOG: actualizado con local/ext para vencimientos ✓
- HTML: regenerado ✓

## Lo que falta verificar

1. Si el "rompiste" se refiere a datos numéricos incorrectos → comparar
   CSV values con Excel manualmente para 1-2 fechas clave
2. Si saldo_deuda tiene algún error de row mapping → verificar con Python
3. Si algún column name en CATALOG no coincide con CSV → grep y comparar
