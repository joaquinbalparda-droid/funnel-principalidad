#!/usr/bin/env python3
"""
Script de actualización automática del Dashboard Funnel Principalidad.
Corre la query en BigQuery, actualiza el HTML y pushea a GitHub.

USO LOCAL (con gcloud autenticado):
  python actualizar_dashboard.py

USO GITHUB ACTIONS (via env vars):
  Requiere los secrets: GCP_CREDENTIALS_JSON, PERSONAL_GITHUB_TOKEN
  El workflow los inyecta como variables de entorno.
"""

import json, base64, re, sys, requests
from datetime import datetime

# Fix encoding para Windows (PowerShell usa cp1252 por defecto)
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ── CONFIGURACIÓN ─────────────────────────────────────────────
import os

# GitHub token: SIEMPRE desde env var (GH Actions secret o export local). No hardcodear tokens en el código.
GITHUB_TOKEN  = os.environ.get("PERSONAL_GITHUB_TOKEN")
if not GITHUB_TOKEN:
    print("  [WARN] PERSONAL_GITHUB_TOKEN no seteado en el entorno — el push a GitHub va a fallar.")
    print("         Local: export PERSONAL_GITHUB_TOKEN=ghp_xxx  |  GH Actions: ya viene del secret.")
GITHUB_REPO   = "joaquinbalparda-droid/funnel-principalidad"
GITHUB_FILE   = "funnel_dashboard.html"
GITHUB_BRANCH = "main"

# GCP credentials: si hay GCP_CREDENTIALS_JSON en env, escribirla a un archivo temporal
_gcp_creds_json = os.environ.get("GCP_CREDENTIALS_JSON")
if _gcp_creds_json:
    import tempfile, atexit
    _tmpfile = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    _tmpfile.write(_gcp_creds_json)
    _tmpfile.close()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _tmpfile.name
    atexit.register(os.unlink, _tmpfile.name)
    print(f"  [GH Actions] Credenciales GCP cargadas desde env var ✓")

# Ruta al HTML en tu compu (ajustá si está en otro lugar)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH  = os.path.join(SCRIPT_DIR, "funnel_dashboard.html")

# Proyecto de billing BigQuery
BQ_PROJECT = "meli-bi-data"

# Mes actual como número (se calcula automáticamente)
import calendar
_now = datetime.now()
MES_ACTUAL = _now.month
MES_YYYYMM = _now.year * 100 + _now.month
MES_ANTERIOR_YYYYMM = (_now.year * 100 + (_now.month - 1)) if _now.month > 1 else ((_now.year - 1) * 100 + 12)
DIAS_TRANSCURRIDOS = _now.day
DIAS_DEL_MES = calendar.monthrange(_now.year, _now.month)[1]
FACTOR_PROYECCION = DIAS_DEL_MES / DIAS_TRANSCURRIDOS

# ── QUERY BIGQUERY ────────────────────────────────────────────
GESTION_UNION = """
  SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado
  FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Carolina_Delgado`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Agustin_Diz`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_JuanC_Rial`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Julian_Torres`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Manuel_Elizarraga`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Mariana_Gonzalez`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Rocio_Angueira`
  -- Soledad Maydana removida a partir del 30/06/2026
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Alejandro_Diaz`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Analia_Maisonnave`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Camila_Coca`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Catalina_Fernandez`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Diego_Moreno`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Emanuel_Dursi`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Fedrico_Vitabile`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Giselda_Allende`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Matias_Mesiano`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Azul_Pacioni`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Barbara_Nuñez`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Diana_Fraser`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Francelys_Perez`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Joaquin_Lescano`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Luciana_Pisacco`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Micaela_Marsuzi`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Sebastian_Jansa`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Cristina_Hsieh`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Sofia_Zhuang`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Daniel_Caceres`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Nicolas_Barrios`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Romina_Di_Paolo`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Santiago_Cordoba`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Mayra_Marchese`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Maria_Segovia`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Matias_Valenzuela`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Maria_Florencia_Lamas`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Maximiliano_Velazquez`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Juan_Capria`
  -- Asesores nuevos junio 2026
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Agustina_Brandoni1`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Maria_Arinelli`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Sofia_Cornu`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Sol_triberti1`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_camila_blanco`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_jesica_gonzalez`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Marina_Formati`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Carlos_Sosa`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Luca_Menghini1`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Federico_Rodriguez1`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Gonzalo_Marin`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Rocio_Vazquez`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Fernanda_vecchio`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Franjo_martina`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Stefania_Lloret`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Rodrigo_Coronel`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Dorelia_Batellini`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Franco_mantilla`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Ayelen_Rolaoser`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Nayra_Luna`
  -- Asesores nuevos agosto 2026
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Masielle_Fiori`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Lucas_Garcia`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Cristian_Gallo`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Antonella_Moretto`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Lautaro_Diaz`
  UNION ALL SELECT Nombre_asesor, Cust_Id, Mes_asignacion, Contactado, Estado, Sub_Estado FROM `meli-bi-data.SBOX_SELLERSMP.Devolucion_Mes_Corriente_Ezequiel_Fernandez1`
"""

