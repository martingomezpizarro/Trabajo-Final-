"""
models.py - Wrappers para modelos econométricos
Trabajo Final de Grado - Riesgo País Argentino
Universidad Nacional de Córdoba
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import warnings
warnings.filterwarnings('ignore')


# ============================================================
# MODELOS DE REGRESIÓN
# ============================================================

def estimar_ols(
    df: pd.DataFrame,
    variable_dep: str,
    variables_ind: List[str],
    constante: bool = True,
    hac: bool = True
) -> Dict[str, Any]:
    """
    Estimación por OLS con errores estándar HAC (Newey-West).
    
    Args:
        df: DataFrame con las variables
        variable_dep: Nombre de la variable dependiente
        variables_ind: Lista de variables independientes
        constante: Si agregar constante
        hac: Si usar errores estándar HAC (Newey-West)
    
    Returns:
        Dict con modelo estimado, resumen y métricas
    """
    import statsmodels.api as sm
    
    data = df[[variable_dep] + variables_ind].dropna()
    y = data[variable_dep]
    X = data[variables_ind]
    
    if constante:
        X = sm.add_constant(X)
    
    if hac:
        modelo = sm.OLS(y, X).fit(cov_type='HAC', cov_kwds={'maxlags': int(len(y)**0.25)})
    else:
        modelo = sm.OLS(y, X).fit()
    
    return {
        'modelo': modelo,
        'resumen': modelo.summary(),
        'r2': modelo.rsquared,
        'r2_adj': modelo.rsquared_adj,
        'aic': modelo.aic,
        'bic': modelo.bic,
        'durbin_watson': sm.stats.stattools.durbin_watson(modelo.resid),
    }


def estimar_var(
    df: pd.DataFrame,
    variables: List[str],
    max_lags: int = 12,
    criterio: str = 'aic'
) -> Dict[str, Any]:
    """
    Estimación de modelo VAR (Vector Autoregression).
    
    Args:
        df: DataFrame con las variables
        variables: Lista de variables endógenas
        max_lags: Máximo de rezagos a considerar
        criterio: Criterio de selección ('aic', 'bic', 'hqic', 'fpe')
    
    Returns:
        Dict con modelo estimado y resultados
    """
    from statsmodels.tsa.api import VAR
    
    data = df[variables].dropna()
    modelo = VAR(data)
    
    # Selección de rezagos
    lag_order = modelo.select_order(maxlags=max_lags)
    optimal_lag = lag_order.selected_orders[criterio]
    
    # Estimación
    resultado = modelo.fit(optimal_lag)
    
    return {
        'modelo': resultado,
        'resumen': resultado.summary(),
        'lags_optimos': optimal_lag,
        'criterios': lag_order.summary(),
        'irf': resultado.irf(periods=20),
        'fevd': resultado.fevd(periods=20),
    }


def estimar_vecm(
    df: pd.DataFrame,
    variables: List[str],
    det_order: int = 0,
    k_ar_diff: int = 1
) -> Dict[str, Any]:
    """
    Estimación de modelo VECM (Vector Error Correction Model).
    
    Args:
        df: DataFrame con las variables
        variables: Lista de variables
        det_order: Orden del determinístico (-1: sin constante, 0: constante restringida, 1: constante)
        k_ar_diff: Número de rezagos en diferencias
    
    Returns:
        Dict con modelo estimado y resultados
    """
    from statsmodels.tsa.vector_ar.vecm import VECM, coint_johansen
    
    data = df[variables].dropna()
    
    # Test de cointegración de Johansen
    johansen = coint_johansen(data, det_order=det_order, k_ar_diff=k_ar_diff)
    
    # Estimación VECM
    modelo = VECM(data, k_ar_diff=k_ar_diff, deterministic='ci')
    resultado = modelo.fit()
    
    return {
        'modelo': resultado,
        'resumen': resultado.summary(),
        'johansen_trace': johansen.lr1,
        'johansen_max_eigen': johansen.lr2,
        'johansen_cv_trace': johansen.cvt,
        'johansen_cv_max_eigen': johansen.cvm,
        'n_cointegracion': sum(johansen.lr1 > johansen.cvt[:, 1]),
    }


def estimar_ardl(
    df: pd.DataFrame,
    variable_dep: str,
    variables_ind: List[str],
    max_lags_dep: int = 4,
    max_lags_ind: int = 4,
    criterio: str = 'aic'
) -> Dict[str, Any]:
    """
    Estimación de modelo ARDL (Autoregressive Distributed Lag).
    
    Args:
        df: DataFrame con las variables
        variable_dep: Variable dependiente
        variables_ind: Variables independientes
        max_lags_dep: Máximo de rezagos de la variable dependiente
        max_lags_ind: Máximo de rezagos de las independientes
        criterio: Criterio de selección ('aic', 'bic')
    
    Returns:
        Dict con modelo estimado y resultados
    """
    from statsmodels.tsa.ardl import ARDL, ardl_select_order
    
    data = df[[variable_dep] + variables_ind].dropna()
    y = data[variable_dep]
    X = data[variables_ind]
    
    # Selección de orden
    sel = ardl_select_order(
        y, max_lags_dep,
        X, max_lags_ind,
        ic=criterio,
        trend='c'
    )
    
    # Estimación
    modelo = sel.model.fit()
    
    return {
        'modelo': modelo,
        'resumen': modelo.summary(),
        'orden_seleccionado': sel.dl_lags,
        'ar_lags': sel.ar_lags,
    }


def estimar_garch(
    serie: pd.Series,
    p: int = 1,
    q: int = 1,
    modelo_vol: str = 'GARCH',
    distribucion: str = 'normal'
) -> Dict[str, Any]:
    """
    Estimación de modelo GARCH (o variantes).
    
    Args:
        serie: Serie de retornos
        p: Orden del componente GARCH
        q: Orden del componente ARCH
        modelo_vol: Tipo de modelo ('GARCH', 'EGARCH', 'GJR-GARCH')
        distribucion: Distribución de errores ('normal', 't', 'skewt', 'ged')
    
    Returns:
        Dict con modelo estimado y resultados
    """
    from arch import arch_model
    
    serie_clean = serie.dropna() * 100  # arch espera retornos en %
    
    if modelo_vol == 'GARCH':
        am = arch_model(serie_clean, vol='Garch', p=p, q=q, dist=distribucion)
    elif modelo_vol == 'EGARCH':
        am = arch_model(serie_clean, vol='EGARCH', p=p, q=q, dist=distribucion)
    elif modelo_vol == 'GJR-GARCH':
        am = arch_model(serie_clean, vol='Garch', p=p, o=1, q=q, dist=distribucion)
    else:
        raise ValueError(f"Modelo de volatilidad '{modelo_vol}' no reconocido.")
    
    resultado = am.fit(disp='off')
    
    return {
        'modelo': resultado,
        'resumen': resultado.summary(),
        'volatilidad_condicional': resultado.conditional_volatility,
        'params': resultado.params,
        'aic': resultado.aic,
        'bic': resultado.bic,
    }


# ============================================================
# PCA - ANÁLISIS DE COMPONENTES PRINCIPALES
# ============================================================

def analisis_pca(
    df: pd.DataFrame,
    n_componentes: Optional[int] = None,
    varianza_minima: float = 0.70
) -> Dict[str, Any]:
    """
    Análisis de Componentes Principales para construir un índice.
    
    Args:
        df: DataFrame con las variables (estandarizadas internamente)
        n_componentes: Número de componentes (si None, se eligen por varianza mínima)
        varianza_minima: Varianza mínima explicada acumulada (default: 70%)
    
    Returns:
        Dict con componentes, cargas, varianza explicada e índice
    """
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    
    data = df.dropna()
    
    # Estandarizar
    scaler = StandardScaler()
    data_scaled = scaler.fit_transform(data)
    
    # PCA completo primero
    pca_full = PCA()
    pca_full.fit(data_scaled)
    
    # Determinar número de componentes
    if n_componentes is None:
        cumvar = np.cumsum(pca_full.explained_variance_ratio_)
        n_componentes = int(np.argmax(cumvar >= varianza_minima) + 1)
    
    # PCA con n_componentes seleccionados
    pca = PCA(n_components=n_componentes)
    scores = pca.fit_transform(data_scaled)
    
    # Crear índice (primer componente principal o combinación ponderada)
    pesos = pca.explained_variance_ratio_ / pca.explained_variance_ratio_.sum()
    indice = scores @ pesos
    
    # DataFrame de cargas
    cargas = pd.DataFrame(
        pca.components_.T,
        index=data.columns,
        columns=[f'PC{i+1}' for i in range(n_componentes)]
    )
    
    return {
        'pca': pca,
        'scaler': scaler,
        'scores': pd.DataFrame(scores, index=data.index, columns=[f'PC{i+1}' for i in range(n_componentes)]),
        'cargas': cargas,
        'varianza_explicada': pca.explained_variance_ratio_,
        'varianza_acumulada': np.cumsum(pca.explained_variance_ratio_),
        'indice': pd.Series(indice, index=data.index, name='Indice_RP'),
        'n_componentes': n_componentes,
        'varianza_total': np.sum(pca.explained_variance_ratio_),
    }


# ============================================================
# COMPARACIÓN DE MODELOS
# ============================================================

def comparar_modelos(
    resultados: Dict[str, Dict]
) -> pd.DataFrame:
    """
    Compara múltiples modelos estimados.
    
    Args:
        resultados: Dict {nombre_modelo: resultado_dict} donde cada
                   resultado tiene al menos 'aic', 'bic', 'r2' (si aplica)
    
    Returns:
        DataFrame comparativo
    """
    comparacion = []
    for nombre, res in resultados.items():
        fila = {'Modelo': nombre}
        for key in ['r2', 'r2_adj', 'aic', 'bic', 'lags_optimos']:
            if key in res:
                fila[key] = res[key]
        comparacion.append(fila)
    
    df = pd.DataFrame(comparacion).set_index('Modelo')
    return df.sort_values('aic', ascending=True) if 'aic' in df.columns else df
