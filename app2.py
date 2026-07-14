"""
Devoteam Dataform AI Studio - Versión Chainlit (Nativa)
Agente conversacional para generar código JS/SQLX para Dataform
"""

import chainlit as cl
import os
import io
import re
import pandas as pd
import requests
from google.cloud import bigquery
from google.cloud import dataform_v1beta1
from google import genai
from google.genai import types
from google.oauth2.credentials import Credentials

# ══════════════════════════════════════════════════════════
# 1. EL "MURO" DE SEGURIDAD (OAUTH NATIVO DE CHAINLIT)
# ══════════════════════════════════════════════════════════
@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: dict,
    default_user: cl.User,
) -> cl.User | None:
    if raw_user_data.get("hd") == "devoteam.com":
        # ¡ESTA ES LA LÍNEA NUEVA QUE FALTA! Guardamos el token en el usuario
        default_user.metadata["oauth_token"] = token
        return default_user
    return None

def get_user_credentials():
    """Extrae el token del usuario activo para que BigQuery y Vertex funcionen con su identidad."""
    user = cl.user_session.get("user")
    if user and "oauth_token" in user.metadata:
        return Credentials(token=user.metadata["oauth_token"])
    return None


# ══════════════════════════════════════════════════════════
# 2. CONFIGURACIÓN Y PROMPT DEL AGENTE
# ══════════════════════════════════════════════════════════
URL_SKILL_1 = "https://raw.githubusercontent.com/devoteamgcloud/dataform-assertions/main/README.md"

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
4. FORMATO: El código SIEMPRE debe ir en bloques de código (javascript o sqlx).
"""

# ══════════════════════════════════════════════════════════
# 3. FUNCIONES BÁSICAS DE LÓGICA (GCP)
# ══════════════════════════════════════════════════════════
def obtener_esquema_bq(project, dataset, tabla):
    client = bigquery.Client(project=project, credentials=get_user_credentials())
    query = f"""
        SELECT column_name, data_type, is_nullable
        FROM `{project}.{dataset}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{tabla}'
        ORDER BY ordinal_position
    """
    df = client.query(query).to_dataframe()
    return df.to_string(index=False)

def cargar_skill_github(url_raw):
    try:
        r = requests.get(url_raw, timeout=5)
        return r.text if r.status_code == 200 else ""
    except:
        return ""

def extraer_bloques_codigo(texto: str) -> list:
    patron = r'\x60{3}(?:javascript|js|sql|sqlx)?\n([\s\S]*?)\x60{3}'
    return re.findall(patron, texto)

def guardar_en_dataform(project_id: str, repository: str, workspace: str, nombre_archivo: str, codigo: str):
    region = "us-central1" 
    client = dataform_v1beta1.DataformClient(credentials=get_user_credentials())
    workspace_path = f"projects/{project_id}/locations/{region}/repositories/{repository}/workspaces/{workspace}"
    ruta_final = f"definitions/{nombre_archivo}"
    bytes_codigo = codigo.encode("utf-8")
    request = dataform_v1beta1.WriteFileRequest(
        workspace=workspace_path,
        path=ruta_final,
        contents=bytes_codigo
    )
    client.write_file(request=request)

# ══════════════════════════════════════════════════════════
# 4. EVENTOS DE CHAINLIT (La Interfaz del Chat)
# ══════════════════════════════════════════════════════════
@cl.on_chat_start
async def start_chat():
    cl.user_session.set("historial", [])
    cl.user_session.set("esquema_contexto", "")
    cl.user_session.set("archivos_gen", {})

    # Chainlit ya validó el login de Google antes de mostrar esta pantalla, vamos directo al grano.
    await cl.Message(
        content="**¡Bienvenido a Devoteam Dataform AI Studio!**\n\nSoy el agente corporativo experto en ingeniería de datos, diseñado para acelerar tus desarrollos en GCP.",
        author="Devoteam AI"
    ).send()

    # ── ONBOARDING CONVERSACIONAL PARA BQ ──
    res_project = await cl.AskUserMessage(content="Para inicializar el entorno seguro, por favor envíame tu **GCP Project ID**:", timeout=120).send()
    
    if res_project:
        project_id = res_project.content if hasattr(res_project, 'content') else res_project.get('content', res_project.get('output', ''))
        cl.user_session.set("project_id", project_id.strip())
        
        res_dataset = await cl.AskUserMessage(content="Genial. Ahora envíame tu **Dataset ID** de trabajo:", timeout=120).send()
        
        if res_dataset:
            dataset_id = res_dataset.content if hasattr(res_dataset, 'content') else res_dataset.get('content', res_dataset.get('output', ''))
            cl.user_session.set("dataset_id", dataset_id.strip())
            
            msg = cl.Message(content=f"⏳ Conectando a BigQuery (`{project_id.strip()}.{dataset_id.strip()}`)...", author="Devoteam AI")
            await msg.send()
            
            try:
                # Validamos conexión a BigQuery
                client = bigquery.Client(project=project_id.strip(), credentials=get_user_credentials())
                client.get_dataset(dataset_id.strip())
                cl.user_session.set("bq_conectado", True)
                msg.content = "✅ **¡Conexión establecida con éxito!** Estructura de datos localizada.\n\n¿En qué te puedo ayudar hoy con Dataform? _(Recuerda que puedes adjuntar requerimientos en PDF o CSVs usando el clip 📎 aquí abajo)_"
                await msg.update()
            except Exception as e:
                cl.user_session.set("bq_conectado", False)
                msg.content = f"❌ **Error al conectar con BigQuery:** `{str(e)}`\n\nPuedes corregir y actualizar los datos escribiendo el ID correcto."
                await msg.update()
    else:
        await cl.Message(content="⚠️ Se agotó el tiempo. Recarga la página cuando estés listo.", author="Devoteam AI").send()

@cl.on_message
async def main(message: cl.Message):
    project_id = cl.user_session.get("project_id")
    if not project_id:
        await cl.Message(content="⚠️ Por favor, recarga la página e indica tu Project ID antes de hablar conmigo.", author="Devoteam AI").send()
        return

    contexto_archivos = ""
    pdf_parts = []
    
    # Procesamiento de archivos adjuntos (PDFs o CSVs con el clip 📎)
    if message.elements:
        for element in message.elements:
            if "pdf" in element.mime:
                with open(element.path, "rb") as f:
                    pdf_bytes = f.read()
                    pdf_parts.append(types.Part.from_data(data=pdf_bytes, mime_type="application/pdf"))
                contexto_archivos += f"\n[Documento cargado: {element.name}]"
            elif "csv" in element.mime or "excel" in element.mime:
                try:
                    df = pd.read_csv(element.path) if "csv" in element.mime else pd.read_excel(element.path)
                    contexto_archivos += f"\nConfiguración de tablas ({element.name}):\n{df.to_string(index=False)}"
                except Exception as e:
                    await cl.ErrorMessage(content=f"Error leyendo {element.name}: {e}").send()

    esquema_ctx = cl.user_session.get("esquema_contexto", "") + contexto_archivos
    
    # Si BQ está conectado, interceptamos el nombre de la tabla en el mensaje
    if cl.user_session.get("bq_conectado"):
        ctx_proyecto = f"Project ID: {project_id}\nDataset: {cl.user_session.get('dataset_id')}\n\n"
        esquema_ctx = ctx_proyecto + esquema_ctx
        
        posible_tabla = re.search(r'\b([A-Za-z][A-Za-z0-9_]{2,})\b', message.content)
        if posible_tabla:
            try:
                esquema_real = obtener_esquema_bq(project_id, cl.user_session.get("dataset_id"), posible_tabla.group(1))
                esquema_ctx = f"Esquema real de BQ:\n{esquema_real}\n\n{esquema_ctx}"
            except:
                pass

    prompt_completo = f"Contexto de tablas:\n{esquema_ctx}\n\nPetición: {message.content}"
    
    historial = cl.user_session.get("historial")
    partes_usuario = [types.Part.from_text(text=prompt_completo)] + pdf_parts

    # Cliente de Gemini (Vertex AI)
    client = genai.Client(vertexai=True, project=project_id, credentials=get_user_credentials())
    skill_assertions = cargar_skill_github(URL_SKILL_1)
    
    instrucciones = f"{SYSTEM_PROMPT}\n\nSKILL (Aserciones Avanzadas):\n{skill_assertions}"

    msg = cl.Message(content="", author="Devoteam AI")
    await msg.send()

    try:
        response = client.models.generate_content_stream(
            model="gemini-3.1-flash-lite-preview",
            contents=[types.Content(role="user", parts=partes_usuario)],
            config=types.GenerateContentConfig(
                system_instruction=instrucciones,
                temperature=0.2
            )
        )
        
        respuesta_completa = ""
        for chunk in response:
            respuesta_completa += chunk.text
            await msg.stream_token(chunk.text)
            
        await msg.update()
        
    except Exception as e:
        await cl.ErrorMessage(content=f"❌ Error de Vertex AI: {str(e)}").send()
        return

    # Guardar historial
    historial.append({"role": "user", "content": message.content})
    historial.append({"role": "assistant", "content": respuesta_completa})
    cl.user_session.set("historial", historial)

    # Extraer código generado y preparar el botón de Despliegue en GCP
    bloques = extraer_bloques_codigo(respuesta_completa)
    if bloques:
        archivos_gen = cl.user_session.get("archivos_gen")
        nombre_fichero = f"dataform_output_{len(archivos_gen)+1}.js"
        
        match_nombre = re.search(r'(?:archivo|file|guardar como)[:\s]+[`"]?(\w+\.(js|sqlx|sql))[`"]?', respuesta_completa, re.IGNORECASE)
        if match_nombre:
            nombre_fichero = match_nombre.group(1)
        elif "sqlx" in respuesta_completa[:200].lower():
            nombre_fichero = nombre_fichero.replace(".js", ".sqlx")
            
        archivos_gen[nombre_fichero] = bloques[0].strip()
        cl.user_session.set("archivos_gen", archivos_gen)

        actions = [
            cl.Action(
                name="deploy_action", 
                value=nombre_fichero, 
                label="🚀 Desplegar a Dataform",
                description="Inyecta este código en GCP"
            )
        ]
        await cl.Message(content=f"_He generado el archivo **{nombre_fichero}**._", actions=actions, author="Devoteam AI").send()

