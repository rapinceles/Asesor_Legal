# app/bcn_scraper.py
import requests
from bs4 import BeautifulSoup
import time
import re

# URL principal de la BCN o Ley Chile
BASE_BCN_URL = "https://www.bcn.cl" # O https://www.leychile.cl
# URL especifica para la busqueda de normativa.
# **NECESITAS ENCONTRAR ESTA URL EN EL SITIO DE LA BCN/LEY CHILE**
BUSQUEDA_NORMATIVA_URL = "https://www.bcn.cl/buscador" # ESTA ES UNA URL DE EJEMPLO, AJUSTA


def buscar_normativa_bcn(consulta: str) -> list:
    """
    Busca normativa legal en el sitio de la BCN (Ley Chile) basada en una consulta.
    Retorna una lista de diccionarios con metadata de la normativa encontrada.
    """
    normativas_encontradas = []
    search_url = BUSQUEDA_NORMATIVA_URL

    # **NECESITAS INSPECCIONAR EL FORMULARIO DE BUSQUEDA EN EL SITIO DE LA BCN**
    # Identifica el nombre del campo de texto para la busqueda y otros campos relevantes.
    payload = {
        "texto": consulta, # ESTE ES EL NOMBRE DE CAMPO DE TEXTO, AJUSTA SI ES DIFERENTE
        # **AÑADE AQUI OTROS CAMPOS DEL FORMULARIO DE BUSQUEDA SI SON NECESARIOS**
        # ej: "tipo_norma": "ley", "vigente": "si", etc.
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    print(f"Buscando normativa en BCN para la consulta: {consulta}")

    try:
        # **VERIFICA SI ES UNA SOLICITUD GET o POST**
        # La mayoria de los buscadores usan GET para busquedas simples en la URL o POST con formulario.
        # response = requests.get(search_url, params=payload, headers=headers, timeout=15) # Ejemplo GET
        response = requests.post(search_url, data=payload, headers=headers, timeout=15) # Ejemplo POST (AJUSTA METODO)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # --- **PARTE CRUCIAL: RASCAR LOS RESULTADOS DE LA BUSQUEDA DE NORMATIVA** ---
        # **NECESITAS INSPECCIONAR LA ESTRUCTURA HTML DE LA PAGINA DE RESULTADOS DE LA BCN**
        # Busca la lista o tabla que contiene los resultados de la normativa.
        # Identifica como se diferencia cada resultado y que elementos contienen la metadata (nombre, tipo, numero, enlace).

        # **EJEMPLOS HIPOTETICOS DE SELECTORES (AJUSTA ESTO):**
        # resultados_list = soup.find_all('div', class_='resultado-norma') # Si cada resultado es un div
        # resultados_table = soup.find('table', id='tablaResultados') # Si los resultados estan en una tabla
        # resultados_links = soup.select('h3.titulo-norma a') # Si el enlace esta en un h3 con clase

        # Por ahora, un placeholder simple: buscar todos los enlaces que parezcan resultados
        # ESTE SELECTOR PROBABLEMENTE NO ES SUFICIENTE, AJUSTA
        result_items = soup.find_all('a', href=True) # Busca todos los enlaces (MUY GENERAL)

        print(f"Elementos encontrados que podrian ser resultados: {len(result_items)}") # Log

        # Limitar a los primeros N resultados relevantes
        count = 0
        for item in result_items:
            # --- **IDENTIFICAR Y EXTRAER METADATA DE CADA RESULTADO (AJUSTA ESTO)** ---
            # Debes poner logica aqui para verificar si el 'item' es un resultado real
            # (ej: el enlace apunta a una ley, el texto es un titulo de norma)
            # y extraer su nombre, numero, fecha, tipo, y el enlace completo.

            link = item['href']
            # Construir URL completa si es relativa
            if link.startswith('/'):
                 full_link = BASE_BCN_URL + link
            else:
                 full_link = link # Asumir completa o ajustar

            # **EJEMPLO HIPOTETICO DE EXTRACCION (AJUSTA ESTO):**
            # Intentar extraer texto del enlace o un elemento cercano que sea el titulo/nombre
            nombre_norma = item.get_text(strip=True)

            # **Añade lógica para extraer tipo, numero, fecha, etc. si estan cerca en el HTML**
            tipo_norma = "Desconocido" # Placeholder
            numero_norma = "N/A"    # Placeholder
            fecha_publicacion = "N/A" # Placeholder

            # **AÑADE LOGICA PARA FILTRAR RESULTADOS RELEVANTES**
            # Por ejemplo, verificar si el enlace contiene "/leyes/ver_txt.html?id=" o "/decretos/"
            # if "/leyes/" in full_link or "/decretos/" in full_link:

            # Por ahora, añadimos un resultado simple si parece un enlace
            if len(nombre_norma) > 5 and full_link.startswith('http'): # Filtro muy basico
                 normativas_encontradas.append({
                     "nombre": nombre_norma,
                     "tipo": tipo_norma, # Ajusta extraccion real
                     "numero": numero_norma, # Ajusta extraccion real
                     "fecha": fecha_publicacion, # Ajusta extraccion real
                     "link": full_link,
                 })
                 count += 1
                 if count >= 10: # Limitar a los primeros 10 resultados (AJUSTA LIMITE)
                     break


        if not normativas_encontradas:
            print("No se encontraron resultados de normativa relevantes.")

    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la solicitud de busqueda BCN para '{consulta}': {e}")
        return []
    except Exception as e:
        print(f"Error general en buscar_normativa_bcn para '{consulta}': {e}")
        return []

    print(f"Busqueda en BCN completada. Normativas encontradas (potenciales): {len(normativas_encontradas)}")
    return normativas_encontradas
