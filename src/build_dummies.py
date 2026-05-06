"""
build_dummies.py — Construye variables dummy y series derivadas.
Escribe un marcador 'DONE.txt' al finalizar para verificar ejecución.
"""
import pandas as pd
import numpy as np
import os, sys, traceback

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'processed')
os.makedirs(OUT, exist_ok=True)

# Marcador de inicio
with open(os.path.join(OUT, '_RUNNING.txt'), 'w') as f:
    f.write('started\n')

try:
    idx = pd.date_range('1999-01-01', pd.Timestamp.today(), freq='B', name='fecha')
    
    with open(os.path.join(OUT, '_RUNNING.txt'), 'a') as f:
        f.write(f'index: {len(idx)} days\n')

    # 1. CEPO
    CEPO = [('2011-10-28','2015-12-16'), ('2019-09-01','2024-12-13')]
    cepo = pd.Series(0, index=idx, name='dummy_cepo', dtype='int8')
    for s, e in CEPO:
        cepo.loc[s:e] = 1
    cepo.to_frame().to_csv(os.path.join(OUT, 'dummy_cepo.csv'))
    with open(os.path.join(OUT, '_RUNNING.txt'), 'a') as f:
        f.write(f'cepo done: {cepo.sum()} days\n')

    # 2. GOBIERNOS
    GOB = [
        ('1999-01-01','1999-12-09',1,'Menem'),
        ('1999-12-10','2001-12-20',2,'De la Rúa'),
        ('2001-12-21','2002-01-01',3,'Transición 2001'),
        ('2002-01-02','2003-05-24',4,'Duhalde'),
        ('2003-05-25','2007-12-09',5,'Néstor Kirchner'),
        ('2007-12-10','2015-12-09',6,'Cristina Kirchner'),
        ('2015-12-10','2019-12-09',7,'Macri'),
        ('2019-12-10','2023-12-09',8,'Alberto Fernández'),
        ('2023-12-10','2030-12-31',9,'Milei'),
    ]
    gob_id = pd.Series(0, index=idx, name='gobierno_id', dtype='int8')
    gob_nm = pd.Series('', index=idx, name='gobierno_nombre')
    for s, e, gid, nm in GOB:
        mask = (idx >= pd.Timestamp(s)) & (idx <= pd.Timestamp(e))
        gob_id[mask] = gid
        gob_nm[mask] = nm
    df_gob = pd.DataFrame({'gobierno_id': gob_id, 'gobierno_nombre': gob_nm})
    df_gob.to_csv(os.path.join(OUT, 'dummy_gob.csv'))
    with open(os.path.join(OUT, '_RUNNING.txt'), 'a') as f:
        f.write(f'gob done: {df_gob["gobierno_id"].nunique()} govs\n')

    # 3. ELECTORAL
    ELEC = [
        '1999-10-24','2001-10-14','2003-04-27','2003-05-18','2005-10-23',
        '2007-10-28','2009-06-28','2011-08-14','2011-10-23','2013-08-11',
        '2013-10-27','2015-08-09','2015-10-25','2015-11-22','2017-08-13',
        '2017-10-22','2019-08-11','2019-10-27','2021-09-12','2021-11-14',
        '2023-08-13','2023-10-22','2023-11-19','2025-08-10','2025-10-26',
    ]
    elec = pd.Series(0, index=idx, name='dummy_electoral', dtype='int8')
    for f_str in ELEC:
        t = pd.Timestamp(f_str)
        ini = t - pd.Timedelta(days=60)
        fin = t + pd.Timedelta(days=60)
        elec.loc[ini:fin] = 1
    elec.to_frame().to_csv(os.path.join(OUT, 'dummy_elec.csv'))
    with open(os.path.join(OUT, '_RUNNING.txt'), 'a') as f:
        f.write(f'elec done: {elec.sum()} days in window\n')

    # 4. DEFAULTS
    DEFAULTS = [pd.Timestamp('2001-12-23'), pd.Timestamp('2014-07-30'), pd.Timestamp('2020-05-22')]
    
    dates_ts = idx.to_series()
    ultimo = pd.Series(pd.Timestamp('1989-07-09'), index=idx, dtype='datetime64[ns]')
    for d in sorted(DEFAULTS):
        ultimo = ultimo.where(dates_ts < d, d)
    ysd = ((dates_ts - ultimo).dt.days / 365.25).rename('years_since_default')
    ysd.to_frame().to_csv(os.path.join(OUT, 'years_since_default.csv'))

    nd = pd.Series(0, index=idx, name='n_defaults', dtype='int8')
    for d in DEFAULTS:
        nd.loc[d:] += 1
    nd.to_frame().to_csv(os.path.join(OUT, 'defaults_history.csv'))
    
    with open(os.path.join(OUT, '_RUNNING.txt'), 'a') as f:
        f.write(f'defaults done: ysd range {ysd.min():.2f} to {ysd.max():.2f}\n')

    # Marcador de éxito
    with open(os.path.join(OUT, 'DONE.txt'), 'w') as f:
        f.write('ALL DONE\n')
        f.write(f'Files: dummy_cepo.csv, dummy_gob.csv, dummy_elec.csv, years_since_default.csv, defaults_history.csv\n')

except Exception as ex:
    with open(os.path.join(OUT, 'ERROR.txt'), 'w') as f:
        f.write(traceback.format_exc())
