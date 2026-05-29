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
    """Inicializa Vertex AI y procesa el chat en la zona central capturando los errores de la API."""
    
    # Recuperamos el proyecto validado por el panel lateral
    project_id = st.session_state.get("project_id", "integracion-snp-glue")

    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel, Content, Part
        
        # Inicializamos Vertex AI dinámicamente con el proyecto activo
        vertexai.init(project=project_id, location="us-central1")
        system_prompt = globals().get("SYSTEM_PROMPT", "Eres un experto en Dataform de Devoteam.")
        model = GenerativeModel("gemini-1.5-flash", system_instruction=system_prompt)

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

        # Realizamos la llamada real. Aquí saltará el 403 si la API está desactivada
        respuesta = model.generate_content(contents)
        return respuesta.text.strip()

    except Exception as e:
        # El error de la API de Google aparecerá en la parte central como respuesta del chat
        return f"❌ Error de Vertex AI (IA de Google):\n\n{e}"

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
                client = bigquery.Client(project=project_id)
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
    
    # Ahora dibujamos la caja. Ya no necesita el parámetro "value" 
    # porque leerá automáticamente lo que metimos en su "key".
    user_input = st.text_area(
        "Tu petición:",
        height=100,
        placeholder="Ej: 'Genera el operate() con MERGE incremental para Z_EVER usando VERTRAG como PK'",
        key="chat_input"
    )
    
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
    col_send, col_clear, col_deploy = st.columns([2.5, 1, 1])
    with col_send:
        enviar = st.button("➤ Generar Consulta", use_container_width=True)
    with col_clear:
        if st.button("Limpiar chat", use_container_width=True):
            st.session_state.historial = []
            st.rerun()
    with col_deploy:
        desplegar = st.button("Desplegar a Dataform", use_container_width=True)

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

    if "archivos_gen" in st.session_state and st.session_state.archivos_gen:
        st.write("---")
        st.markdown("#### 🚀 Desplegar directamente a Dataform")
    
    # 1. Recuperamos de la memoria el archivo extraído
        nombre_fichero = list(st.session_state.archivos_gen.keys())[-1]
        codigo_fichero = st.session_state.archivos_gen[nombre_fichero]

    # 👁️ VISOR DE CÓDIGO REAL (¡Aquí es donde se hace totalmente visible!)
        st.markdown(f"**📄 Contenido generado para el archivo `{nombre_fichero}`:**")
    
    # Detectamos si es SQLX o JS para que Streamlit lo pinte con colores bonitos
        tipo_lenguaje = "sql" if nombre_fichero.endswith((".sqlx", ".sql")) else "javascript"
        st.code(codigo_fichero, language=tipo_lenguaje)


    # 2. Configuración del destino en Google Cloud (aparece justo abajo del código)
        st.write("Configura el destino en tu repositorio de GCP antes de enviar:")
        col_repo, col_work = st.columns(2)
        with col_repo:
            repo_input = st.text_input("Repositorio Dataform:", value="mrp-repository")
        with col_work:
            work_input = st.text_input("Tu Workspace (Rama Git):", value="desarrollo-compartido")

    # 3. El botón físico de envío
        if st.button(f"📥 Confirmar e Inyectar `{nombre_fichero}` en GCP", type="primary", use_container_width=True):
            with st.spinner("Estableciendo conexión con la API de GCP..."):
                try:
                    guardar_en_dataform(
                        project_id=st.session_state.get("project_id", ""),
                        repository=repo_input,
                        workspace=work_input,
                        nombre_archivo=nombre_fichero,
                        codigo=codigo_fichero
                    )
                    st.success(f"🎉 ¡Éxito absoluto! El archivo `{nombre_fichero}` ya ha sido creado en tu Workspace.")
                except Exception as e:
                    st.error(f"❌ La API de Dataform rechazó la escritura: {e}")

    if desplegar:
        # Comprobamos que haya código generado en la memoria antes de intentar subir nada
        if "archivos_gen" in st.session_state and st.session_state.archivos_gen:
            with st.spinner("Inyectando código en Google Cloud..."):
                try:
                    nombre_fichero = list(st.session_state.archivos_gen.keys())[-1]
                    codigo_fichero = st.session_state.archivos_gen[nombre_fichero]
                    
                    # Llamamos a la API (puedes ajustar el repo y workspace fijos o leerlos del sidebar)
                    guardar_en_dataform(
                        project_id=st.session_state.get("project_id", "integracion-snp-glue"),
                        repository="mrp-repository", 
                        workspace="desarrollo-compartido",
                        nombre_archivo=nombre_fichero,
                        codigo=codigo_fichero
                    )
                    st.success(f"✅ ¡El archivo `{nombre_fichero}` se ha desplegado en Dataform correctamente!")
                except Exception as e:
                    st.error(f"❌ Error al desplegar: {e}")
        else:
            # Si le da al botón sin haber generado código primero, le avisamos
            st.warning("⚠️ No hay ningún código generado todavía. Pregúntale algo al Agente primero.")
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
