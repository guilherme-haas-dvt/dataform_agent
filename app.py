"""
Dataform AI Studio
Agente conversacional para generar código JS/SQLX para Dataform
"""

import streamlit as st
from streamlit_oauth import OAuth2Component
from google.oauth2.credentials import Credentials

# 2. Variables de configuración para Google (Pon esto de momento, luego las cambiaremos por las reales)
CLIENT_ID = st.secrets["GOOGLE_CLIENT_ID"]
CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]
AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REVOKE_URL = "https://oauth2.googleapis.com/revoke"
SCOPES = "https://www.googleapis.com/auth/cloud-platform https://www.googleapis.com/auth/bigquery"

import os
import io
import json
import zipfile
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import requests

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
    background: #FFFFFF;
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
# CONTROL DE ACCESO (OAUTH)
# ══════════════════════════════════════════════════════════
# Inicializamos el componente de login
oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZATION_URL, TOKEN_URL, TOKEN_URL, REVOKE_URL)

# Si el usuario no ha iniciado sesión, detenemos la app y le mostramos el botón
if "auth" not in st.session_state:
    st.title("🔒 Acceso Compartido - Dataform AI Studio")
    st.write("Por favor, inicia sesión con tu cuenta de Devoteam para acceder al agente.")
    
    # Este botón redirige a Google y vuelve a la app local (http://localhost:8501)
resultado_login = oauth2.authorize_button("Conectar con mi cuenta Devoteam", "https://tu-app.streamlit.app", SCOPES)    
    if resultado_login:
        # Si Google dice que el usuario es válido, guardamos sus datos en la sesión
        st.session_state["auth"] = resultado_login
        st.rerun()
    st.stop() # Bloquea el resto de la app hasta que se pulse el botón

# Si llega aquí, es que ya está logueado. Creamos su 'llave' personal:
token_acceso = st.session_state["auth"]["token"]["access_token"]
llave_usuario = Credentials(token_acceso)



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
Eres un Arquitecto de Datos Senior experto en Google Cloud, BigQuery y Dataform para Devoteam.
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

REGLAS CRÍTICAS DE COSTES Y FORMATO DE RESPUESTA (OBLIGATORIO):
1. PROHIBIDO SALUDAR O DESPEDIRSE. No digas 'Hola', 'Aquí tienes', ni 'Espero que te sirva'.
2. CERO EXPLICACIONES. No justifiques el código ni pongas secciones de "Prácticas recomendadas".
3. VE DIRECTO AL GRANO. Devuelve MÁXIMO 1 línea de texto introductorio y luego inmediatamente el bloque de código.
4. FORMATO: El código SIEMPRE debe ir en bloques ```javascript o ```sqlx.

