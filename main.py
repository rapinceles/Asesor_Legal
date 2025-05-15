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

# Importar los scrapers. Si no necesitas SEIA en modo Legal, puedes mover la logica condicional.
from app.seia_scraper import buscar_empresa # Aun se usa para modo Ambiental
from app.bcn_scraper import buscar_normativa_bcn # <-- ¡Importar el scraper de BCN!


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
    analisis: str = Form(...), # Consulta del usuario
    empresa: str = Form(...), # Nombre de la empresa (usado en modo Ambiental)
    sector: str = Form(...), # Tipo de asesor (Controla que scraper usar)
    documentos: List[UploadFile] = File(default=None)
):
    # --- Lógica condicional basada en el 'sector' (Tipo de asesor) ---
    datos_externos_formateados = "" # Variable para almacenar los datos de SEIA o BCN

    if sector.lower() == "ambiental":
        print(f"Modo Ambiental activado. Buscando en SEIA para: {empresa}")
        # Buscar proyectos y raspar documentos/RCAs del SEIA
        proyectos_seia = buscar_empresa(empresa) # Llama al scraper de SEIA

        # Formatear los datos obtenidos del SEIA para el prompt
        if proyectos_seia:
            datos_externos_formateados += "Información relevante extraída del SEIA:\n\n"
            for i, proyecto in enumerate(proyectos_seia):
                datos_externos_formateados += f"--- Proyecto SEIA {i+1}: {proyecto.get('nombre_proyecto', 'N/A')} (Código: {proyecto.get('codigo', 'N/A')}) ---\n"
                datos_externos_formateados += f"Enlace Expediente: {proyecto.get('link_expediente', 'No disponible')}\n"
                # Añadir mas datos del proyecto si son utiles
                documentos_rcas = proyecto.get('documentos_rcas', [])
                if documentos_rcas:
                    datos_externos_formateados += "Documentos/RCAs encontrados para este proyecto:\n"
                    for j, doc in enumerate(documentos_rcas):
                        datos_externos_formateados += f"  - Tipo: {doc.get('documento_tipo', 'Sin tipo')}, Folio: {doc.get('folio', 'N/A')}, Fecha: {doc.get('fecha', 'N/A')}\n"
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
        # Buscar normativa en BCN usando la consulta del usuario (el campo analisis)
        normativas_bcn = buscar_normativa_bcn(analisis) # <-- ¡Llama al scraper de BCN!

        # Formatear los resultados de la BCN para el prompt
        if normativas_bcn:
            datos_externos_formateados += "Normativa encontrada en BCN (potencialmente relevante):\n\n"
            for i, norma in enumerate(normativas_bcn):
                datos_externos_formateados += f"--- Norma BCN {i+1} ---\n"
                datos_externos_formateados += f"Nombre/Título: {norma.get('nombre', 'N/A')}\n"
                datos_externos_formateados += f"Tipo: {norma.get('tipo', 'N/A')}\n" # Requiere extraccion real en scraper BCN
                datos_externos_formateados += f"Número: {norma.get('numero', 'N/A')}\n" # Requiere extraccion real en scraper BCN
                datos_externos_formateados += f"Fecha: {norma.get('fecha', 'N/A')}\n" # Requiere extraccion real en scraper BCN
                datos_externos_formateados += f"Enlace: {norma.get('link', 'No disponible')}\n"
                datos_externos_formateados += "\n"
            datos_externos_formateados += "---\n\n"
        else:
            datos_externos_formateados = "No se encontró normativa relevante en BCN para la consulta.\n\n"


    # Puedes añadir logica para otros modos aqui (administrativo, etc.)
    # elif sector.lower() == "administrativo":
    #    datos_externos_formateados = f"Modo Administrativo activado. Lógica a implementar.\n\n"


    else:
        # Modo desconocido o no seleccionado
        datos_externos_formateados = "Tipo de asesor no especificado o desconocido. No se realizó búsqueda externa automatizada.\n\n"
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
                    # Intenta decodificar con utf-8, si falla, intenta latin-1
                    contenido = contenido_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        contenido = contenido_bytes.decode('latin-1')
                    except Exception:
                        contenido = f"Error al decodificar el archivo {doc.filename}." # Mensaje de error si falla
                except Exception:
                     contenido = f"Error al leer el archivo {doc.filename}." # Otros errores al leer
                contenidos.append(contenido)

    texto_docs = "\n\n".join(contenidos) if contenidos else "Sin documentos adjuntos."


    # --- Construir el prompt MEJORADO para GPT (Ajustado para modos y datos externos) ---
    # El prompt del sistema y del usuario se ajustan automaticamente con la informacion formateada.

    client = openai.OpenAI()

    # Ajustar el prompt del sistema segun el tipo de asesor para guiar la respuesta
    system_prompt_content = f"""Eres un asesor experto en normativa, regulaciones y análisis en Chile.
Tu rol y enfoque principal es: **{sector.capitalize()}**.

Tu objetivo es proporcionar un análisis detallado, estructurado, profesional y preciso sobre la consulta del usuario, basándote en TODA la información proporcionada (consulta, empresa, datos externos -SEIA o BCN-, documentos adjuntos) y tu conocimiento general como experto {sector.lower()}.

Directrices generales para la respuesta:
1.  **Estructura:** Divide la respuesta en secciones claras usando encabezados (ej: Análisis, Normativa/Datos Relevantes, Evaluación de Riesgos, Recomendaciones).
2.  **Contenido:** Profundiza en los aspectos relevantes segun el tipo de asesor (ambiental, legal, administrativo).
3.  **Uso de Fuentes:** **Es CRUCIAL que uses la información proporcionada en 'Datos Externos Obtenidos' y 'Documentos Adjuntos'.** No inventes datos que no esten ahi. Si la informacion clave está en esas secciones, REFHIÉRETE a ella en tu analisis.
4.  **Citación:** Siempre que sea posible y relevante, cita las fuentes **proporcionadas** (ej: "Según la RCA X encontrada en SEIA...", "El documento adjunto indica...", "La norma Y de BCN establece..."). Si la información relevante no fue proporcionada por el scraper o los documentos, indica que tu respuesta se basa en conocimiento general.
5.  **Riesgos y Recomendaciones:** Identifica riesgos y formula recomendaciones concretas, BASADAS EN LA INFORMACION PROPORCIONADA Y TU ANALISIS.
6.  **Formato:** Usa viñetas dentro de las secciones.
7.  **Idioma:** Responde siempre en español de Chile.
"""

    # El prompt del usuario solo contiene la informacion de entrada para que el modelo la procese
    prompt_user_content = f"""
Información para el análisis:

Empresa: {empresa}
Tipo de asesor solicitado: {sector}

Consulta específica:
{analisis}

--- Datos Externos Obtenidos ({sector}) ---
{datos_externos_formateados} # <-- Datos formateados de SEIA o BCN
---------------------------------------

--- Contenido de Documentos Adjuntos ---
{texto_docs}
------------------------------------

Por favor, realiza el análisis solicitado siguiendo tus directrices como asesor {sector.lower()}.
"""

    try:
        response = client.chat.completions.create(
             model="gpt-3.5-turbo", # Puedes cambiar a "gpt-4" si lo necesitas y tienes acceso
             messages=[
                 {"role": "system", "content": system_prompt_content},
                 {"role": "user", "content": prompt_user_content}
             ],
             temperature=0.7
         )

        respuesta_texto = response.choices[0].message.content

        return respuesta_texto


    except openai.APIError as e:
        print(f"Error de la API de OpenAI: {e}")
        # Devolver un mensaje de error mas amigable si falla la API de OpenAI
        return f"Error al comunicarse con la inteligencia artificial (API OpenAI): {e}"
    except requests.exceptions.RequestException as e:
         print(f"Error de solicitud HTTP al scraper: {e}")
         # Devolver un mensaje de error si falla la solicitud del scraper
         return f"Error al buscar información externa (SEIA/BCN): {e}"
    except Exception as e:
        print(f"Error general al generar análisis: {e}")
        return f"Error inesperado al procesar la solicitud: {str(e)}"