@cl.action_callback("deploy_action")
async def on_action(action: cl.Action):
    """Se ejecuta cuando el usuario pulsa el botón de 'Desplegar a Dataform'"""
    nombre_fichero = action.value
    codigo = cl.user_session.get("archivos_gen").get(nombre_fichero)
    
    project_id = cl.user_session.get("project_id")
    repo = cl.user_session.get("repo_df")
    workspace = cl.user_session.get("workspace_df")

    await action.remove() # Ocultamos el botón para no duplicar clicks
    
    # ── ONBOARDING CONVERSACIONAL PARA DEPLOY ──
    if not repo:
        res_repo = await cl.AskUserMessage(content="📁 No tengo configurado el repositorio. ¿Cuál es el nombre de tu **Repositorio Dataform**?", timeout=60).send()
        if res_repo:
            repo = res_repo.content if hasattr(res_repo, 'content') else res_repo.get('content', '')
            cl.user_session.set("repo_df", repo.strip())
        else:
            return
            
    if not workspace:
        res_ws = await cl.AskUserMessage(content="🌿 ¿Y en qué **Workspace (Rama Git)** quieres que lo inyecte?", timeout=60).send()
        if res_ws:
            workspace = res_ws.content if hasattr(res_ws, 'content') else res_ws.get('content', '')
            cl.user_session.set("workspace_df", workspace.strip())
        else:
            return
    
    msg_espera = cl.Message(content="⏳ Estableciendo conexión segura con GCP...", author="Devoteam AI")
    await msg_espera.send()
    
    try:
        guardar_en_dataform(project_id, repo, workspace, nombre_fichero, codigo)
        msg_espera.content = f"✅ ¡Éxito! El código ha sido desplegado directamente en `definitions/{nombre_fichero}` dentro de tu entorno Devoteam GCP."
        await msg_espera.update()
    except Exception as e:
        await cl.ErrorMessage(content=f"❌ La API rechazó el despliegue: {str(e)}").send()