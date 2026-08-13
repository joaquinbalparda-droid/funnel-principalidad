#!/usr/bin/env python3
"""
Dashboard Historico Principalidad - Script de actualizacion
Query: meli-bi-data.SBOX_SELLERSMP.Asignados_Historicos_Principalidad_V3

USO: python actualizar_historico.py
REQUISITO: gcloud auth application-default login
"""

import json, base64, sys, requests
from datetime import datetime

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8','utf8'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ('utf-8','utf8'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ── CONFIGURACION ──────────────────────────────────────────────
import os as _os
GITHUB_TOKEN  = _os.environ.get("PERSONAL_GITHUB_TOKEN", "")
GITHUB_REPO   = "joaquinbalparda-droid/funnel-principalidad"
GITHUB_FILE   = "funnel_dashboard.html"
GITHUB_BRANCH = "main"

import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH  = os.path.join(SCRIPT_DIR, "funnel_dashboard.html")
BQ_PROJECT = "meli-bi-data"

# ── DIAS HABILES POR MES ──────────────────────────────────────
# Nov/Dic 2025: valores aproximados (ajustar si hace falta)
DIAS_HABILES = {
    202511: 19,   # Nov 2025 (aprox)
    202512: 21,   # Dic 2025 (aprox)
    202601: 21,
    202602: 18,
    202603: 20,
    202604: 20,   # Abril 2026 (mes completo)
    202605: 19,
    202606: 20,
    202607: 22,
    202608: 20,
    202609: 22,
    202610: 21,
    202611: 20,
    202612: 21,
}

# ── TL CASE ───────────────────────────────────────────────────
TL_CASE = """
    CASE
      WHEN Nombre_asesor IN ('Agustin Diz','Carolina Delgado','Juan Cruz Rial','Julian Torres',
                             'Manuel Elizarraga','Mariana Gonzalez','Rocio Angueira',
                             'Evelyn Albarracin','Manuel Uranga','Rocio Gonzalez','Nelson Salas',
                             'Mayra Marchese','Maria Segovia','Matías Valenzuela','Matias Valenzuela',
                             'Camila Blanco','Franco Mantilla',
                             'Lucas Garcia','Cristian Gallo') THEN 'mjo'
      WHEN Nombre_asesor IN ('Alejandro Diaz','Analia Maisonnave','Camila Coca','Catalina Fernandez',
                             'Diego Moreno','Emanuel Dursi','Federico Vitabile','Giselda Allende','Matias Mesiano',
                             'Ignacio Arias','Barbara Diaz',
                             'Daniel Caceres','Romina Di Paolo','Florencia Lamas','Maria Florencia Lamas','Maximiliano Velazquez',
                             'Luca Menghini','Martina Franjo') THEN 'ag'
      WHEN Nombre_asesor IN ('Azul Pacioni','Barbara Nuñez','Diana Fraser','Francelys Perez',
                             'Joaquin Lescano','Luciana Pisacco','Micaela Marsuzi','Sebastian Jansa',
                             'Niurka Pinzon',
                             'Nicolas Barrios','Santiago Cordoba','Juan Capria',
                             'Sol Triberti','Carlos Sosa','Gonzalo Marin','Nayra Luna',
                             'Ezequiel Fernandez','Antonella Moretto','Lautaro Diaz') THEN 'fq'
      WHEN Nombre_asesor IN ('Cristina Hsieh','Sofia Zhuang',
                             'Francisco Yu','Martin Yu WEN Yu','Tzu Sung Chen') THEN 'sz'
      WHEN Nombre_asesor IN ('Agustina Brandoni','Agustina brandoni',
                             'Maria Arinelli','Maria de los Angeles Arinelli',
                             'Sofia Cornu','Sofia Cornú',
                             'Jesica Gonzalez',
                             'Marina Formati','Marina De Formati',
                             'Federico Rodriguez',
                             'Rocio Vazquez','Rocio vazquez',
                             'Fernanda Vecchio','Stefania Lloret',
                             'Rodrigo Coronel','Dorelia Batellini','Dorelia Battelini',
                             'Ayelen Rolaoser',
                             'Masielle Fiori') THEN 'th'
    END
"""

import calendar as _cal
MES_ACTUAL      = int(datetime.now().strftime('%Y%m'))
_now            = datetime.now()
MES_ANTERIOR    = (_now.year * 100 + (_now.month - 1)) if _now.month > 1 else ((_now.year - 1) * 100 + 12)
DIAS_TRANSCU    = _now.day
DIAS_DEL_MES    = _cal.monthrange(_now.year, _now.month)[1]
FACTOR_PROY     = DIAS_DEL_MES / DIAS_TRANSCU

DEVOLUCION_UNION = """
  SELECT Nombre_asesor, CAST(Cust_Id AS STRING) AS Cust_Id, CAST(Contactado AS STRING) AS Contactado, Estado
  FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Carolina_Delgado`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Agustin_Diz`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_JuanC_Rial`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Julian_Torres`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Manuel_Elizarraga`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Mariana_Gonzalez`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Rocio_Angueira`
  -- Soledad Maydana removida a partir del 30/06/2026
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Alejandro_Diaz`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Analia_Maisonnave`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Camila_Coca`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Catalina_Fernandez`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Diego_Moreno`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Emanuel_Dursi`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Fedrico_Vitabile`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Giselda_Allende`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Matias_Mesiano`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Azul_Pacioni`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Barbara_Nu\u00f1ez`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Diana_Fraser`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Francelys_Perez`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Joaquin_Lescano`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Luciana_Pisacco`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Micaela_Marsuzi`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Sebastian_Jansa`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Cristina_Hsieh`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Sofia_Zhuang`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Daniel_Caceres`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Nicolas_Barrios`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Romina_Di_Paolo`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Santiago_Cordoba`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Mayra_Marchese`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Maria_Segovia`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Matias_Valenzuela`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Maria_Florencia_Lamas`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Maximiliano_Velazquez`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Juan_Capria`
  -- Asesores nuevos junio 2026
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Agustina_Brandoni1`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Maria_Arinelli`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Sofia_Cornu`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Sol_triberti1`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_camila_blanco`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_jesica_gonzalez`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Marina_Formati`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Carlos_Sosa`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Luca_Menghini1`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Federico_Rodriguez1`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Gonzalo_Marin`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Rocio_Vazquez`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Fernanda_vecchio`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Franjo_martina`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Stefania_Lloret`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Rodrigo_Coronel`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Dorelia_Batellini`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Franco_mantilla`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Ayelen_Rolaoser`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Nayra_Luna`
  -- Asesores nuevos agosto 2026
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Masielle_Fiori`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Lucas_Garcia`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Cristian_Gallo`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Antonella_Moretto`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Lautaro_Diaz`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Ezequiel_Fernandez1`
"""

# Igual que DEVOLUCION_UNION pero incluyendo Mes_asignacion (para el fallback del mes anterior)
DEVOLUCION_UNION_CON_MES = """
  SELECT Nombre_asesor, CAST(Cust_Id AS STRING) AS Cust_Id, CAST(Contactado AS STRING) AS Contactado, Estado, Mes_asignacion
  FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Carolina_Delgado`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Agustin_Diz`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_JuanC_Rial`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Julian_Torres`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Manuel_Elizarraga`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Mariana_Gonzalez`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Rocio_Angueira`
  -- Soledad Maydana removida a partir del 30/06/2026
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Alejandro_Diaz`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Analia_Maisonnave`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Camila_Coca`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Catalina_Fernandez`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Diego_Moreno`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Emanuel_Dursi`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Fedrico_Vitabile`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Giselda_Allende`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Matias_Mesiano`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Azul_Pacioni`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Barbara_Nu\u00f1ez`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Diana_Fraser`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Francelys_Perez`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Joaquin_Lescano`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Luciana_Pisacco`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Micaela_Marsuzi`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Sebastian_Jansa`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Cristina_Hsieh`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Sofia_Zhuang`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Daniel_Caceres`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Nicolas_Barrios`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Romina_Di_Paolo`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Santiago_Cordoba`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Mayra_Marchese`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Maria_Segovia`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Matias_Valenzuela`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Maria_Florencia_Lamas`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Maximiliano_Velazquez`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Juan_Capria`
  -- Asesores nuevos junio 2026
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Agustina_Brandoni1`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Maria_Arinelli`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Sofia_Cornu`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Sol_triberti1`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_camila_blanco`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_jesica_gonzalez`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Marina_Formati`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Carlos_Sosa`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Luca_Menghini1`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Federico_Rodriguez1`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Gonzalo_Marin`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Rocio_Vazquez`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Fernanda_vecchio`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Franjo_martina`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Stefania_Lloret`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Rodrigo_Coronel`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Dorelia_Batellini`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Franco_mantilla`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Ayelen_Rolaoser`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Nayra_Luna`
  -- Asesores nuevos agosto 2026
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Masielle_Fiori`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Lucas_Garcia`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Cristian_Gallo`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Antonella_Moretto`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Lautaro_Diaz`
  UNION ALL SELECT Nombre_asesor, CAST(Cust_Id AS STRING), CAST(Contactado AS STRING), Estado, Mes_asignacion FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Ezequiel_Fernandez1`
"""