TL_CASE = """
    CASE
      WHEN b.Nombre_asesor IN ('Alejandro Diaz','Analia Maisonnave',
                               'Diego Moreno','Emanuel Dursi','Federico Vitabile','Giselda Allende','Matias Mesiano',
                               'Ignacio Arias','Barbara Diaz',
                               'Daniel Caceres','Romina Di Paolo','Florencia Lamas','Maria Florencia Lamas','Maximiliano Velazquez',
                               'Luca Menghini','Martina Franjo') THEN 'ag'
      WHEN b.Nombre_asesor IN ('Barbara Nuñez','Diana Fraser','Francelys Perez',
                               'Joaquin Lescano','Luciana Pisacco','Sebastian Jansa',
                               'Niurka Pinzon',
                               'Nicolas Barrios','Santiago Cordoba','Juan Capria',
                               'Sol Triberti','Carlos Sosa','Gonzalo Marin','Nayra Luna',
                               'Ezequiel Fernandez','Antonella Moretto','Lautaro Diaz') THEN 'fq'
      WHEN b.Nombre_asesor IN ('Agustin Diz','Carolina Delgado','Juan Cruz Rial','Julian Torres',
                               'Manuel Elizarraga','Mariana Gonzalez','Rocio Angueira',
                               'Evelyn Albarracin','Manuel Uranga','Rocio Gonzalez','Nelson Salas',
                               'Mayra Marchese','Maria Segovia','Matías Valenzuela','Matias Valenzuela',
                               'Camila Blanco','Franco Mantilla',
                               'Lucas Garcia','Cristian Gallo') THEN 'mjo'
      WHEN b.Nombre_asesor IN ('Cristina Hsieh','Sofia Zhuang',
                               'Francisco Yu','Martin Yu WEN Yu','Tzu Sung Chen') THEN 'sz'
      WHEN b.Nombre_asesor IN ('Agustina Brandoni','Agustina brandoni',
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

def build_query(mes, mes_yyyymm, mes_anterior_yyyymm):
    return f"""
WITH gestion_raw AS ({GESTION_UNION}),
gestion AS (
  -- Deduplicar: si un seller aparece en múltiples tablas, queda una sola fila
  SELECT
    Nombre_asesor, Cust_Id, Mes_asignacion,
    MAX(Contactado) AS Contactado,
    MAX(Estado)     AS Estado,
    MAX(Sub_Estado) AS Sub_Estado
  FROM gestion_raw
  GROUP BY 1, 2, 3
),
tpv AS (
  -- TPV por seller: M-1 (mes anterior) y M0 (mes actual)
  SELECT
    CAST(SELLER AS STRING) AS seller_str,
    MAX(CASE WHEN MES = CAST({mes_anterior_yyyymm} AS STRING) THEN TPV_ARS ELSE 0 END) AS tpv_m1,
    MAX(CASE WHEN MES = CAST({mes_yyyymm}          AS STRING) THEN TPV_ARS ELSE 0 END) AS tpv_m0
  FROM `meli-bi-data.SBOX_SELLERSMP.REPAGOS_2025_PRINCIPALIDAD_1`
  WHERE MES IN (CAST({mes_anterior_yyyymm} AS STRING), CAST({mes_yyyymm} AS STRING))
  GROUP BY 1
),
base AS (
  -- Potenciado se evalúa por seller individual (cualquier estado, como en historico)
  SELECT
    b.Nombre_asesor, b.Cust_Id, b.Prioridad,
    b.Promo_Cuotas_Rubro,
    {TL_CASE} AS Team_Lider,
    g.Contactado, g.Estado, g.Sub_Estado,
    COALESCE(t.tpv_m1, 0) AS seller_tpv_m1,
    COALESCE(t.tpv_m0, 0) * {FACTOR_PROYECCION:.6f} AS seller_tpv_m0p,
    CASE
      WHEN g.Estado = 'CONVERTIDO'
       AND (COALESCE(t.tpv_m0, 0) * {FACTOR_PROYECCION:.6f} - COALESCE(t.tpv_m1, 0)) > 2000000
       AND (COALESCE(t.tpv_m0, 0) * {FACTOR_PROYECCION:.6f} - COALESCE(t.tpv_m1, 0)) > COALESCE(t.tpv_m1, 0) * 0.3
      THEN 1 ELSE 0
    END AS Es_Potenciado
  FROM `meli-bi-data.SBOX_SELLERSMP.Base_Mes_Corriente_Principalidad` b
  LEFT JOIN gestion g ON b.Nombre_asesor = g.Nombre_asesor AND b.Cust_Id = g.Cust_Id AND g.Mes_asignacion = {mes}
  LEFT JOIN tpv t ON CAST(b.Cust_Id AS STRING) = t.seller_str
  WHERE b.Mes_asignacion = {mes}
)
SELECT
  CASE
    WHEN Prioridad = 130 THEN 'CALENTAMIENTO'
    WHEN Promo_Cuotas_Rubro IS NOT NULL AND TRIM(Promo_Cuotas_Rubro) != '' THEN 'PROMO CUOTAS'
    ELSE 'TOTAL'
  END AS Campana,
  CASE
    WHEN Promo_Cuotas_Rubro IS NOT NULL AND TRIM(Promo_Cuotas_Rubro) != ''
    THEN CASE
      WHEN UPPER(TRIM(Promo_Cuotas_Rubro)) LIKE '%DISPONIBLE%' THEN 'DISPONIBLE'
      WHEN UPPER(TRIM(Promo_Cuotas_Rubro)) LIKE '%PIDIO%' OR UPPER(TRIM(Promo_Cuotas_Rubro)) LIKE '%ASESOR%' THEN 'PIDIO ASESOR'
      WHEN UPPER(TRIM(Promo_Cuotas_Rubro)) LIKE '%ACTIV%' THEN 'YA ACTIVO'
      ELSE UPPER(TRIM(Promo_Cuotas_Rubro))
    END
    ELSE NULL
  END AS Sub_Campana,
  Team_Lider,
  Nombre_asesor,
  COUNT(*)                                                             AS Leads,
  COUNTIF(Contactado = TRUE)                                          AS Contactados,
  COUNTIF(Estado = 'CONVERTIDO')                                      AS Convertidos,
  COUNTIF(Estado = 'PENDIENTE')                                       AS Pendientes,
  COUNTIF(Estado IN ('NEGOCIACION', 'SOLICITUD DE TASA'))             AS En_Negociacion,
  COUNTIF(Estado = 'RECHAZADO')                                       AS Rechazados,
  COUNTIF(Es_Potenciado = 1)                                          AS Potenciados,
  SUM(CASE WHEN Es_Potenciado=1 THEN seller_tpv_m0p ELSE 0 END)      AS TPV_M0P_Pot,
  SUM(CASE WHEN Es_Potenciado=1 THEN seller_tpv_m1  ELSE 0 END)      AS TPV_M1_Pot
