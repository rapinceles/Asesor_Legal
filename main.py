# main.py
from fastapi import FastAPI, Form, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, Response
from typing import List
import openai
import os
import json

# Importar los scrapers
from app.seia_scraper import buscar_empresa
from app.bcn_scraper import buscar_normativa_bcn # Importar el nuevo scraper de BCN


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
@app.post("/analizar_formulario/")
async def analizar_formulario(
    analisis: str = Form(...),
    empresa: str = Form(...),
    sector: str = Form(...), # Tipo de asesor
    documentos: List[UploadFile] = File(default=None)
):
    # --- Lógica condicional basada en el 'sector' (Tipo de asesor) ---
    datos_externos_formateados = "" # Variable para almacenar los datos de SEIA o BCN

    if sector.lower() == "ambiental":
        print(f"Modo Ambiental activado. Buscando en SEIA para: {empresa}")
        # Buscar proyectos y raspar documentos/RCAs del SEIA
        # Retorna una lista de diccionarios de proyecto
        proyectos_seia = buscar_empresa(empresa)

        # Formatear los datos obtenidos del SEIA para el prompt
        if proyectos_seia:
            datos_externos_formateados += "Información relevante extraída del SEIA:\n\n"
            for i, proyecto in enumerate(proyectos_seia):
                datos_externos_formateados += f"--- Proyecto {i+1}: {proyecto.get('nombre_proyecto', 'N/A')} (Código: {proyecto.get('codigo', 'N/A')}) ---\n"
                datos_externos_formateados += f"Enlace Expediente: {proyecto.get('link_expediente', 'No disponible')}\n"
                datos_externos_formateados += f"Región: {proyecto.get('region', 'N/A')}\n"
                datos_externos_formateados += f"Fecha Ingreso: {proyecto.get('fecha_ingreso', 'N/A')}\n\n"

                # Formatear los documentos/RCAs encontrados para este proyecto
                documentos_rcas = proyecto.get('documentos_rcas', [])
                if documentos_rcas:
                    datos_externos_formateados += "Documentos/RCAs encontrados para este proyecto:\n"
                    for j, doc in enumerate(documentos_rcas):
                        datos_externos_formateados += f"  - {doc.get('documento_tipo', 'Documento sin tipo')} (Folio: {doc.get('folio', 'N/A')}, Fecha: {doc.get('fecha', 'N/A')})\n"
                        if doc.get('link_pdf', 'No disponible') != "No disponible":
                            datos_externos_formateados += f"    Enlace PDF: {doc.get('link_pdf')}\n"
                    datos_externos_formateados += "\n"
                else:
                    datos_externos_formateados += "No se encontraron documentos/RCAs específicos en SEIA para este proyecto.\n\n"
            datos_externos_formateados += "---\n\n"
        else:
            datos_externos_formateados = "No se encontraron proyectos relevantes en el SEIA para la búsqueda.\n\n"

    elif sector.lower() == "legal": # --- Lógica para el modo "Legal" ---
        print(f"Modo Legal activado. Buscando normativa en BCN para: {analisis}")
        # Buscar normativa en BCN usando la consulta del usuario
        normativas_bcn = buscar_normativa_bcn(analisis)

        # Formatear los resultados de la BCN para el prompt
        if normativas_bcn:
            datos_externos_formateados += "Normativa encontrada en BCN (potencialmente relevante):\n\n"
            for i, norma in enumerate(normativas_bcn):
                datos_externos_formateados += f"--- Norma {i+1} ---\n"
                datos_externos_formateados += f"Nombre: {norma.get('nombre', 'N/A')}\n"
                datos_externos_formateados += f"Tipo: {norma.get('tipo', 'N/A')}\n" # Requiere extraccion real en scraper
                datos_externos_formateados += f"Número: {norma.get('numero', 'N/A')}\n" # Requiere extraccion real en scraper
                datos_externos_formateados += f"Fecha: {norma.get('fecha', 'N/A')}\n" # Requiere extraccion real en scraper
                datos_externos_formateados += f"Enlace: {norma.get('link', 'No disponible')}\n"
                datos_externos_formateados += "\n"
            datos_externos_formateados += "---\n\n"
        else:
            datos_externos_formateados = "No se encontró normativa relevante en BCN para la consulta.\n\n"


    elif sector.lower() == "administrativo": # --- Lógica para el modo "Administrativo" ---
         # Puedes añadir aqui logica especifica para el modo administrativo
         datos_externos_formateados = f"Modo Administrativo activado. Puedes implementar lógica de búsqueda o análisis específica aquí.\n\n"
         # Por ahora, no hace busqueda externa

    else:
        # Modo desconocido o no seleccionado
        datos_externos_formateados = "Tipo de asesor no especificado o desconocido. No se realizó búsqueda externa.\n\n"
        # No se realiza busqueda externa


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


    # --- Construir el prompt MEJORADO para GPT (Ajustado para modos y datos externos) ---

    client = openai.OpenAI()

    # Ajustar el prompt del sistema segun el tipo de asesor
    system_prompt_content = """Eres un asesor experto en normativa, regulaciones y análisis de riesgos en Chile.
Tu objetivo es proporcionar un análisis detallado, estructurado, profesional y preciso sobre la consulta del usuario, basándote en TODA la información proporcionada (consulta, empresa, datos externos -SEIA o BCN-, documentos adjuntos).

Directrices generales para la respuesta:
1.  **Estructura:** Divide la respuesta en secciones claras usando encabezados.
2.  **Contenido:** Profundiza en los aspectos relevantes segun el tipo de asesor (ambiental, legal, administrativo).
3.  **Citación:** Siempre que sea posible y relevante, cita explícitamente las fuentes proporcionadas (datos del SEIA, normativa BCN, documentos adjuntos).
4.  **Riesgos y Recomendaciones:** Identifica riesgos y formula recomendaciones concretas basadas en el analisis y las fuentes.
5.  **Formato:** Usa viñetas dentro de las secciones.
6.  **Idioma:** Responde siempre en español de Chile.
"""

    # Ajustar el prompt del usuario incluyendo los datos externos y documentos
    prompt_user_content = f"""
Por favor, realiza el análisis solicitado basándote en la siguiente información:

Información de la Empresa:
Nombre proporcionado: {empresa}
Tipo de asesor solicitado: {sector}

Consulta específica a analizar:
{analisis}

--- Datos Externos Obtenidos ({sector}) ---
{datos_externos_formateados} # <-- ¡Incluir aquí los datos de SEIA o BCN formateados!
---------------------------------------

--- Contenido de Documentos Adjuntos ---
{texto_docs}
------------------------------------

Genera el análisis siguiendo estrictamente las directrices y usando la información proporcionada. Adapta tu enfoque segun el 'Tipo de asesor' solicitado. Si no hay datos externos o documentos, basa tu respuesta en tu conocimiento general y la consulta.
"""

    try:
        response = client.chat.completions.create(
             model="gpt-3.5-turbo", # Puedes cambiar a "gpt-4" si lo necesitas y tienes acceso
             messages=[
                 {"role": "system", "content": system_prompt_content}, # Usamos la variable
                 {"role": "user", "content": prompt_user_content} # Usamos la variable
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
