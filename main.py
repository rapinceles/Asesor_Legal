from fastapi import FastAPI, Query
from app.seia_scraper import buscar_empresa
from app.analisis_legal import generar_analisis

app = FastAPI()

@app.get("/")
def home():
    return {"mensaje": "Agente SaaS Ambiental Inteligente activo."}

@app.get("/analizar/")
def analizar(nombre_empresa: str = Query(..., description="Nombre de la empresa")):
    datos = buscar_empresa(nombre_empresa)
    resultado = generar_analisis(nombre_empresa, datos)
    return {"empresa": nombre_empresa, "analisis": resultado}