FROM base b
WHERE Team_Lider IS NOT NULL
GROUP BY 1, 2, 3, 4
ORDER BY Campana, Sub_Campana, Team_Lider, Nombre_asesor
"""

# ── FUNCIONES PRINCIPALES ─────────────────────────────────────

def run_bigquery(sql):
    """Corre la query usando bq CLI (primero) o Python library (fallback)."""
    import subprocess, tempfile, os

    # ── Intento 1: bq CLI ────────────────────────────────────────
    try:
        result = subprocess.run(
            ['bq', 'query', '--use_legacy_sql=false', '--format=json',
             '--max_rows=500', f'--project_id={BQ_PROJECT}', sql],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0 and result.stdout.strip():
            rows = json.loads(result.stdout)
            print(f"  bq CLI ✓")
            return rows if isinstance(rows, list) else []
        elif result.returncode != 0:
            print(f"  bq CLI error: {result.stderr[:200]}")
    except FileNotFoundError:
        print("  bq CLI no encontrado, probando Python library...")
    except Exception as e:
        print(f"  bq CLI falló: {e}")

    # ── Intento 2: BigQuery REST API via gcloud token ────────────
    try:
        token_result = subprocess.run(
            ['gcloud', 'auth', 'print-access-token'],
            capture_output=True, text=True, timeout=15
        )
        if token_result.returncode == 0:
            token = token_result.stdout.strip()
            print("  BigQuery REST API (gcloud token) ✓")
            rows = _run_bq_rest(sql, token)
            if rows is not None:
                return rows
    except FileNotFoundError:
        print("  gcloud no encontrado, probando Python library...")
    except Exception as e:
        print(f"  REST API falló: {e}")

    # ── Intento 3: Python BigQuery library (con retry por quota y tablas faltantes) ─
    import time, re as _re
    MAX_RETRIES = 4
    RETRY_DELAYS = [30, 60, 90, 120]   # segundos entre intentos
    current_sql = sql
    for attempt in range(MAX_RETRIES):
        try:
            from google.cloud import bigquery
            client = bigquery.Client(project=BQ_PROJECT)
            print("  Python BigQuery library ✓")
            rows = list(client.query(current_sql).result())
            return [dict(row) for row in rows]
        except Exception as e:
            err_str = str(e)
            is_quota = 'quotaExceeded' in err_str or 'Quota exceeded' in err_str or '403' in err_str
            is_not_found = '404' in err_str or 'Not found' in err_str or 'notFound' in err_str
            # Errores transitorios de fuentes externas (Sheets sobrecargado, "Resources exceeded", etc.)
            is_transient = (
                'Resources exceeded' in err_str
                or 'overloaded' in err_str.lower()
                or 'Sheets service' in err_str
                or '503' in err_str
                or 'backendError' in err_str
                or 'rateLimitExceeded' in err_str
            )
            if (is_quota or is_transient) and attempt < MAX_RETRIES - 1:
                wait = RETRY_DELAYS[attempt]
                motivo = "Quota exceeded" if is_quota else "Error transitorio (fuente externa sobrecargada)"
                print(f"  {motivo} — esperando {wait}s antes de reintentar (intento {attempt+2}/{MAX_RETRIES})...")
                time.sleep(wait)
                continue
            if is_not_found:
                # Extraer nombre de tabla faltante y sacarla del UNION ALL
                match = _re.search(r'Table [^\s:]+:([^\s]+) was not found', err_str)
                if not match:
                    match = _re.search(r'Not found: Table [^\s]+\.([^\s]+)', err_str)
                if match:
                    missing = match.group(1).replace(':', '.').split('.')[-1]  # solo el nombre de tabla
                    print(f"  Tabla no encontrada: {missing} — removiendo y reintentando...")
                    # Remover la línea UNION ALL que contiene esa tabla
                    lines = current_sql.split('\n')
                    new_lines = [l for l in lines if missing not in l]
                    current_sql = '\n'.join(new_lines)
                    continue
            print(f"  ERROR BigQuery: {e}")
            return None
    return None


def _run_bq_rest(sql, token, billing_project=None, max_wait_secs=120):
    """Ejecuta una query en BigQuery usando la REST API (jobs.insert + poll)."""
    import time as _time
    project = billing_project or BQ_PROJECT
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    # Lanzar el job
    job_body = {
        'configuration': {
            'query': {
                'query': sql,
                'useLegacySql': False,
            }
        }
    }
    r = requests.post(
        f'https://bigquery.googleapis.com/bigquery/v2/projects/{project}/jobs',
        headers=headers, json=job_body, timeout=30
    )
    if not r.ok:
        print(f"  REST API error al crear job: {r.status_code} {r.text[:300]}")
        return None
    job = r.json()
    job_id = job['jobReference']['jobId']
    job_project = job['jobReference']['projectId']
    print(f"  Job lanzado: {job_id}")

    # Polling hasta completar
    start = _time.time()
    while _time.time() - start < max_wait_secs:
        _time.sleep(3)
        status_r = requests.get(
            f'https://bigquery.googleapis.com/bigquery/v2/projects/{job_project}/jobs/{job_id}',
            headers=headers, timeout=15
        )
        if not status_r.ok:
            print(f"  Error polling job: {status_r.status_code}")
            return None
        status = status_r.json()
        state = status.get('status', {}).get('state', '')
        if state == 'DONE':
            errors = status.get('status', {}).get('errors', [])
            if errors:
                print(f"  Job falló: {errors[0].get('message','')[:200]}")
                return None
            break
        print(f"  Job estado: {state} ({int(_time.time()-start)}s)...")
    else:
        print(f"  Timeout esperando job")
        return None

    # Obtener resultados paginando
    all_rows = []
    page_token = None
    while True:
        params = {'maxResults': 500}
        if page_token:
            params['pageToken'] = page_token
        res_r = requests.get(
            f'https://bigquery.googleapis.com/bigquery/v2/projects/{job_project}/queries/{job_id}',
            headers=headers, params=params, timeout=30
        )
        if not res_r.ok:
            print(f"  Error obteniendo resultados: {res_r.status_code}")
            return None
        res = res_r.json()
        schema_fields = res.get('schema', {}).get('fields', [])
        field_names = [f['name'] for f in schema_fields]
        for row in res.get('rows', []):
            vals = [cell.get('v') for cell in row.get('f', [])]
            all_rows.append(dict(zip(field_names, vals)))
        page_token = res.get('pageToken')
        if not page_token:
            break
    print(f"  {len(all_rows)} filas obtenidas via REST ✓")
    return all_rows

def transform_rows(bq_rows):
    """Convierte filas de BQ al formato DATA + TPV_DATA del dashboard."""
    data, tpv_data = [], []
    for row in bq_rows:
        r = {k.lower(): v for k, v in row.items()}
        campana = str(r.get('campana', '') or '').strip()
        if campana not in ('CALENTAMIENTO', 'PROMO CUOTAS', 'TOTAL'):
            continue
        sub = str(r.get('sub_campana', '') or '').strip() or None
        tl  = str(r.get('team_lider', '') or '').lower().strip()
        nom = str(r.get('nombre_asesor', '') or '').strip()

        # Columnas nuevas del build_query reescrito:
        # potenciados = COUNT por-seller de Es_Potenciado=1 (calculado en SQL)
        # tpv_m0p_pot = SUM de TPV M0 proyectado solo de potenciados (ya incluye FACTOR_PROYECCION)
        # tpv_m1_pot  = SUM de TPV M-1 solo de potenciados
        pot_count = int(r.get('potenciados', 0) or 0)
        tpv_m0p   = float(r.get('tpv_m0p_pot', 0) or 0)   # ya proyectado en SQL
        tpv_m1    = float(r.get('tpv_m1_pot',  0) or 0)
        tpv_inc   = round(tpv_m0p - tpv_m1, 2) if pot_count > 0 else 0.0

        # DATA incluye campos de funnel + TPV (para mostrar en tabla)
        data.append({
            "campana":     campana,
            "sub":         sub,
            "tl":          tl,
            "name":        nom,
            "leads":       int(r.get('leads', 0) or 0),
            "cont":        int(r.get('contactados', 0) or 0),
            "conv":        int(r.get('convertidos', 0) or 0),
            "pend":        int(r.get('pendientes', 0) or 0),
            "neg":         int(r.get('en_negociacion', 0) or 0),
            "rech":        int(r.get('rechazados', 0) or 0),
            "pot":         pot_count,
            "tpv_m0p":     round(tpv_m0p, 2),
            "tpv_m1":      tpv_m1,
            "tpv_inc_pot": tpv_inc,
        })
        # TPV_DATA separado para el strip de KPIs de arriba
        tpv_data.append({
            "campana":     campana,
            "tl":          tl,
            "name":        nom,
            "conv":        int(r.get('convertidos', 0) or 0),
            "tpv_m1":      tpv_m1,
            "tpv_m0p":     round(tpv_m0p, 2),
            "pot":         pot_count,
            "tpv_inc_pot": tpv_inc,
        })
    return data, tpv_data

def build_tpv_query(mes, mes_yyyymm, mes_anterior_yyyymm):
    return f"""
