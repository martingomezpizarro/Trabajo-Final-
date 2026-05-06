"""
Patches visualizador_template.html:
1. Replaces CATALOG with multi-source format (sources:[{freq,file,dateCol,valCol}])
2. Updates buildIndex, getSeries, applyTransforms and call sites
3. Adds new series: TI, oferta_demanda, saldo_deuda, vencimientos
Run: python notebooks/update_template.py
"""
import re, os

TEMPLATE = os.path.join(os.path.dirname(__file__), 'visualizador_template.html')

with open(TEMPLATE, 'r', encoding='utf-8') as f:
    html = f.read()

# ═══════════════════════════════════════════════════════════════════════
# 1. REPLACE CATALOG
# ═══════════════════════════════════════════════════════════════════════
NEW_CATALOG = """\
/* ── CATALOG ── */
// Items: {id,label,file,dateCol,valCol,unit,freq} (single-source)
// or:    {id,label,unit,sources:[{freq,file,dateCol,valCol},...]} (multi-source)
// getSeries() picks the best available source for the current UI frequency.
const CATALOG = [

  /* ── SECTOR MONETARIO Y CAMBIARIO ── */

  { grp:'Reservas y Liquidez', clr:'#7c3aed', items:[
    { id:'res_brutas', label:'Reservas Brutas BCRA', file:'001_reservas_brutas.csv', dateCol:'fecha', valCol:'valor', unit:'Mill. USD', freq:'D' }
  ]},

  { grp:'Sistema Bancario', clr:'#0ea5e9', subs:[
    { sub:'Depósitos', items:[
      { id:'dep_total',    label:'Depósitos Totales (ARS)',    file:'021_dep_total.csv',              dateCol:'fecha', valCol:'valor',                      unit:'Mill. ARS', freq:'D' },
      { id:'dep_usd_tot',  label:'Depósitos USD — Total',      file:'depositos_usd_totales.csv',      dateCol:'fecha', valCol:'depositos_usd_z',             unit:'Mill. USD', freq:'D' },
      { id:'dep_usd_res',  label:'Depósitos USD — Residentes', file:'depositos_usd_residentes.csv',   dateCol:'fecha', valCol:'depositos_usd_residentes_aa', unit:'Mill. USD', freq:'D' },
      { id:'dep_usd_priv', label:'Depósitos USD — Sec. Priv.', file:'depositos_usd_secprivnofin.csv', dateCol:'fecha', valCol:'depositos_usd_aa',            unit:'Mill. USD', freq:'D' }
    ]},
    { sub:'Préstamos', items:[
      { id:'prest_usd', label:'Préstamos Privados USD', file:'prestamos_privados_usd_q.csv', dateCol:'fecha', valCol:'prestamos_privados_usd_q', unit:'Mill. USD', freq:'D' }
    ]}
  ]},

  { grp:'Tipo de Cambio y Brecha', clr:'#f59e0b', items:[
    { id:'tc_mep',   label:'TC MEP (dólar financiero)',    file:'brecha_cambiaria.csv', dateCol:'fecha', valCol:'mep',              unit:'ARS/USD', freq:'D' },
    { id:'tc_a3500', label:'TC Oficial (A3500)',            file:'brecha_cambiaria.csv', dateCol:'fecha', valCol:'bcra_a3500',       unit:'ARS/USD', freq:'D' },
    { id:'brecha',   label:'Brecha Cambiaria MEP/Oficial', file:'brecha_cambiaria.csv', dateCol:'fecha', valCol:'brecha_cambiaria', unit:'ratio',   freq:'D' }
  ]},

  { grp:'ITCRM — Tipo de Cambio Real Multilateral', clr:'#14b8a6', subs:[
    { sub:'General', items:[
      { id:'itcrm',     label:'ITCRM Multilateral', file:'itcrm_diario.csv', dateCol:'Periodo', valCol:'ITCRM',               unit:'Índice base 2001=100', freq:'D' }
    ]},
    { sub:'América', items:[
      { id:'itcrm_bra', label:'Brasil',      file:'itcrm_diario.csv', dateCol:'Periodo', valCol:'ITCRB Brasil',         unit:'Índice', freq:'D' },
      { id:'itcrm_usa', label:'EEUU',        file:'itcrm_diario.csv', dateCol:'Periodo', valCol:'ITCRB Estados Unidos', unit:'Índice', freq:'D' },
      { id:'itcrm_chi', label:'Chile',       file:'itcrm_diario.csv', dateCol:'Periodo', valCol:'ITCRB Chile',          unit:'Índice', freq:'D' },
      { id:'itcrm_uru', label:'Uruguay',     file:'itcrm_diario.csv', dateCol:'Periodo', valCol:'ITCRB Uruguay',        unit:'Índice', freq:'D' },
      { id:'itcrm_mex', label:'México',      file:'itcrm_diario.csv', dateCol:'Periodo', valCol:'ITCRB México',         unit:'Índice', freq:'D' },
      { id:'itcrm_can', label:'Canadá',      file:'itcrm_diario.csv', dateCol:'Periodo', valCol:'ITCRB Canadá',         unit:'Índice', freq:'D' },
      { id:'itcrm_sud', label:'Sudamérica',  file:'itcrm_diario.csv', dateCol:'Periodo', valCol:'ITCRB Sudamérica*',    unit:'Índice', freq:'D' }
    ]},
    { sub:'Europa', items:[
      { id:'itcrm_eur', label:'Zona Euro',   file:'itcrm_diario.csv', dateCol:'Periodo', valCol:'ITCRB Zona Euro',   unit:'Índice', freq:'D' },
      { id:'itcrm_gbr', label:'Reino Unido', file:'itcrm_diario.csv', dateCol:'Periodo', valCol:'ITCRB Reino Unido', unit:'Índice', freq:'D' },
      { id:'itcrm_sui', label:'Suiza',       file:'itcrm_diario.csv', dateCol:'Periodo', valCol:'ITCRB Suiza',       unit:'Índice', freq:'D' }
    ]},
    { sub:'Asia', items:[
      { id:'itcrm_chn', label:'China',   file:'itcrm_diario.csv', dateCol:'Periodo', valCol:'ITCRB China',   unit:'Índice', freq:'D' },
      { id:'itcrm_jap', label:'Japón',   file:'itcrm_diario.csv', dateCol:'Periodo', valCol:'ITCRB Japón',   unit:'Índice', freq:'D' },
      { id:'itcrm_ind', label:'India',   file:'itcrm_diario.csv', dateCol:'Periodo', valCol:'ITCRB India',   unit:'Índice', freq:'D' },
      { id:'itcrm_vie', label:'Vietnam', file:'itcrm_diario.csv', dateCol:'Periodo', valCol:'ITCRB Vietnam', unit:'Índice', freq:'D' }
    ]}
  ]},

  /* ── SECTOR EXTERNO: COMERCIO ── */

  { grp:'Intercambio Comercial (ICA)', clr:'#10b981', subs:[
    { sub:'Resumen', items:[
      { id:'ica_saldo', label:'Saldo Comercial',       unit:'Mill. USD', sources:[
          {freq:'M', file:'ica_intercambio_comercial_argentino_valores_mensuales.csv',    dateCol:'indice_tiempo', valCol:'ica_saldo_comercial'},
          {freq:'Q', file:'ica_intercambio_comercial_argentino_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'saldo_comercial'},
          {freq:'A', file:'ica_intercambio_comercial_argentino_valores_anuales.csv',       dateCol:'indice_tiempo', valCol:'saldo_comercial'}
      ]},
      { id:'ica_expo',  label:'Exportaciones — Total', unit:'Mill. USD', sources:[
          {freq:'M', file:'ica_intercambio_comercial_argentino_valores_mensuales.csv',    dateCol:'indice_tiempo', valCol:'ica_expo_totales'},
          {freq:'Q', file:'ica_intercambio_comercial_argentino_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'ica_expo_totales'},
          {freq:'A', file:'ica_intercambio_comercial_argentino_valores_anuales.csv',       dateCol:'indice_tiempo', valCol:'ica_expo_totales'}
      ]},
      { id:'ica_impo',  label:'Importaciones — Total', unit:'Mill. USD', sources:[
          {freq:'M', file:'ica_intercambio_comercial_argentino_valores_mensuales.csv',    dateCol:'indice_tiempo', valCol:'ica_importaciones_totales'},
          {freq:'Q', file:'ica_intercambio_comercial_argentino_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'ica_importaciones_totales'},
          {freq:'A', file:'ica_intercambio_comercial_argentino_valores_anuales.csv',       dateCol:'indice_tiempo', valCol:'ica_importaciones_totales'}
      ]}
    ]},
    { sub:'Exportaciones por Rubro', items:[
      { id:'ica_pp',   label:'Prod. Primarios (PP)',   unit:'Mill. USD', sources:[
          {freq:'M', file:'ica_intercambio_comercial_argentino_valores_mensuales.csv',    dateCol:'indice_tiempo', valCol:'ica_exportacion_productos_primarios'},
          {freq:'Q', file:'ica_intercambio_comercial_argentino_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'ica_exportacion_productos_primarios'},
          {freq:'A', file:'ica_intercambio_comercial_argentino_valores_anuales.csv',       dateCol:'indice_tiempo', valCol:'ica_exportacion_productos_primarios'}
      ]},
      { id:'ica_moa',  label:'MOA',                    unit:'Mill. USD', sources:[
          {freq:'M', file:'ica_intercambio_comercial_argentino_valores_mensuales.csv',    dateCol:'indice_tiempo', valCol:'ica_exportacion_manufacturas_origen_agropecuario'},
          {freq:'Q', file:'ica_intercambio_comercial_argentino_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'ica_exportacion_manufacturas_origen_agropecuario'},
          {freq:'A', file:'ica_intercambio_comercial_argentino_valores_anuales.csv',       dateCol:'indice_tiempo', valCol:'ica_exportacion_manufacturas_origen_agropecuario'}
      ]},
      { id:'ica_moi',  label:'MOI',                    unit:'Mill. USD', sources:[
          {freq:'M', file:'ica_intercambio_comercial_argentino_valores_mensuales.csv',    dateCol:'indice_tiempo', valCol:'ica_exportacion_manufacturas_origen_industrial'},
          {freq:'Q', file:'ica_intercambio_comercial_argentino_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'ica_exportacion_manufacturas_origen_industrial'},
          {freq:'A', file:'ica_intercambio_comercial_argentino_valores_anuales.csv',       dateCol:'indice_tiempo', valCol:'ica_exportacion_manufacturas_origen_industrial'}
      ]},
      { id:'ica_comb', label:'Combustible y Energía',  unit:'Mill. USD', sources:[
          {freq:'M', file:'ica_intercambio_comercial_argentino_valores_mensuales.csv',    dateCol:'indice_tiempo', valCol:'ica_exportacion_combustible_energia'},
          {freq:'Q', file:'ica_intercambio_comercial_argentino_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'ica_exportacion_combustible_energia'},
          {freq:'A', file:'ica_intercambio_comercial_argentino_valores_anuales.csv',       dateCol:'indice_tiempo', valCol:'ica_exportacion_combustible_energia'}
      ]}
    ]},
    { sub:'Importaciones por Rubro', items:[
      { id:'ica_ibk',   label:'Bienes de Capital',     unit:'Mill. USD', sources:[
          {freq:'M', file:'ica_intercambio_comercial_argentino_valores_mensuales.csv',    dateCol:'indice_tiempo', valCol:'ica_importaciones_bienes_capital'},
          {freq:'Q', file:'ica_intercambio_comercial_argentino_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'ica_importaciones_bienes_capital'},
          {freq:'A', file:'ica_intercambio_comercial_argentino_valores_anuales.csv',       dateCol:'indice_tiempo', valCol:'ica_importaciones_bienes_capital'}
      ]},
      { id:'ica_ibi',   label:'Bienes Intermedios',     unit:'Mill. USD', sources:[
          {freq:'M', file:'ica_intercambio_comercial_argentino_valores_mensuales.csv',    dateCol:'indice_tiempo', valCol:'ica_importaciones_bienes_intermedios'},
          {freq:'Q', file:'ica_intercambio_comercial_argentino_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'ica_importaciones_bienes_intermedios'},
          {freq:'A', file:'ica_intercambio_comercial_argentino_valores_anuales.csv',       dateCol:'indice_tiempo', valCol:'ica_importaciones_bienes_intermedios'}
      ]},
      { id:'ica_icmb',  label:'Combustibles/Lubric.',   unit:'Mill. USD', sources:[
          {freq:'M', file:'ica_intercambio_comercial_argentino_valores_mensuales.csv',    dateCol:'indice_tiempo', valCol:'ica_importaciones_combustibles_lubricantes'},
          {freq:'Q', file:'ica_intercambio_comercial_argentino_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'ica_importaciones_combustibles_lubricantes'},
          {freq:'A', file:'ica_intercambio_comercial_argentino_valores_anuales.csv',       dateCol:'indice_tiempo', valCol:'ica_importaciones_combustibles_lubricantes'}
      ]},
      { id:'ica_ipbk',  label:'Piezas y Acces. BK',     unit:'Mill. USD', sources:[
          {freq:'M', file:'ica_intercambio_comercial_argentino_valores_mensuales.csv',    dateCol:'indice_tiempo', valCol:'ica_importaciones_piezas_accesorios_bienes_capital'},
          {freq:'Q', file:'ica_intercambio_comercial_argentino_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'ica_importaciones_piezas_accesorios_bienes_capital'},
          {freq:'A', file:'ica_intercambio_comercial_argentino_valores_anuales.csv',       dateCol:'indice_tiempo', valCol:'ica_importaciones_piezas_accesorios_bienes_capital'}
      ]},
      { id:'ica_ibc',   label:'Bienes de Consumo',      unit:'Mill. USD', sources:[
          {freq:'M', file:'ica_intercambio_comercial_argentino_valores_mensuales.csv',    dateCol:'indice_tiempo', valCol:'ica_importaciones_bienes_consumo'},
          {freq:'Q', file:'ica_intercambio_comercial_argentino_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'ica_importaciones_bienes_consumo'},
          {freq:'A', file:'ica_intercambio_comercial_argentino_valores_anuales.csv',       dateCol:'indice_tiempo', valCol:'ica_importaciones_bienes_consumo'}
      ]},
      { id:'ica_iauto', label:'Vehículos Automotores',  unit:'Mill. USD', sources:[
          {freq:'M', file:'ica_intercambio_comercial_argentino_valores_mensuales.csv',    dateCol:'indice_tiempo', valCol:'ica_importaciones_vehiculos_automotores_pasajeros'},
          {freq:'Q', file:'ica_intercambio_comercial_argentino_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'ica_importaciones_vehiculos_automotores_pasajeros'},
          {freq:'A', file:'ica_intercambio_comercial_argentino_valores_anuales.csv',       dateCol:'indice_tiempo', valCol:'ica_importaciones_vehiculos_automotores_pasajeros'}
      ]}
    ]},
    { sub:'Términos de Intercambio', items:[
      { id:'ti_nominal',  label:'Términos de Intercambio (nominal)',   file:'ti_mensual.csv', dateCol:'fecha', valCol:'ti_nominal',      unit:'Índice 2004=100', freq:'M' },
      { id:'ti_base100',  label:'Términos de Intercambio (base 100)',  file:'ti_mensual.csv', dateCol:'fecha', valCol:'ti_base100',      unit:'Índice',          freq:'M' },
      { id:'ti_expo_p',   label:'Precios Exportaciones',               file:'ti_mensual.csv', dateCol:'fecha', valCol:'expo_precios',    unit:'Índice',          freq:'M' },
      { id:'ti_expo_q',   label:'Cantidades Exportadas',               file:'ti_mensual.csv', dateCol:'fecha', valCol:'expo_cantidades', unit:'Índice',          freq:'M' },
      { id:'ti_impo_p',   label:'Precios Importaciones',               file:'ti_mensual.csv', dateCol:'fecha', valCol:'impo_precios',    unit:'Índice',          freq:'M' },
      { id:'ti_impo_q',   label:'Cantidades Importadas',               file:'ti_mensual.csv', dateCol:'fecha', valCol:'impo_cantidades', unit:'Índice',          freq:'M' }
    ]}
  ]},

  { grp:'Saldo Comercial por Países', clr:'#06b6d4', subs:[
    { sub:'Totales y Regiones', items:[
      { id:'sc_tot',   label:'Total Mundial',        unit:'Mill. USD', sources:[
          {freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_totales'},
          {freq:'Q', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_trimes.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_totales'},
          {freq:'A', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_totales'}
      ]},
      { id:'sc_alat',  label:'América Latina',       unit:'Mill. USD', sources:[
          {freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_total_america_latina'},
          {freq:'Q', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_trimes.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_total_america_latina'},
          {freq:'A', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_total_america_latina'}
      ]},
      { id:'sc_merc',  label:'Mercosur',             unit:'Mill. USD', sources:[
          {freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_total_mercosur'},
          {freq:'Q', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_trimes.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_total_mercosur'},
          {freq:'A', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_total_mercosur'}
      ]},
      { id:'sc_alp',   label:'Alianza del Pacífico', unit:'Mill. USD', sources:[
          {freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_total_alianza_pacifico'},
          {freq:'A', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_total_alianza_pacifico'}
      ]},
      { id:'sc_ue',    label:'Unión Europea',        unit:'Mill. USD', sources:[
          {freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_total_ue'},
          {freq:'Q', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_trimes.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_total_ue'},
          {freq:'A', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_total_ue'}
      ]},
      { id:'sc_asia',  label:'Asia Pacífico',        unit:'Mill. USD', sources:[
          {freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_total_asia_pacifico'},
          {freq:'Q', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_trimes.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_asia_pacifico'},
          {freq:'A', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_total_asia_pacifico'}
      ]},
      { id:'sc_afr',   label:'África',               unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_total_africa'}]},
      { id:'sc_nafta', label:'NAFTA',                unit:'Mill. USD', sources:[
          {freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_total_nafta'},
          {freq:'A', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_total_nafta'}
      ]},
      { id:'sc_aladi', label:'ALADI',                unit:'Mill. USD', sources:[
          {freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_aladi'},
          {freq:'A', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_aladi'}
      ]},
      { id:'sc_asean', label:'ASEAN',                unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_asean'}]}
    ]},
    { sub:'América', items:[
      { id:'sc_bra',   label:'Brasil',    unit:'Mill. USD', sources:[
          {freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_brasil'},
          {freq:'Q', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_trimes.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_brasil'},
          {freq:'A', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_brasil'}
      ]},
      { id:'sc_usa',   label:'EEUU',     unit:'Mill. USD', sources:[
          {freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_estados_unidos'},
          {freq:'Q', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_trimes.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_estados_unidos'},
          {freq:'A', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_estados_unidos'}
      ]},
      { id:'sc_uru',   label:'Uruguay',  unit:'Mill. USD', sources:[
          {freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_uruguay'},
          {freq:'Q', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_trimes.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_uruguay'},
          {freq:'A', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_uruguay'}
      ]},
      { id:'sc_par',   label:'Paraguay', unit:'Mill. USD', sources:[
          {freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_paraguay'},
          {freq:'Q', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_trimes.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_paraguay'},
          {freq:'A', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_paraguay'}
      ]},
      { id:'sc_chi',   label:'Chile',    unit:'Mill. USD', sources:[
          {freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_chile'},
          {freq:'Q', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_trimes.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_chile'},
          {freq:'A', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_chile'}
      ]},
      { id:'sc_ven',   label:'Venezuela',     unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_venezuela'}]},
      { id:'sc_bol',   label:'Bolivia',       unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_bolivia'}]},
      { id:'sc_col',   label:'Colombia',      unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_colombia'}]},
      { id:'sc_mex',   label:'México',        unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_mexico'}]},
      { id:'sc_per',   label:'Perú',          unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_peru'}]},
      { id:'sc_ecu',   label:'Ecuador',       unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_ecuador'}]},
      { id:'sc_can',   label:'Canadá',        unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_canada'}]},
      { id:'sc_rlat',  label:'Resto Am. Lat.',unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_resto_america_latina'}]}
    ]},
    { sub:'Europa', items:[
      { id:'sc_ale',   label:'Alemania',    unit:'Mill. USD', sources:[
          {freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_alemania'},
          {freq:'A', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_alemania'}
      ]},
      { id:'sc_esp',   label:'España',      unit:'Mill. USD', sources:[
          {freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_espana'},
          {freq:'A', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_espana'}
      ]},
      { id:'sc_fra',   label:'Francia',     unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_francia'}]},
      { id:'sc_ita',   label:'Italia',      unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_italia'}]},
      { id:'sc_pba',   label:'Países Bajos',unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_paises_bajos'}]},
      { id:'sc_gbr',   label:'Reino Unido', unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_reino_unido'}]},
      { id:'sc_pol',   label:'Polonia',     unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_polonia'}]},
      { id:'sc_por',   label:'Portugal',    unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_portugal'}]},
      { id:'sc_aut',   label:'Austria',     unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_austria'}]},
      { id:'sc_bel',   label:'Bélgica',     unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_belgica'}]},
      { id:'sc_sui',   label:'Suiza',       unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_suiza'}]},
      { id:'sc_reue',  label:'Resto UE',    unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_resto_ue'}]}
    ]},
    { sub:'Asia y Pacífico', items:[
      { id:'sc_chn',   label:'China',       unit:'Mill. USD', sources:[
          {freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_china'},
          {freq:'Q', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_trimes.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_china'},
          {freq:'A', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_china'}
      ]},
      { id:'sc_jap',   label:'Japón',       unit:'Mill. USD', sources:[
          {freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_japon'},
          {freq:'Q', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_trimes.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_japon'},
          {freq:'A', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_japon'}
      ]},
      { id:'sc_ind',   label:'India',       unit:'Mill. USD', sources:[
          {freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_india'},
          {freq:'Q', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_trimes.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_india'},
          {freq:'A', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_india'}
      ]},
      { id:'sc_rus',   label:'Rusia',       unit:'Mill. USD', sources:[
          {freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_rusia'},
          {freq:'Q', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_trimes.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_rusia'}
      ]},
      { id:'sc_cor',   label:'Corea',       unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_corea'}]},
      { id:'sc_tai',   label:'Tailandia',   unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_tailandia'}]},
      { id:'sc_twn',   label:'Taiwán',      unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_taiwan'}]},
      { id:'sc_vie',   label:'Vietnam',     unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_vietnam'}]},
      { id:'sc_idn',   label:'Indonesia',   unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_indonesia'}]},
      { id:'sc_isr',   label:'Israel',      unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_israel'}]},
      { id:'sc_aus',   label:'Australia',   unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_australia'}]},
      { id:'sc_nzl',   label:'Nueva Zelanda',unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_nueva_zelanda'}]},
      { id:'sc_reap',  label:'Resto Asia Pac.',unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_resto_asia_pacifico'}]}
    ]},
    { sub:'África', items:[
      { id:'sc_ang',   label:'Angola',      unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_angola'}]},
      { id:'sc_arg2',  label:'Argelia',     unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_argelia'}]},
      { id:'sc_egi',   label:'Egipto',      unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_egipto'}]},
      { id:'sc_mar',   label:'Marruecos',   unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_marruecos'}]},
      { id:'sc_saf',   label:'Sudáfrica',   unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_sudafrica'}]},
      { id:'sc_reaf',  label:'Resto África',unit:'Mill. USD', sources:[{freq:'M', file:'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv', dateCol:'indice_tiempo', valCol:'ica_saldo_comercial_resto_africa'}]}
    ]}
  ]},

  /* ── SECTOR EXTERNO: BALANCE DE PAGOS ── */

  { grp:'Balance de Pagos (MBP6)', clr:'#8b5cf6', subs:[
    { sub:'Cuenta Corriente', items:[
      { id:'bp_cc',    label:'Total Cuenta Corriente',           unit:'Mill. USD', sources:[
          {freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'total_cuenta_corriente'},
          {freq:'A', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv',      dateCol:'indice_tiempo', valCol:'total_cuenta_corriente'}
      ]},
      { id:'bp_bys',   label:'Bienes y Servicios',              unit:'Mill. USD', sources:[
          {freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'cuenta_corriente_total_bienes_servicios'},
          {freq:'A', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv',      dateCol:'indice_tiempo', valCol:'cuenta_corriente_total_bienes_servicios'}
      ]},
      { id:'bp_bienes',label:'  ↳ Bienes (neto)',               unit:'Mill. USD', sources:[
          {freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'cuenta_corriente_bienes_servicios_total_bienes'},
          {freq:'A', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv',      dateCol:'indice_tiempo', valCol:'cuenta_corriente_bienes_servicios_total_bienes'}
      ]},
      { id:'bp_exp',   label:'    ↳ Exportaciones FOB',         unit:'Mill. USD', sources:[
          {freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'cuenta_corrientes_bienes_servicios_bienes_exportaciones_fob'},
          {freq:'A', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv',      dateCol:'indice_tiempo', valCol:'cuenta_corrientes_bienes_servicios_bienes_exportaciones_fob'}
      ]},
      { id:'bp_imp',   label:'    ↳ Importaciones FOB',         unit:'Mill. USD', sources:[
          {freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'cuenta_corrientes_bienes_servicios_bienes_importaciones_fob'},
          {freq:'A', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv',      dateCol:'indice_tiempo', valCol:'cuenta_corrientes_bienes_servicios_bienes_importaciones_fob'}
      ]},
      { id:'bp_serv',  label:'  ↳ Servicios (neto)',            unit:'Mill. USD', sources:[
          {freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'cuenta_corriente_bienes_servicios_total_servicios'},
          {freq:'A', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv',      dateCol:'indice_tiempo', valCol:'cuenta_corriente_bienes_servicios_total_servicios'}
      ]},
      { id:'bp_si',    label:'    ↳ Ingresos de Servicios',     unit:'Mill. USD', sources:[{freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'cuenta_corriente_bienes_servicios_ingresos_servicios'}]},
      { id:'bp_se',    label:'    ↳ Egresos de Servicios',      unit:'Mill. USD', sources:[{freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'cuenta_corriente_bienes_servicios_egresos_servicios'}]},
      { id:'bp_ip',    label:'Ingresos Primarios',              unit:'Mill. USD', sources:[
          {freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'cuenta_corriente_total_ingresos_primarios'},
          {freq:'A', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv',      dateCol:'indice_tiempo', valCol:'cuenta_corriente_total_ingresos_primarios'}
      ]},
      { id:'bp_ip_rem',label:'  ↳ Remuneración de Empleados',  unit:'Mill. USD', sources:[
          {freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'cuenta_corriente_ingresos_primarios_rem_empleados'},
          {freq:'A', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv',      dateCol:'indice_tiempo', valCol:'cuenta_corriente_ingresos_primarios_rem_empleados'}
      ]},
      { id:'bp_ip_ri', label:'  ↳ Rentas de Inversión (total)',unit:'Mill. USD', sources:[
          {freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'cuenta_corriente_ingresos_primarios_total_rentas_inversion'},
          {freq:'A', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv',      dateCol:'indice_tiempo', valCol:'cuenta_corriente_ingresos_primarios_total_rentas_inversion'}
      ]},
      { id:'bp_ip_id', label:'    ↳ Inv. Directa',             unit:'Mill. USD', sources:[
          {freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'cta_cte_ingresos_primarios_rentas_inversion_directa'},
          {freq:'A', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv',      dateCol:'indice_tiempo', valCol:'cta_cte_ingresos_primarios_rentas_inversion_directa'}
      ]},
      { id:'bp_ip_ic', label:'    ↳ Inv. de Cartera',          unit:'Mill. USD', sources:[
          {freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'ingresos_primarios_rentas_inversion_inversion_cartera'},
          {freq:'A', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv',      dateCol:'indice_tiempo', valCol:'ingresos_primarios_rentas_inversion_inversion_cartera'}
      ]},
      { id:'bp_ip_oi', label:'    ↳ Otra Inversión',           unit:'Mill. USD', sources:[{freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'cuenta_corriente_ingresos_primarios_rentas_otra_inversion'}]},
      { id:'bp_is',    label:'Ingresos Secundarios',           unit:'Mill. USD', sources:[
          {freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'cuenta_corriente_ingresos_secundarios'},
          {freq:'A', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv',      dateCol:'indice_tiempo', valCol:'cuenta_corriente_ingresos_secundarios'}
      ]}
    ]},
    { sub:'Cuenta Financiera', items:[
      { id:'bp_cap',   label:'Cuenta Capital',                 unit:'Mill. USD', sources:[
          {freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'total_cuenta_capital'},
          {freq:'A', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv',      dateCol:'indice_tiempo', valCol:'total_cuenta_capital'}
      ]},
      { id:'bp_cf',    label:'Total Cuenta Financiera',        unit:'Mill. USD', sources:[
          {freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'total_cuenta_financiera'},
          {freq:'A', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv',      dateCol:'indice_tiempo', valCol:'total_cuenta_financiera'}
      ]},
      { id:'bp_id',    label:'Inversión Directa',              unit:'Mill. USD', sources:[
          {freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'cuenta_financiera_total_inversion_directa'},
          {freq:'A', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv',      dateCol:'indice_tiempo', valCol:'cuenta_financiera_total_inversion_directa'}
      ]},
      { id:'bp_id_ap', label:'  ↳ Activos: Particip. Capital', unit:'Mill. USD', sources:[{freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'cta_fin_inversion_directa_activos_participaciones_capital'}]},
      { id:'bp_id_ad', label:'  ↳ Activos: Inst. Deuda',       unit:'Mill. USD', sources:[{freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'cuenta_financiera_inversion_directa_activos_instrumentosuda'}]},
      { id:'bp_id_pp', label:'  ↳ Pasivos: Particip. Capital', unit:'Mill. USD', sources:[{freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'cta_fin_inversion_directa_pasivos_participaciones_capital'}]},
      { id:'bp_id_pd', label:'  ↳ Pasivos: Inst. Deuda',       unit:'Mill. USD', sources:[{freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'cta_fin_inversion_directa_pasivos_instrumentos_deuda'}]},
      { id:'bp_ic',    label:'Inversión de Cartera',           unit:'Mill. USD', sources:[
          {freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'cuenta_financiera_total_inversion_cartera'},
          {freq:'A', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv',      dateCol:'indice_tiempo', valCol:'cuenta_financiera_total_inversion_cartera'}
      ]},
      { id:'bp_ic_ap', label:'  ↳ Activos: Participaciones',   unit:'Mill. USD', sources:[{freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'cta_fin_inversion_cartera_activos_participaciones_capital'}]},
      { id:'bp_ic_ad', label:'  ↳ Activos: Inst. Deuda',       unit:'Mill. USD', sources:[{freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'cuenta_financiera_inversion_cartera_activos_instrumentosuda'}]},
      { id:'bp_ic_pp', label:'  ↳ Pasivos: Participaciones',   unit:'Mill. USD', sources:[{freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'cta_fin_inversion_cartera_pasivos_participaciones_capital'}]},
      { id:'bp_ic_pd', label:'  ↳ Pasivos: Inst. Deuda',       unit:'Mill. USD', sources:[{freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'cuenta_financiera_inversion_cartera_pasivos_instrumentosuda'}]},
      { id:'bp_df',    label:'Derivados Financieros',          unit:'Mill. USD', sources:[{freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'cuenta_financierarivados_financieros'}]},
      { id:'bp_oi',    label:'Otra Inversión',                 unit:'Mill. USD', sources:[
          {freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'cuenta_financiera_total_otra_inversion'},
          {freq:'A', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv',      dateCol:'indice_tiempo', valCol:'cuenta_financiera_total_otra_inversion'}
      ]},
      { id:'bp_oi_a',  label:'  ↳ Activos (adquisición neta)', unit:'Mill. USD', sources:[{freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'cta_fin_otra_inversion_adquisicion_neta_activos_financieros'}]},
      { id:'bp_oi_p',  label:'  ↳ Pasivos (emisión neta)',     unit:'Mill. USD', sources:[{freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'cuenta_financieratra_inversion_emision_neta_pasivos'}]},
      { id:'bp_res',   label:'Activos de Reserva',             unit:'Mill. USD', sources:[
          {freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'activos_reserva'},
          {freq:'A', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv',      dateCol:'indice_tiempo', valCol:'activos_reserva'}
      ]},
      { id:'bp_err',   label:'Errores y Omisiones',            unit:'Mill. USD', sources:[
          {freq:'Q', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv', dateCol:'indice_tiempo', valCol:'errores_omisiones_netos'},
          {freq:'A', file:'balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv',      dateCol:'indice_tiempo', valCol:'errores_omisiones_netos'}
      ]}
    ]}
  ]},

  /* ── PBI Y CUENTAS NACIONALES ── */

  { grp:'PBI y Cuentas Nacionales', clr:'#ec4899', subs:[
    { sub:'En dólares (MEP)', items:[
      { id:'pbi_usd',  label:'PBI — USD MEP (trimestral)',    file:'pbi_trimestral_usd_mep.csv', dateCol:'periodo', valCol:'pbi_usd_mm',       unit:'Mill. USD', freq:'Q' },
      { id:'tc_mep_q', label:'TC MEP promedio (trimestral)',  file:'pbi_trimestral_usd_mep.csv', dateCol:'periodo', valCol:'tc_mep_promedio',   unit:'ARS/USD',   freq:'Q' }
    ]},
    { sub:'En pesos corrientes', items:[
      { id:'pbi_ars',  label:'PBI — Pesos corrientes',        file:'pbi_trimestral_usd_mep.csv',                                              dateCol:'periodo',       valCol:'pbi_pesos_mm',                     unit:'Mill. ARS', freq:'Q' },
      { id:'pbi_dol',  label:'PBI — USD corriente (INDEC)',   file:'pbi_usd_pc_producto_interno_bruto_precios_corrientes_base_1993_valores_.csv', dateCol:'indice_tiempo', valCol:'pib_dolares_precios_corrientes',  unit:'Mill. USD', freq:'Q' },
      { id:'pbi_pc',   label:'PBI per cápita (USD)',          file:'pbi_usd_pc_producto_interno_bruto_precios_corrientes_base_1993_valores_.csv', dateCol:'indice_tiempo', valCol:'pib_per_capita_dolares_corrientes', unit:'USD',      freq:'Q' },
      { id:'pbi_tcn',  label:'Tipo de Cambio Nominal (INDEC)',file:'pbi_usd_pc_producto_interno_bruto_precios_corrientes_base_1993_valores_.csv', dateCol:'indice_tiempo', valCol:'tcn_pesos_dolares',               unit:'ARS/USD',  freq:'Q' },
      { id:'pbi_ipc',  label:'Índice de Precios Constantes',  file:'pbi_usd_pc_producto_interno_bruto_precios_corrientes_base_1993_valores_.csv', dateCol:'indice_tiempo', valCol:'indice_precios_constantes',        unit:'Índice',   freq:'Q' }
    ]},
    { sub:'Oferta y Demanda Agregada (pesos const. 2004)', items:[
      { id:'od_pbi',          label:'PBI (constante 2004)',       file:'oferta_demanda.csv', dateCol:'fecha', valCol:'pbi_const',          unit:'Mill. ARS const.', freq:'Q' },
      { id:'od_consumo_priv', label:'Consumo Privado',            file:'oferta_demanda.csv', dateCol:'fecha', valCol:'consumo_priv_const', unit:'Mill. ARS const.', freq:'Q' },
      { id:'od_consumo_pub',  label:'Consumo Público',            file:'oferta_demanda.csv', dateCol:'fecha', valCol:'consumo_pub_const',  unit:'Mill. ARS const.', freq:'Q' },
      { id:'od_fbkf',         label:'Formación Bruta de Capital', file:'oferta_demanda.csv', dateCol:'fecha', valCol:'fbkf_const',         unit:'Mill. ARS const.', freq:'Q' },
      { id:'od_expo',         label:'Exportaciones (real)',       file:'oferta_demanda.csv', dateCol:'fecha', valCol:'expo_const',          unit:'Mill. ARS const.', freq:'Q' },
      { id:'od_impo',         label:'Importaciones (real)',       file:'oferta_demanda.csv', dateCol:'fecha', valCol:'impo_const',          unit:'Mill. ARS const.', freq:'Q' }
    ]}
  ]},

  /* ── FINANZAS PÚBLICAS ── */

  { grp:'Finanzas Públicas', clr:'#84cc16', subs:[
    { sub:'Resultado Fiscal', items:[
      { id:'fis_prima',    label:'Superávit Primario',              file:'Resultado fiscal-unificado.xlsx', dateCol:'indice_tiempo', valCol:'superavit_primario',                            unit:'Mill. ARS', freq:'M' },
      { id:'fis_prima2',   label:'Superávit Primario s/ privat.',   file:'Resultado fiscal-unificado.xlsx', dateCol:'indice_tiempo', valCol:'superavit_primario_sin_privatizaciones',        unit:'Mill. ARS', freq:'M' },
      { id:'fis_fin',      label:'Resultado Financiero',            file:'Resultado fiscal-unificado.xlsx', dateCol:'indice_tiempo', valCol:'resultado_fin',                                unit:'Mill. ARS', freq:'M' },
      { id:'fis_fin2',     label:'Resultado Financiero s/ privat.', file:'Resultado fiscal-unificado.xlsx', dateCol:'indice_tiempo', valCol:'resultado_fin_sin_privatizaciones',             unit:'Mill. ARS', freq:'M' },
      { id:'fis_res_eco',  label:'Resultado Económico',             file:'Resultado fiscal-unificado.xlsx', dateCol:'indice_tiempo', valCol:'resultado_economico_ahorro_desahorro',          unit:'Mill. ARS', freq:'M' },
      { id:'fis_prima_sf', label:'Resultado Primario s/ rentas',    file:'Resultado fiscal-unificado.xlsx', dateCol:'indice_tiempo', valCol:'resultados_primarios_sin_rentas',               unit:'Mill. ARS', freq:'M' }
    ]},
    { sub:'Ingresos', items:[
      { id:'fis_ing',      label:'Ingresos Corrientes — Total',     file:'Resultado fiscal-unificado.xlsx', dateCol:'indice_tiempo', valCol:'ing_corr',                                     unit:'Mill. ARS', freq:'M' },
      { id:'fis_ing_trib', label:'  ↳ Tributarios',                 file:'Resultado fiscal-unificado.xlsx', dateCol:'indice_tiempo', valCol:'ing_corr_ing_tributarios',                     unit:'Mill. ARS', freq:'M' },
      { id:'fis_ing_ss',   label:'  ↳ Aportes Seg. Social',         file:'Resultado fiscal-unificado.xlsx', dateCol:'indice_tiempo', valCol:'ing_corr_aportes_contrib_seg_soc',             unit:'Mill. ARS', freq:'M' },
      { id:'fis_ing_ntrib',label:'  ↳ No Tributarios',              file:'Resultado fiscal-unificado.xlsx', dateCol:'indice_tiempo', valCol:'ing_corr_ing_no_tributarios',                  unit:'Mill. ARS', freq:'M' },
      { id:'fis_ing_rp',   label:'  ↳ Rentas de la Propiedad',      file:'Resultado fiscal-unificado.xlsx', dateCol:'indice_tiempo', valCol:'ing_corr_ren_prop_total_ren_prop',             unit:'Mill. ARS', freq:'M' },
      { id:'fis_ing_ren_bcra',label:'  ↳ Rentas percibidas BCRA',  file:'Resultado fiscal-unificado.xlsx', dateCol:'indice_tiempo', valCol:'ing_corr_ren_prop_ren_percidas_bcra',           unit:'Mill. ARS', freq:'M' },
      { id:'fis_ing_tc',   label:'  ↳ Transf. Corrientes',          file:'Resultado fiscal-unificado.xlsx', dateCol:'indice_tiempo', valCol:'ing_corr_transf_corr',                         unit:'Mill. ARS', freq:'M' }
    ]},
    { sub:'Gastos', items:[
      { id:'fis_gtos',     label:'Gastos Corrientes — Total',       file:'Resultado fiscal-unificado.xlsx', dateCol:'indice_tiempo', valCol:'gtos_corr',                                    unit:'Mill. ARS', freq:'M' },
      { id:'fis_gtos_rem', label:'  ↳ Remuneraciones',              file:'Resultado fiscal-unificado.xlsx', dateCol:'indice_tiempo', valCol:'gtos_corr_gtos_cons_operacion_remuneraciones',  unit:'Mill. ARS', freq:'M' },
      { id:'fis_gtos_bs',  label:'  ↳ Bienes y Servicios',          file:'Resultado fiscal-unificado.xlsx', dateCol:'indice_tiempo', valCol:'gtos_corr_gtos_cons_operacion_bienes_servicios',unit:'Mill. ARS', freq:'M' },
      { id:'fis_gtos_ii',  label:'  ↳ Intereses Deuda Interna',     file:'Resultado fiscal-unificado.xlsx', dateCol:'indice_tiempo', valCol:'gtos_corr_int_ot_ren_prop_int_deuda_int',      unit:'Mill. ARS', freq:'M' },
      { id:'fis_gtos_ie',  label:'  ↳ Intereses Deuda Externa',     file:'Resultado fiscal-unificado.xlsx', dateCol:'indice_tiempo', valCol:'gtos_corr_int_ot_ren_prop_int_deuda_ext',      unit:'Mill. ARS', freq:'M' },
      { id:'fis_gtos_int_n',label:' ↳ Intereses Netos',            file:'Resultado fiscal-unificado.xlsx', dateCol:'indice_tiempo', valCol:'gtos_corr_int_ot_ren_prop_int_netos',           unit:'Mill. ARS', freq:'M' },
      { id:'fis_gtos_ss',  label:'  ↳ Prestaciones Seg. Social',    file:'Resultado fiscal-unificado.xlsx', dateCol:'indice_tiempo', valCol:'gtos_corr_prestaciones_seg_soc',               unit:'Mill. ARS', freq:'M' },
      { id:'fis_gtos_tcp', label:'  ↳ Transf. Corrientes Prov.',    file:'Resultado fiscal-unificado.xlsx', dateCol:'indice_tiempo', valCol:'gtos_corr_transf_corr_sec_pub_prov_caba_rec_cop',unit:'Mill. ARS', freq:'M' },
      { id:'fis_gtos_uni', label:'  ↳ Transf. Corrientes Univ.',    file:'Resultado fiscal-unificado.xlsx', dateCol:'indice_tiempo', valCol:'gtos_corr_transf_corr_sec_pub_uni',             unit:'Mill. ARS', freq:'M' },
      { id:'fis_gtos_cap', label:'Gastos de Capital — Total',       file:'Resultado fiscal-unificado.xlsx', dateCol:'indice_tiempo', valCol:'gtos_cap',                                     unit:'Mill. ARS', freq:'M' },
      { id:'fis_gtos_ird', label:'  ↳ Inversión Real Directa',      file:'Resultado fiscal-unificado.xlsx', dateCol:'indice_tiempo', valCol:'gtos_cap_inversion_real_directa',               unit:'Mill. ARS', freq:'M' }
    ]}
  ]},

  /* ── DEUDA Y RIESGO SOBERANO ── */

  { grp:'Deuda y Defaults', clr:'#f97316', subs:[
    { sub:'Historia Crediticia', items:[
      { id:'def_hist',  label:'Nº de Defaults (histórico)',  file:'defaults_history.csv',    dateCol:'fecha', valCol:'n_defaults',          unit:'count', freq:'D' },
      { id:'yrs_def',   label:'Años desde último Default',   file:'years_since_default.csv', dateCol:'fecha', valCol:'years_since_default', unit:'años',  freq:'D' }
    ]},
    { sub:'Saldo de Deuda Bruta (USD)', items:[
      { id:'deu_total',    label:'Deuda Bruta Total',              file:'saldo_deuda.csv', dateCol:'fecha', valCol:'deuda_total',            unit:'Mill. USD', freq:'Q' },
      { id:'deu_normal',   label:'  ↳ En situación de pago normal',file:'saldo_deuda.csv', dateCol:'fecha', valCol:'deuda_pago_normal',      unit:'Mill. USD', freq:'Q' },
      { id:'deu_titulos',  label:'  ↳ Títulos Públicos',           file:'saldo_deuda.csv', dateCol:'fecha', valCol:'deuda_titulos_publicos', unit:'Mill. USD', freq:'Q' },
      { id:'deu_bonos',    label:'    ↳ Bonos',                    file:'saldo_deuda.csv', dateCol:'fecha', valCol:'deuda_bonos',            unit:'Mill. USD', freq:'Q' },
      { id:'deu_letras',   label:'    ↳ Letras',                   file:'saldo_deuda.csv', dateCol:'fecha', valCol:'deuda_letras',           unit:'Mill. USD', freq:'Q' },
      { id:'deu_org',      label:'  ↳ Organismos Internacionales', file:'saldo_deuda.csv', dateCol:'fecha', valCol:'deuda_org_internac',     unit:'Mill. USD', freq:'Q' },
      { id:'deu_fmi',      label:'    ↳ FMI',                      file:'saldo_deuda.csv', dateCol:'fecha', valCol:'deuda_fmi',              unit:'Mill. USD', freq:'Q' },
      { id:'deu_bid',      label:'    ↳ BID',                      file:'saldo_deuda.csv', dateCol:'fecha', valCol:'deuda_bid',              unit:'Mill. USD', freq:'Q' },
      { id:'deu_birf',     label:'    ↳ BIRF',                     file:'saldo_deuda.csv', dateCol:'fecha', valCol:'deuda_birf',             unit:'Mill. USD', freq:'Q' },
      { id:'deu_caf',      label:'    ↳ CAF',                      file:'saldo_deuda.csv', dateCol:'fecha', valCol:'deuda_caf',              unit:'Mill. USD', freq:'Q' },
      { id:'deu_bilat',    label:'  ↳ Bilaterales',                file:'saldo_deuda.csv', dateCol:'fecha', valCol:'deuda_bilaterales',      unit:'Mill. USD', freq:'Q' },
      { id:'deu_cparis',   label:'  ↳ Club de París',              file:'saldo_deuda.csv', dateCol:'fecha', valCol:'deuda_club_paris',       unit:'Mill. USD', freq:'Q' },
      { id:'deu_bcra',     label:'  ↳ Anticipos BCRA',             file:'saldo_deuda.csv', dateCol:'fecha', valCol:'deuda_anticipos_bcra',   unit:'Mill. USD', freq:'Q' },
      { id:'deu_diferido', label:'En situación de pago diferido',  file:'saldo_deuda.csv', dateCol:'fecha', valCol:'deuda_pago_diferido',    unit:'Mill. USD', freq:'Q' },
      { id:'deu_elegib',   label:'Deuda elegible pendiente reestr.',file:'saldo_deuda.csv', dateCol:'fecha', valCol:'deuda_elegible_pend',   unit:'Mill. USD', freq:'Q' }
    ]},
    { sub:'Vencimientos a 2 años (USD)', items:[
      { id:'venc_total',  label:'Vencimientos Totales',    file:'vencimientos_2y.csv', dateCol:'fecha', valCol:'venc_total',       unit:'Mill. USD', freq:'Q' },
      { id:'venc_bonos',  label:'  ↳ Bonos',               file:'vencimientos_2y.csv', dateCol:'fecha', valCol:'venc_bonos',       unit:'Mill. USD', freq:'Q' },
      { id:'venc_fmi',    label:'  ↳ FMI',                 file:'vencimientos_2y.csv', dateCol:'fecha', valCol:'venc_fmi',         unit:'Mill. USD', freq:'Q' },
      { id:'venc_bid',    label:'  ↳ BID',                 file:'vencimientos_2y.csv', dateCol:'fecha', valCol:'venc_bid',         unit:'Mill. USD', freq:'Q' },
      { id:'venc_birf',   label:'  ↳ BIRF',                file:'vencimientos_2y.csv', dateCol:'fecha', valCol:'venc_birf',        unit:'Mill. USD', freq:'Q' },
      { id:'venc_caf',    label:'  ↳ CAF',                 file:'vencimientos_2y.csv', dateCol:'fecha', valCol:'venc_caf',         unit:'Mill. USD', freq:'Q' },
      { id:'venc_letras', label:'  ↳ Letras del Tesoro',   file:'vencimientos_2y.csv', dateCol:'fecha', valCol:'venc_letras',      unit:'Mill. USD', freq:'Q' },
      { id:'venc_bilat',  label:'  ↳ Bilaterales',         file:'vencimientos_2y.csv', dateCol:'fecha', valCol:'venc_bilaterales', unit:'Mill. USD', freq:'Q' },
      { id:'venc_banca',  label:'  ↳ Banca Comercial',     file:'vencimientos_2y.csv', dateCol:'fecha', valCol:'venc_banca_com',   unit:'Mill. USD', freq:'Q' }
    ]}
  ]},

  /* ── CONDICIONES FINANCIERAS GLOBALES ── */

  { grp:'Condiciones Financieras Globales', clr:'#ef4444', subs:[
    { sub:'Volatilidad e Incertidumbre', items:[
      { id:'vix',    label:'VIX — CBOE Volatility Index', file:'vix.csv',    dateCol:'fecha', valCol:'Adj Close', unit:'Índice', freq:'D' },
      { id:'dxy',    label:'DXY — US Dollar Index',       file:'dxy.csv',    dateCol:'fecha', valCol:'Adj Close', unit:'Índice', freq:'D' }
    ]},
    { sub:'Tasas de Interés EEUU', items:[
      { id:'ust2y',  label:'US Treasury 2Y',  file:'ust2y.csv',  dateCol:'fecha', valCol:'Adj Close', unit:'%', freq:'D' },
      { id:'ust5y',  label:'US Treasury 5Y',  file:'ust5y.csv',  dateCol:'fecha', valCol:'Adj Close', unit:'%', freq:'D' },
      { id:'ust10y', label:'US Treasury 10Y', file:'ust10y.csv', dateCol:'fecha', valCol:'Adj Close', unit:'%', freq:'D' },
      { id:'ust30y', label:'US Treasury 30Y', file:'ust30y.csv', dateCol:'fecha', valCol:'Adj Close', unit:'%', freq:'D' }
    ]},
    { sub:'OFR — Financial Stress Index', items:[
      { id:'ofr_fsi', label:'OFR FSI — Total',               file:'ofr_fsi.csv', dateCol:'Date', valCol:'OFR FSI',                  unit:'Índice', freq:'D' },
      { id:'ofr_cre', label:'  ↳ Crédito',                   file:'ofr_fsi.csv', dateCol:'Date', valCol:'Credit',                   unit:'Índice', freq:'D' },
      { id:'ofr_eq',  label:'  ↳ Acciones (valuación)',       file:'ofr_fsi.csv', dateCol:'Date', valCol:'Equity valuation',         unit:'Índice', freq:'D' },
      { id:'ofr_sf',  label:'  ↳ Activos Seguros',            file:'ofr_fsi.csv', dateCol:'Date', valCol:'Safe assets',              unit:'Índice', freq:'D' },
      { id:'ofr_fund',label:'  ↳ Financiamiento',             file:'ofr_fsi.csv', dateCol:'Date', valCol:'Funding',                  unit:'Índice', freq:'D' },
      { id:'ofr_vol', label:'  ↳ Volatilidad',                file:'ofr_fsi.csv', dateCol:'Date', valCol:'Volatility',               unit:'Índice', freq:'D' },
      { id:'ofr_us',  label:'  ↳ Componente EEUU',            file:'ofr_fsi.csv', dateCol:'Date', valCol:'United States',            unit:'Índice', freq:'D' },
      { id:'ofr_adv', label:'  ↳ Otras Ec. Avanzadas',        file:'ofr_fsi.csv', dateCol:'Date', valCol:'Other advanced economies', unit:'Índice', freq:'D' },
      { id:'ofr_em',  label:'  ↳ Mercados Emergentes',        file:'ofr_fsi.csv', dateCol:'Date', valCol:'Emerging markets',         unit:'Índice', freq:'D' }
    ]}
  ]}
];"""

