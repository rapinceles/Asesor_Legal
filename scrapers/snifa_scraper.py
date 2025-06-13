# scrapers/snifa_scraper.py
import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from models.snifa_models import SancionSNIFA

SNIFA_SEARCH_URL = "https://snifa.sma.gob.cl/Busqueda/Busqueda"

def sincronizar_sanciones_por_empresa(db: Session, nombre_empresa: str):
    # Como este scraper aún no está desarrollado, simplemente imprimimos un mensaje
    # y salimos para que no detenga el programa.
    print(f"Buscando sanciones para '{nombre_empresa}' en SNIFA... (Función pendiente)")
    # Cuando lo desarrolles, aquí irá la lógica de requests, BeautifulSoup, etc.
    return