REGLA EXTRA: Cuando uses assertions nonNull sobre una columna, 
esa columna DEBE estar en el SELECT y GROUP BY de la consulta. 
Si no es posible incluirla, omite la assertion y avisa al usuario.
"""

# ══════════════════════════════════════════════════════════
# PERMISOS DE BIGQUERY
# ══════════════════════════════════════════════════════════

def obtener_esquema_bq(project, dataset, tabla, credenciales):
    # Añadimos 'credentials=credenciales' para que use el login del usuario
    client = bigquery.Client(project=project, credentials=credenciales)
    
    query = f"""
        SELECT column_name, data_type, is_nullable
        FROM `{project}.{dataset}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{tabla}'
        ORDER BY ordinal_position
    """
    df = client.query(query).to_dataframe()
    return df.to_string(index=False)

# ══════════════════════════════════════════════════════════
# FUNCIONES DE BIGQUERY
# ══════════════════════════════════════════════════════════
def obtener_esquema_bq(project, dataset, tabla):
    client = bigquery.Client(project=project)
    
    query = f"""
        SELECT column_name, data_type, is_nullable
        FROM `{project}.{dataset}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{tabla}'
        ORDER BY ordinal_position
    """
    df = client.query(query).to_dataframe()
    return df.to_string(index=False)

def listar_tablas_dataset(client: bigquery.Client, project: str, dataset: str) -> list:
    """Lista todas las tablas de un dataset."""
    tablas = list(client.list_tables(f"{project}.{dataset}"))
    return [t.table_id for t in tablas]

# ══════════════════════════════════════════════════════════
# FUNCIÓN DE LLAMADA SKILLS EN GITHUB
# ══════════════════════════════════════════════════════════
def cargar_skill_github(url_raw):
    try:
        r = requests.get(url_raw, timeout=5)
        return r.text if r.status_code == 200 else ""
    except:
        return ""

# URLs de las dos skills públicas: 
URL_SKILL_1 = "https://raw.githubusercontent.com/devoteamgcloud/dataform-assertions/main/README.md"

# ══════════════════════════════════════════════════════════
# FUNCIÓN DE LLAMADA AL MODELO
# ══════════════════════════════════════════════════════════
def llamar_agente(mensaje: str, historial: list, esquema_ctx: str, pdf_parts: list) -> str:
    # 1. Importamos librería
    from google import genai
    from google.genai import types
    import os
    
    # Descargamos el conocimiento de las dos fuentes públicas
    skill_assertions = cargar_skill_github(URL_SKILL_1)

    system_prompt = (
    f"{SYSTEM_PROMPT}\n\n"
    "REGLA IMPORTANTE: Usa SIEMPRE assertions nativas de Dataform por defecto.\n"
    "SOLO usa la skill externa si el usuario pide explícitamente 'assertions avanzadas':\n\n"
    f"SKILL 1 (Aserciones Avanzadas - solo si se pide):\n{skill_assertions}\n\n"
)

    # Recuperamos  proyecto
    project_id = st.session_state.get("project_id", "")
    if not project_id:
        return "⚠️ Primero conecta tu proyecto en el panel lateral."

    try:
        # 2. 
        client = genai.Client(
            vertexai=True,
            project=project_id,
            credentials=llave_usuario 
        )
        
        if st.session_state.conectado:
            import re
            ctx_proyecto = (
            f"Project ID: {st.session_state.project_id}\n"
            f"Dataset: {st.session_state.dataset_id}\n\n"
    )
            esquema_ctx = ctx_proyecto + esquema_ctx

            posible_tabla = re.search(r'\b([A-Za-z][A-Za-z0-9_]{2,})\b', mensaje)
            if posible_tabla:
                try:
                    esquema_real = obtener_esquema_bq(
                        st.session_state.project_id,
                        st.session_state.dataset_id,
                        posible_tabla.group(1)
                    )
                    esquema_ctx = f"Esquema real de BQ:\n{esquema_real}\n\n{esquema_ctx}"
                except:
                    pass
                     
        prompt_completo = f"Contexto de tablas:\n{esquema_ctx}\n\nPetición: {mensaje}"

        # 3. Llamamos al modelo
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt_completo)]
                )
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2
            )
        )
        
        return response.text

    except Exception as e:
        return f"❌ Error de Vertex AI: {str(e)}"

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
# GUARDAR CODIGO EN DATAFORM
# ══════════════════════════════════════════════════════════

def guardar_en_dataform(project_id: str, repository: str, workspace: str, nombre_archivo: str, codigo: str):
    """Escribe un archivo directamente en el Workspace de Dataform usando la API de Google."""
    from google.cloud import dataform_v1beta1
    
    # Elige la región donde tengas creado tu Dataform (normalmente us-central1 o europe-west3)
    region = "us-central1" 
    
    client = dataform_v1beta1.DataformClient()
    
    # Construimos la "dirección exacta" de tu espacio de trabajo en Google Cloud
    workspace_path = f"projects/{project_id}/locations/{region}/repositories/{repository}/workspaces/{workspace}"
    
    # Preparamos la ruta de la carpeta donde van los modelos (definitions/)
    ruta_final = f"definitions/{nombre_archivo}"
    
    # Convertimos el texto del código a bytes para que viaje seguro por internet
    bytes_codigo = codigo.encode("utf-8")
    
    # Creamos la petición de escritura
    request = dataform_v1beta1.WriteFileRequest(
        workspace=workspace_path,
        path=ruta_final,
        contents=bytes_codigo
    )
    
    # Lanzamos la llamada a la API
    client.write_file(request=request)

# ══════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════
with st.sidebar:
    st.header("🔌 Conexión a BigQuery")
    st.write("Introduce el entorno de datos para tu proyecto de Dataform.")

    project_id = st.text_input("GCP Project ID", value="")
    dataset_id = st.text_input("Dataset ID", value="")

    if "conectado" not in st.session_state:
        st.session_state.conectado = False

    # El botón ahora SOLO valida BigQuery
    if st.button("Inicializar Conexión", use_container_width=True):
        with st.spinner("Verificando acceso a BigQuery..."):
            try:
                from google.cloud import bigquery
                client = bigquery.Client(project=project_id, credentials=llave_usuario)
                dataset_ref = client.dataset(dataset_id)
                client.get_dataset(dataset_ref)  # Valida si existe el dataset
                
                st.session_state.conectado = True
                st.session_state.project_id = project_id
                st.session_state.dataset_id = dataset_id
                st.success("¡Estructura de datos localizada!")
            except Exception as e:
                st.session_state.conectado = False
                st.error(f"❌ Error en BigQuery: {e}")

    st.write("---")

    if st.session_state.conectado:
        st.markdown(
            f"""
            <div style="background-color: #d4edda; padding: 10px; border-radius: 5px; border-left: 5px solid #28a745;">
                <b style="color: #155724;">🟢 DATASET CONECTADO</b><br>
                <small style="color: #155724;">Proyecto: {st.session_state.project_id}</small><br>
                <small style="color: #155724;">Dataset: {st.session_state.dataset_id}</small>
            </div>
            """, 
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div style="background-color: #f8d7da; padding: 10px; border-radius: 5px; border-left: 5px solid #dc3545;">
                <b style="color: #721c24;">🔴 SIN DATOS</b><br>
                <small style="color: #721c24;">Configura BigQuery para activar el entorno.</small>
            </div>
            """, 
            unsafe_allow_html=True
        )