# Replace CATALOG block
old_catalog_re = re.compile(r'/\* ── CATALOG ── \*/.*?^];', re.DOTALL | re.MULTILINE)
m = old_catalog_re.search(html)
assert m, "CATALOG block not found!"
html = html[:m.start()] + NEW_CATALOG + html[m.end():]
print("CATALOG replaced")

# ═══════════════════════════════════════════════════════════════════════
# 2. UPDATE buildIndex
# ═══════════════════════════════════════════════════════════════════════
old_buildIndex = """function buildIndex() {
  function indexItems(items, clr) {
    items.forEach(it => { IDX[it.id] = it; it.grpClr = clr; });
  }
  function indexLevel(subs, clr) {
    subs.forEach(s => {
      if (s.items) indexItems(s.items, clr);
      if (s.subs)  indexLevel(s.subs, clr);
    });
  }
  CATALOG.forEach(g => {
    if (g.items) indexItems(g.items, g.clr);
    if (g.subs)  indexLevel(g.subs, g.clr);
  });
}"""

new_buildIndex = """function buildIndex() {
  const order = {D:0,W:1,M:2,Q:3,A:4};
  function indexItems(items, clr) {
    items.forEach(it => {
      IDX[it.id] = it;
      it.grpClr = clr;
      if (it.sources && !it.freq) {
        it.freq = it.sources.reduce((best, s) => order[s.freq] < order[best] ? s.freq : best, it.sources[0].freq);
      }
    });
  }
  function indexLevel(subs, clr) {
    subs.forEach(s => {
      if (s.items) indexItems(s.items, clr);
      if (s.subs)  indexLevel(s.subs, clr);
    });
  }
  CATALOG.forEach(g => {
    if (g.items) indexItems(g.items, g.clr);
    if (g.subs)  indexLevel(g.subs, g.clr);
  });
}"""

