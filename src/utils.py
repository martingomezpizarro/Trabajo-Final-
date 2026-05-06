"""
utils.py - Utilidades generales para el trabajo final
Trabajo Final de Grado - Riesgo País Argentino
Universidad Nacional de Córdoba
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple


# ============================================================
# TESTS ESTADÍSTICOS
# ============================================================

def test_estacionariedad(
    serie: pd.Series,
    nombre: str = 'Serie',
    significancia: float = 0.05
) -> Dict:
    """
    Realiza tests de estacionariedad (ADF y KPSS) sobre una serie.
    
    Args:
        serie: Serie temporal a testear
        nombre: Nombre descriptivo de la serie
        significancia: Nivel de significancia (default: 0.05)
    
    Returns:
        Dict con resultados de ambos tests
    """
    from statsmodels.tsa.stattools import adfuller, kpss
    
    serie_clean = serie.dropna()
    
    # Test ADF (H0: tiene raíz unitaria / no estacionaria)
    adf_result = adfuller(serie_clean, autolag='AIC')
    adf_stat, adf_pvalue = adf_result[0], adf_result[1]
    adf_estacionaria = adf_pvalue < significancia
    
    # Test KPSS (H0: estacionaria)
    try:
        kpss_result = kpss(serie_clean, regression='c', nlags='auto')
        kpss_stat, kpss_pvalue = kpss_result[0], kpss_result[1]
        kpss_estacionaria = kpss_pvalue > significancia
    except Exception:
        kpss_stat, kpss_pvalue = np.nan, np.nan
        kpss_estacionaria = None
    
    # Conclusión combinada
    if adf_estacionaria and kpss_estacionaria:
        conclusion = '✅ Estacionaria'
    elif not adf_estacionaria and not kpss_estacionaria:
        conclusion = '❌ No estacionaria'
    else:
        conclusion = '⚠️ Resultados mixtos'
    
    return {
        'Variable': nombre,
        'ADF_stat': round(adf_stat, 4),
        'ADF_pvalue': round(adf_pvalue, 4),
        'ADF_estacionaria': adf_estacionaria,
        'KPSS_stat': round(kpss_stat, 4) if not np.isnan(kpss_stat) else np.nan,
        'KPSS_pvalue': round(kpss_pvalue, 4) if not np.isnan(kpss_pvalue) else np.nan,
        'KPSS_estacionaria': kpss_estacionaria,
        'Conclusión': conclusion
    }


def test_causalidad_granger(
    df: pd.DataFrame,
    variable_dep: str,
    variable_ind: str,
    max_lags: int = 12,
    significancia: float = 0.05
) -> Dict:
    """
    Test de causalidad de Granger entre dos variables.
    
    Args:
        df: DataFrame con ambas variables
        variable_dep: Nombre de la variable dependiente
        variable_ind: Nombre de la variable independiente
        max_lags: Número máximo de rezagos a testear
        significancia: Nivel de significancia
    
    Returns:
        Dict con resultados del test
    """
    from statsmodels.tsa.stattools import grangercausalitytests
    
    data = df[[variable_dep, variable_ind]].dropna()
    
    resultados = grangercausalitytests(data, maxlag=max_lags, verbose=False)
    
    # Extraer p-values del test F para cada lag
    pvalues = {}
    for lag, result in resultados.items():
        f_test = result[0]['ssr_ftest']
        pvalues[lag] = f_test[1]  # p-value
    
    min_pvalue_lag = min(pvalues, key=pvalues.get)
    
    return {
        'Variable_Dep': variable_dep,
        'Variable_Ind': variable_ind,
        'Mejor_Lag': min_pvalue_lag,
        'P_Value': round(pvalues[min_pvalue_lag], 4),
        'Causalidad_Granger': pvalues[min_pvalue_lag] < significancia,
        'Todos_PValues': pvalues
    }


# ============================================================
# TRANSFORMACIONES DE SERIES
# ============================================================

def transformar_serie(
    serie: pd.Series,
    transformacion: str = 'nivel'
) -> pd.Series:
    """
    Aplica transformaciones comunes a una serie temporal.
    
    Args:
        serie: Serie temporal
        transformacion: Tipo de transformación
            - 'nivel': sin transformación
            - 'log': logaritmo natural
            - 'diff': primera diferencia
            - 'log_diff': diferencia del logaritmo (retornos log)
            - 'pct_change': variación porcentual
            - 'z_score': estandarización
    
    Returns:
        Serie transformada
    """
    if transformacion == 'nivel':
        return serie
    elif transformacion == 'log':
        return np.log(serie)
    elif transformacion == 'diff':
        return serie.diff().dropna()
    elif transformacion == 'log_diff':
        return np.log(serie).diff().dropna()
    elif transformacion == 'pct_change':
        return serie.pct_change().dropna()
    elif transformacion == 'z_score':
        return (serie - serie.mean()) / serie.std()
    else:
        raise ValueError(f"Transformación '{transformacion}' no reconocida.")


def crear_rezagos(
    df: pd.DataFrame,
    columnas: List[str],
    n_lags: int = 5
) -> pd.DataFrame:
    """
    Crea columnas de rezagos para las variables indicadas.
    
    Args:
        df: DataFrame original
        columnas: Lista de columnas a rezagar
        n_lags: Número de rezagos
    
    Returns:
        DataFrame con las columnas de rezagos agregadas
    """
    df_result = df.copy()
    for col in columnas:
        for lag in range(1, n_lags + 1):
            df_result[f'{col}_lag{lag}'] = df_result[col].shift(lag)
    return df_result


# ============================================================
# MÉTRICAS Y RESUMEN
# ============================================================

def resumen_estadistico(df: pd.DataFrame) -> pd.DataFrame:
    """
    Genera un resumen estadístico extendido del DataFrame.
    
    Args:
        df: DataFrame con series temporales
    
    Returns:
        DataFrame con estadísticas descriptivas extendidas
    """
    from scipy import stats
    
    resumen = pd.DataFrame()
    
    for col in df.columns:
        serie = df[col].dropna()
        resumen[col] = {
            'N': len(serie),
            'Inicio': serie.index.min().strftime('%Y-%m-%d') if hasattr(serie.index, 'strftime') else str(serie.index.min()),
            'Fin': serie.index.max().strftime('%Y-%m-%d') if hasattr(serie.index, 'strftime') else str(serie.index.max()),
            'Media': serie.mean(),
            'Mediana': serie.median(),
            'Desvío': serie.std(),
            'Min': serie.min(),
            'Max': serie.max(),
            'Asimetría': serie.skew(),
            'Curtosis': serie.kurtosis(),
            'Jarque-Bera (p)': stats.jarque_bera(serie)[1],
        }
    
    return resumen.T


def metricas_prediccion(
    y_real: np.ndarray,
    y_pred: np.ndarray
) -> Dict:
    """
    Calcula métricas de evaluación de predicción.
    
    Args:
        y_real: Valores reales
        y_pred: Valores predichos
    
    Returns:
        Dict con las métricas
    """
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    
    rmse = np.sqrt(mean_squared_error(y_real, y_pred))
    mae = mean_absolute_error(y_real, y_pred)
    r2 = r2_score(y_real, y_pred)
    mape = np.mean(np.abs((y_real - y_pred) / y_real)) * 100
    
    return {
        'RMSE': round(rmse, 4),
        'MAE': round(mae, 4),
        'R²': round(r2, 4),
        'MAPE (%)': round(mape, 2),
    }
