from fastapi import FastAPI, Form, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, Response
from typing import List # Asegúrate de importar List
import openai
import os # Importar os para acceder a variables de entorno

# Aunque importaste generate_analisis y buscar_empresa de app.analisis_legal y app.seia_scraper
# parece que la lógica de OpenAI y SEIA está directamente en main.py en la version mostrada.
# Si decides mover la logica a los otros archivos, ajusta main.py para llamarlas.
# from app.analisis_legal import generate_analisis # Descomentar si la logica de analisis vuelve aqui
from app.seia_scraper import buscar_empresa # Esta importacion parece correcta

app = FastAPI()

# Configurar carpetas estaticas y plantillas HTML
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static") # Asumiendo que tus plantillas estan en una carpeta 'static'

# Configurar la clave de la API de OpenAI
# Para openai>=1.0.0, la variable OPENAI_API_KEY debe estar en el entorno, y la librería la detecta
# automaticamente al instanciar OpenAI() o al hacer la llamada si la variable esta seteada globalmente.
# No necesitas setear openai.api_key = os.getenv("OPENAI_API_KEY") para versiones >= 1.0.0


# Ruta raiz que carga la interfaz visual
@app.get("/", response_class=HTMLResponse)
async def render_form(request: Request):
    # Asegúrate de que index.html este en la carpeta 'static'
    return templates.TemplateResponse("index.html", {"request": request})


# Ruta para recibir y procesar formulario
# Nota: La URL en el fetch de index.html DEBE ser exactamente "/analizar-formulario/"
@app.post("/analizar-formulario/")
async def analizar_formulario(
    analisis: str = Form(...),
    empresa: str = Form(...),
    sector: str = Form(...),
    documentos: List[UploadFile] = File(default=None) # Usar List[UploadFile] para multiples archivos
):
    # Buscar proyectos reales en el SEIA
    # Asegúrate que buscar_empresa este definida o importada y funcione correctamente
    datos_seia = buscar_empresa(empresa)

    # Procesar documentos subidos
    contenidos = []
    if documentos:
        for doc in documentos:
            # Manejar si no se suben archivos o si hay error al leer
            # doc.filename == '' ocurre si el campo file esta en el form pero no se selecciona archivo
            if doc.filename == '':
                 continue

            try:
                # Leer el contenido del archivo de forma asíncrona
                contenido_bytes = await doc.read()
                # Intenta decodificar, manejando posibles errores de codificación
                try:
                    contenido = contenido_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                         # Intentar otra codificacion si utf-8 falla
                         contenido = contenido_bytes.decode('latin-1')
                    except Exception:
                         contenido = f"Error al decodificar el archivo {doc.filename}." # Mensaje si falla la decodificacion

                contenidos.append(contenido)
            except Exception as e:
                 # Si hay un error al leer el archivo (ej. no es un archivo valido)
                contenidos.append(f"No se pudo leer el archivo {doc.filename}: {e}")


    texto_docs = "\n\n".join(contenidos) if contenidos else "Sin documentos adjuntos."

    # --- Construir el prompt MEJORADO para GPT ---

    # Instanciar el cliente de OpenAI (recomendado para versiones >= 1.0.0)
    # La librería leerá OPENAI_API_KEY del entorno automáticamente
    client = openai.OpenAI()

    try:
        response = client.chat.completions.create( # Usar la nueva sintaxis con el cliente
             model="gpt-3.5-turbo", # Puedes cambiar a "gpt-4" si lo necesitas y tienes acceso
             messages=[
                 # Prompt del sistema: Define el rol, tono y expectativas generales de FORMATO y CONTENIDO
                 {"role": "system", "content": """Eres un asesor experto en normativa ambiental, legal, técnica y de riesgo en Chile.
Tu objetivo es proporcionar un análisis **detallado, estructurado, profesional y preciso** sobre la consulta del usuario, basándote en toda la información proporcionada.

Directrices para la respuesta:
1.  **Estructura:** Divide la respuesta en secciones claras usando encabezados (ej: 1. Normativa Aplicable, 2. Análisis Técnico/Situacional, 3. Evaluación de Riesgos, 4. Recomendaciones).
2.  **Contenido Técnico/Legal:** Profundiza en los aspectos técnicos y legales relevantes.
3.  **Citación:** Siempre que sea posible y relevante, **cita explícitamente la normativa ambiental y legal chilena aplicable** (ej: Ley N° 19.300, D.S. N° 40/2012 RCA, D.S. N° 90/2000 Norma de Emisión, Código de Aguas, etc.). No inventes citas; indica las normativas generales o principios si no puedes citar un artículo específico relevante de tu conocimiento.
4.  **Riesgos:** Identifica y describe claramente los **riesgos** técnicos, legales y operacionales asociados a la consulta o la situación de la empresa.
5.  **Recomendaciones:** Formula **recomendaciones concretas, prácticas y aplicables** que la empresa pueda seguir.
6.  **Formato:** Usa **viñetas** dentro de las secciones para listar puntos clave (normas, riesgos, recomendaciones específicas). Asegúrate de que el texto sea legible y bien organizado.
7.  **Idioma:** Responde siempre en español de Chile.
"""},
                 # Prompt del usuario: Contiene la información específica de la consulta y los datos de entrada
                 {"role": "user", "content": f"""
Por favor, realiza el análisis técnico y legal solicitado basándote en la siguiente información:

Información de la Empresa:
Nombre: {empresa}
Tipo de asesor solicitado: {sector}

Consulta específica a analizar:
{analisis}

Información relevante extraída del SEIA:
{datos_seia.get('proyectos', 'No se encontraron proyectos en SEIA relevantes para esta empresa en el SEIA.')}

Contenido de los Documentos Adjuntos (si fueron proporcionados):
{texto_docs}

Genera el análisis siguiendo estrictamente las directrices de estructura, contenido técnico/legal, citación, riesgos y recomendaciones detalladas en tus instrucciones de sistema. Asegúrate de que sea un análisis profundo y aplicable al contexto chileno.
"""}
             ],
             temperature=0.7 # Un poco mas alto que 0.6 para fomentar creatividad, pero no demasiado
         )

        # Asumiendo que la respuesta es texto en el primer choice
        respuesta_texto = response.choices[0].message.content

        # Puedes añadir aquí un paso para post-procesar el texto si el formato no es perfecto
        # Por ejemplo, si quieres convertir Markdown simple a HTML (requiere una lib como markdown)
        # import markdown
        # respuesta_html = markdown.markdown(respuesta_texto)
        # return HTMLResponse(content=respuesta_html)

        # Si simplemente quieres el texto con saltos de linea basicos (usando pre-wrap en el frontend)
        return respuesta_texto


    except openai.APIError as e:
        # Manejar errores específicos de la API de OpenAI
        print(f"Error de la API de OpenAI: {e}")
        return f"Error de la API de OpenAI: {e}"
    except Exception as e:
        # Capturar cualquier otro error y devolverlo como texto
        print(f"Error general al generar análisis: {e}") # Imprimir el error en los logs de Render
        return f"Error al generar análisis: {str(e)}"