assert old_buildIndex in html, "buildIndex not found!"
html = html.replace(old_buildIndex, new_buildIndex, 1)
print("buildIndex updated")

# ═══════════════════════════════════════════════════════════════════════
# 3. UPDATE getSeries
# ═══════════════════════════════════════════════════════════════════════
old_getSeries = """async function getSeries(id) {
  const item = IDX[id];
  if (!item) throw new Error(`Serie ${id} no encontrada`);
  const parsed = await loadFile(item.file);
  return extractSeries(parsed, item.dateCol, item.valCol);
}"""

new_getSeries = """async function getSeries(id) {
  const item = IDX[id];
  if (!item) throw new Error(`Serie ${id} no encontrada`);
  if (!item.sources) {
    const parsed = await loadFile(item.file);
    return { ...extractSeries(parsed, item.dateCol, item.valCol), nativeFreq: item.freq };
  }
  const order = {D:0,W:1,M:2,Q:3,A:4};
  const tgt = order[freq];
  const srcs = item.sources;
  let src = srcs.find(s => s.freq === freq);
  if (!src) {
    const finer = srcs.filter(s => order[s.freq] < tgt).sort((a,b) => order[b.freq]-order[a.freq]);
    if (finer.length) src = finer[0];
  }
  if (!src) {
    const coarser = srcs.filter(s => order[s.freq] > tgt).sort((a,b) => order[a.freq]-order[b.freq]);
    if (coarser.length) src = coarser[0];
  }
  if (!src) src = srcs[0];
  const parsed = await loadFile(src.file);
  return { ...extractSeries(parsed, src.dateCol, src.valCol), nativeFreq: src.freq };
}"""