WITH gestion AS ({GESTION_UNION}),
base AS (
  SELECT
    b.Nombre_asesor, b.Cust_Id, b.Prioridad, b.Promo_Cuotas_Rubro,
    {TL_CASE} AS Team_Lider,
    g.Estado
  FROM `meli-bi-data.SBOX_SELLERSMP.Base_Mes_Corriente_Principalidad` b
  LEFT JOIN gestion g ON b.Nombre_asesor = g.Nombre_asesor AND b.Cust_Id = g.Cust_Id AND g.Mes_asignacion = {mes}
  WHERE b.Mes_asignacion = {mes}
    AND g.Estado = 'CONVERTIDO'
),
tpv AS (
  SELECT
    SELLER,
    MAX(CASE WHEN MES = '{mes_anterior_yyyymm}' THEN TPV_ARS                  ELSE 0 END) AS tpv_m_menos_1,
    MAX(CASE WHEN MES = '{mes_yyyymm}'          THEN TPV_ARS                  ELSE 0 END) AS tpv_m0,
    MAX(CASE WHEN MES = '{mes_yyyymm}'          THEN TPV_ARS_PROYECTADO_MES   ELSE 0 END) AS tpv_m0_proy
  FROM `meli-bi-data.SBOX_SELLERSMP.REPAGOS_2025_PRINCIPALIDAD_1`
  WHERE MES IN ('{mes_anterior_yyyymm}', '{mes_yyyymm}')
  GROUP BY 1
)
SELECT
  CASE
    WHEN Prioridad = 130 THEN 'CALENTAMIENTO'
    WHEN Promo_Cuotas_Rubro IS NOT NULL AND TRIM(Promo_Cuotas_Rubro) != '' THEN 'PROMO CUOTAS'
    ELSE 'TOTAL'
  END AS Campana,
  Team_Lider,
  Nombre_asesor,
  COUNT(*)                                                                AS Convertidos,
  SUM(COALESCE(t.tpv_m_menos_1, 0))                                      AS TPV_M_menos_1,
  SUM(COALESCE(t.tpv_m0, 0))                                             AS TPV_M0,
  SUM(COALESCE(t.tpv_m0_proy, 0))                                        AS TPV_M0_Proyectado,
  COUNTIF(
    COALESCE(t.tpv_m0_proy, 0) > 2000000
    AND COALESCE(t.tpv_m0_proy, 0) > COALESCE(t.tpv_m_menos_1, 0) * 1.3
  )                                                                       AS Potenciados,
  SUM(CASE
    WHEN COALESCE(t.tpv_m0_proy, 0) > 2000000
     AND COALESCE(t.tpv_m0_proy, 0) > COALESCE(t.tpv_m_menos_1, 0) * 1.3
    THEN COALESCE(t.tpv_m0_proy, 0) - COALESCE(t.tpv_m_menos_1, 0)
    ELSE 0
  END)                                                                    AS TPV_Incremental_Potenciados