# ══════════════════════════════════════════════════════════
# CUERPO PRINCIPAL
# ══════════════════════════════════════════════════════════
st.markdown("""
<div class="main-header">
  <div style="font-size:30px">⚙️</div>
  <div>
    <h1>Dataform AI Studio</h1>
    <p>Agente conversacional para generar código JS/SQLX · Conecta BQ, sube PDFs y refina el código en chat</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────
tab_chat, tab_archivos = st.tabs(["💬 Chat con el Agente", "📁 Archivos generados"])

# ══════════════════════════════════════════════════════════
# TAB 1: CHAT
# ══════════════════════════════════════════════════════════
with tab_chat:
    
    
            
    # ── Accesos rápidos ──────────────────────────────────
    st.markdown("#### ⚡ Accesos rápidos")
    st.write("Haz clic en una plantilla para ejecutarla automáticamente:")
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
    if "_pending_prompt" in st.session_state and st.session_state["_pending_prompt"]:
        st.session_state["chat_input"] = st.session_state.pop("_pending_prompt")
    

    st.markdown("#### 📎 Contexto adicional para el agente")
    st.write("Estos inputs se añaden como contexto en la siguiente petición del chat.")

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
        st.markdown("#### 📊 CSV / Sheets (lista de tablas, configuración de PKs)")
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
    
    user_input = st.text_area(
        "Tu petición:",
        height=100,
        placeholder="Ej: 'Genera el operate() con MERGE incremental para Z_EVER usando VERTRAG como PK'",
        key="chat_input"
    )
    
    col_send, col_clear= st.columns([2.5, 1])
    with col_send:
        enviar = st.button("➤ Generar Consulta", use_container_width=True)
    with col_clear:
        if st.button("Limpiar chat", use_container_width=True):
            st.session_state.historial = []
            st.rerun()

    if enviar and user_input.strip():
        with st.spinner("Generando..."):
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

with st.container(border=True):
    for msg in st.session_state.historial:
        if msg["role"] == "user":
            st.markdown(f"<div class='msg-label-user'>TÚ</div><div class='msg-user'>{msg['display']}</div>", unsafe_allow_html=True)
        else:
            # Renderizar respuesta del agente: separar código del texto
            contenido = msg["content"]
            import re
            partes = re.split(r'(```(?:javascript|js|sql|sqlx)?\n[\s\S]*?```)', contenido)
            
            st.markdown(f"<div class='msg-label-agent'>⚙️ AGENTE</div>", unsafe_allow_html=True)
            for parte in partes:
                if parte.startswith("```"):
                    lang = re.match(r'```(\w+)', parte)
                    lenguaje = lang.group(1) if lang else "sql"
                    codigo = re.sub(r'^```[\w]*\n', '', parte)
                    codigo = re.sub(r'```$', '', codigo).strip()
                    st.code(codigo, language=lenguaje)
                else:
                    if parte.strip():
                        texto_html = parte.strip().replace('\n', '<br>')
                        st.markdown(f"<div class='msg-agent'>{texto_html}</div>", unsafe_allow_html=True)

    if "archivos_gen" in st.session_state and st.session_state.archivos_gen:
        st.write("---")
        st.markdown("#### Desplegar directamente a Dataform")
    
        nombre_fichero = list(st.session_state.archivos_gen.keys())[-1]
        codigo_fichero = st.session_state.archivos_gen[nombre_fichero]

    # 2. Configuración del destino en Google Cloud (aparece justo abajo del código)
        st.write("Configura el destino en tu repositorio de GCP antes de enviar:")
        nombre_fichero_final = st.text_input(
        "Nombre del archivo final (puedes cambiarlo):", 
        value=nombre_fichero,
        key="input_nombre_magico"
    )

        col_repo, col_work = st.columns(2)
        with col_repo:
            repo_input = st.text_input(
                "Repositorio Dataform:", 
                value="", 
            )
        with col_work:
            work_input = st.text_input(
                "Tu Workspace (Rama Git):", 
                value="", 
            )

        st.write("")
        texto_boton = f"Confirmar e Inyectar fichero en GCP"
        
        if st.button(texto_boton):
            if not repo_input or not work_input:
                st.error("⚠️ Por favor, rellena el Repositorio y el Workspace antes de inyectar en GCP.")
            else:
                with st.spinner("Estableciendo conexión con la API de Dataform..."):
                    try:
                        guardar_en_dataform(
                            project_id=st.session_state.get("project_id", ""),
                            repository=repo_input,
                            workspace=work_input,
                            nombre_archivo=nombre_fichero,
                            codigo=codigo_fichero
                        )
                        st.success(f" El archivo {nombre_fichero} ya ha sido creado.")
                    except Exception as e:
                        st.error(f"La API de Dataform rechazó la escritura: {e}")

       
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