assert old_getSeries in html, "getSeries not found!"
html = html.replace(old_getSeries, new_getSeries, 1)
print("getSeries updated")

# ═══════════════════════════════════════════════════════════════════════
# 4. UPDATE applyTransforms signature
# ═══════════════════════════════════════════════════════════════════════
old_applyT = """async function applyTransforms(dates, values, item) {
  let d = [...dates], v = [...values];
  const cfg = getCfg(item.id);
  // 1. resample
  ({ dates:d, values:v } = resample(d, v, item.freq, freq));"""

new_applyT = """async function applyTransforms(dates, values, item, nativeFreq) {
  let d = [...dates], v = [...values];
  const cfg = getCfg(item.id);
  // 1. resample
  ({ dates:d, values:v } = resample(d, v, nativeFreq || item.freq, freq));"""

assert old_applyT in html, "applyTransforms not found!"
html = html.replace(old_applyT, new_applyT, 1)
print("applyTransforms updated")

# ═══════════════════════════════════════════════════════════════════════
# 5. UPDATE renderInd call site
# ═══════════════════════════════════════════════════════════════════════
old_ri = "  let { dates, values, maValues } = await applyTransforms(raw.dates, raw.values, item);"
new_ri = "  let { dates, values, maValues } = await applyTransforms(raw.dates, raw.values, item, raw.nativeFreq);"
count = html.count(old_ri)
assert count >= 1, f"renderInd applyTransforms call not found (found {count})"
html = html.replace(old_ri, new_ri)
print(f"applyTransforms call sites updated ({count})")

