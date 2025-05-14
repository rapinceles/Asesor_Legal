from fastapi import FastAPI, Form, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
import openai

from app.analisis_legal import generar_analisis
from app.seia_scraper import buscar_empresa

app = FastAPI()

# Configurar carpetas estáticas y plantilla HTML
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static")

# Ruta raíz que carga la interfaz visual
@app.get("/", response_class=HTMLResponse)
async def render_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Ruta para recibir y procesar formulario
@app.post("/analizar_formulario")
async def analizar_formulario(
    analisis: str = Form(...),
    empresa: str = Form(...),
    sector: str = Form(...),
    documentos: List[UploadFile] = File(default=None)
):
    # Buscar proyectos reales en el SEIA
    datos_seia = buscar_empresa(empresa)

    # Procesar documentos subidos
    contenidos = []
    if documentos:
        for doc in documentos:
            try:
                contenido = await doc.read()
                contenidos.append(contenido.decode("utf-8", errors="ignore"))
            except:
                contenidos.append("No se pudo leer el archivo.")

    texto_docs = "\n\n".join(contenidos) if contenidos else "Sin documentos adjuntos."

    # Construir prompt para GPT
    prompt = f"""
Empresa: {empresa}
Tipo de asesor: {sector}
Consulta: {analisis}

Proyectos en SEIA:
{datos_seia.get('proyectos', [])}

Contenido adicional:
{texto_docs}

Entrega un análisis técnico y legal aplicable, citando normativas ambientales, recomendaciones y detección de riesgos.
"""

    try:
        respuesta = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un asesor legal ambiental chileno con experiencia en ingeniería, derecho y evaluación ambiental."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6
        )
        return respuesta.choices[0].message["content"]
    except Exception as e:
        return f"Error al generar análisis: {str(e)}"