_MES_ANT_MES_NUM = _now.month - 1 if _now.month > 1 else 12   # número de mes del mes anterior (ej. 4 = abril)

QUERY = f"""
WITH tpv AS (
  SELECT
    CAST(SELLER AS STRING) AS seller_str,
    MAX(CASE WHEN MES = CAST({MES_ANTERIOR} AS STRING) THEN TPV_ARS ELSE 0 END) AS tpv_m1,
    MAX(CASE WHEN MES = CAST({MES_ACTUAL}   AS STRING) THEN TPV_ARS ELSE 0 END) AS tpv_m0
  FROM `meli-bi-data.SBOX_SELLERSMP.REPAGOS_2025_PRINCIPALIDAD_1`
  WHERE MES IN (CAST({MES_ANTERIOR} AS STRING), CAST({MES_ACTUAL} AS STRING))
  GROUP BY 1
),
mes_actual_base AS (
  -- Usa Base_Mes_Corriente (todos los leads asignados) igual que Gestion Mes Actual
  -- Devolucion se usa solo para Estado/Contactado via LEFT JOIN
  SELECT
    b.Nombre_asesor,
    d.Contactado,
    COALESCE(d.Estado, 'PENDIENTE') AS Estado,
    CASE
      WHEN (COALESCE(t.tpv_m0, 0) * {FACTOR_PROY:.4f}) > 2000000
       AND (COALESCE(t.tpv_m0, 0) * {FACTOR_PROY:.4f}) > COALESCE(t.tpv_m1, 0) * 1.3
      THEN '1' ELSE '0'
    END AS Potenciado_M1
  FROM `meli-bi-data.SBOX_SELLERSMP.Base_Mes_Corriente_Principalidad` b
  LEFT JOIN ({DEVOLUCION_UNION_CON_MES}) d
    ON  b.Nombre_asesor = d.Nombre_asesor
    AND CAST(b.Cust_Id AS STRING) = d.Cust_Id
    AND CAST(d.Mes_asignacion AS INT64) = {_now.month}
  LEFT JOIN tpv t ON CAST(b.Cust_Id AS STRING) = t.seller_str
  WHERE b.Mes_asignacion = {_now.month}
    AND b.Nombre_asesor NOT IN ('Azul Pacioni','Micaela Marsuzi','Catalina Fernandez','Camila Coca','Camila Cocca')
),
-- Fallback mes anterior: activo SOLO si la tabla historica aun no tiene datos del mes anterior.
-- Usa Mes_asignacion para identificar registros del mes anterior en las tablas en tiempo real.
mes_anterior_fallback AS (
  SELECT
    {MES_ANTERIOR} AS Mes,
    d.Nombre_asesor,
    d.Contactado,
    d.Estado,
    '0' AS Potenciado_M1
  FROM ({DEVOLUCION_UNION_CON_MES}) d
  WHERE SAFE_CAST(d.Mes_asignacion AS INT64) = {_MES_ANT_MES_NUM}
    AND NOT EXISTS (
      SELECT 1
      FROM `meli-bi-data.SBOX_SELLERSMP.Asignados_Historicos_Principalidad_V3`
      WHERE Mes = {MES_ANTERIOR}
      LIMIT 1
    )
)
SELECT
  Mes,
  {TL_CASE} AS Team_Lider,
  Nombre_asesor,
  COUNT(*)                              AS Leads,
  COUNTIF(LOWER(CAST(Contactado AS STRING)) IN ('true','si','sí','1')) AS Contactados,
  COUNTIF(Estado = 'CONVERTIDO')        AS Convertidos,
  COUNTIF(Estado = 'RECHAZADO')         AS Rechazados,
  COUNTIF(Estado IN ('NEGOCIACION', 'SOLICITUD DE TASA')) AS En_Negociacion,
  COUNTIF(Estado = 'PENDIENTE')         AS Pendientes,
  COUNTIF(Potenciado_M1 = '1')          AS Potenciados_M1
FROM (
  -- Meses cerrados (historico)
  SELECT Mes, Nombre_asesor, Contactado, Estado, CAST(Potenciado_M1 AS STRING) AS Potenciado_M1
  FROM `meli-bi-data.SBOX_SELLERSMP.Asignados_Historicos_Principalidad_V3`
  WHERE Mes >= 202511 AND Mes < {MES_ACTUAL}

  UNION ALL

  -- Fallback mes anterior (solo activo si la tabla historica no tiene ese mes todavia)
  SELECT Mes, Nombre_asesor, Contactado, Estado, Potenciado_M1
  FROM mes_anterior_fallback

  UNION ALL

  -- Mes en curso con potenciados calculados via TPV (fuente siempre = tablas en tiempo real)
  SELECT {MES_ACTUAL} AS Mes, Nombre_asesor, Contactado, Estado, Potenciado_M1
  FROM mes_actual_base
) src
GROUP BY 1, 2, 3
HAVING Team_Lider IS NOT NULL
ORDER BY 1, 2, 3
"""