# ═══════════════════════════════════════════════════════════════════════
# 6. UPDATE analysis tab
# ═══════════════════════════════════════════════════════════════════════
old_anl1 = """  const raw1 = await getSeries(s1);
  const it1 = IDX[s1];
  let dates = raw1.dates, vals = raw1.values;"""
new_anl1 = """  const raw1 = await getSeries(s1);
  const it1 = IDX[s1];
  const freq1 = raw1.nativeFreq || it1.freq;
  let dates = raw1.dates, vals = raw1.values;"""
assert old_anl1 in html, "analysis raw1 not found"
html = html.replace(old_anl1, new_anl1, 1)

old_r1 = "    const res = resample(dates, vals, it1.freq, fFreq);"
new_r1 = "    const res = resample(dates, vals, freq1, fFreq);"
assert old_r1 in html, "analysis resample1 not found"
html = html.replace(old_r1, new_r1, 1)

old_anl2 = """    const raw2 = await getSeries(s2);
    const it2 = IDX[s2];
    let d2 = raw2.dates, v2 = raw2.values;"""
new_anl2 = """    const raw2 = await getSeries(s2);
    const it2 = IDX[s2];
    const freq2 = raw2.nativeFreq || it2.freq;
    let d2 = raw2.dates, v2 = raw2.values;"""
