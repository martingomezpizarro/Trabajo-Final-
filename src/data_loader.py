"""
data_loader.py - Módulo de descarga de datos desde múltiples APIs
Trabajo Final de Grado - Riesgo País Argentino
Universidad Nacional de Córdoba
"""

import pandas as pd
import numpy as np
import requests
from datetime import datetime
from typing import Optional

# ============================================================
# YAHOO FINANCE
# ============================================================

def descargar_yahoo_finance(
    ticker: str,
    fecha_inicio: str,
    fecha_fin: str,
    columna: str = 'Close'
) -> Optional[pd.DataFrame]:
    """
    Descarga datos de Yahoo Finance.
    
    Args:
        ticker: Símbolo del activo (ej: '^VIX', 'DX-Y.NYB', 'CL=F')
        fecha_inicio: Fecha inicio 'YYYY-MM-DD'
        fecha_fin: Fecha fin 'YYYY-MM-DD'
        columna: Columna a extraer ('Close', 'Open', 'High', 'Low', 'Volume')
    
    Returns:
        DataFrame con la serie temporal o None si falla
    """
    try:
        import yfinance as yf
        data = yf.download(ticker, start=fecha_inicio, end=fecha_fin, progress=False)
        if data.empty:
            return None
        
        # Manejar MultiIndex si existe
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        
        df = data[[columna]].copy()
        df.columns = [ticker]
        df.index = pd.DatetimeIndex(df.index)
        df.index.name = 'fecha'
        return df.dropna()
    except Exception as e:
        print(f"Error descargando {ticker} de Yahoo Finance: {e}")
        return None


# ============================================================
# FRED (Federal Reserve Economic Data)
# ============================================================

def descargar_fred(
    serie_id: str,
    fecha_inicio: str,
    fecha_fin: str,
    api_key: Optional[str] = None
) -> Optional[pd.DataFrame]:
    """
    Descarga datos de FRED (Federal Reserve Economic Data).
    
    Requiere API key de FRED (gratuita): https://fred.stlouisfed.org/docs/api/api_key.html
    
    Args:
        serie_id: ID de la serie en FRED (ej: 'DGS10', 'VIXCLS')
        fecha_inicio: Fecha inicio 'YYYY-MM-DD'
        fecha_fin: Fecha fin 'YYYY-MM-DD'
        api_key: API key de FRED (si None, usa variable de entorno FRED_API_KEY)
    
    Returns:
        DataFrame con la serie temporal o None si falla
    """
    try:
        import os
        if api_key is None:
            api_key = os.environ.get('FRED_API_KEY', '')
        
        if not api_key:
            print("⚠️  FRED API key no configurada. Configurar con:")
            print("    os.environ['FRED_API_KEY'] = 'tu_api_key'")
            print("    Obtener en: https://fred.stlouisfed.org/docs/api/api_key.html")
            return None
        
        url = f"https://api.stlouisfed.org/fred/series/observations"
        params = {
            'series_id': serie_id,
            'api_key': api_key,
            'file_type': 'json',
            'observation_start': fecha_inicio,
            'observation_end': fecha_fin,
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        observations = data.get('observations', [])
        
        if not observations:
            return None
        
        df = pd.DataFrame(observations)
        df['date'] = pd.to_datetime(df['date'])
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df = df.set_index('date')[['value']]
        df.columns = [serie_id]
        df.index.name = 'fecha'
        return df.dropna()
        
    except Exception as e:
        print(f"Error descargando {serie_id} de FRED: {e}")
        return None


# ============================================================
# BCRA (Banco Central de la República Argentina)
# ============================================================

def descargar_bcra(
    variable: str,
    fecha_inicio: str,
    fecha_fin: str
) -> Optional[pd.DataFrame]:
    """
    Descarga datos de la API del BCRA.
    
    Documentación: https://www.bcra.gob.ar/BCRAyVos/Catalogo_de_APIs_702.asp
    
    Variables comunes:
        - 'usd_of': Tipo de cambio oficial
        - 'reservas': Reservas internacionales
        - 'base_monetaria': Base monetaria
        - 'tasa_politica': Tasa de política monetaria
    
    Args:
        variable: Nombre de la variable BCRA
        fecha_inicio: Fecha inicio 'YYYY-MM-DD'
        fecha_fin: Fecha fin 'YYYY-MM-DD'
    
    Returns:
        DataFrame con la serie temporal o None si falla
    """
    # Mapeo de nombres amigables a endpoints del BCRA
    BCRA_ENDPOINTS = {
        'usd_of': {
            'url': 'https://api.bcra.gob.ar/estadisticas/v2.0/DatosVariable/4',
            'nombre': 'TC_Oficial'
        },
        'reservas': {
            'url': 'https://api.bcra.gob.ar/estadisticas/v2.0/DatosVariable/1',
            'nombre': 'Reservas_Internacionales'
        },
        'base_monetaria': {
            'url': 'https://api.bcra.gob.ar/estadisticas/v2.0/DatosVariable/15',
            'nombre': 'Base_Monetaria'
        },
        'tasa_politica': {
            'url': 'https://api.bcra.gob.ar/estadisticas/v2.0/DatosVariable/6',
            'nombre': 'Tasa_Politica'
        },
        'inflacion_mensual': {
            'url': 'https://api.bcra.gob.ar/estadisticas/v2.0/DatosVariable/27',
            'nombre': 'Inflacion_Mensual'
        },
        'usd_blue': {
            'url': 'https://api.bcra.gob.ar/estadisticas/v2.0/DatosVariable/5',
            'nombre': 'TC_Blue'
        },
    }
    
    try:
        if variable in BCRA_ENDPOINTS:
            endpoint = BCRA_ENDPOINTS[variable]
            url = f"{endpoint['url']}"
            nombre_col = endpoint['nombre']
        else:
            # Búsqueda dinámica en el catálogo
            print(f"ℹ️  Buscando variable '{variable}' en el catálogo del BCRA...")
            cat_url = 'https://api.bcra.gob.ar/estadisticas/v2.0/PrincipalesVariables'
            headers = {'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0'}
            # Usamos verify=False por los típicos problemas de certificados del BCRA
            res_cat = requests.get(cat_url, headers=headers, timeout=30, verify=False)
            res_cat.raise_for_status()
            catalogo = res_cat.json().get('results', [])
            
            # Buscar coincidencia (case insensitive)
            id_variable = None
            for v in catalogo:
                desc = v.get('descripcion', '')
                if variable.lower() in desc.lower():
                    id_variable = v.get('idVariable')
                    nombre_col = variable
                    print(f"✅  Variable encontrada: ID {id_variable} - {desc}")
                    break
            
            if id_variable is None:
                print(f"⚠️  Variable '{variable}' no encontrada en el catálogo del BCRA.")
                print("   Sugerencia: Revisa los términos de búsqueda.")
                return None
            
            url = f"https://api.bcra.gob.ar/estadisticas/v2.0/DatosVariable/{id_variable}"
        
        # Formatear fechas para BCRA (DD/MM/YYYY)
        fi = datetime.strptime(fecha_inicio, '%Y-%m-%d').strftime('%Y-%m-%d')
        ff = datetime.strptime(fecha_fin, '%Y-%m-%d').strftime('%Y-%m-%d')
        
        url_req = f"{url}/{fi}/{ff}"
        
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        }
        
        response = requests.get(url_req, headers=headers, timeout=30, verify=False)
        response.raise_for_status()
        
        data = response.json()
        results = data.get('results', [])
        
        if not results:
            return None
        
        df = pd.DataFrame(results)
        df['fecha'] = pd.to_datetime(df['fecha'], format='%d/%m/%Y', errors='coerce')
        df = df.dropna(subset=['fecha'])
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
        df = df.set_index('fecha')[['valor']]
        df.columns = [nombre_col]
        return df.dropna().sort_index()
        
    except Exception as e:
        print(f"Error descargando {variable} del BCRA: {e}")
        return None


