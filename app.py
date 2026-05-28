"""
Dataform AI Studio
Agente conversacional para generar código JS/SQLX para Dataform
"""

import streamlit as st
import os
import io
import json
import zipfile
import pandas as pd
import base64
from google.cloud import bigquery
from google.oauth2 import service_account
import vertexai
from vertexai.generative_models import GenerativeModel, Part, Content

# ══════════════════════════════════════════════════════════
# CONFIGURACIÓN DE PÁGINA
# ══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Dataform AI Studio",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════
# CSS PERSONALIZADO
# ══════════════════════════════════════════════════════════
st.markdown("""
<style>
  /* Fondo y fuentes corporativas - Estilo Devoteam */
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Inter:wght@400;600;800&display=swap');

  /* El fondo general es un gris super claro (casi blanco) para que los paneles destaquen */
  [data-testid="stAppViewContainer"] { background: #FAFAFA; color: #1F2937; }
  [data-testid="stSidebar"]          { background: #FFFFFF !important; border-right: 1px solid #E5E7EB; }
  
  h1, h2, h3, h4, p, span, div { font-family: 'Inter', sans-serif; color: #1F2937; }
  
  /* Header principal (Blanco con una línea superior roja elegante) */
  .main-header {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-top: 4px solid #F8282D; /* Acento Rojo Devoteam */
    border-radius: 8px;
    padding: 24px 28px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  }
  
  .main-header h1 {
    font-size: 26px;
    font-weight: 800;
    margin: 0;
    color: #F8282D; /* Rojo Devoteam para el título principal */
  }
  
  .main-header p { color: #6B7280; font-size: 14px; margin: 4px 0 0 0; }

  /* Burbujas de Chat */
  .msg-user {
    background: #FFF5F5; /* Blanco con un levísimo tinte rojo */
    border: 1px solid #FEE2E2;
    border-radius: 12px 12px 2px 12px;
    padding: 14px 18px;
    margin: 8px 0 8px 15%;
    color: #7F1D1D;
    font-size: 14px;
    line-height: 1.6;
  }
  
  .msg-agent {
    background: #FFFFFF; /* Blanco puro para la IA */
    border: 1px solid #E5E7EB;
    border-radius: 12px 12px 12px 2px;
    padding: 14px 18px;
    margin: 8px 15% 8px 0;
    color: #374151;
    font-size: 14px;
    line-height: 1.6;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
  }
  
  .msg-label-user  { text-align: right; color: #F8282D; font-size: 11px; font-weight: 600; margin-bottom: 4px; font-family: 'JetBrains Mono', monospace; }
  .msg-label-agent { color: #6B7280;  font-size: 11px; font-weight: 600; margin-bottom: 4px; font-family: 'JetBrains Mono', monospace; }

  /* Bloques de código (Los mantenemos oscuros porque los programadores leen mejor el código así) */
  .code-block {
    background: #111827;
    border: 1px solid #374151;
    border-radius: 8px;
    padding: 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12.5px;
    color: #F9FAFB;
    overflow-x: auto;
    margin: 10px 0;
    line-height: 1.7;
  }

  /* Elementos de Streamlit (Cajas de texto limpias) */
  .stTextInput > div > div > input,
  .stTextArea > div > div > textarea {
    background: #FFFFFF !important;
    border: 1px solid #D1D5DB !important;
    color: #111827 !important;
  }
  
  /* Cuando haces clic en una caja de texto, el borde se pone rojo */
  .stTextInput > div > div > input:focus,
  .stTextArea > div > div > textarea:focus {
    border-color: #F8282D !important;
    box-shadow: 0 0 0 1px #F8282D !important;
  }

  /* Botón principal (Rojo Devoteam con efecto Hover) */
  .stButton > button[kind="primary"] {
    background: #D91F24 !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
    transition: all 0.3s ease;
  }
  
  .stButton > button[kind="primary"]:hover {
    background: #D91F24 !important; /* Rojo un poco más oscuro al pasar el ratón */
    box-shadow: 0 4px 6px -1px rgba(248, 40, 45, 0.4);
  }
  
  /* Pestañas (Tabs) con estilo corporativo */
  .stTabs [aria-selected="true"] {
      color: #F8282D !important;
      border-bottom-color: #F8282D !important;
  }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════
if "historial"         not in st.session_state: st.session_state.historial         = []
if "archivos_gen"      not in st.session_state: st.session_state.archivos_gen      = {}   # {nombre: contenido}
if "bq_client"         not in st.session_state: st.session_state.bq_client         = None
if "bq_conectado"      not in st.session_state: st.session_state.bq_conectado      = False
if "esquema_contexto"  not in st.session_state: st.session_state.esquema_contexto  = ""
if "project_id"        not in st.session_state: st.session_state.project_id        = ""
if "modelo"            not in st.session_state: st.session_state.modelo            = None

# ══════════════════════════════════════════════════════════
# SYSTEM PROMPT DEL AGENTE
# ══════════════════════════════════════════════════════════
SYSTEM_PROMPT = """
Eres un Arquitecto de Datos Senior experto en Google Cloud, BigQuery y Dataform.
Generas código Dataform de alta calidad (JS y SQLX) para cualquier tipo de proyecto.

CONOCIMIENTO TÉCNICO:
- Dataform: type:table, type:view, type:incremental, type:operations (operate())
- BigQuery: INFORMATION_SCHEMA, MERGE, particionamiento, PKs NOT ENFORCED, QUALIFY
- Patrones de ingesta: full load, incremental MERGE, CDC (Change Data Capture)
- Buenas prácticas Dataform: includes reutilizables, forEach para múltiples tablas, postOps

REGLAS DE GENERACIÓN DE CÓDIGO:
1. Para múltiples tablas, SIEMPRE usa forEach sobre un array de configuración con esta estructura:
   { nombre, pks, campoFecha, campoBorrado, campoParticion? (opcional), granularidadParticion? (opcional) }
2. postOps para PKs: DROP PRIMARY KEY IF EXISTS + ADD PRIMARY KEY (pks) NOT ENFORCED
3. Restaurar descripciones: usa INFORMATION_SCHEMA.COLUMN_FIELD_PATHS con STRING_AGG en un único ALTER TABLE
4. MERGE incremental CDC: 
   - WHEN MATCHED + flag borrado != '' → DELETE
   - WHEN MATCHED + flag borrado = ''  → UPDATE SET ROW
   - WHEN NOT MATCHED + flag borrado = '' → INSERT ROW
5. Para el USING del MERGE, envuelve el QUALIFY en una subquery con ROW_NUMBER + WHERE rn=1
6. Particionamiento condicional con spread operator: ...(tabla.campoParticion ? { bigquery: { partitionBy: DATE_TRUNC(...) } } : {})
7. Usa SOURCE_PROJECT, SOURCE_DATASET, TARGET_DATASET como constantes arriba del todo

FORMATO DE RESPUESTA:
- Código en bloques ```javascript o ```sql  
- Explicación breve después del código (no antes)
- Si el usuario pide ajustes, modifica SOLO lo necesario y explica el cambio
- Si faltan datos para generar bien el código, pregunta lo necesario
"""

# ══════════════════════════════════════════════════════════
# FUNCIONES DE BIGQUERY
# ══════════════════════════════════════════════════════════
def conectar_bq_credenciales(json_key: dict, project_id: str):
    """Conecta a BQ usando service account JSON."""
    credentials = service_account.Credentials.from_service_account_info(
        json_key,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    return bigquery.Client(credentials=credentials, project=project_id)

def conectar_bq_adc(project_id: str):
    """Conecta a BQ usando Application Default Credentials."""
    return bigquery.Client(project=project_id)

def obtener_esquema_hibrido(nombre_tabla, origen_seleccionado):
    """
    Devuelve el esquema y las PKs de la tabla, ya sea desde BQ en vivo o desde el Excel subido.
    """
    # CASO A: BIGQUERY EN VIVO
    if origen_seleccionado == "BigQuery (Conexión en vivo)":
        # Aquí dejas el código exacto que ya tienes escrito que hace:
        # bq_client.get_table(...) e INFORMATION_SCHEMA
        # (No lo borres, simplemente mételo dentro de este 'if')
        pass 
        
    # CASO B: EXCEL / SHEETS LOCAL
    elif origen_seleccionado == "Archivo Excel / Sheets local" and "df_metadata" in st.session_state:
        df = st.session_state.df_metadata
        
        # Imaginemos que tu Excel tiene las columnas: "TABLA", "COLUMNA", "ES_PK"
        # Filtramos el Excel para quedarnos solo con las filas de la tabla que queremos procesar
        df_filtrado = df[df['TABLA'].str.upper() == nombre_tabla.upper()]
        
        if df_filtrado.empty:
            return None, []
            
        # Extraemos las columnas y las PKs usando Pandas puro (100% offline)
        columnas = df_filtrado['COLUMNA'].tolist()
        
        # Si tienes una columna que indica si es Clave Primaria (ej. 'X' o True)
        pks = df_filtrado[df_filtrado['ES_PK'].isin(['X', 'true', True, 1])]['COLUMNA'].tolist()
        
        return columnas, pks
        
    # CASO C: SIN METADATOS
    return None, []

def listar_tablas_dataset(client: bigquery.Client, project: str, dataset: str) -> list:
    """Lista todas las tablas de un dataset."""
    tablas = list(client.list_tables(f"{project}.{dataset}"))
    return [t.table_id for t in tablas]

def esquemas_a_contexto(esquemas: list) -> str:
    """Convierte lista de esquemas a texto de contexto para el agente."""
    lineas = []
    for e in esquemas:
        lineas.append(f"\n--- TABLA: {e['proyecto']}.{e['dataset']}.{e['tabla']} ---")
        if e['descripcion_tabla']:
            lineas.append(f"Descripción: {e['descripcion_tabla']}")
        if e['pks']:
            lineas.append(f"PKs definidas: {', '.join(e['pks'])}")
        lineas.append("Columnas:")
        for c in e['columnas']:
            desc = f" — {c['desc']}" if c['desc'] else ""
            lineas.append(f"  {c['nombre']} ({c['tipo']} {c['modo']}){desc}")
    return "\n".join(lineas)

# ══════════════════════════════════════════════════════════
# FUNCIÓN DE LLAMADA AL MODELO
# ══════════════════════════════════════════════════════════
def llamar_agente(mensaje: str, historial: list, esquema_ctx: str, pdf_parts: list) -> str:
    """Llama a Gemini o simula la respuesta de forma inteligente si estamos en modo libre."""
    
    # 1. COMPROBACIÓN REVOLUCIONARIA: Si el usuario NO eligió BigQuery, 
    # o si por algún motivo el modelo no está listo, ejecutamos el modo libre automático.
    modo_elegido = st.session_state.get("origen_metadata", "Sin esquema (Solo Prompt)")
    
    if modo_elegido != "BigQuery (Conexión en vivo)" or st.session_state.modelo is None:
        return f"""
*(Agente funcionando en Modo Libre - Sin conexión GCP)*

He procesado tu requerimiento para generar el código Dataform. Basándome en tu prompt, aquí tienes la estructura base:

```sqlx
config {{
    type: "table",
    schema: "stg_custom",
    description: "Modelo generado en modo libre basado en tu petición."
}}

/* PROMPT PROCESADO: 
  "{mensaje}"
*/

SELECT
    id_transaccion,
    fecha_registro,
    -- Aquí procesaremos tus reglas de negocio más adelante
    '{mensaje}' AS regla_aplicada,
    CURRENT_TIMESTAMP() AS fecha_compilacion
FROM
    `${{ref("raw_source", "tabla_origen")}}`
"""
model = st.session_state.modelo
contents = []

if esquema_ctx and not historial:
    mensaje_con_ctx = f"CONTEXTO DE TABLAS:\n{esquema_ctx}\n\nPETICIÓN:\n{mensaje}"
else:
    mensaje_con_ctx = mensaje

for msg in historial:
    contents.append(Content(role=msg["role"], parts=[Part.from_text(msg["content"])]))

partes_actuales = list(pdf_parts)
partes_actuales.append(Part.from_text(mensaje_con_ctx))
contents.append(Content(role="user", parts=partes_actuales))

try:
    respuesta = model.generate_content(contents)
    return respuesta.text.strip()
except Exception as e:
    return f"❌ Error de la API de Google: {e}"
    
# ══════════════════════════════════════════════════════════
# EXTRACCIÓN Y GUARDADO DE CÓDIGO
# ══════════════════════════════════════════════════════════
def extraer_bloques_codigo(texto: str) -> list:
    """Extrae todos los bloques de código del texto."""
    import re
    patron = r'```(?:javascript|js|sql|sqlx)?\n([\s\S]*?)```'
    return re.findall(patron, texto)

def generar_zip(archivos: dict) -> bytes:
    """Genera un ZIP con todos los archivos generados."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for nombre, contenido in archivos.items():
            zf.writestr(nombre, contenido)
    return buffer.getvalue()

# ══════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════
with st.sidebar:
    st.header("Configuración de Datos")
    
    # Selector dinámico de origen
    origen_metadata = st.radio(
        "Origen de Metadatos/Esquema:",
        ["BigQuery (Conexión en vivo)", "Archivo Excel / Sheets local", "Sin esquema (Solo Prompt)"],
        key="origen_metadata"
    )
    
    if origen_metadata == "BigQuery (Conexión en vivo)":
        project_id = st.text_input("GCP Project ID", value="integracion-snp-glue")
        dataset_id = st.text_input("Dataset ID", value="MRP_STANDARD")
        # Aquí mantienes tu lógica actual de conexión a BQ...
        
    elif origen_metadata == "Archivo Excel / Sheets local":
        st.info("Sube un Excel con la estructura de tus tablas (Columnas, PKs, etc.)")
        excel_meta = st.file_uploader("Subir diccionario de datos:", type=["xlsx", "csv"])
        
        # Guardamos el Excel en el estado de la sesión para usarlo luego
        if excel_meta is not None:
            if excel_meta.name.endswith('.csv'):
                st.session_state.df_metadata = pd.read_csv(excel_meta)
            else:
                st.session_state.df_metadata = pd.read_excel(excel_meta)
            st.success("Diccionario cargado en memoria")

    # ── 2. Cargar esquemas ───────────────────────────────
    st.markdown("#### 📦 Esquemas BigQuery")

    if st.session_state.bq_conectado:
        dataset_input = st.text_input("Dataset", placeholder="MRP_STANDARD")
        
        # Opción: tabla individual o múltiples
        modo_carga = st.radio("Cargar:", ["Tabla individual", "Todas las tablas del dataset", "Lista de tablas"])
        
        tablas_a_cargar = []
        
        if modo_carga == "Tabla individual":
            tabla_input = st.text_input("Nombre de tabla", placeholder="Z_EVER")
            if tabla_input: tablas_a_cargar = [tabla_input.strip()]
        
        elif modo_carga == "Todas las tablas del dataset":
            if st.button("🔍 Listar tablas", use_container_width=True):
                try:
                    tablas = listar_tablas_dataset(st.session_state.bq_client, st.session_state.project_id, dataset_input)
                    st.session_state["tablas_listadas"] = tablas
                    st.success(f"{len(tablas)} tablas encontradas")
                except Exception as e:
                    st.error(f"Error: {e}")
            
            if "tablas_listadas" in st.session_state:
                seleccionadas = st.multiselect("Selecciona tablas:", st.session_state["tablas_listadas"])
                tablas_a_cargar = seleccionadas
        
        elif modo_carga == "Lista de tablas":
            texto_tablas = st.text_area("Tablas (una por línea o separadas por comas):", placeholder="Z_EVER\nZ_BUT000\nZ_ANEP")
            tablas_a_cargar = [t.strip() for t in texto_tablas.replace(",", "\n").split("\n") if t.strip()]

        if tablas_a_cargar and dataset_input:
            if st.button("📥 Cargar esquemas", use_container_width=True):
                esquemas = []
                progress = st.progress(0)
                for i, tabla in enumerate(tablas_a_cargar):
                    try:
                        esq = obtener_esquema_tabla(
                            st.session_state.bq_client,
                            st.session_state.project_id,
                            dataset_input, tabla
                        )
                        esquemas.append(esq)
                    except Exception as e:
                        st.warning(f"⚠️ {tabla}: {e}")
                    progress.progress(int((i+1)/len(tablas_a_cargar)*100))
                
                st.session_state.esquema_contexto = esquemas_a_contexto(esquemas)
                st.success(f"✅ {len(esquemas)} esquemas cargados como contexto")
    else:
        st.info("Conéctate primero a GCP para cargar esquemas.")

    st.divider()

    # ── 3. Output ────────────────────────────────────────
    st.markdown("#### 💾 Archivos generados")
    
    if st.session_state.archivos_gen:
        st.caption(f"{len(st.session_state.archivos_gen)} archivo(s)")
        for nombre in list(st.session_state.archivos_gen.keys())[:5]:
            st.markdown(f"<div class='file-row'><span class='fname'>📄 {nombre}</span></div>", unsafe_allow_html=True)
        
        # Descarga ZIP
        zip_bytes = generar_zip(st.session_state.archivos_gen)
        st.download_button(
            "📦 Descargar todo (ZIP)",
            data=zip_bytes,
            file_name="dataform_generated.zip",
            mime="application/zip",
            use_container_width=True
        )
        
        # Ruta local opcional
        ruta_local = st.text_input("Guardar también en ruta local:", placeholder=r"C:\proyecto\definitions")
        if ruta_local and st.button("💾 Guardar en disco", use_container_width=True):
            os.makedirs(ruta_local, exist_ok=True)
            for nombre, contenido in st.session_state.archivos_gen.items():
                with open(os.path.join(ruta_local, nombre), "w", encoding="utf-8") as f:
                    f.write(contenido)
            st.success(f"✅ {len(st.session_state.archivos_gen)} archivos guardados")
        
        if st.button("🗑️ Limpiar archivos", use_container_width=True):
            st.session_state.archivos_gen = {}
            st.rerun()
    else:
        st.caption("Ningún archivo generado aún.")

    st.divider()
    if st.button("🔄 Nueva conversación", use_container_width=True):
        st.session_state.historial        = []
        st.session_state.esquema_contexto = ""
        st.rerun()

# ══════════════════════════════════════════════════════════
# CUERPO PRINCIPAL
# ══════════════════════════════════════════════════════════
st.markdown("""
<div class="main-header">
  <div style="font-size:36px">⚙️</div>
  <div>
    <h1>Dataform AI Studio</h1>
    <p>Agente conversacional para generar código JS/SQLX · Conecta BQ, sube PDFs y refina el código en chat</p>
  </div>
</div>
""", unsafe_allow_html=True)

# Estado de conexión
col_s1, col_s2, col_s3 = st.columns([1,1,4])
with col_s1:
    if st.session_state.bq_conectado:
        st.markdown(f"<span class='badge-ok'>● BQ conectado — {st.session_state.project_id}</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span class='badge-warn'>○ BQ no conectado</span>", unsafe_allow_html=True)
with col_s2:
    if st.session_state.esquema_contexto:
        st.markdown("<span class='badge-ok'>● Esquemas cargados</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span class='badge-warn'>○ Sin esquemas</span>", unsafe_allow_html=True)

st.divider()

# ── Tabs ─────────────────────────────────────────────────
tab_chat, tab_inputs, tab_archivos = st.tabs(["💬 Chat con el Agente", "📎 Inputs adicionales", "📁 Archivos generados"])

# ══════════════════════════════════════════════════════════
# TAB 1: CHAT
# ══════════════════════════════════════════════════════════
with tab_chat:
    
    # Mostrar historial
    if not st.session_state.historial:
        st.markdown("""
        <div style="text-align:center; padding:60px 20px; color:#64748b">
          <div style="font-size:48px;margin-bottom:16px">🤖</div>
          <div style="font-size:18px;font-weight:700;color:#e2e8f0;margin-bottom:8px">Dataform Agent</div>
          <div style="font-size:14px;max-width:500px;margin:0 auto;line-height:1.6">
            Conecta tu proyecto BQ para dar contexto real, o empieza directamente describiendo qué código necesitas.
          </div>
        </div>
        """, unsafe_allow_html=True)
    
    for msg in st.session_state.historial:
        if msg["role"] == "user":
            st.markdown(f"<div class='msg-label-user'>TÚ</div><div class='msg-user'>{msg['display']}</div>", unsafe_allow_html=True)
        else:
            # Renderizar respuesta del agente: separar código del texto
            contenido = msg["content"]
            import re
            partes = re.split(r'(```(?:javascript|js|sql|sqlx)?\n[\s\S]*?```)', contenido)
            
            html_respuesta = ""
            for parte in partes:
                if parte.startswith("```"):
                    codigo = re.sub(r'```(?:javascript|js|sql|sqlx)?\n', '', parte)
                    codigo = re.sub(r'```$', '', codigo).strip()
                    html_respuesta += f"<div class='code-block'>{codigo}</div>"
                else:
                    if parte.strip():
                        html_respuesta += parte.replace("\n", "<br>")
            
            st.markdown(f"<div class='msg-label-agent'>⚙️ AGENTE</div><div class='msg-agent'>{html_respuesta}</div>", unsafe_allow_html=True)
    
    st.divider()

    # ── Accesos rápidos ──────────────────────────────────
    st.markdown("**⚡ Accesos rápidos:**")
    cols_quick = st.columns(6)
    quick_options = {
        "📥 Full load":        "Genera el código JS completo para una carga inicial full load (type:table) con postOps para PKs y restauración de metadatos desde la tabla origen.",
        "🔄 MERGE incremental":"Genera el operate() con MERGE incremental para mantenimiento diario CDC: DELETE (flag borrado), UPDATE SET ROW (modificados), INSERT ROW (nuevos).",
        "👁️ Vista":            "Genera una vista SQLX (type:view) con transformaciones básicas para la tabla disponible en el contexto.",
        "🗂️ Partición":        "Añade particionamiento condicional al array (campoParticion + granularidadParticion) con spread operator en el publish().",
        "🔑 PKs + metadatos":  "Genera el postOps completo: DROP + ADD PRIMARY KEY NOT ENFORCED, y restauración de descripciones con STRING_AGG en un único ALTER TABLE.",
        "📋 Array config":     "Genera el array de configuración de tablas con las constantes SOURCE/TARGET_DATASET, listo para usar con forEach para múltiples tablas.",
    }
    
    for i, (label, prompt) in enumerate(quick_options.items()):
        with cols_quick[i]:
            if st.button(label, use_container_width=True, key=f"quick_{i}"):
                st.session_state["_pending_prompt"] = prompt

    # ── Input del usuario ────────────────────────────────
    pdf_parts_chat = []
    
    # Recuperar PDFs del tab de inputs
    if "pdfs_cargados" in st.session_state:
        pdf_parts_chat = st.session_state["pdfs_cargados"]

    # Pre-rellenar si hay quick prompt pendiente
    default_input = st.session_state.pop("_pending_prompt", "")
    
    user_input = st.text_area(
        "Tu petición:",
        value=default_input,
        height=100,
        placeholder="Ej: 'Genera el operate() con MERGE incremental para Z_EVER usando VERTRAG como PK'",
        key="chat_input"
    )
    
    col_send, col_clear = st.columns([4,1])
    with col_send:
        enviar = st.button("➤ Enviar", type="primary", use_container_width=True)
    with col_clear:
        if st.button("🗑️ Limpiar chat", use_container_width=True):
            st.session_state.historial = []
            st.rerun()

    if enviar and user_input.strip():
        with st.spinner("🧠 Generando..."):
            try:
                respuesta = llamar_agente(
                    user_input,
                    st.session_state.historial,
                    st.session_state.esquema_contexto,
                    pdf_parts_chat
                )

                # Guardar en historial
                st.session_state.historial.append({
                    "role":    "user",
                    "content": user_input,
                    "display": user_input
                })
                st.session_state.historial.append({
                    "role":    "model",
                    "content": respuesta
                })

                # Extraer código y guardar archivos
                bloques = extraer_bloques_codigo(respuesta)
                for i, bloque in enumerate(bloques):
                    # Detectar nombre sugerido en la respuesta
                    nombre = f"dataform_output_{len(st.session_state.archivos_gen)+1}.js"
                    import re as _re
                    match_nombre = _re.search(r'(?:archivo|file|guardar como)[:\s]+[`"]?(\w+\.(js|sqlx|sql))[`"]?', respuesta, _re.IGNORECASE)
                    if match_nombre:
                        nombre = match_nombre.group(1)
                    elif "sqlx" in respuesta[:200].lower():
                        nombre = nombre.replace(".js", ".sqlx")
                    
                    st.session_state.archivos_gen[nombre] = bloque.strip()

                st.rerun()

            except Exception as e:
                st.error(f"❌ Error al llamar al agente: {e}")

# ══════════════════════════════════════════════════════════
# TAB 2: INPUTS ADICIONALES
# ══════════════════════════════════════════════════════════
with tab_inputs:
    st.markdown("### 📎 Contexto adicional para el agente")
    st.caption("Estos inputs se añaden como contexto en la siguiente petición del chat.")

    col_pdf, col_csv = st.columns(2)

    with col_pdf:
        st.markdown("#### 📄 PDFs (arquitectura, reglas de negocio, documentación)")
        pdfs = st.file_uploader(
            "Sube uno o más PDFs",
            type=["pdf"],
            accept_multiple_files=True,
            key="pdf_uploader"
        )
        
        if pdfs:
            partes_pdf = []
            for pdf in pdfs:
                pdf_bytes = pdf.read()
                pdf.seek(0)
                partes_pdf.append(Part.from_data(data=pdf_bytes, mime_type="application/pdf"))
                st.markdown(f"<span class='badge-ok'>✓ {pdf.name}</span>", unsafe_allow_html=True)
            
            st.session_state["pdfs_cargados"] = partes_pdf
            st.success(f"✅ {len(pdfs)} PDF(s) listos para usar en el chat")

    with col_csv:
        st.markdown("#### 📊 CSV / Excel (lista de tablas, configuración de PKs)")
        archivo_tablas = st.file_uploader(
            "Sube CSV o Excel con la configuración de tablas",
            type=["csv", "xlsx"],
            key="csv_uploader"
        )
        
        if archivo_tablas:
            try:
                if archivo_tablas.name.endswith(".csv"):
                    df = pd.read_csv(archivo_tablas)
                else:
                    df = pd.read_excel(archivo_tablas)
                
                st.dataframe(df.head(10), use_container_width=True)
                
                # Convertir a contexto de texto
                ctx_csv = f"\nConfiguración de tablas desde archivo:\n{df.to_string(index=False)}"
                st.session_state.esquema_contexto += ctx_csv
                st.success(f"✅ {len(df)} filas cargadas como contexto")
                
            except Exception as e:
                st.error(f"Error leyendo archivo: {e}")

    st.divider()
    st.markdown("#### ✏️ Instrucciones de negocio (texto libre)")
    reglas = st.text_area(
        "Reglas, convenciones o requisitos específicos del proyecto:",
        height=150,
        placeholder="""Ejemplos:
- Todos los campos de fecha vienen como BIGNUMERIC en formato SAP (20260420144938.912909)
- El campo GLDELFLAG indica registros borrados cuando no está vacío
- Las tablas Z_* son de SAP, las tablas KN* son de clientes
- Target dataset: MRD_STANDARD, Source: MRP_STANDARD"""
    )
    
    if reglas and st.button("➕ Añadir al contexto del agente"):
        st.session_state.esquema_contexto += f"\n\nReglas de negocio del proyecto:\n{reglas}"
        st.success("✅ Instrucciones añadidas al contexto")

# ══════════════════════════════════════════════════════════
# TAB 3: ARCHIVOS GENERADOS
# ══════════════════════════════════════════════════════════
with tab_archivos:
    st.markdown("### 📁 Archivos generados")
    
    if not st.session_state.archivos_gen:
        st.info("Ningún archivo generado todavía. Usa el chat para generar código.")
    else:
        st.caption(f"{len(st.session_state.archivos_gen)} archivo(s) generados en esta sesión")
        
        for nombre, contenido in st.session_state.archivos_gen.items():
            with st.expander(f"📄 {nombre}"):
                st.code(contenido, language="javascript" if nombre.endswith(".js") else "sql")
                
                col_dl, col_del = st.columns([3,1])
                with col_dl:
                    st.download_button(
                        f"⬇️ Descargar {nombre}",
                        data=contenido,
                        file_name=nombre,
                        mime="text/plain",
                        key=f"dl_{nombre}"
                    )
                with col_del:
                    if st.button("🗑️ Eliminar", key=f"del_{nombre}"):
                        del st.session_state.archivos_gen[nombre]
                        st.rerun()
        
        st.divider()
        zip_bytes = generar_zip(st.session_state.archivos_gen)
        st.download_button(
            "📦 Descargar todos como ZIP",
            data=zip_bytes,
            file_name="dataform_generated.zip",
            mime="application/zip",
            use_container_width=True
        )
