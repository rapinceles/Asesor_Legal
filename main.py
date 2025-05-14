from fastapi import FastAPI, Form, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, Response # Importar Response
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
# Es crucial que la variable de entorno OPENAI_API_KEY este configurada en Render
# openai.api_key = os.getenv("OPENAI_API_KEY") # Esta forma de configurar es para openai<1.0.0
# Para openai>=1.0.0, la variable OPENAI_API_KEY debe estar en el entorno, y la librería la detecta
# automaticamente o puedes pasarla al instanciar OpenAI()


# Ruta raiz que carga la interfaz visual
@app.get("/", response_class=HTMLResponse)
async def render_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request}) # Asegúrate de que index.html este en 'static'


# Ruta para recibir y procesar formulario
@app.post("/analizar-formulario/")
async def analizar_formulario(
    analisis: str = Form(...),
    empresa: str = Form(...),
    sector: str = Form(...), # Usaste sector en el prompt, asi que lo mantengo aqui
    documentos: List[UploadFile] = File(default=None) # Usar List[UploadFile] para multiples archivos
):
    # Buscar proyectos reales en el SEIA
    datos_seia = buscar_empresa(empresa) # Asegúrate que buscar_empresa este definida o importada

    # Procesar documentos subidos
    contenidos = []
    if documentos:
        for doc in documentos:
            # Manejar si no se suben archivos o si hay error al leer
            if doc.filename == '':
                 continue # Saltar si el campo de archivo está vacío pero se envió el formulario

            try:
                # Leer el contenido del archivo. Asumimos texto, ajusta si son PDFs, etc.
                # Render y Uvicorn manejan async, usa await doc.read()
                contenido_bytes = await doc.read()
                # Intenta decodificar, manejando posibles errores de codificación
                try:
                    contenido = contenido_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                         # Intentar otra codificacion si utf-8 falla
                         contenido = contenido_bytes.decode('latin-1')
                    except Exception:
                         contenido = "Error al decodificar el archivo." # Mensaje si falla la decodificacion

                contenidos.append(contenido)
            except Exception as e:
                 # Si hay un error al leer el archivo (ej. no es un archivo valido)
                contenidos.append(f"No se pudo leer el archivo {doc.filename}: {e}")


    texto_docs = "\n\n".join(contenidos) if contenidos else "Sin documentos adjuntos."

    # Construir prompt para GPT
    prompt = f"""
    Prompt de análisis legal ambiental:

    Empresa: {empresa}
    Tipo de asesor: {sector}
    Consulta: {analisis}

    Proyectos en SEIA:
    {datos_seia.get('proyectos', 'No se encontraron proyectos en SEIA.')} # Usar .get por si la clave no existe

    Contenido adicional (Documentos Adjuntos):
    {texto_docs}

    Entrega un análisis técnico y legal aplicable, citando normativas ambientales, recomendaciones y
    evaluación de riesgos, basándote en la información proporcionada, los proyectos encontrados en SEIA y los documentos adjuntos.
    """ # Asegúrate de cerrar las triples comillas del f-string aquí

    try:
        # --- Inicio de la corrección en la llamada a OpenAI ---
        # Si usas openai>=1.0.0, la API key se debe configurar en el entorno
        # La librería la detecta automáticamente o puedes instanciar el cliente:
        # client = openai.OpenAI() # Opcional: Instanciar el cliente
        # response = client.chat.completions.create( # Usar la nueva sintaxis con el cliente

        # O, si la API key esta en el entorno, puedes usar la llamada directa asi:
        response = openai.chat.completions.create( # <-- ¡Llamada corregida!
             model="gpt-3.5-turbo", # o "gpt-4" si lo tienes disponible
             messages=[
                 {"role": "system", "content": "Eres un asesor experto en normativa ambiental, legal, técnica y de riesgo en Chile. Tu objetivo es proporcionar un análisis detallado, citando fuentes legales relevantes cuando sea posible, y ofreciendo recomendaciones prácticas y evaluación de riesgos."}, # Prompt de sistema mejorado
                 {"role": "user", "content": prompt} # Usamos el prompt construido arriba
             ],
             temperature=0.6
         )
        # --- Fin de la corrección ---

        # Asumiendo que la respuesta es texto
        # return response.choices[0].message.content # Esto devuelve solo el texto
        # Podrias querer devolverlo como HTMLResponse para mostrarlo en la interfaz
        # return HTMLResponse(content=response.choices[0].message.content)
        # O simplemente devolver el texto y que el frontend lo maneje
        return response.choices[0].message.content


    except Exception as e:
        # Capturar y devolver el error como texto
        # Ahora este mensaje de error deberia ser diferente si la correccion funciona
        print(f"Error detallado en la llamada a OpenAI: {e}") # Opcional: imprimir el error en los logs de Render para debug
        return f"Error al generar análisis: {str(e)}"

