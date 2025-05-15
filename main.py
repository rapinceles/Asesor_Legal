# main.py - Código con sangría corregida en procesamiento de documentos
from fastapi import FastAPI, Form, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
import openai
import os

# Asegúrate de que estos imports existan si usas las funciones
# from app.analisis_legal import generate_analisis # Si no la usas directamente, no necesitas importar
from app.seia_scraper import buscar_empresa # Importa el scraper de SEIA
# from app.bcn_scraper import buscar_normativa_bcn # Descomenta si ya tienes este archivo y quieres usarlo


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
    empresa: str = Form(...), # Nombre de la empresa
    sector: str = Form(...), # Tipo de asesor
    documentos: List[UploadFile] = File(default=None)
):
    # --- Lógica para obtener datos externos (SEIA o BCN) ---
    # Esta parte llama a los scrapers si el modo lo requiere.
    # Si el scraper de BCN no esta listo, el modo 'legal' solo usara la consulta y documentos.
    datos_externos_formateados = ""

    if sector.lower() == "ambiental":
        print(f"Modo Ambiental activado. Buscando en SEIA para: {empresa}")
        # Buscar proyectos en SEIA (usando la version simple o avanzada del scraper)
        proyectos_seia = buscar_empresa(empresa) # Llama a buscar_empresa de seia_scraper.py

        # Formatear los datos obtenidos del SEIA para el prompt
        if proyectos_seia:
            datos_externos_formateados += "Información relevante extraída del SEIA:\n\n"
            # Formatear la lista de proyectos y sus documentos/RCAs (segun lo que retorne tu buscar_empresa)
            # Este formateo debe coincidir con la estructura de datos que devuelve tu seia_scraper.py
            # Si tu buscar_empresa solo retorna lista de nombres o diccionarios basicos, ajusta aqui.
            # EL SIGUIENTE ES UN EJEMPLO DE FORMATEO SI buscar_empresa retorna una lista de diccionarios de proyecto con 'documentos_rcas'
            if isinstance(proyectos_seia, list): # Verificar si es lista de proyectos
                 for i, proyecto in enumerate(proyectos_seia):
                     datos_externos_formateados += f"--- Proyecto SEIA {i+1}: {proyecto.get('nombre_proyecto', 'N/A')} (Código: {proyecto.get('codigo', 'N/A')}) ---\n"
                     datos_externos_formateados += f"Enlace Expediente: {proyecto.get('link_expediente', 'No disponible')}\n"
                     # Añadir mas datos del proyecto si son utiles
                     documentos_rcas = proyecto.get('documentos_rcas', []) # Asumiendo que hay una clave 'documentos_rcas'
                     if documentos_rcas:
                         datos_externos_formateados += "Documentos/RCAs encontrados para este proyecto:\n"
                         for j, doc in enumerate(documentos_rcas):
                             # Asumiendo estructura de diccionario de documentos {'documento_tipo': ..., 'folio': ..., 'fecha': ..., 'link_pdf': ...}
                             datos_externos_formateados += f"  - Tipo: {doc.get('documento_tipo', 'Sin tipo')}, Folio: {doc.get('folio', 'N/A')}, Fecha: {doc.get('fecha', 'N/A')}\n"
                             if doc.get('link_pdf', 'No disponible') != "No disponible":
                                 datos_externos_formateados += f"    Enlace PDF: {doc.get('link_pdf')}\n"
                         datos_externos_formateados += "\n"
                     else:
                         datos_externos_formateados += "No se encontraron documentos/RCAs específicos en SEIA para este proyecto.\n\n"
                 datos_externos_formateados += "---\n\n"
            else: # Si buscar_empresa retorna otra estructura (ej: diccionario con clave 'proyectos')
                 # Ajusta este formateo a la estructura real de tu funcion buscar_empresa
                 datos_externos_formateados += f"Resultados SEIA (formato inesperado o básico):\n {str(proyectos_seia)}\n\n---\n\n" # Formateo basico como texto

        else:
            datos_externos_formateados = "No se encontraron proyectos relevantes en el SEIA para la búsqueda.\n\n"

    elif sector.lower() == "legal": # --- Lógica para el modo "Legal" ---
        print(f"Modo Legal activado. Buscando normativa en BCN para: {analisis}")
        # Buscar normativa en BCN usando la consulta del usuario (si bcn_scraper.py esta listo)
        # **DESCOMENTA LAS LINEAS DE ABAJO SI bcn_scraper.py YA EXISTE Y ESTA AJUSTADO**
        # try:
        #    normativas_bcn = buscar_normativa_bcn(analisis) # Llama al scraper de BCN
        # except Exception as e:
        #    print(f"Error llamando a bcn_scraper: {e}")
        #    normativas_bcn = [] # Vaciar si hay error en el scraper

        # Formatear los resultados de la BCN para el prompt (si se encontraron)
        # if normativas_bcn:
        #     datos_externos_formateados += "Normativa encontrada en BCN (potencialmente relevante):\n\n"
        #     for i, norma in enumerate(normativas_bcn):
        #         # Asumiendo estructura de diccionario de normativa {'nombre': ..., 'link': ..., etc.}
        #         datos_externos_formateados += f"--- Norma BCN {i+1} ---\n"
        #         datos_externos_formateados += f"Nombre/Título: {norma.get('nombre', 'N/A')}\n"
        #         datos_externos_formateados += f"Tipo: {norma.get('tipo', 'N/A')}\n" # Requiere extraccion real en scraper BCN
        #         datos_externos_formateados += f"Número: {norma.get('numero', 'N/A')}\n" # Requiere extraccion real en scraper BCN
        #         datos_externos_formateados += f"Fecha: {norma.get('fecha', 'N/A')}\n" # Requiere extraccion real en scraper BCN
        #         datos_externos_formateados += f"Enlace: {norma.get('link', 'No disponible')}\n"
        #         datos_externos_formateados += "\n"
        #     datos_externos_formateados += "---\n\n"
        # else:
        #     # Si el scraper de BCN no se llamó o no encontró nada
        #     datos_externos_formateados = "No se encontró normativa relevante en BCN para la consulta (o el scraper no está activo/funcionando).\n\n"

        # **MIENTRAS EL SCRAPER DE BCN NO ESTÉ LISTO, USA ESTO EN MODO LEGAL:**
        datos_externos_formateados = "Modo Legal activado. La búsqueda automática en BCN no está implementada/activa. Por favor, proporciona información legal relevante en la consulta o documentos adjuntos.\n\n"


    elif sector.lower() == "administrativo": # --- Lógica para el modo "Administrativo" ---
         # Puedes añadir aqui logica especifica para el modo administrativo
         datos_externos_formateados = f"Modo Administrativo activado. Puedes implementar lógica de búsqueda o análisis específica aquí.\n\n"


    else:
        # Modo desconocido o no seleccionado
        datos_externos_formateados = "Tipo de asesor no especificado o desconocido. No se realizó búsqueda externa automatizada.\n\n"
        # No se realiza busqueda externa


    # Procesar documentos subidos (como antes) - CON LA SANGRIA CORREGIDA
    contenidos = []
    if documentos:
        for doc in documentos:
            if doc.filename == '':
                 continue
            try: # <-- INICIO DEL BLOQUE TRY para leer el archivo individual
                contenido_bytes = await doc.read()
                try:
                    # Intenta decodificar con utf-8, si falla, intenta latin-1
                    contenido = contenido_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                         contenido = contenido_bytes.decode('latin-1')
                    except Exception: # Este except está bien alineado con el try de arriba (decodificacion)
                         contenido = f"Error al decodificar el archivo {doc.filename}."
                # ESTE EXCEPT DEBE ESTAR ALINEADO CON EL PRIMER TRY DE LA LINEA 106 (O DONDE EMPIECE TU TRY)
            except Exception as e: # <-- ¡SANGRIA CORREGIDA AQUÍ! Debe estar al mismo nivel que el 'try' de lectura de archivo
                 contenido = f"Error al leer el archivo {doc.filename}: {e}" # La linea dentro del except tambien se ajusta

            contenidos.append(contenido) # ESTA LINEA DEBE ESTAR ALINEADA CON EL 'FOR' DE DOCUMENTOS

    texto_docs = "\n\n".join(contenidos) if contenidos else "Sin documentos adjuntos."


    # --- Construir el prompt MEJORADO para GPT ---
    # El prompt incluye la consulta, datos externos (si se obtuvieron/formatearon) y documentos.

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

    try: # <-- INICIO DEL BLOQUE TRY principal para la llamada a la IA
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

    except openai.APIError as e: # <-- Except para errores de la API de OpenAI
        print(f"Error de la API de OpenAI: {e}")
        # Devolver un mensaje de error mas amigable si falla la API de OpenAI
        return f"Error al comunicarse con la inteligencia artificial (API OpenAI): {e}"
    except requests.exceptions.RequestException as e: # <-- Except para errores de los scrapers (SEIA/BCN)
         print(f"Error de solicitud HTTP al scraper: {e}")
         # Devolver un mensaje de error si falla la solicitud del scraper
         return f"Error al buscar información externa (SEIA/BCN): {e}"
    except Exception as e: # <-- Except general para cualquier otro error
        print(f"Error general al generar análisis: {e}")
        return f"Error inesperado al procesar la solicitud: {str(e)}"
