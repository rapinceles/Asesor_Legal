# main.py
from fastapi import FastAPI, Form, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, Response
from typing import List
import openai
import os
import json # Importar json para manejar datos estructurados si es necesario

# Importar la funcion buscar_empresa del scraper
from app.seia_scraper import buscar_empresa

app = FastAPI()

# Configurar carpetas estaticas y plantillas HTML
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static")

# Configurar la clave de la API de OpenAI (la librería la lee del entorno OPENAI_API_KEY)


# Ruta raiz que carga la interfaz visual
@app.get("/", response_class=HTMLResponse)
async def render_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Ruta para recibir y procesar formulario
# La URL debe coincidir con el fetch en index.html (guion bajo y barra final)
@app.post("/analizar_formulario/") # <--- URL con guiones bajos!
async def analizar_formulario(
    analisis: str = Form(...),
    empresa: str = Form(...), # Usamos 'empresa' para buscar el proyecto
    sector: str = Form(...), # Tipo de asesor
    documentos: List[UploadFile] = File(default=None) # Usar List[UploadFile] para multiples archivos
):
    # --- Lógica para el modo "Ambiental" (basada en el campo 'sector') ---
    # Puedes añadir aqui la lógica para otros modos si son diferentes
    seia_data_formatted = ""
    if sector.lower() == "ambiental":
        print(f"Modo Ambiental activado. Buscando en SEIA para: {empresa}")
        # Buscar proyectos y raspar documentos/RCAs del SEIA
        # La función ahora retorna una lista de diccionarios de proyecto
        proyectos_seia = buscar_empresa(empresa)

        # Formatear los datos obtenidos del SEIA (proyectos y sus documentos/RCAs)
        if proyectos_seia:
            seia_data_formatted += "Información relevante extraída del SEIA:\n\n"
            for i, proyecto in enumerate(proyectos_seia):
                seia_data_formatted += f"--- Proyecto {i+1}: {proyecto.get('nombre_proyecto', 'N/A')} (Código: {proyecto.get('codigo', 'N/A')}) ---\n"
                seia_data_formatted += f"Enlace Expediente: {proyecto.get('link_expediente', 'No disponible')}\n"
                seia_data_formatted += f"Región: {proyecto.get('region', 'N/A')}\n"
                seia_data_formatted += f"Fecha Ingreso: {proyecto.get('fecha_ingreso', 'N/A')}\n\n"

                # Formatear los documentos/RCAs encontrados para este proyecto
                documentos_rcas = proyecto.get('documentos_rcas', [])
                if documentos_rcas:
                    seia_data_formatted += "Documentos/RCAs encontrados para este proyecto:\n"
                    for j, doc in enumerate(documentos_rcas):
                        seia_data_formatted += f"  - {doc.get('documento_tipo', 'Documento sin tipo')} (Folio: {doc.get('folio', 'N/A')}, Fecha: {doc.get('fecha', 'N/A')})\n"
                        if doc.get('link_pdf', 'No disponible') != "No disponible":
                            seia_data_formatted += f"    Enlace PDF: {doc.get('link_pdf')}\n"
                    seia_data_formatted += "\n"
                else:
                    seia_data_formatted += "No se encontraron documentos/RCAs específicos para este proyecto.\n\n"
            seia_data_formatted += "---\n\n"
        else:
            seia_data_formatted = "No se encontraron proyectos relevantes en el SEIA para la búsqueda.\n\n"

    elif sector.lower() == "legal" or sector.lower() == "administrativo":
         # Lógica para otros modos: quizás no buscar en SEIA, o buscar otra cosa
         seia_data_formatted = f"Modo {sector} activado. No se realizó búsqueda específica en SEIA para este modo.\n\n"
         # Puedes añadir aqui otra logica de busqueda o recoleccion de datos si aplica

    else:
        # Modo desconocido o no seleccionado
        seia_data_formatted = "Tipo de asesor no especificado o desconocido.\n\n"
        # No se realiza busqueda en SEIA ni otra logica especifica


    # Procesar documentos subidos (como antes)
    contenidos = []
    if documentos:
        for doc in documentos:
            if doc.filename == '':
                 continue
            try:
                contenido_bytes = await doc.read()
                try:
                    contenido = contenido_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                         contenido = contenido_bytes.decode('latin-1')
                    except Exception:
                         contenido = f"Error al decodificar el archivo {doc.filename}."
                contenidos.append(contenido)
            except Exception as e:
                contenidos.append(f"No se pudo leer el archivo {doc.filename}: {e}")

    texto_docs = "\n\n".join(contenidos) if contenidos else "Sin documentos adjuntos."


    # --- Construir el prompt MEJORADO para GPT ---

    client = openai.OpenAI()

    try:
        # Incluir los datos del SEIA y los documentos adjuntos en el prompt del usuario
        prompt_user_content = f"""
Por favor, realiza el análisis técnico y legal solicitado basándote en la siguiente información:

Información de la Empresa:
Nombre proporcionado: {empresa}
Tipo de asesor solicitado: {sector}

Consulta específica a analizar:
{analisis}

{seia_data_formatted} # <-- ¡Incluir aquí los datos del SEIA/RCAs formateados!

Contenido de los Documentos Adjuntos (si fueron proporcionados):
{texto_docs}

Genera el análisis siguiendo estrictamente las directrices de estructura, contenido técnico/legal, citación, riesgos y recomendaciones detalladas en tus instrucciones de sistema. Enfócate en la consulta específica y utiliza la información del SEIA y documentos para fundamentar tu respuesta en el contexto chileno.
"""

        response = client.chat.completions.create(
             model="gpt-3.5-turbo", # Puedes cambiar a "gpt-4" si lo necesitas y tienes acceso
             messages=[
                 # Prompt del sistema: Define el rol, tono y expectativas generales de FORMATO y CONTENIDO
                 {"role": "system", "content": """Eres un asesor experto en normativa ambiental, legal, técnica y de riesgo en Chile.
Tu objetivo es proporcionar un análisis **detallado, estructurado, profesional y preciso** sobre la consulta del usuario, basándote en TODA la información proporcionada (consulta, empresa, datos del SEIA/RCAs, documentos adjuntos).

Directrices para la respuesta:
1.  **Estructura:** Divide la respuesta en secciones claras usando encabezados (ej: 1. Normativa Aplicable, 2. Análisis Técnico/Situacional, 3. Evaluación de Riesgos, 4. Recomendaciones).
2.  **Contenido Técnico/Legal:** Profundiza en los aspectos técnicos y legales relevantes. **Haz referencia directa a los documentos/RCAs del SEIA proporcionados cuando sea aplicable al análisis de la consulta.**
3.  **Citación:** Siempre que sea posible y relevante, **cita explícitamente la normativa ambiental y legal chilena aplicable (leyes, reglamentos, DS, etc.) Y haz referencia a las RCAs específicas si se proporcionaron en los datos del SEIA (ej: "Según la RCA N° XXX...", "El expediente ZZZ indica...").** No inventes citas ni datos de RCAs; usa solo la información proporcionada.
4.  **Riesgos:** Identifica y describe claramente los **risgos** técnicos, legales y operacionales asociados a la consulta o la situación de la empresa, **conectándolos con las normativas y RCAs relevantes si la información está disponible.**
5.  **Recomendaciones:** Formula **recomendaciones concretas, prácticas y aplicables** para la empresa, **basadas en el análisis y la información del SEIA/RCAs.**
6.  **Formato:** Usa **viñetas** dentro de las secciones para listar puntos clave. Asegúrate de que el texto sea legible y bien organizado.
7.  **Idioma:** Responde siempre en español de Chile.
"""},
                 {"role": "user", "content": prompt_user_content} # Usamos la variable con todo el contenido
             ],
             temperature=0.7
         )

        respuesta_texto = response.choices[0].message.content

        return respuesta_texto


    except openai.APIError as e:
        print(f"Error de la API de OpenAI: {e}")
        return f"Error de la API de OpenAI: {e}"
    except Exception as e:
        print(f"Error general al generar análisis: {e}")
        return f"Error al generar análisis: {str(e)}"
