#!/usr/bin/env python3
"""
server.py — Servidor local mínimo para re-ejecutar secciones del análisis básico
desde botones en el reporte HTML.

Uso:
    python notebooks/server.py [--port 8765]

Abre http://localhost:8765/ y muestra outputs/analisis_basico/reporte.html.
Cada botón "🔁 Re-ejecutar" llama a /api/run?secciones=N&reuse=1&invalidate=...
que dispara `python 02a_analisis_basico.py --secciones N --reuse-cache --invalidate ...`.
"""
import argparse
import json
import os
import subprocess
import sys
import threading

# Forzar UTF-8 en stdout/stderr (Windows console cp1252)
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
_REPORT_DIR = _PROJECT_ROOT / 'outputs' / 'analisis_basico'
_RUNNER_OUT_DIR = _PROJECT_ROOT / 'outputs' / 'analisis_basico_runner'
_PY_SCRIPT = _SCRIPT_DIR / '02a_analisis_basico.py'
_RUNNER_SCRIPT = _SCRIPT_DIR / 'analisis_runner.py'
_VIZ_HTML = _SCRIPT_DIR / 'visualizador.html'
_CSV_DIR  = _SCRIPT_DIR / 'Variables Regresivas'

# Lock para evitar runs concurrentes
_run_lock = threading.Lock()
_last_log = []

# Estado de runs del nuevo flujo (analisis_runner.py)
# { run_id: {'status': 'running'|'done'|'error', 'started_at': ..., 'finished_at': ...,
#            'input_json': path, 'out_json': path, 'output_dir': path, 'log': [...]} }
_runs = {}
_runs_lock = threading.Lock()


def _runner_subprocess(run_id: str, input_json: Path, out_json: Path,
                       output_dir: Path, preview_only: bool = False):
    """Lanza analisis_runner.py en un thread y actualiza _runs[run_id]."""
    args = [sys.executable, str(_RUNNER_SCRIPT),
            '--input-json', str(input_json),
            '--out-json', str(out_json),
            '--output-dir', str(output_dir)]
    if preview_only:
        args.append('--preview-only')

    def _run():
        try:
            proc = subprocess.run(args, capture_output=True, text=True,
                                  encoding='utf-8', errors='replace',
                                  cwd=str(_PROJECT_ROOT), timeout=3600)
            log = (proc.stdout + '\n' + proc.stderr).splitlines()
            with _runs_lock:
                _runs[run_id]['log'] = log[-500:]
                _runs[run_id]['status'] = 'done' if proc.returncode == 0 else 'error'
                _runs[run_id]['finished_at'] = __import__('datetime').datetime.now().isoformat()
        except Exception as e:
            with _runs_lock:
                _runs[run_id]['status'] = 'error'
                _runs[run_id]['log'] = [f'Excepción: {e}']

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t


def _guardar_csv_desde_payload(series: list) -> Path:
    """Guarda un CSV en Variables Regresivas/ con timestamp y devuelve su path.
    Es opcional/auditoría — el runner no lo lee."""
    _CSV_DIR.mkdir(parents=True, exist_ok=True)
    ts = __import__('datetime').datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    csv_path = _CSV_DIR / f'analisis_series_{ts}.csv'
    rows = []
    for s in series:
        rows.append({
            '#': len(rows) + 1,
            'Serie A': s.get('label', ''),
            'Safe': s.get('safe', ''),
            'Estacionariedad': s.get('estacionariedad', ''),
            'Dependiente': 'Sí' if s.get('es_dependiente') else '',
            'N_obs': len(s.get('values', [])),
            'Desde': (s.get('dates') or [''])[0],
            'Hasta': (s.get('dates') or [''])[-1],
        })
    try:
        import csv as _csv
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            w = _csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
            w.writeheader()
            w.writerows(rows)
        print(f'  💾 CSV registro: {csv_path.name}')
    except Exception as e:
        print(f'  ⚠️ No pude escribir CSV registro: {e}')
    return csv_path


def _run_subprocess(args_list):
    """Ejecuta el script y captura stdout/stderr."""
    global _last_log
    cmd = [sys.executable, str(_PY_SCRIPT)] + args_list
    print(f'\n>>> {" ".join(cmd)}\n')
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding='utf-8', errors='replace',
                              cwd=str(_PROJECT_ROOT), timeout=900)
        _last_log = (proc.stdout + '\n' + proc.stderr).splitlines()[-200:]
        return proc.returncode == 0, _last_log
    except subprocess.TimeoutExpired:
        _last_log = ['Timeout (15 min) excedido']
        return False, _last_log
    except Exception as e:
        _last_log = [f'Excepción: {e}']
        return False, _last_log