QUERY_TPV_COHORT = f"""
WITH
hist_conv AS (
  -- Solo meses cerrados: excluimos el mes actual para no duplicar con curr_conv
  SELECT CAST(Cust_Id AS STRING) AS seller_str, Nombre_asesor, CAST(Mes AS INT64) AS cohort_mes
  FROM `meli-bi-data.SBOX_SELLERSMP.Asignados_Historicos_Principalidad_V3`
  WHERE Estado = 'CONVERTIDO' AND Mes >= 202501 AND Mes < {MES_ACTUAL}
),
prev_converted AS (
  -- Sellers que ya tienen cohort en meses anteriores (para excluirlos de curr_conv)
  SELECT DISTINCT seller_str FROM hist_conv
),
curr_conv AS (
  -- Solo NUEVAS conversiones del mes actual: sellers que no se convirtieron antes
  SELECT CAST(d.Cust_Id AS STRING) AS seller_str, d.Nombre_asesor, {MES_ACTUAL} AS cohort_mes
  FROM ({DEVOLUCION_UNION}) d
  LEFT JOIN prev_converted p ON CAST(d.Cust_Id AS STRING) = p.seller_str
  WHERE d.Estado = 'CONVERTIDO'
    AND p.seller_str IS NULL
),
all_conv AS (SELECT * FROM hist_conv UNION ALL SELECT * FROM curr_conv),
tpv_raw AS (
  -- Filtro de meses para evitar full scan (cohorts desde 202501, incluye M-1 de ene = 202412 y M+2 de mes actual)
  SELECT CAST(SELLER AS STRING) AS seller_str, CAST(MES AS STRING) AS mes_str, TPV_ARS,
         COALESCE(VC_ARS, 0) AS VC_ARS
  FROM `meli-bi-data.SBOX_SELLERSMP.REPAGOS_2025_PRINCIPALIDAD_1`
  WHERE SAFE_CAST(MES AS INT64) >= 202412
),
cohort_base AS (
  SELECT
    c.cohort_mes,
    {TL_CASE} AS team_lider,
    c.Nombre_asesor, c.seller_str,
    FORMAT_DATE('%Y%m', DATE_ADD(PARSE_DATE('%Y%m', CAST(c.cohort_mes AS STRING)), INTERVAL -1 MONTH)) AS mes_m1,
    CAST(c.cohort_mes AS STRING) AS mes_0,
    FORMAT_DATE('%Y%m', DATE_ADD(PARSE_DATE('%Y%m', CAST(c.cohort_mes AS STRING)), INTERVAL  1 MONTH)) AS mes_p1,
    FORMAT_DATE('%Y%m', DATE_ADD(PARSE_DATE('%Y%m', CAST(c.cohort_mes AS STRING)), INTERVAL  2 MONTH)) AS mes_p2
  FROM all_conv c
),
tpv_joined AS (
  SELECT cb.*,
    COALESCE(tm1.TPV_ARS,0)  AS tpv_minus1,
    COALESCE(tm1.VC_ARS,0)   AS vc_minus1,
    CASE WHEN cb.mes_0  = '{MES_ACTUAL}' THEN COALESCE(tm0.TPV_ARS,0)*{FACTOR_PROY:.6f} ELSE COALESCE(tm0.TPV_ARS,0) END AS tpv_m0,
    CASE WHEN cb.mes_0  = '{MES_ACTUAL}' THEN COALESCE(tm0.VC_ARS,0)*{FACTOR_PROY:.6f}  ELSE COALESCE(tm0.VC_ARS,0)  END AS vc_m0,
    CASE WHEN cb.mes_p1 = '{MES_ACTUAL}' THEN COALESCE(tp1.TPV_ARS,0)*{FACTOR_PROY:.6f} ELSE COALESCE(tp1.TPV_ARS,0) END AS tpv_p1,
    CASE WHEN cb.mes_p1 = '{MES_ACTUAL}' THEN COALESCE(tp1.VC_ARS,0)*{FACTOR_PROY:.6f}  ELSE COALESCE(tp1.VC_ARS,0)  END AS vc_p1,
    CASE WHEN cb.mes_p2 = '{MES_ACTUAL}' THEN COALESCE(tp2.TPV_ARS,0)*{FACTOR_PROY:.6f} ELSE COALESCE(tp2.TPV_ARS,0) END AS tpv_p2,
    CASE WHEN cb.mes_p2 = '{MES_ACTUAL}' THEN COALESCE(tp2.VC_ARS,0)*{FACTOR_PROY:.6f}  ELSE COALESCE(tp2.VC_ARS,0)  END AS vc_p2
  FROM cohort_base cb
  LEFT JOIN tpv_raw tm1 ON cb.seller_str=tm1.seller_str AND tm1.mes_str=cb.mes_m1
  LEFT JOIN tpv_raw tm0 ON cb.seller_str=tm0.seller_str AND tm0.mes_str=cb.mes_0
  LEFT JOIN tpv_raw tp1 ON cb.seller_str=tp1.seller_str AND tp1.mes_str=cb.mes_p1
  LEFT JOIN tpv_raw tp2 ON cb.seller_str=tp2.seller_str AND tp2.mes_str=cb.mes_p2
),
with_inc AS (
  SELECT *,
    (tpv_m0-tpv_minus1) AS inc_m0,    (tpv_p1-tpv_minus1) AS inc_m1,    (tpv_p2-tpv_minus1) AS inc_m2,
    (vc_m0-vc_minus1)   AS inc_vc_m0, (vc_p1-vc_minus1)   AS inc_vc_m1, (vc_p2-vc_minus1)   AS inc_vc_m2,
    ((tpv_m0-tpv_minus1)>2000000 AND (tpv_m0-tpv_minus1)>tpv_minus1*0.3) AS pot_m0,
    ((tpv_p1-tpv_minus1)>2000000 AND (tpv_p1-tpv_minus1)>tpv_minus1*0.3) AS pot_m1,
    ((tpv_p2-tpv_minus1)>2000000 AND (tpv_p2-tpv_minus1)>tpv_minus1*0.3) AS pot_m2
  FROM tpv_joined
)
SELECT
  cohort_mes, team_lider, Nombre_asesor,
  COUNT(*)                                               AS convertidos,
  COUNTIF(pot_m0)                                        AS pot_m0,
  SUM(CASE WHEN pot_m0 THEN inc_m0    ELSE 0 END)        AS tpv_inc_m0,
  SUM(CASE WHEN pot_m0 THEN inc_vc_m0 ELSE 0 END)        AS vc_inc_m0,
  COUNTIF(pot_m1)                                        AS pot_m1,
  SUM(CASE WHEN pot_m1 THEN inc_m1    ELSE 0 END)        AS tpv_inc_m1,
  SUM(CASE WHEN pot_m1 THEN inc_vc_m1 ELSE 0 END)        AS vc_inc_m1,
  COUNTIF(pot_m2)                                        AS pot_m2,
  SUM(CASE WHEN pot_m2 THEN inc_m2    ELSE 0 END)        AS tpv_inc_m2,
  SUM(CASE WHEN pot_m2 THEN inc_vc_m2 ELSE 0 END)        AS vc_inc_m2
FROM with_inc
WHERE team_lider IS NOT NULL
GROUP BY 1,2,3
ORDER BY 1,2,3
"""

def run_bigquery(sql):
    import subprocess
    try:
        result = subprocess.run(
            ['bq','query','--use_legacy_sql=false','--format=json',
             '--max_rows=100000',f'--project_id={BQ_PROJECT}',sql],
            capture_output=True, text=True, timeout=300)
        if result.returncode == 0 and result.stdout.strip():
            try:
                rows = json.loads(result.stdout)
                print(f"  bq CLI [OK] — {len(rows) if isinstance(rows,list) else '?'} filas")
                return rows if isinstance(rows, list) else []
            except json.JSONDecodeError as je:
                print(f"  bq CLI JSON error: {je} — stdout inicio: {result.stdout[:300]}")
        elif result.returncode != 0:
            print(f"  bq CLI error (returncode={result.returncode}):")
            print(f"    STDERR: {result.stderr[:500]}")
            print(f"    STDOUT: {result.stdout[:200]}")
    except FileNotFoundError:
        print("  bq CLI no encontrado, probando Python library...")
    except subprocess.TimeoutExpired:
        print("  bq CLI TIMEOUT (300s) — query demasiado lenta")
    except Exception as e:
        print(f"  bq CLI fallo: {e}")
    import time
    MAX_RETRIES = 4
    RETRY_DELAYS = [30, 60, 90, 120]
    for attempt in range(MAX_RETRIES):
        try:
            from google.cloud import bigquery
            import google.auth, subprocess as _sp
            # Intentar primero con gcloud auth print-access-token (incluye Drive scope si se hizo login con --enable-gdrive-access)
            creds = None
            try:
                token = _sp.run(['gcloud', 'auth', 'print-access-token'], capture_output=True, text=True, timeout=10).stdout.strip()
                if token and not token.startswith('ERROR'):
                    from google.oauth2.credentials import Credentials as _GCreds
                    creds = _GCreds(token=token)
                    print("  Usando token de gcloud auth login (con Drive scope)")
            except Exception:
                pass
            if creds is None:
                creds, _ = google.auth.default(scopes=[
                    'https://www.googleapis.com/auth/cloud-platform',
                    'https://www.googleapis.com/auth/bigquery',
                    'https://www.googleapis.com/auth/drive.readonly',
                ])
            client = bigquery.Client(project=BQ_PROJECT, credentials=creds)
            print("  Python BigQuery library [OK]")
            rows = list(client.query(sql).result())
            return [dict(row) for row in rows]
        except Exception as e:
            err_str = str(e)
            is_quota = 'quotaExceeded' in err_str or 'Quota exceeded' in err_str or '403' in err_str
            if is_quota and attempt < MAX_RETRIES - 1:
                wait = RETRY_DELAYS[attempt]
                print(f"  Quota exceeded — esperando {wait}s antes de reintentar (intento {attempt+2}/{MAX_RETRIES})...")
                time.sleep(wait)
                continue
            print(f"  ERROR BigQuery: {e}")
            return None
    return None

def transform_tpv_cohort_rows(bq_rows):
    data = []
    for row in bq_rows:
        r = {k.lower(): v for k, v in row.items()}
        try:
            cohort = int(r.get('cohort_mes', 0))
        except Exception:
            continue
        tl   = str(r.get('team_lider', '') or '').lower().strip()
        name = str(r.get('nombre_asesor', '') or '').strip()
        if not tl or not name:
            continue
        data.append({
            "cohort":     cohort,
            "tl":         tl,
            "name":       name,
            "conv":       int(r.get('convertidos',  0) or 0),
            "pot_m0":     int(r.get('pot_m0',       0) or 0),
            "tpv_inc_m0": round(float(r.get('tpv_inc_m0', 0) or 0), 2),
            "vc_inc_m0":  round(float(r.get('vc_inc_m0',  0) or 0), 2),
            "pot_m1":     int(r.get('pot_m1',       0) or 0),
            "tpv_inc_m1": round(float(r.get('tpv_inc_m1', 0) or 0), 2),
            "vc_inc_m1":  round(float(r.get('vc_inc_m1',  0) or 0), 2),
            "pot_m2":     int(r.get('pot_m2',       0) or 0),
            "tpv_inc_m2": round(float(r.get('tpv_inc_m2', 0) or 0), 2),
            "vc_inc_m2":  round(float(r.get('vc_inc_m2',  0) or 0), 2),
        })
    return data