FROM base b
LEFT JOIN tpv t ON b.Cust_Id = SAFE_CAST(t.SELLER AS INT64)
WHERE Team_Lider IS NOT NULL
GROUP BY 1, 2, 3
ORDER BY Campana, Team_Lider, Nombre_asesor
"""

def transform_tpv_rows(bq_rows):
    """Convierte filas de TPV al formato TPV_DATA del dashboard."""
    data = []
    for row in bq_rows:
        r = {k.lower(): v for k, v in row.items()}
        campana = str(r.get('campana', '') or '').strip()
        if campana not in ('CALENTAMIENTO', 'PROMO CUOTAS', 'TOTAL'):
            continue
        data.append({
            "campana":    campana,
            "tl":         str(r.get('team_lider', '') or '').lower().strip(),
            "name":       str(r.get('nombre_asesor', '') or '').strip(),
            "conv":       int(r.get('convertidos', 0) or 0),
            "tpv_m1":     float(r.get('tpv_m_menos_1', 0) or 0),
            "tpv_m0":     float(r.get('tpv_m0', 0) or 0),
            "tpv_m0p":    float(r.get('tpv_m0_proyectado', 0) or 0),
            "pot":        int(r.get('potenciados', 0) or 0),
            "tpv_inc_pot":float(r.get('tpv_incremental_potenciados', 0) or 0),
        })
    return data

def _build_camp_snap(data, existing_snap_js):
    """Construye CAMP_SNAP preservando TODOS los snapshots históricos.
    Clave = YYYYMMDD → una entrada por día de actualización.
    Si el mismo día se corre dos veces, sobreescribe con datos más frescos.
    """
    # Parsear CAMP_SNAP existente del HTML (preserva todo el historial)
    try:
        snap = json.loads(existing_snap_js) if existing_snap_js else {}
    except Exception:
        snap = {}

    # Calcular totales del día de hoy por campaña (de data)
    camp_totals = {}
    for row in data:
        camp = row.get('campana', 'TOTAL')
        if camp not in ('CALENTAMIENTO', 'PROMO CUOTAS', 'TOTAL'):
            continue
        if camp not in camp_totals:
            camp_totals[camp] = {'leads':0,'cont':0,'conv':0,'rech':0,'neg':0,'pend':0,'pot':0}
        t = camp_totals[camp]
        t['leads'] += row.get('leads', 0)
        t['cont']  += row.get('cont', 0)
        t['conv']  += row.get('conv', 0)
        t['rech']  += row.get('rech', 0)
        t['neg']   += row.get('neg', 0)
        t['pend']  += row.get('pend', 0)
        t['pot']   += row.get('pot', 0)

    # Guardar con clave YYYYMMDD (permite comparar día comparable entre meses)
    if camp_totals:
        fecha_key = datetime.now().strftime('%Y%m%d')   # ej: "20260521"
        snap[fecha_key] = {'nota': datetime.now().strftime('%d/%m/%Y')}
        for camp, vals in camp_totals.items():
            snap[fecha_key][camp] = vals
        print(f"   Snapshot guardado para {fecha_key} (total keys: {len(snap)})")

    return snap

def read_looker_for_dashboard(mes_yyyymm):
    """Lee LOOKERV2 para el mes actual y retorna {asesor: {pot, tpv_m0p, tpv_m1, tpv_inc}}.

    Usa los mismos datos que ven los asesores en Looker → mismos potenciados/TPV que en Looker.
    Columnas LOOKERV2 (0-based, iguales a actualizar_historico.py):
      0: CUST ID  1: MES (cohort YYYYMM)  2: ASESOR
      8: TPV M-1 (baseline)  20: TPV INC M0  46: M0 COMPLETO
    Regla potenciado: TPV_INC_M0 > $2M AND TPV_INC_M0 > TPV_BASE * 30%
    """
    import csv, io
    from collections import defaultdict
    try:
        import google.auth, google.auth.transport.requests as _gatr
    except ImportError:
        print("  [WARN] google-auth no disponible — TPV/pot vendrán de BQ (pueden diferir de Looker)")
        return {}

    SHEET_ID     = '11xFxl_XYFIhLGmokYJM9HpBUu53uRoUhWNqdqfHVPs8'
    TAB          = 'LOOKERV2'
    COL_MES      = 1
    COL_ASESOR   = 2
    COL_TPV_BASE = 8    # TPV M-1 (baseline)
    COL_TPV_INC  = 20   # TPV incremental M0
    TPV_MIN      = 2_000_000
    TPV_PCT      = 0.30

    print(f"  Leyendo LOOKERV2 para mes {mes_yyyymm}...")

    # Auth: gcloud print-access-token primero, luego ADC como fallback
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
            print(f"  [WARN] Auth Google Drive falló: {e} — usando valores BQ")
            return {}

    url  = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={TAB}'
    resp = requests.get(url, headers={'Authorization': f'Bearer {token}'}, allow_redirects=True)
    if resp.status_code != 200:
        print(f"  [WARN] HTTP {resp.status_code} al leer LOOKERV2 — usando valores BQ")
        return {}

    rows = list(csv.reader(io.StringIO(resp.content.decode('utf-8'))))
    if len(rows) < 2:
        print("  [WARN] LOOKERV2 vacío — usando valores BQ")
        return {}

    # Intenta ubicar columna TPV M-1 por nombre en header (fallback al índice fijo)
    header = rows[0]
    try:
        col_base = next(i for i, h in enumerate(header)
                        if 'tpv' in h.lower() and ('m-1' in h.lower() or 'm -1' in h.lower()))
        if col_base != COL_TPV_BASE:
            print(f"  [INFO] TPV M-1 en col {col_base} (esperaba {COL_TPV_BASE})")
    except StopIteration:
        col_base = COL_TPV_BASE

    def _parse(s):
        s = str(s).strip()
        neg = s.startswith('-') or '- $' in s
        s = s.replace('$', '').replace(' ', '').replace('.', '').replace('-', '').replace(',', '.')
        try:
            return -float(s) if neg else float(s)
        except Exception:
            return 0.0

    mes_str = str(mes_yyyymm)
    agg     = defaultdict(lambda: {'pot': 0, 'tpv_m0p': 0.0, 'tpv_m1': 0.0, 'tpv_inc': 0.0, 'conv': 0})
    skipped = 0

    for row in rows[1:]:
        if len(row) <= max(col_base, COL_TPV_INC, COL_ASESOR):
            skipped += 1
            continue
        if str(row[COL_MES]).strip() != mes_str:
            continue
        asesor = str(row[COL_ASESOR]).strip()
        if not asesor:
            skipped += 1
            continue

        tpv_base = _parse(row[col_base])
        tpv_inc  = _parse(row[COL_TPV_INC]) if len(row) > COL_TPV_INC else 0.0
        is_pot   = tpv_inc > TPV_MIN and tpv_inc > tpv_base * TPV_PCT

        acc = agg[asesor]
        acc['conv'] += 1
        if is_pot:
            acc['pot']     += 1
            acc['tpv_m0p'] += tpv_base + tpv_inc   # TPV total M0
            acc['tpv_m1']  += tpv_base
            acc['tpv_inc'] += tpv_inc

    if skipped:
        print(f"  ({skipped} filas LOOKERV2 omitidas — sin asesor/mes o cols insuficientes)")

    result    = dict(agg)
    total_pot = sum(v['pot'] for v in result.values())
    print(f"  LOOKERV2 mes {mes_str}: {len(result)} asesores con conv | {total_pot} potenciados ✓")
    return result


def _merge_looker_into_data(data, tpv_data, looker_pot):
    """Override pot/TPV en DATA y TPV_DATA con valores de LOOKERV2.

    Si el asesor tiene múltiples campañas, distribuye los potenciados
    proporcionalmente según conversiones por campaña.
    Si no está en LOOKERV2, pone pot=0 (no hay conversiones en el Sheet).
    """
    from collections import defaultdict

    for ds in (data, tpv_data):
        # Agrupar índices por asesor
        by_name = defaultdict(list)
        for i, row in enumerate(ds):
            by_name[row['name']].append(i)

        for asesor, indices in by_name.items():
            if asesor not in looker_pot:
                # Asesor sin datos en Sheet: fuerza a 0
                for i in indices:
                    ds[i]['pot']         = 0
                    ds[i]['tpv_m0p']     = 0.0
                    ds[i]['tpv_m1']      = 0.0
                    ds[i]['tpv_inc_pot'] = 0.0
                continue

            ld         = looker_pot[asesor]
            total_pot  = ld['pot']
            tot_m0p    = ld['tpv_m0p']
            tot_m1     = ld['tpv_m1']
            tot_inc    = ld['tpv_inc']

            if len(indices) == 1:
                i = indices[0]
                ds[i]['pot']         = total_pot
                ds[i]['tpv_m0p']     = round(tot_m0p, 2)
                ds[i]['tpv_m1']      = round(tot_m1, 2)
                ds[i]['tpv_inc_pot'] = round(tot_inc, 2)
            else:
                # Distribuir proporcional a conversiones
                total_conv = sum(ds[i]['conv'] for i in indices) or 1
                remaining_pot = total_pot
                for idx_pos, i in enumerate(indices):
                    frac = ds[i]['conv'] / total_conv
                    if idx_pos == len(indices) - 1:
                        # Último row: asigna el resto para evitar redondeo
                        pot_i = remaining_pot
                    else:
                        pot_i = round(total_pot * frac)
                        remaining_pot -= pot_i
                    ds[i]['pot']         = pot_i
                    ds[i]['tpv_m0p']     = round(tot_m0p * frac, 2)
                    ds[i]['tpv_m1']      = round(tot_m1  * frac, 2)
                    ds[i]['tpv_inc_pot'] = round(tot_inc  * frac, 2)


def update_and_push(data, tpv_data=None):
    """Lee desde GitHub (fuente canonica), actualiza marcadores funnel, guarda local y pushea."""
    today = datetime.now().strftime('%d/%m/%Y %H:%M')
    data_js = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    tpv_js  = json.dumps(tpv_data or [], ensure_ascii=False, separators=(',', ':'))

    # 1. Obtener contenido canónico desde GitHub
    headers = {'Authorization': f'token {GITHUB_TOKEN}', 'Content-Type': 'application/json'}
    r = requests.get(f'https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}', headers=headers)
    if not r.ok:
        print(f"  [ERROR] No se pudo leer de GitHub: {r.status_code}")
        return None
    github_data = r.json()
    sha = github_data.get('sha', '')
    html_content = base64.b64decode(github_data['content']).decode('utf-8')
    print(f"  Leido de GitHub: {len(html_content)} bytes")

    # 2. Procesar: actualizar marcadores
    import re as _re
    snap_match = _re.search(r'/\* %%CAMP_SNAP_LINE%% \*/var CAMP_SNAP=({.*?});', html_content)
    existing_snap_js = snap_match.group(1) if snap_match else '{}'
    snap = _build_camp_snap(data, existing_snap_js)
    snap_js = json.dumps(snap, ensure_ascii=False, separators=(',', ':'))

    lines = html_content.splitlines(keepends=True)
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if '%%UPDATED%%' in stripped:
            new_lines.append(f"/* %%UPDATED%% */var UPDATED='{today}';\n")
        elif '%%DATA_LINE%%' in stripped:
            new_lines.append(f'/* %%DATA_LINE%% */var DATA={data_js};\n')
        elif '%%TPV_DATA_LINE%%' in stripped:
            new_lines.append(f'/* %%TPV_DATA_LINE%% */var TPV_DATA={tpv_js};\n')
        elif '%%CAMP_SNAP_LINE%%' in stripped:
            new_lines.append(f'/* %%CAMP_SNAP_LINE%% */var CAMP_SNAP={snap_js};\n')
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
        json={'message': f'Auto-update {today}', 'content': content_b64, 'sha': sha, 'branch': GITHUB_BRANCH}
    )
    if r.status_code in (200, 201):
        return html_new
    else:
        print(f"  [ERROR] Push GitHub: {r.status_code} - {r.text[:200]}")
        return None  # push falló: el HTML local se guardó, pero GitHub NO se actualizó

# ── MAIN ──────────────────────────────────────────────────────

def main():
    print(f"\n[>>] Actualizando dashboard - Mes {MES_ACTUAL} ({datetime.now().strftime('%d/%m/%Y %H:%M')})")
    print("─" * 50)

    # 1. Una sola query: funnel + TPV
    print("1. Corriendo query en BigQuery (funnel + TPV)...")
    sql = build_query(MES_ACTUAL, MES_YYYYMM, MES_ANTERIOR_YYYYMM)
    rows = run_bigquery(sql)
    if not rows:
        print("❌ No se obtuvieron datos. Abortando.")
        sys.exit(1)
    print(f"   {len(rows)} filas obtenidas")

    # 2. Transformar
    print("2. Procesando datos...")
    data, tpv_data = transform_rows(rows)

    # 2b. Override TPV/potenciados con LOOKERV2 (misma fuente que Looker → sin diferencias)
    print("2b. Leyendo TPV/potenciados desde LOOKERV2 (Sheet)...")
    looker_pot = read_looker_for_dashboard(MES_YYYYMM)
    if looker_pot:
        _merge_looker_into_data(data, tpv_data, looker_pot)
        print("   Potenciados/TPV actualizados desde Sheet ✓")
    else:
        print("   [AVISO] LOOKERV2 no disponible — usando valores de BQ (pueden diferir de Looker)")

    total_pot = sum(r['pot'] for r in tpv_data)
    total_tpv = sum(r['tpv_m0p'] for r in tpv_data)
    print(f"   {len(data)} filas funnel | {total_pot} potenciados | TPV M0 total: {total_tpv:,.0f}")
    sample = [(r['name'], r['conv'], r['tpv_m0p']) for r in tpv_data if r['tpv_m0p'] > 0][:5]
    if sample:
        print(f"   Ejemplo TPV no-cero (fuente Sheet): {sample}")

    # 3. Actualizar HTML (lee de GitHub, no del archivo local)
    print(f"3. Actualizando HTML via GitHub (incluye snapshot de campañas)...")
    html_new = update_and_push(data, tpv_data)
    print("   HTML actualizado ✓ | CAMP_SNAP actualizado con foto de hoy")

    ok = html_new is not None
    if ok:
        print(f"   [OK] Publicado en: https://joaquinbalparda-droid.github.io/funnel-principalidad/funnel_dashboard.html")
    else:
        print("   [ERROR] Error al subir a GitHub — el workflow debe marcarse como FALLIDO")

    print("─" * 50)
    if ok:
        print("[OK] Listo!\n")
    else:
        print("[FAIL] El push a GitHub falló — revisar token/secret PERSONAL_GITHUB_TOKEN.\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