assert old_anl2 in html, "analysis raw2 not found"
html = html.replace(old_anl2, new_anl2, 1)

old_r2 = "      const res2 = resample(d2, v2, it2.freq, fFreq);"
new_r2 = "      const res2 = resample(d2, v2, freq2, fFreq);"
assert old_r2 in html, "analysis resample2 not found"
html = html.replace(old_r2, new_r2, 1)

old_anl3 = """    const raw2 = await getSeries(s2);
    const it2 = IDX[s2];
    dates = raw2.dates; vals = raw2.values;"""
new_anl3 = """    const raw2 = await getSeries(s2);
    const it2 = IDX[s2];
    const freq2b = raw2.nativeFreq || it2.freq;
    dates = raw2.dates; vals = raw2.values;"""
assert old_anl3 in html, "analysis raw2b not found"
html = html.replace(old_anl3, new_anl3, 1)

old_r3 = "      const res = resample(dates, vals, it2.freq, fFreq);"
new_r3 = "      const res = resample(dates, vals, freq2b, fFreq);"
assert old_r3 in html, "analysis resample2b not found"
html = html.replace(old_r3, new_r3, 1)
print("Analysis tab updated")

# ═══════════════════════════════════════════════════════════════════════
# WRITE
# ═══════════════════════════════════════════════════════════════════════
with open(TEMPLATE, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"\nDone. Template saved: {TEMPLATE}")