def transform_rows(bq_rows):
    data = []
    for row in bq_rows:
        r  = {k.lower(): v for k, v in row.items()}
        try:
            mes = int(r.get('mes', 0))
        except Exception:
            continue
        tl   = str(r.get('team_lider','') or '').lower().strip()
        name = str(r.get('nombre_asesor','') or '').strip()
        if not tl or not name:
            continue
        dh = DIAS_HABILES.get(mes, 20)
        data.append({
            "mes":   mes,
            "dh":    dh,
            "tl":    tl,
            "name":  name,
            "leads": int(r.get('leads',0) or 0),
            "cont":  int(r.get('contactados',0) or 0),
            "conv":  int(r.get('convertidos',0) or 0),
            "rech":  int(r.get('rechazados',0) or 0),
            "neg":   int(r.get('en_negociacion',0) or 0),
            "pend":  int(r.get('pendientes',0) or 0),
            "pot":   int(r.get('potenciados_m1',0) or 0),
        })
    return data

# ── SNAPSHOT HARDCODEADO ABRIL 2026 ──────────────────────────────────────────
# Fuente: commit 8b7f802c0e5e (Auto-update historico 30/04/2026)
# Se usa como fallback si Asignados_Historicos_Principalidad_V3 no tiene 202604
APRIL_2026_HARDCODED = [
  {"mes":202604,"dh":20,"tl":"ag","name":"Alejandro Diaz",      "leads":245,"cont":95, "conv":14,"rech":33,"neg":10,"pend":37,"pot":5},
  {"mes":202604,"dh":20,"tl":"ag","name":"Analia Maisonnave",   "leads":236,"cont":152,"conv":10,"rech":72,"neg":3, "pend":15,"pot":2},
  {"mes":202604,"dh":20,"tl":"ag","name":"Camila Coca",         "leads":239,"cont":122,"conv":8, "rech":40,"neg":24,"pend":43,"pot":5},
  {"mes":202604,"dh":20,"tl":"ag","name":"Catalina Fernandez",  "leads":218,"cont":81, "conv":7, "rech":45,"neg":8, "pend":21,"pot":0},
  {"mes":202604,"dh":20,"tl":"ag","name":"Diego Moreno",        "leads":241,"cont":93, "conv":10,"rech":46,"neg":2, "pend":32,"pot":2},
  {"mes":202604,"dh":20,"tl":"ag","name":"Emanuel Dursi",       "leads":244,"cont":113,"conv":13,"rech":52,"neg":16,"pend":32,"pot":4},
  {"mes":202604,"dh":20,"tl":"ag","name":"Federico Vitabile",   "leads":243,"cont":97, "conv":10,"rech":44,"neg":7, "pend":37,"pot":4},
  {"mes":202604,"dh":20,"tl":"ag","name":"Giselda Allende",     "leads":250,"cont":111,"conv":15,"rech":48,"neg":11,"pend":13,"pot":7},
  {"mes":202604,"dh":20,"tl":"ag","name":"Matias Mesiano",      "leads":232,"cont":115,"conv":14,"rech":66,"neg":7, "pend":25,"pot":3},
  {"mes":202604,"dh":20,"tl":"fq","name":"Azul Pacioni",        "leads":232,"cont":126,"conv":5, "rech":98,"neg":3, "pend":17,"pot":0},
  {"mes":202604,"dh":20,"tl":"fq","name":"Barbara Nuñez",       "leads":239,"cont":110,"conv":17,"rech":61,"neg":1, "pend":17,"pot":6},
  {"mes":202604,"dh":20,"tl":"fq","name":"Diana Fraser",        "leads":234,"cont":70, "conv":2, "rech":33,"neg":13,"pend":11,"pot":2},
  {"mes":202604,"dh":20,"tl":"fq","name":"Francelys Perez",     "leads":240,"cont":109,"conv":11,"rech":62,"neg":11,"pend":26,"pot":2},
  {"mes":202604,"dh":20,"tl":"fq","name":"Joaquin Lescano",     "leads":232,"cont":119,"conv":8, "rech":78,"neg":4, "pend":16,"pot":2},
  {"mes":202604,"dh":20,"tl":"fq","name":"Luciana Pisacco",     "leads":241,"cont":112,"conv":6, "rech":64,"neg":4, "pend":36,"pot":2},
  {"mes":202604,"dh":20,"tl":"fq","name":"Micaela Marsuzi",     "leads":233,"cont":117,"conv":10,"rech":82,"neg":10,"pend":16,"pot":3},
  {"mes":202604,"dh":20,"tl":"fq","name":"Sebastian Jansa",     "leads":245,"cont":123,"conv":21,"rech":57,"neg":17,"pend":28,"pot":7},
  {"mes":202604,"dh":20,"tl":"mjo","name":"Agustin Diz",        "leads":245,"cont":97, "conv":14,"rech":40,"neg":13,"pend":30,"pot":2},
  {"mes":202604,"dh":20,"tl":"mjo","name":"Carolina Delgado",   "leads":238,"cont":105,"conv":14,"rech":70,"neg":9, "pend":12,"pot":6},
  {"mes":202604,"dh":20,"tl":"mjo","name":"Juan Cruz Rial",     "leads":245,"cont":128,"conv":19,"rech":56,"neg":7, "pend":45,"pot":5},
  {"mes":202604,"dh":20,"tl":"mjo","name":"Julian Torres",      "leads":236,"cont":169,"conv":11,"rech":126,"neg":9,"pend":23,"pot":4},
  {"mes":202604,"dh":20,"tl":"mjo","name":"Manuel Elizarraga",  "leads":245,"cont":142,"conv":13,"rech":109,"neg":4,"pend":16,"pot":2},
  {"mes":202604,"dh":20,"tl":"mjo","name":"Mariana Gonzalez",   "leads":243,"cont":113,"conv":11,"rech":63,"neg":6, "pend":27,"pot":4},
  {"mes":202604,"dh":20,"tl":"mjo","name":"Rocio Angueira",     "leads":238,"cont":111,"conv":8, "rech":52,"neg":30,"pend":18,"pot":3},
  {"mes":202604,"dh":20,"tl":"mjo","name":"Soledad Maydana",    "leads":235,"cont":125,"conv":11,"rech":65,"neg":6, "pend":35,"pot":3},
  {"mes":202604,"dh":20,"tl":"sz","name":"Cristina Hsieh",      "leads":142,"cont":110,"conv":11,"rech":80,"neg":9, "pend":6, "pot":3},
  {"mes":202604,"dh":20,"tl":"sz","name":"Sofia Zhuang",        "leads":46, "cont":29, "conv":5, "rech":14,"neg":4, "pend":1, "pot":3},
]