def _run_kalman(payload: dict) -> dict:
    import pandas as _pd
    import numpy as _np
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    target_data = payload.get('target', {})
    exog_list = payload.get('exog', [])
    freq = payload.get('freq', 'MS') # e.g. 'MS'
    is_flow = payload.get('is_flow', False)
    order_str = payload.get('order', '4,1,4')
    seasonal_order_str = payload.get('seasonal_order', '1,0,1,12')

    try:
        order = tuple(map(int, order_str.split(',')))
        seasonal_order = tuple(map(int, seasonal_order_str.split(',')))
    except:
        order = (4,1,4)
        seasonal_order = (1,0,1,12)

    if not target_data.get('dates'):
        return {'ok': False, 'error': 'Target dates empty'}

    tdates = _pd.to_datetime(target_data['dates'])
    tvals = target_data['values']
    ts = _pd.Series(tvals, index=tdates, name='target').dropna()

    exog_df = None
    if exog_list:
        cols = []
        for i, e in enumerate(exog_list):
            edates = _pd.to_datetime(e.get('dates', []))
            evals = e.get('values', [])
            es = _pd.Series(evals, index=edates, name=e.get('label', f'exog_{i}')).dropna()
            cols.append(es)
        if cols:
            exog_raw = _pd.concat(cols, axis=1)
            # Forward fill exogenas mensualmente (o promediar). Promediamos.
            exog_df = exog_raw.resample(freq).mean().ffill().bfill()

    # Mover target a freq destino
    if freq == 'MS':
        if exog_df is not None:
            target_df = _pd.DataFrame(index=exog_df.index, columns=['target'])
        else:
            target_df = _pd.DataFrame(index=_pd.date_range(ts.index.min(), ts.index.max(), freq='MS'), columns=['target'])

        for q_date in ts.index:
            m = q_date.month
            y = q_date.year
            # Mover dato al ultimo mes del trimestre
            if m in [1, 2, 3]: tm = 3
            elif m in [4, 5, 6]: tm = 6
            elif m in [7, 8, 9]: tm = 9
            else: tm = 12
            
            target_date = _pd.Timestamp(year=y, month=tm, day=1)
            val = ts.loc[q_date]
            if is_flow:
                val = val / 3.0
            
            if target_date in target_df.index:
                target_df.loc[target_date, 'target'] = val
    else:
        target_df = ts.resample(freq).mean().to_frame(name='target')

    if exog_df is not None:
        common_idx = target_df.index.intersection(exog_df.index)
        df_model = _pd.concat([target_df.loc[common_idx], exog_df.loc[common_idx]], axis=1)
        exog_train = df_model[exog_df.columns].astype(float)
        y_train = df_model['target'].astype(float)
    else:
        df_model = target_df
        exog_train = None
        y_train = df_model['target'].astype(float)

    # El filtro de Kalman en statsmodels no requiere quitar NaNs de la endogena. 
    # Solo asegurarse que la exogena no tenga NaNs. (ffill/bfill arriba lo soluciona)
    
    modelo = SARIMAX(
        y_train,
        exog=exog_train,
        order=order,
        seasonal_order=seasonal_order,
        trend="c",
        enforce_stationarity=False,
        enforce_invertibility=False,
    )
    try:
        resultado = modelo.fit(disp=False, maxiter=500, method="powell")
        import numpy as np
        if getattr(resultado, "aic", np.nan) != getattr(resultado, "aic", np.nan) or np.isnan(float(getattr(resultado, "aic", np.nan))):
            raise ValueError("AIC is NaN")
    except:
        k = modelo.k_params
        import numpy as np
        start_params = np.zeros(k)
        start_params[-1] = 1.0 # Varianza base
        resultado = modelo.fit(start_params=start_params, disp=False, maxiter=500, method="powell")

    y_pred_in = resultado.predict()
    
    # Errores y Diagnostico
    residuos = resultado.resid.dropna()
    try:
        import statsmodels.api as sm
        lb = sm.stats.acorr_ljungbox(residuos, lags=[min(12, len(residuos) // 5)], return_df=True)
        lb_pval = float(lb["lb_pvalue"].values[0])
    except:
        lb_pval = None

    mask_obs = ~_np.isnan(y_train.values)
    rmse_in = float(_np.sqrt(_np.mean((y_train.values[mask_obs] - y_pred_in.values[mask_obs]) ** 2))) if mask_obs.sum() > 0 else None

    # Resultados serializables
    return {
        'ok': True,
        'dates': [d.strftime('%Y-%m-%d') for d in df_model.index],
        'y_obs': [float(v) if not _pd.isna(v) else None for v in y_train.values],
        'y_pred': [float(v) if not _pd.isna(v) else None for v in y_pred_in.values],
        'residuals': [float(v) if not _pd.isna(v) else None for v in residuos.values],
        'summary': str(resultado.summary()),
        'params': {str(k): float(v) for k, v in resultado.params.items()},
        'aic': float(resultado.aic),
        'bic': float(resultado.bic),
        'rmse': rmse_in,
        'ljung_box_pval': lb_pval
    }


def _run_granger(payload: dict) -> dict:
    """Calcula causalidad de Granger pairwise (matriz) y/o rolling.

    payload = {
        series: [{label, dates: [YYYY-MM-DD], values: [float], order_i?: 0|1|2}, ...],
        max_lag: int,
        alpha: float,
        mode: 'pairwise' | 'rolling',
        rolling: { window: int, step: int, causa_idx: int, efecto_idx: int }   # solo en mode='rolling'
    }
    """
    import pandas as _pd
    import numpy as _np
    from statsmodels.tsa.stattools import grangercausalitytests as _gct

    series_in = payload.get('series') or []
    max_lag   = max(1, int(payload.get('max_lag', 4)))
    alpha     = float(payload.get('alpha', 0.05))
    mode      = (payload.get('mode') or 'pairwise').lower()

    if len(series_in) < 2:
        return {'ok': False, 'error': 'Se requieren al menos 2 series'}

    # Construir panel transformado a forma estacionaria
    cols = {}
    labels = []
    for s in series_in:
        lab = s.get('label') or f'serie_{len(labels)}'
        dates = s.get('dates') or []
        vals  = s.get('values') or []
        ord_i = int(s.get('order_i', 0) or 0)
        if not dates or not vals or len(dates) != len(vals):
            continue
        ser = _pd.Series(vals, index=_pd.to_datetime(dates), name=lab).dropna()
        ser = _pd.to_numeric(ser, errors='coerce').dropna()
        if ord_i == 1:
            ser = ser.diff()
        # ord_i == 2 → no aplica, descartar
        if ord_i >= 2:
            continue
        cols[lab] = ser
        labels.append(lab)

    if len(labels) < 2:
        return {'ok': False, 'error': 'Series insuficientes tras transformación'}

    df = _pd.concat(cols.values(), axis=1).dropna(how='any')
    df.columns = labels
    if len(df) < max_lag * 4 + 5:
        return {'ok': False, 'error': f'Pocas observaciones tras alinear ({len(df)})'}

    n = len(labels)

    if mode == 'pairwise':
        pmat = [[None] * n for _ in range(n)]
        lagmat = [[0] * n for _ in range(n)]
        rows = []
        for i, causa in enumerate(labels):
            for j, efecto in enumerate(labels):
                if i == j:
                    continue
                sub = df[[efecto, causa]].dropna()
                if len(sub) < max_lag * 4 + 5:
                    continue
                try:
                    res = _gct(sub, maxlag=max_lag, verbose=False)
                    pvals = {lag: float(res[lag][0]['ssr_ftest'][1]) for lag in res}
                    best_lag = min(pvals, key=pvals.get)
                    pmat[i][j]   = pvals[best_lag]
                    lagmat[i][j] = int(best_lag)
                    rows.append({
                        'causa': causa, 'efecto': efecto,
                        'lag_opt': int(best_lag), 'p_value': pvals[best_lag],
                        'significativo': pvals[best_lag] < alpha,
                    })
                except Exception:
                    continue
        return {
            'ok': True, 'mode': 'pairwise',
            'labels': labels, 'pmat': pmat, 'lagmat': lagmat,
            'alpha': alpha, 'max_lag': max_lag, 'n_obs': int(len(df)),
            'pairs': rows,
        }

    if mode == 'rolling':
        rcfg = payload.get('rolling') or {}
        T = len(df)
        window = int(rcfg.get('window') or max(40, T // 3))
        step   = max(1, int(rcfg.get('step') or max(1, window // 25)))
        # Pares: si vienen indices úsalos; si no, top-K más significativos en pairwise
        pairs_req = rcfg.get('pairs')  # lista de {causa_idx, efecto_idx}
        if not pairs_req:
            # Computar pairwise rápido y elegir top 4
            quick = []
            for i in range(n):
                for j in range(n):
                    if i == j:
                        continue
                    sub = df[[labels[j], labels[i]]].dropna()
                    if len(sub) < max_lag * 4 + 5:
                        continue
                    try:
                        r = _gct(sub, maxlag=max_lag, verbose=False)
                        p = float(min(r[lag][0]['ssr_ftest'][1] for lag in r))
                        quick.append((p, i, j))
                    except Exception:
                        continue
            quick.sort()
            pairs_req = [{'causa_idx': i, 'efecto_idx': j} for _, i, j in quick[:4]]

        out_series = []
        for pr in pairs_req:
            i = int(pr['causa_idx']); j = int(pr['efecto_idx'])
            if i == j or i >= n or j >= n:
                continue
            causa, efecto = labels[i], labels[j]
            centros, pvals_w = [], []
            for start in range(0, T - window + 1, step):
                sub = df[[efecto, causa]].iloc[start:start + window].dropna()
                if len(sub) < max_lag * 4 + 5:
                    continue
                try:
                    r = _gct(sub, maxlag=max_lag, verbose=False)
                    p_min = float(min(r[lag][0]['ssr_ftest'][1] for lag in r))
                    centros.append(sub.index[len(sub) // 2].strftime('%Y-%m-%d'))
                    pvals_w.append(p_min)
                except Exception:
                    continue
            out_series.append({
                'causa': causa, 'efecto': efecto,
                'causa_idx': i, 'efecto_idx': j,
                'dates': centros, 'pvalues': pvals_w,
            })
        return {
            'ok': True, 'mode': 'rolling',
            'labels': labels, 'alpha': alpha, 'max_lag': max_lag,
            'window': window, 'step': step, 'n_obs': int(T),
            'series': out_series,
        }

    return {'ok': False, 'error': f'mode desconocido: {mode}'}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # silencio en consola

    def _send(self, code, body, ctype='text/html; charset=utf-8'):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Cache-Control', 'no-store')
        body_b = body if isinstance(body, bytes) else body.encode('utf-8')
        self.send_header('Content-Length', str(len(body_b)))
        self.end_headers()
        self.wfile.write(body_b)

    def _send_file(self, path: Path, ctype: str):
        if not path.exists():
            return self._send(404, f'No existe: {path}')
        with open(path, 'rb') as f:
            data = f.read()
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path)
        # API
        if u.path == '/api/run':
            qs = parse_qs(u.query)
            secciones = qs.get('secciones', [''])[0]
            invalidate = qs.get('invalidate', [''])[0]
            reuse = qs.get('reuse', ['0'])[0] == '1'

            args = []
            if secciones:
                args += ['--secciones', secciones]
            if invalidate:
                args += ['--invalidate', invalidate]
            if reuse:
                args += ['--reuse-cache']
            # Forzar generación de reporte (asegurar sec 10 incluida si reportable)
            if secciones and '10' not in secciones.split(','):
                args[args.index('--secciones') + 1] = secciones + ',10'

            if _run_lock.locked():
                return self._send(409,
                    json.dumps({'ok': False, 'error': 'Ya hay un run en curso'}),
                    'application/json')

            with _run_lock:
                ok, log = _run_subprocess(args)
            return self._send(200,
                json.dumps({'ok': ok, 'log_tail': log[-30:]}),
                'application/json')

        if u.path == '/api/log':
            return self._send(200, json.dumps({'log': _last_log}),
                              'application/json')

        # Nuevo flujo: estado y resultados de un run del analisis_runner
        if u.path == '/api/run-status':
            qs = parse_qs(u.query)
            run_id = qs.get('id', [''])[0]
            with _runs_lock:
                rec = _runs.get(run_id)
            if not rec:
                return self._send(404, json.dumps({'ok': False, 'error': 'run_id no existe'}),
                                  'application/json')
            return self._send(200, json.dumps({
                'ok': True,
                'run_id': run_id,
                'status': rec.get('status'),
                'started_at': rec.get('started_at'),
                'finished_at': rec.get('finished_at'),
                'log_tail': rec.get('log', [])[-30:],
            }), 'application/json')

        if u.path == '/api/run-results':
            qs = parse_qs(u.query)
            run_id = qs.get('id', [''])[0]
            with _runs_lock:
                rec = _runs.get(run_id)
            if not rec:
                return self._send(404, json.dumps({'ok': False, 'error': 'run_id no existe'}),
                                  'application/json')
            out_json = rec.get('out_json')
            if not out_json or not Path(out_json).exists():
                return self._send(202, json.dumps({
                    'ok': False, 'status': rec.get('status'),
                    'error': 'Resultados aún no disponibles',
                }), 'application/json')
            return self._send_file(Path(out_json), 'application/json')

        # Servir PNGs del output_dir de un run (para render nativo en visualizador)
        if u.path.startswith('/api/run-png/'):
            # /api/run-png/<run_id>/<filename.png>
            parts = u.path.split('/', 4)
            if len(parts) >= 5:
                run_id, fname = parts[3], parts[4]
                with _runs_lock:
                    rec = _runs.get(run_id)
                if rec:
                    p = Path(rec['output_dir']) / fname
                    if p.is_file():
                        return self._send_file(p, 'image/png')
            return self._send(404, 'PNG no encontrado')

        # Estático: root → visualizador.html (con tab Análisis Básico embebido)
        if u.path in ('/', '/index.html', '/visualizador.html'):
            if _VIZ_HTML.exists():
                return self._send_file(_VIZ_HTML, 'text/html; charset=utf-8')
            return self._send_file(_REPORT_DIR / 'reporte.html', 'text/html; charset=utf-8')

        # /reporte.html → reporte del análisis básico (lo carga el iframe)
        if u.path == '/reporte.html':
            return self._send_file(_REPORT_DIR / 'reporte.html', 'text/html; charset=utf-8')

        # Imágenes y otros archivos del reporte (sec05_*.png, etc.)
        target = _REPORT_DIR / u.path.lstrip('/')
        if target.is_file():
            ext = target.suffix.lower()
            ct = {'.png': 'image/png', '.jpg': 'image/jpeg',
                  '.html': 'text/html; charset=utf-8', '.css': 'text/css',
                  '.js': 'application/javascript', '.csv': 'text/csv'}.get(ext, 'application/octet-stream')
            return self._send_file(target, ct)

        # Fallback: archivos relativos a notebooks/ (data/, etc. usados por visualizador)
        viz_target = _SCRIPT_DIR / u.path.lstrip('/')
        if viz_target.is_file():
            ext = viz_target.suffix.lower()
            ct = {'.png': 'image/png', '.jpg': 'image/jpeg',
                  '.html': 'text/html; charset=utf-8', '.css': 'text/css',
                  '.js': 'application/javascript', '.csv': 'text/csv'}.get(ext, 'application/octet-stream')
            return self._send_file(viz_target, ct)

        self._send(404, f'No encontrado: {u.path}')

    def _read_json_body(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8', errors='replace')
        return json.loads(body)

    def _start_runner(self, payload: dict, preview_only: bool):
        """Persiste input.json + CSV de registro y lanza analisis_runner.py."""
        import datetime as _dt
        run_id = _dt.datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = _RUNNER_OUT_DIR / run_id
        output_dir.mkdir(parents=True, exist_ok=True)
        input_json = output_dir / 'input.json'
        out_json   = output_dir / 'out.json'

        with open(input_json, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        # CSV de registro (no requerido por el runner, queda como auditoría)
        csv_path = None
        try:
            csv_path = _guardar_csv_desde_payload(payload.get('series', []))
        except Exception as _e:
            print(f'  ⚠️ CSV registro falló: {_e}')

        with _runs_lock:
            _runs[run_id] = {
                'status': 'running',
                'started_at': _dt.datetime.now().isoformat(),
                'finished_at': None,
                'input_json': str(input_json),
                'out_json': str(out_json),
                'output_dir': str(output_dir),
                'csv_path': str(csv_path) if csv_path else None,
                'preview_only': preview_only,
                'log': [],
            }
        _runner_subprocess(run_id, input_json, out_json, output_dir, preview_only)
        return run_id

    def do_POST(self):
        u = urlparse(self.path)

        # Nuevo: preview de combinatoria (corre el runner con --preview-only)
        if u.path == '/api/preview-basico':
            try:
                payload = self._read_json_body()
            except Exception as e:
                return self._send(400, json.dumps({'ok': False, 'error': f'JSON inválido: {e}'}),
                                  'application/json')
            try:
                run_id = self._start_runner(payload, preview_only=True)
            except Exception as e:
                return self._send(500, json.dumps({'ok': False, 'error': str(e)}),
                                  'application/json')
            return self._send(200, json.dumps({'ok': True, 'run_id': run_id}),
                              'application/json')

        # Nuevo: run completo en background
        if u.path == '/api/run-basico':
            try:
                payload = self._read_json_body()
            except Exception as e:
                return self._send(400, json.dumps({'ok': False, 'error': f'JSON inválido: {e}'}),
                                  'application/json')
            try:
                run_id = self._start_runner(payload, preview_only=False)
            except Exception as e:
                return self._send(500, json.dumps({'ok': False, 'error': str(e)}),
                                  'application/json')
            return self._send(200, json.dumps({'ok': True, 'run_id': run_id}),
                              'application/json')

        if u.path == '/api/granger':
            try:
                payload = self._read_json_body()
                out = _run_granger(payload)
                return self._send(200, json.dumps(out), 'application/json')
            except Exception as e:
                import traceback as _tb
                return self._send(500, json.dumps({
                    'ok': False, 'error': str(e), 'trace': _tb.format_exc()[-1500:]
                }), 'application/json')

        if u.path == '/api/kalman':
            try:
                payload = self._read_json_body()
                out = _run_kalman(payload)
                return self._send(200, json.dumps(out), 'application/json')
            except Exception as e:
                import traceback as _tb
                return self._send(500, json.dumps({
                    'ok': False, 'error': str(e), 'trace': _tb.format_exc()[-1500:]
                }), 'application/json')

        if u.path == '/api/save-and-run':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8', errors='replace')

            _CSV_DIR.mkdir(parents=True, exist_ok=True)
            csv_path = _CSV_DIR / 'analisis_series_visualizador.csv'
            try:
                with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                    f.write(body)
                print(f'  💾 CSV recibido: {csv_path}')
            except Exception as e:
                return self._send(500,
                    json.dumps({'ok': False, 'error': f'No pude escribir CSV: {e}'}),
                    'application/json')

            if _run_lock.locked():
                return self._send(409,
                    json.dumps({'ok': False, 'error': 'Ya hay un run en curso'}),
                    'application/json')

            # Leer config opcional del visualizador (freq, lags, max_vars, modelos)
            qs = parse_qs(u.query)
            extra = []
            qs_to_cli = {
                'freq':         '--freq',
                'lag_ardl_dep': '--max-lag-ardl-dep',
                'lag_ardl_ind': '--max-lag-ardl-ind',
                'lag_var':      '--max-lag-var',
                'lag_vecm':     '--max-lag-vecm',
                'max_vars':     '--max-vars',
                'modelos':      '--modelos',
            }
            for k, cli in qs_to_cli.items():
                v = qs.get(k, [''])[0].strip()
                if v:
                    extra += [cli, v]

            with _run_lock:
                ok, log = _run_subprocess([
                    '--invalidate', 'panel,ctx,est,ardl,var,vecm,consolidado',
                    '--csv', csv_path.name,
                ] + extra)
            return self._send(200,
                json.dumps({'ok': ok, 'log_tail': log[-30:]}),
                'application/json')

        self._send(404, f'POST no soportado: {u.path}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8765)
    ap.add_argument('--no-open', action='store_true',
                    help='No abrir el navegador automáticamente')
    args = ap.parse_args()

    if not (_REPORT_DIR / 'reporte.html').exists():
        print(f'⚠️  Falta {_REPORT_DIR / "reporte.html"}.')
        print(f'   Generálo con: python {_PY_SCRIPT.relative_to(_PROJECT_ROOT)}')

    url = f'http://localhost:{args.port}/'
    print(f'🌐 Servidor en {url}')
    print(f'   Reporte: {_REPORT_DIR / "reporte.html"}')
    print(f'   Script:  {_PY_SCRIPT}')
    print(f'   Ctrl+C para detener.\n')

    if not args.no_open:
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception:
            pass

    srv = ThreadingHTTPServer(('localhost', args.port), Handler)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print('\n👋 Servidor detenido')
        srv.shutdown()


if __name__ == '__main__':
    main()