# ============================================================
# WORLD BANK
# ============================================================

def descargar_world_bank(
    indicador: str,
    fecha_inicio: str,
    fecha_fin: str,
    pais: str = 'ARG'
) -> Optional[pd.DataFrame]:
    """
    Descarga datos del World Bank.
    
    Args:
        indicador: Código del indicador del World Bank
        fecha_inicio: Fecha inicio 'YYYY-MM-DD'
        fecha_fin: Fecha fin 'YYYY-MM-DD'
        pais: Código ISO3 del país (default: 'ARG')
    
    Returns:
        DataFrame con la serie temporal o None si falla
    """
    try:
        anio_inicio = int(fecha_inicio[:4])
        anio_fin = int(fecha_fin[:4])
        
        url = f"https://api.worldbank.org/v2/country/{pais}/indicator/{indicador}"
        params = {
            'date': f"{anio_inicio}:{anio_fin}",
            'format': 'json',
            'per_page': 1000
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if len(data) < 2 or not data[1]:
            return None
        
        records = data[1]
        df = pd.DataFrame([{
            'fecha': pd.Timestamp(f"{r['date']}-01-01"),
            'valor': r['value']
        } for r in records if r['value'] is not None])
        
        if df.empty:
            return None
        
        df = df.set_index('fecha').sort_index()
        df.columns = [indicador]
        return df
        
    except Exception as e:
        print(f"Error descargando {indicador} del World Bank: {e}")
        return None


# ============================================================
# ÁMBITO FINANCIERO (Riesgo País, Dólar Blue, etc.)
# ============================================================

def descargar_ambito(
    variable: str,
    fecha_inicio: str,
    fecha_fin: str
) -> Optional[pd.DataFrame]:
    """
    Descarga datos de Ámbito Financiero.
    
    ⚠️  La API de Ámbito puede cambiar. Si falla, considerar scraping
    o fuentes alternativas.
    
    Args:
        variable: Nombre de la variable (riesgo_pais_arg, dolar_blue, etc.)
        fecha_inicio: Fecha inicio 'YYYY-MM-DD'
        fecha_fin: Fecha fin 'YYYY-MM-DD'
    
    Returns:
        DataFrame con la serie temporal o None si falla
    """
    # TODO: Implementar según la fuente final que elija Martín
    # Opciones:
    #   1. API de Ámbito Financiero (si disponible)
    #   2. Scraping de sitios financieros
    #   3. Datos de J.P. Morgan vía Bloomberg/Reuters
    #   4. Datos descargados manualmente
    
    print(f"⚠️  Fuente 'ambito' para '{variable}' pendiente de implementar.")
    print(f"   Opciones:")
    print(f"   1. Descargar CSV manualmente y cargarlo")
    print(f"   2. Usar API alternativa")
    print(f"   3. Implementar scraping")
    
    # Placeholder: cargar desde CSV si existe
    import os
    csv_path = os.path.join('..', 'data', 'raw', f'{variable}.csv')
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
        df.index.name = 'fecha'
        return df
    
    return None


# ============================================================
# ARGENTINA DATOS (Riesgo País)
# ============================================================

def descargar_argentinadatos(
    variable: str,
    fecha_inicio: str,
    fecha_fin: str
) -> Optional[pd.DataFrame]:
    """
    Descarga datos de la API pública de ArgentinaDatos.
    
    Documentación: https://argentinadatos.com/
    
    Args:
        variable: Identificador ('riesgo_pais')
        fecha_inicio: Fecha inicio 'YYYY-MM-DD'
        fecha_fin: Fecha fin 'YYYY-MM-DD'
    
    Returns:
        DataFrame con la serie temporal o None si falla
    """
    try:
        url_map = {
            'riesgo_pais': 'https://api.argentinadatos.com/v1/finanzas/indices/riesgo-pais'
        }
        
        if variable not in url_map:
            print(f"⚠️  Variable '{variable}' no soportada en API ArgentinaDatos.")
            return None
            
        response = requests.get(url_map[variable], timeout=30)
        response.raise_for_status()
        
        data = response.json()
        if not data:
            return None
            
        df = pd.DataFrame(data)
        df['fecha'] = pd.to_datetime(df['fecha'])
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
        df = df.set_index('fecha')[['valor']]
        df.columns = [variable]
        
        # Filtrar fechas
        mask = (df.index >= pd.Timestamp(fecha_inicio)) & (df.index <= pd.Timestamp(fecha_fin))
        df = df.loc[mask]
        
        return df.sort_index() if not df.empty else None
        
    except Exception as e:
        print(f"Error descargando {variable} de ArgentinaDatos: {e}")
        return None


# ============================================================
# UTILIDADES DE ARMONIZACIÓN
# ============================================================

def armonizar_frecuencia(
    serie: pd.Series,
    frecuencia: str = 'D',
    metodo: str = 'ffill'
) -> pd.Series:
    """
    Armoniza la frecuencia de una serie temporal.
    
    Args:
        serie: Serie temporal con DatetimeIndex
        frecuencia: Frecuencia objetivo ('D', 'W', 'M', 'Q')
        metodo: Método de relleno ('ffill', 'bfill', 'interpolate')
    
    Returns:
        Serie con la frecuencia armonizada
    """
    if frecuencia in ['D', 'B']:
        # Para diaria, resamplear y rellenar
        serie_resampled = serie.resample('D').last()
    elif frecuencia == 'W':
        serie_resampled = serie.resample('W').last()
    elif frecuencia == 'M':
        serie_resampled = serie.resample('M').last()
    elif frecuencia == 'Q':
        serie_resampled = serie.resample('Q').last()
    else:
        serie_resampled = serie
    
    if metodo == 'ffill':
        return serie_resampled.ffill()
    elif metodo == 'bfill':
        return serie_resampled.bfill()
    elif metodo == 'interpolate':
        return serie_resampled.interpolate(method='time')
    else:
        return serie_resampled


def consolidar_series(
    series_dict: dict,
    frecuencia: str = 'D',
    metodo_relleno: str = 'ffill'
) -> pd.DataFrame:
    """
    Consolida múltiples series en un DataFrame con frecuencia uniforme.
    
    Args:
        series_dict: Dict {nombre: pd.Series}
        frecuencia: Frecuencia objetivo
        metodo_relleno: Método de relleno de NaN
    
    Returns:
        DataFrame consolidado
    """
    df = pd.DataFrame()
    for nombre, serie in series_dict.items():
        serie_arm = armonizar_frecuencia(serie, frecuencia, metodo_relleno)
        df[nombre] = serie_arm
    
    return df