# ── MAPEO ASESOR → TL ──────────────────────────────────────────────────────
ASESOR_TL = {
    # MJO - Maria Jose Ochoa
    'Agustin Diz':'mjo','Carolina Delgado':'mjo','Juan Cruz Rial':'mjo','Julian Torres':'mjo',
    'Manuel Elizarraga':'mjo','Mariana Gonzalez':'mjo','Rocio Angueira':'mjo',
    # Soledad Maydana removida a partir del 30/06/2026
    'Evelyn Albarracin':'mjo','Manuel Uranga':'mjo','Rocio Gonzalez':'mjo','Nelson Salas':'mjo',
    'Mayra Marchese':'mjo','Maria Segovia':'mjo','Matías Valenzuela':'mjo','Matias Valenzuela':'mjo',
    'Camila Blanco':'mjo','Franco Mantilla':'mjo',
    'Lucas Garcia':'mjo','Cristian Gallo':'mjo',
    # AG - Analia Goias
    'Alejandro Diaz':'ag','Analia Maisonnave':'ag','Camila Coca':'ag','Catalina Fernandez':'ag',
    'Diego Moreno':'ag','Emanuel Dursi':'ag','Federico Vitabile':'ag','Giselda Allende':'ag',
    'Matias Mesiano':'ag','Ignacio Arias':'ag','Barbara Diaz':'ag',
    'Daniel Caceres':'ag','Romina Di Paolo':'ag','Florencia Lamas':'ag','Maria Florencia Lamas':'ag','Maximiliano Velazquez':'ag',
    'Luca Menghini':'ag','Martina Franjo':'ag',
    # FQ - Francisco Quinteros
    'Azul Pacioni':'fq','Barbara Nuñez':'fq','Diana Fraser':'fq','Francelys Perez':'fq',
    'Joaquin Lescano':'fq','Luciana Pisacco':'fq','Micaela Marsuzi':'fq','Sebastian Jansa':'fq',
    'Niurka Pinzon':'fq',
    'Nicolas Barrios':'fq','Santiago Cordoba':'fq','Juan Capria':'fq',
    'Sol Triberti':'fq','Carlos Sosa':'fq','Gonzalo Marin':'fq','Nayra Luna':'fq',
    'Ezequiel Fernandez':'fq','Antonella Moretto':'fq','Lautaro Diaz':'fq',
    # SZ - Sofia Zhuang
    'Cristina Hsieh':'sz','Sofia Zhuang':'sz',
    'Francisco Yu':'sz','Martin Yu WEN Yu':'sz','Tzu Sung Chen':'sz',
    # TH - Tomas Herold
    'Agustina Brandoni':'th','Agustina brandoni':'th',
    'Maria Arinelli':'th','Maria de los Angeles Arinelli':'th',
    'Sofia Cornu':'th','Sofia Cornú':'th',
    'Jesica Gonzalez':'th',
    'Marina Formati':'th','Marina De Formati':'th',
    'Federico Rodriguez':'th',
    'Rocio Vazquez':'th','Rocio vazquez':'th',
    'Fernanda Vecchio':'th','Stefania Lloret':'th',
    'Rodrigo Coronel':'th','Dorelia Batellini':'th','Dorelia Battelini':'th',
    'Ayelen Rolaoser':'th',
    'Masielle Fiori':'th',
}

def _parse_ars(s):
    """' $1.000.000' o '- $83.515' → float (formato ARS: punto=miles, coma=decimal)"""
    s = str(s).strip()
    negative = s.startswith('-') or ('- $' in s)
    s = s.replace('$','').replace(' ','').replace('.','').replace('-','')
    try:
        return -float(s) if negative else float(s)
    except Exception:
        return 0.0

def _parse_pct(s):
    """'75,73%' o '-8,35%' → float"""
    s = str(s).strip().replace('%','').replace(',','.').replace(' ','')
    try:
        return float(s)
    except Exception:
        return 0.0

def read_looker_sheet():
    """
    Lee 'LOOKERV2' del Google Sheet y retorna lista de dicts con el mismo
    formato que transform_tpv_cohort_rows().

    Reglas de potenciado (aplicadas por seller):
      pot_m0: tpv_inc_m0 > 2_000_000 AND tpv_inc_m0 > tpv_m1_base * 0.30
      pot_m1: tpv_inc_m1 > 2_000_000 AND tpv_inc_m1 > tpv_m1_base * 0.30  (solo si M1 COMPLETO)
      pot_m2: columna POTENCIADO del sheet (historia completa validada) (solo si M2 COMPLETO)

    Columnas clave del sheet (índices 0-based, mapa completo de 131 cols):
      0: CUST ID  1: MES (cohort YYYYMM)  2: ASESOR
      8: TPV M-1  (baseline = TPV mes anterior a la conversión, col I)
     Total/POINT: 20 TPV INC M0, 21 VC INC M0 | 32 TPV INC M1, 33 VC INC M1 | 44 TPV INC M2, 45 VC INC M2
     QR:          56 TPV INC M0 QR, 57 VC INC M0 QR | 65 TPV INC M1 QR, 66 VC INC M1 QR | 74 TPV INC M2 QR, 75 VC INC M2 QR
     LINK:        84 TPV INC M0 LINK, 85 VC INC M0 LINK | 92 TPV INC M1 LINK, 93 VC INC M1 LINK | 100 TPV INC M2 LINK, 101 VC INC M2 LINK
    103: M0 COMPLETO  104: M1 COMPLETO  105: M2 COMPLETO
    109: TEAM LIDER  115: POTENCIADO (clasificación final = M2)
    """
    import csv, io
    from collections import defaultdict
    try:
        import google.auth, google.auth.transport.requests as _gatr
    except ImportError:
        print("  google-auth no disponible, saltando LOOKERV2")
        return []

    SHEET_ID = '11xFxl_XYFIhLGmokYJM9HpBUu53uRoUhWNqdqfHVPs8'
    TAB      = 'LOOKERV2'

    # Índices fijos (mapa completo de 131 columnas, confirmado)
    COL_MES      = 1
    COL_ASESOR   = 2
    COL_TPV_BASE = 8   # TPV M-1 (baseline, col I)
    # Total / POINT
    COL_TPV_M0   = 20; COL_VC_M0  = 21
    COL_TPV_M1   = 32; COL_VC_M1  = 33
    COL_TPV_M2   = 44; COL_VC_M2  = 45
    # QR
    COL_TPV_M0_QR = 56; COL_VC_M0_QR = 57
    COL_TPV_M1_QR = 65; COL_VC_M1_QR = 66
    COL_TPV_M2_QR = 74; COL_VC_M2_QR = 75
    # Link de pago
    COL_TPV_M0_LINK = 84; COL_VC_M0_LINK = 85
    COL_TPV_M1_LINK = 92; COL_VC_M1_LINK = 93
    COL_TPV_M2_LINK = 100; COL_VC_M2_LINK = 101
    # Flags de completitud / TL / clasificación final
    COL_M0_OK    = 103; COL_M1_OK = 104; COL_M2_OK = 105
    COL_TL       = 109
    COL_POT_FINAL= 115  # columna POTENCIADO = clasificación M2 definitiva

    TPV_MIN      = 2_000_000   # $2M mínimo incremental
    TPV_PCT_BASE = 0.30        # 30% del baseline

    print(f"  Leyendo Google Sheet '{TAB}'...")
    try:
        creds, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/drive.readonly'])
        creds.refresh(_gatr.Request())
    except Exception as e:
        print(f"  ERROR auth Google Drive: {e}")
        return []

    url = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={TAB}'
    resp = requests.get(url, headers={'Authorization': f'Bearer {creds.token}'}, allow_redirects=True)
    if resp.status_code != 200:
        print(f"  ERROR HTTP {resp.status_code} al leer LOOKERV2")
        return []

    rows = list(csv.reader(io.StringIO(resp.content.decode('utf-8'))))
    if len(rows) < 2:
        print("  LOOKERV2 vacío")
        return []

    # Buscar columna TPV M-1 por nombre en header (fallback al índice fijo)
    header = rows[0]
    try:
        col_base = next(i for i, h in enumerate(header)
                        if 'tpv' in h.lower() and 'm-1' in h.lower().replace('m -1','m-1'))
        if col_base != COL_TPV_BASE:
            print(f"  [INFO] TPV M-1 encontrada en col {col_base} (esperaba {COL_TPV_BASE}), usando {col_base}")
        COL_TPV_BASE_USE = col_base
    except StopIteration:
        print(f"  [WARN] Columna 'TPV M-1' no encontrada en header, usando índice fijo {COL_TPV_BASE}")
        COL_TPV_BASE_USE = COL_TPV_BASE

    def _truthy(v):
        s = str(v).strip().upper()
        return s in ('1', 'SI', 'SÍ', 'TRUE', 'VERDADERO', 'S', 'Y', 'YES', 'COMPLETO')

    def _is_potenciado(inc, base):
        """Regla: inc > $2M Y inc > 30% del baseline."""
        return inc > TPV_MIN and inc > base * TPV_PCT_BASE

    # Estructura de acumulación
    agg = defaultdict(lambda: {
        'conv': 0,
        'pot_m0': 0, 'tpv_inc_m0': 0.0, 'vc_inc_m0': 0.0,
        'tpv_inc_m0_qr': 0.0, 'vc_inc_m0_qr': 0.0,
        'tpv_inc_m0_link': 0.0, 'vc_inc_m0_link': 0.0,
        'pot_m1': 0, 'tpv_inc_m1': 0.0, 'vc_inc_m1': 0.0,
        'tpv_inc_m1_qr': 0.0, 'vc_inc_m1_qr': 0.0,
        'tpv_inc_m1_link': 0.0, 'vc_inc_m1_link': 0.0,
        'pot_m2': 0, 'tpv_inc_m2': 0.0, 'vc_inc_m2': 0.0,
        'tpv_inc_m2_qr': 0.0, 'vc_inc_m2_qr': 0.0,
        'tpv_inc_m2_link': 0.0, 'vc_inc_m2_link': 0.0,
        'tl': '', 'name': '',
    })

    skipped = 0
    for row in rows[1:]:
        if len(row) <= max(COL_POT_FINAL, COL_TPV_BASE_USE):
            skipped += 1
            continue

        asesor  = row[COL_ASESOR].strip()
        mes_raw = row[COL_MES].strip()
        if not asesor or not mes_raw.isdigit():
            skipped += 1
            continue

        cohort = int(mes_raw)
        tl = ASESOR_TL.get(asesor, '')
        if not tl:
            tl_sheet = row[COL_TL].strip().lower() if len(row) > COL_TL else ''
            if tl_sheet:
                tl = tl_sheet
        if not tl:
            skipped += 1
            continue

        m1_ok = _truthy(row[COL_M1_OK]) if len(row) > COL_M1_OK else False
        m2_ok = _truthy(row[COL_M2_OK]) if len(row) > COL_M2_OK else False

        # Valores numéricos — Total/POINT
        tpv_base = _parse_ars(row[COL_TPV_BASE_USE])
        tpv0     = _parse_ars(row[COL_TPV_M0]) if len(row) > COL_TPV_M0 else 0.0
        vc0      = _parse_ars(row[COL_VC_M0])  if len(row) > COL_VC_M0  else 0.0
        tpv1     = _parse_ars(row[COL_TPV_M1]) if len(row) > COL_TPV_M1 else 0.0
        vc1      = _parse_ars(row[COL_VC_M1])  if len(row) > COL_VC_M1  else 0.0
        tpv2     = _parse_ars(row[COL_TPV_M2]) if len(row) > COL_TPV_M2 else 0.0
        vc2      = _parse_ars(row[COL_VC_M2])  if len(row) > COL_VC_M2  else 0.0
        # QR
        tpv0_qr  = _parse_ars(row[COL_TPV_M0_QR])   if len(row) > COL_TPV_M0_QR  else 0.0
        vc0_qr   = _parse_ars(row[COL_VC_M0_QR])    if len(row) > COL_VC_M0_QR   else 0.0
        tpv1_qr  = _parse_ars(row[COL_TPV_M1_QR])   if len(row) > COL_TPV_M1_QR  else 0.0
        vc1_qr   = _parse_ars(row[COL_VC_M1_QR])    if len(row) > COL_VC_M1_QR   else 0.0
        tpv2_qr  = _parse_ars(row[COL_TPV_M2_QR])   if len(row) > COL_TPV_M2_QR  else 0.0
        vc2_qr   = _parse_ars(row[COL_VC_M2_QR])    if len(row) > COL_VC_M2_QR   else 0.0
        # Link de pago
        tpv0_lnk = _parse_ars(row[COL_TPV_M0_LINK]) if len(row) > COL_TPV_M0_LINK else 0.0
        vc0_lnk  = _parse_ars(row[COL_VC_M0_LINK])  if len(row) > COL_VC_M0_LINK  else 0.0
        tpv1_lnk = _parse_ars(row[COL_TPV_M1_LINK]) if len(row) > COL_TPV_M1_LINK else 0.0
        vc1_lnk  = _parse_ars(row[COL_VC_M1_LINK])  if len(row) > COL_VC_M1_LINK  else 0.0
        tpv2_lnk = _parse_ars(row[COL_TPV_M2_LINK]) if len(row) > COL_TPV_M2_LINK else 0.0
        vc2_lnk  = _parse_ars(row[COL_VC_M2_LINK])  if len(row) > COL_VC_M2_LINK  else 0.0

        # Clasificaciones
        pot_m0 = _is_potenciado(tpv0, tpv_base)
        pot_m1 = m1_ok and _is_potenciado(tpv1, tpv_base)
        # M2: usar la columna POTENCIADO del sheet (historia completa validada)
        pot_m2 = m2_ok and row[COL_POT_FINAL].strip().upper() == 'POTENCIADO'

        key = (asesor, cohort)
        acc = agg[key]
        acc['name'] = asesor
        acc['tl']   = tl
        acc['conv'] += 1

        if pot_m0:
            acc['pot_m0']          += 1
            acc['tpv_inc_m0']      += tpv0
            acc['vc_inc_m0']       += vc0
            acc['tpv_inc_m0_qr']   += tpv0_qr
            acc['vc_inc_m0_qr']    += vc0_qr
            acc['tpv_inc_m0_link'] += tpv0_lnk
            acc['vc_inc_m0_link']  += vc0_lnk
        if pot_m1:
            acc['pot_m1']          += 1
            acc['tpv_inc_m1']      += tpv1
            acc['vc_inc_m1']       += vc1
            acc['tpv_inc_m1_qr']   += tpv1_qr
            acc['vc_inc_m1_qr']    += vc1_qr
            acc['tpv_inc_m1_link'] += tpv1_lnk
            acc['vc_inc_m1_link']  += vc1_lnk
        if pot_m2:
            acc['pot_m2']          += 1
            acc['tpv_inc_m2']      += tpv2
            acc['vc_inc_m2']       += vc2
            acc['tpv_inc_m2_qr']   += tpv2_qr
            acc['vc_inc_m2_qr']    += vc2_qr
            acc['tpv_inc_m2_link'] += tpv2_lnk
            acc['vc_inc_m2_link']  += vc2_lnk

    if skipped:
        print(f"  ({skipped} filas ignoradas — sin asesor/mes/TL o incompletas)")

    result = []
    for (asesor, cohort), acc in sorted(agg.items(), key=lambda x: (x[0][1], x[0][0])):
        result.append({
            "cohort":          cohort,
            "tl":              acc['tl'],
            "name":            acc['name'],
            "conv":            acc['conv'],
            "pot_m0":          acc['pot_m0'],
            "tpv_inc_m0":      round(acc['tpv_inc_m0'],      2),
            "vc_inc_m0":       round(acc['vc_inc_m0'],       2),
            "tpv_inc_m0_qr":   round(acc['tpv_inc_m0_qr'],   2),
            "vc_inc_m0_qr":    round(acc['vc_inc_m0_qr'],    2),
            "tpv_inc_m0_link": round(acc['tpv_inc_m0_link'], 2),
            "vc_inc_m0_link":  round(acc['vc_inc_m0_link'],  2),
            "pot_m1":          acc['pot_m1'],
            "tpv_inc_m1":      round(acc['tpv_inc_m1'],      2),
            "vc_inc_m1":       round(acc['vc_inc_m1'],       2),
            "tpv_inc_m1_qr":   round(acc['tpv_inc_m1_qr'],   2),
            "vc_inc_m1_qr":    round(acc['vc_inc_m1_qr'],    2),
            "tpv_inc_m1_link": round(acc['tpv_inc_m1_link'], 2),
            "vc_inc_m1_link":  round(acc['vc_inc_m1_link'],  2),
            "pot_m2":          acc['pot_m2'],
            "tpv_inc_m2":      round(acc['tpv_inc_m2'],      2),
            "vc_inc_m2":       round(acc['vc_inc_m2'],       2),
            "tpv_inc_m2_qr":   round(acc['tpv_inc_m2_qr'],   2),
            "vc_inc_m2_qr":    round(acc['vc_inc_m2_qr'],    2),
            "tpv_inc_m2_link": round(acc['tpv_inc_m2_link'], 2),
            "vc_inc_m2_link":  round(acc['vc_inc_m2_link'],  2),
        })

    cohorts_found = sorted(set(r['cohort'] for r in result))
    tot_pot = sum(r['pot_m0'] for r in result)
    print(f"  LOOKERV2 leído: {len(rows)-1} filas → {len(result)} advisor-cohorts | "
          f"{len(cohorts_found)} cohorts {cohorts_found} | {tot_pot} potenciados M0 total")
    return result


def read_cumpl_sheet():
    """Lee 'Target por Asesor' del Google Sheet y retorna lista de dicts para CUMPL_DATA."""
    import csv, io
    try:
        import google.auth, google.auth.transport.requests as _gatr
    except ImportError:
        print("  google-auth no disponible, saltando cumplimiento sheet")
        return []

    SHEET_ID = '11xFxl_XYFIhLGmokYJM9HpBUu53uRoUhWNqdqfHVPs8'
    GID      = '2021908322'

    print("  Leyendo Google Sheet 'Target por Asesor'...")
    # Obtener token: primero gcloud auth print-access-token, luego ADC como fallback
    token = None
    try:
        import subprocess as _sp
        token = _sp.run(['gcloud', 'auth', 'print-access-token'], capture_output=True, text=True, timeout=10).stdout.strip()
        if token and token.startswith('ERROR'):
            token = None
    except Exception:
        pass
    if not token:
        try:
            creds, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/drive.readonly'])
            creds.refresh(_gatr.Request())
            token = creds.token
        except Exception as e:
            print(f"  ERROR auth Google Drive: {e}")
            return []

    url = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}'
    resp = requests.get(url, headers={'Authorization': f'Bearer {token}'}, allow_redirects=True)
    if resp.status_code != 200:
        print(f"  ERROR HTTP {resp.status_code} al leer sheet")
        return []

    rows = list(csv.reader(io.StringIO(resp.content.decode('utf-8'))))
    if len(rows) < 2:
        return []

    # 1ra pasada: parsear todo
    all_records = []
    for row in rows[1:]:
        if len(row) < 11:
            continue
        asesor = row[0].strip()
        if not asesor or not row[2].strip().isdigit():
            continue
        tl = ASESOR_TL.get(asesor, '')
        if not tl:
            continue
        mes = int(row[2].strip())
        mes_ingreso = int(row[1].strip()) if row[1].strip().isdigit() else 0
        obj    = int(_parse_ars(row[8]))   if row[8].strip()  else 1_000_000
        dc_inc = round(_parse_ars(row[9])) if row[9].strip()  else 0
        pct    = round(_parse_pct(row[10]), 2) if row[10].strip() else 0.0
        nivel  = row[11].strip() if len(row) > 11 else ''
        all_records.append({
            'asesor': asesor, 'mes_ingreso': mes_ingreso, 'mes': mes,
            'tl': tl, 'obj': obj, 'dc_inc': dc_inc, 'pct': pct, 'nivel': nivel,
        })

    # 2da pasada: quedarnos con los últimos 8 meses que tengan datos reales (pct != 0)
    from collections import defaultdict
    mes_has_data = defaultdict(bool)
    for rec in all_records:
        if rec['pct'] != 0.0 or rec['dc_inc'] != 0:
            mes_has_data[rec['mes']] = True

    valid_meses = sorted(m for m, ok in mes_has_data.items() if ok)
    recent = set(valid_meses[-8:]) if valid_meses else set()

    data = [rec for rec in all_records if rec['mes'] in recent]
    print(f"  Sheet leído: {len(data)} registros, {len(recent)} meses con datos ({sorted(recent)})")
    return data

def read_portfolio_from_looker(n_meses=3):
    """Lee LOOKERV2 y retorna registros individuales de convertidos (últimos n_meses cohorts).
    Formato: [{asesor, mes, cust_id, tpv_base, tpv_inc, vc_inc, pot}]
    Usado por PORTFOLIO_DATA en el HTML → Vista Asesor → cartera de convertidos.
    """
    import csv, io
    try:
        import google.auth, google.auth.transport.requests as _gatr
    except ImportError:
        print("  [WARN] google-auth no disponible, saltando portfolio")
        return []

    SHEET_ID     = '11xFxl_XYFIhLGmokYJM9HpBUu53uRoUhWNqdqfHVPs8'
    TAB          = 'LOOKERV2'
    COL_CUST_ID    = 0
    COL_MES        = 1
    COL_ASESOR     = 2
    COL_TPV_BASE   = 8    # TPV M-1 (baseline)
    # Total / POINT
    COL_TPV_INC    = 20   # TPV incremental M0
    COL_VC_INC     = 21   # VC incremental M0
    # QR
    COL_TPV_INC_QR  = 56
    COL_VC_INC_QR   = 57
    # Link de pago
    COL_TPV_INC_LNK = 84
    COL_VC_INC_LNK  = 85
    # Flags / TL / clasificación
    COL_M0_OK      = 103
    COL_TL         = 109
    COL_POT_FINAL  = 115  # POTENCIADO (clasificación M2 completa)
    TPV_MIN        = 2_000_000
    TPV_PCT        = 0.30

    # Calcular últimos n_meses cohorts desde MES_ACTUAL
    now = datetime.now()
    cohorts = set()
    y, m = now.year, now.month
    for _ in range(n_meses):
        cohorts.add(y * 100 + m)
        m -= 1
        if m == 0:
            m = 12; y -= 1

    print(f"  Leyendo PORTFOLIO desde LOOKERV2 (cohorts {sorted(cohorts)})...")

    token = None
    try:
        import subprocess as _sp
        token = _sp.run(['gcloud', 'auth', 'print-access-token'],
                        capture_output=True, text=True, timeout=10).stdout.strip()
        if token and token.startswith('ERROR'):
            token = None
    except Exception:
        pass
    if not token:
        try:
            creds, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/drive.readonly'])
            creds.refresh(_gatr.Request())
            token = creds.token
        except Exception as e:
            print(f"  [WARN] Auth falló: {e}")
            return []

    url  = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={TAB}'
    resp = requests.get(url, headers={'Authorization': f'Bearer {token}'}, allow_redirects=True)
    if resp.status_code != 200:
        print(f"  [WARN] HTTP {resp.status_code} leyendo portfolio")
        return []

    rows = list(csv.reader(io.StringIO(resp.content.decode('utf-8'))))
    if len(rows) < 2:
        return []

    # Columna TPV M-1 por nombre (fallback a índice fijo)
    header = rows[0]
    try:
        col_base = next(i for i, h in enumerate(header)
                        if 'tpv' in h.lower() and ('m-1' in h.lower() or 'm -1' in h.lower()))
    except StopIteration:
        col_base = COL_TPV_BASE

    def _parse(s):
        s = str(s).strip()
        neg = s.startswith('-') or '- $' in s
        s = s.replace('$','').replace(' ','').replace('.','').replace('-','').replace(',','.')
        try:
            return -float(s) if neg else float(s)
        except Exception:
            return 0.0

    result = []
    skipped = 0
    for row in rows[1:]:
        if len(row) <= max(col_base, COL_TPV_INC, COL_VC_INC, COL_ASESOR):
            skipped += 1
            continue
        mes_raw = str(row[COL_MES]).strip()
        if not mes_raw.isdigit() or int(mes_raw) not in cohorts:
            continue
        asesor   = str(row[COL_ASESOR]).strip()
        cust_id  = str(row[COL_CUST_ID]).strip()
        if not asesor or not cust_id:
            skipped += 1
            continue

        tl = ASESOR_TL.get(asesor, '')
        if not tl:
            tl = row[COL_TL].strip().lower() if len(row) > COL_TL else ''

        tpv_base  = _parse(row[col_base])
        tpv_inc   = _parse(row[COL_TPV_INC])    if len(row) > COL_TPV_INC    else 0.0
        vc_inc    = _parse(row[COL_VC_INC])     if len(row) > COL_VC_INC     else 0.0
        tpv_qr    = _parse(row[COL_TPV_INC_QR]) if len(row) > COL_TPV_INC_QR else 0.0
        vc_qr     = _parse(row[COL_VC_INC_QR])  if len(row) > COL_VC_INC_QR  else 0.0
        tpv_lnk   = _parse(row[COL_TPV_INC_LNK])if len(row) > COL_TPV_INC_LNK else 0.0
        vc_lnk    = _parse(row[COL_VC_INC_LNK]) if len(row) > COL_VC_INC_LNK  else 0.0
        # Potenciado: regla TPV INC M0 > $2M y > 30% del baseline
        is_pot_m0 = int(tpv_inc > TPV_MIN and tpv_inc > tpv_base * TPV_PCT)
        # Potenciado final (clasificación M2, del sheet)
        is_pot_final = int(len(row) > COL_POT_FINAL and row[COL_POT_FINAL].strip().upper() == 'POTENCIADO')

        result.append({
            'asesor':   asesor,
            'tl':       tl,
            'mes':      int(mes_raw),
            'cust_id':  cust_id,
            'tpv_base': round(tpv_base, 2),
            'tpv_inc':  round(tpv_inc, 2),
            'vc_inc':   round(vc_inc, 2),
            'tpv_qr':   round(tpv_qr, 2),
            'vc_qr':    round(vc_qr, 2),
            'tpv_lnk':  round(tpv_lnk, 2),
            'vc_lnk':   round(vc_lnk, 2),
            'pot':      is_pot_m0,
            'pot_final': is_pot_final,
        })

    print(f"  Portfolio: {len(result)} sellers en {len(cohorts)} cohorts ({skipped} omitidos)")
    return result


def update_and_push(data, tpv_cohort_data=None, cumpl_data=None, portfolio_data=None):
    """Lee desde GitHub (fuente canonica), actualiza marcadores hist, guarda local y pushea."""
    today = datetime.now().strftime('%d/%m/%Y %H:%M')
    data_js      = json.dumps(data,            ensure_ascii=False, separators=(',',':')) if data             is not None else None
    cohort_js    = json.dumps(tpv_cohort_data, ensure_ascii=False, separators=(',',':')) if tpv_cohort_data  is not None else None
    cumpl_js     = json.dumps(cumpl_data,      ensure_ascii=False, separators=(',',':')) if cumpl_data       is not None else None
    portfolio_js = json.dumps(portfolio_data,  ensure_ascii=False, separators=(',',':')) if portfolio_data   is not None else None

    # 1. Obtener contenido canónico desde GitHub
    headers = {'Authorization':f'token {GITHUB_TOKEN}','Content-Type':'application/json'}
    r = requests.get(f'https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}', headers=headers)
    if not r.ok:
        print(f"  [ERROR] No se pudo leer de GitHub: {r.status_code}")
        return None
    github_data = r.json()
    sha = github_data.get('sha','')
    html_content = base64.b64decode(github_data['content']).decode('utf-8')
    print(f"  Leido de GitHub: {len(html_content)} bytes")

    # 2. Reemplazar lineas con marcadores hist
    lines = html_content.splitlines(keepends=True)
    new_lines = []
    for line in lines:
        s = line.rstrip('\n\r')
        if '%%HIST_UPDATED%%' in s:
            new_lines.append(f"/* %%HIST_UPDATED%% */var UPDATED_HIST='{today}';\n")
        elif '%%HIST_DATA_LINE%%' in s:
            if data_js is None:
                new_lines.append(line)  # preservar datos existentes
            else:
                new_lines.append(f'/* %%HIST_DATA_LINE%% */var DATA_HIST={data_js};\n')
        elif '%%TPV_COHORT_LINE%%' in s:
            if cohort_js is None:
                new_lines.append(line)  # preservar datos existentes
            else:
                new_lines.append(f'/* %%TPV_COHORT_LINE%% */var TPV_COHORT_DATA={cohort_js};\n')
        elif '%%MES_ACTUAL_LINE%%' in s:
            new_lines.append(f'/* %%MES_ACTUAL_LINE%% */var MES_ACTUAL_NUM={MES_ACTUAL};\n')
        elif '%%CUMPL_DATA_LINE%%' in s:
            if cumpl_data is None:
                new_lines.append(line)  # preservar datos existentes si el sheet falló
            else:
                new_lines.append(f'/* %%CUMPL_DATA_LINE%% */var CUMPL_DATA={cumpl_js};\n')
        elif '%%PORTFOLIO_DATA_LINE%%' in s:
            if portfolio_js is None:
                new_lines.append(line)  # preservar existente
            else:
                new_lines.append(f'/* %%PORTFOLIO_DATA_LINE%% */var PORTFOLIO_DATA={portfolio_js};\n')
        else:
            new_lines.append(line)
    html_new = ''.join(new_lines)

    # 3. Guardar localmente
    with open(HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(html_new)

    # 4. Push a GitHub
    content_b64 = base64.b64encode(html_new.encode('utf-8')).decode()
    r = requests.put(
        f'https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}',
        headers=headers,
        json={'message':f'Auto-update historico {today}','content':content_b64,'sha':sha,'branch':GITHUB_BRANCH}
    )
    if r.status_code in (200, 201):
        return html_new
    else:
        print(f"  [ERROR] Push GitHub: {r.status_code}")
        return html_new

def update_cumpl_only():
    """Actualiza SOLO la sección de cumplimiento (lee Google Sheet, pushea a GitHub)."""
    print(f"\n[>>] Actualizando SOLO cumplimiento ({datetime.now().strftime('%d/%m/%Y %H:%M')})")
    print("-" * 55)
    print("Leyendo cumplimiento desde Google Sheet...")
    cumpl_data = read_cumpl_sheet()
    if not cumpl_data:
        print("[ERROR] No se pudo leer el Sheet de cumplimiento. Verificá las credenciales.")
        sys.exit(1)
    print(f"   {len(cumpl_data)} registros de cumplimiento")
    print("Actualizando HTML y pusheando a GitHub...")
    html_new = update_and_push(None, None, cumpl_data)
    if html_new:
        print("[OK] Cumplimiento actualizado en GitHub Pages")
    else:
        print("[ERROR] Falló el push a GitHub")
    print("-" * 55)

def main():
    # Modo --cumpl-only: solo actualiza la sección de cumplimiento sin tocar BigQuery
    if '--cumpl-only' in sys.argv:
        update_cumpl_only()
        return

    print(f"\n[>>] Actualizando dashboard historico ({datetime.now().strftime('%d/%m/%Y %H:%M')})")
    print("-" * 55)
    print("1. Corriendo query histórica en BigQuery...")
    rows = run_bigquery(QUERY)
    if not rows:
        print("[ERROR] No se obtuvieron datos. Abortando.")
        sys.exit(1)
    print(f"   {len(rows)} filas obtenidas")
    print("2. Procesando datos históricos...")
    data = transform_rows(rows)
    meses = sorted(set(r['mes'] for r in data))
    print(f"   {len(data)} registros | {len(meses)} meses: {meses}")

    # Fallback: si Asignados_Historicos no tiene abril 2026, usar snapshot hardcodeado del 30/04
    if 202604 not in meses:
        print("   ⚠️  Abril 2026 no encontrado en BQ — usando snapshot hardcodeado (30/04/2026)")
        data.extend(APRIL_2026_HARDCODED)
        data.sort(key=lambda r: (r['mes'], r['tl'], r['name']))
        meses = sorted(set(r['mes'] for r in data))
        print(f"   Con fallback: {len(data)} registros | {len(meses)} meses: {meses}")

    print("3a. Leyendo TPV/VC Cohort histórico desde BigQuery...")
    bq_cohort_rows = run_bigquery(QUERY_TPV_COHORT)
    bq_cohort_data = transform_tpv_cohort_rows(bq_cohort_rows) if bq_cohort_rows else []
    if bq_cohort_data:
        bq_meses = sorted(set(r['cohort'] for r in bq_cohort_data))
        print(f"   {len(bq_cohort_data)} registros BQ | cohorts: {bq_meses}")
    else:
        print("   Sin datos BQ para cohort (se usará solo LOOKERV2)")

    print("3b. Leyendo TPV/VC Cohort mes actual desde LOOKERV2 (Google Sheet)...")
    looker_data = read_looker_sheet()
    if not looker_data:
        print("   Sin datos LOOKERV2 — usando solo BigQuery")

    # Combinar: LOOKERV2 tiene prioridad para los meses que cubre (anula BQ para esos cohorts)
    looker_keys = set((r['cohort'], r['name']) for r in looker_data)
    looker_cohorts = set(r['cohort'] for r in looker_data)
    # De BQ nos quedamos solo con los cohorts que NO están en LOOKERV2
    bq_filtered = [r for r in bq_cohort_data if r['cohort'] not in looker_cohorts]
    tpv_cohort_data = bq_filtered + looker_data
    all_cohorts = sorted(set(r['cohort'] for r in tpv_cohort_data))
    print(f"   Merge final: {len(tpv_cohort_data)} registros | cohorts: {all_cohorts}")


    print("4. Leyendo cumplimiento desde Google Sheet...")
    cumpl_data = read_cumpl_sheet()
    if cumpl_data is None or cumpl_data == []:
        print("   Sin datos de cumplimiento (sheet no disponible o vacío)")
        print("   AVISO: Se preservarán los datos de cumplimiento existentes en el HTML.")
        cumpl_data = None  # None = preservar datos existentes; [] = sobreescribir con vacío

    print("4b. Leyendo cartera de convertidos (portfolio) desde LOOKERV2...")
    portfolio_data = read_portfolio_from_looker(n_meses=3)
    if not portfolio_data:
        print("   Sin datos de portfolio — se preservarán los existentes en el HTML.")
        portfolio_data = None

    print(f"5. Actualizando HTML via GitHub...")
    html_new = update_and_push(data, tpv_cohort_data, cumpl_data, portfolio_data)
    ok = html_new is not None
    if ok:
        print(f"   [OK] https://joaquinbalparda-droid.github.io/funnel-principalidad/funnel_dashboard.html")
    else:
        print("   [ERROR] Error al subir a GitHub")
    print("-" * 55)
    print("[OK] Listo!\n")

if __name__ == '__main__':
    main()
