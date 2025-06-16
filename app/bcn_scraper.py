# app/bcn_scraper.py
import requests
from bs4 import BeautifulSoup
import time

# URL base del sitio de la BCN (para construir enlaces completos)
BASE_BCN_URL = "https://www.bcn.cl" # O https://www.leychile.cl

# --- **IDENTIFICA LA URL DE BUSQUEDA** ---
# Ve a la pagina de la BCN, busca normativa, y copia la URL de la barra de direcciones
# después de buscar. Pégala abajo. Ejemplo: https://www.bcn.cl/portal/resultado-busqueda
BUSQUEDA_NORMATIVA_URL = "PON_AQUI_LA_URL_DE_BUSQUEDA_DE_NORMATIVA_DE_LA_BCN" # <-- ¡AJUSTA ESTO!

def buscar_normativa_bcn(consulta: str) -> list:
    """
    Busca normativa legal en el sitio de la BCN (Ley Chile) basada en una consulta.
    Usa los selectores identificados en la pagina de resultados.
    """
    normativas_encontradas = []
    search_url = BUSQUEDA_NORMATIVA_URL

    # --- **IDENTIFICA EL FORMULARIO DE BUSQUEDA** ---
    # Ve a la pagina donde buscas normativa.
    # Haz clic derecho en el campo donde escribes la consulta, "Inspeccionar".
    # Busca el atributo 'name' de ese campo (ej: name="texto", name="q"). PONLO ABAJO.
    # En la URL que me mostraste, parece que el campo se llama 'texto'.
    payload = {
        "texto": consulta, # <-- ¡Este parece ser el nombre del campo de consulta! CONFIRMA EN LA INSPECCION
        # **AÑADE AQUI OTROS CAMPOS DEL FORMULARIO SI SON NECESARIOS**
        # Revisa el formulario completo si buscas opciones de filtrado (ley, decreto, vigente, etc.)
    }

    headers = {
        "User-Agent": "Mozilla/5.0" # Simula un navegador
    }

    print(f"Intentando buscar normativa en BCN para: {consulta}")

    try:
        # --- **IDENTIFICA EL METODO DE ENVIO DEL FORMULARIO (GET o POST)** ---
        # En la pagina donde buscas, inspecciona el tag <form>. Mira el atributo 'method'.
        # La URL que me mostraste incluye los terminos en la URL (?texto=...), lo que sugiere un metodo GET.
        # Descomenta la linea correcta.
        response = requests.get(search_url, params=payload, headers=headers, timeout=15) # <-- ¡Si el formulario usa GET, usa esta linea!
        # response = requests.post(search_url, data=payload, headers=headers, timeout=15) # Si el formulario usa POST

        response.raise_for_status() # Lanza error si la solicitud falla

        soup = BeautifulSoup(response.content, 'html.parser')

        # --- **AHORA USAMOS LOS SELECTORES QUE IDENTIFICASTE** ---
        # Buscamos todos los bloques que corresponden a un resultado individual (<div class="result-item">)
        # **AJUSTA ESTE SELECTOR si la clase 'result-item' no es correcta o si los resultados no son divs**
        resultado_items = soup.find_all('div', class_='result-item')

        print(f"Bloques de resultados encontrados (div.result-item): {len(resultado_items)}")

        # --- **EXTRAER INFORMACION DE CADA RESULTADO** ---
        # Iteramos sobre cada bloque de resultado encontrado
        for i, item in enumerate(resultado_items):
            # Dentro de cada bloque 'result-item', buscamos el enlace (<a>) que lleva a la norma.
            # Vimos en la inspeccion que hay un <a> tag dentro de este bloque (probablemente en result-item__header).
            # **AJUSTA ESTE SELECTOR si el enlace no es un <a> o si está en otro lugar dentro del bloque 'result-item'**
            link_elemento = item.find('a', href=True)

            link = None
            nombre_norma = "Nombre no encontrado"
            full_link = "Enlace no disponible"

            if link_elemento:
                 link = link_elemento.get('href', '#') # Obtiene el valor del atributo href
                 nombre_norma = link_elemento.get_text(strip=True) # Obtiene el texto del enlace (que suele ser el nombre)

                 # Construir URL completa si es relativa
                 if link.startswith('/'):
                     full_link = BASE_BCN_URL + link
                 else:
                      full_link = link # Asumir completa o ajustar si es necesario

            # --- **EXTRAER OTROS DATOS (TIPO, NUMERO, FECHA) - ¡NECESITA AJUSTE!** ---
            # Vuelve a inspeccionar el HTML de un 'result-item'. ¿Donde están el tipo de norma (Ley, Decreto), el número y la fecha?
            # Pueden estar en otros divs o elementos dentro del 'result-item'.
            # **Añade lógica para encontrar y extraer esos datos.**
            # EJEMPLO HIPOTETICO: Si el numero esta en un <p class="numero"> y la fecha en <span class="fecha">
            # numero_elemento = item.find('p', class_='numero')
            # numero_norma = numero_elemento.get_text(strip=True) if numero_elemento else "N/A"
            # fecha_elemento = item.find('span', class_='fecha')
            # fecha_publicacion = fecha_elemento.get_text(strip=True) if fecha_elemento else "N/A"
            # tipo_norma = "???"; # Esto es mas dificil, a veces esta en el nombre o en otra clase

            # Por ahora, usaremos placeholders si no puedes extraerlos aun:
            tipo_norma = "Desconocido" # <-- ¡AJUSTA EXTRACCION REAL si puedes!
            numero_norma = "N/A"    # <-- ¡AJUSTA EXTRACCION REAL si puedes!
            fecha_publicacion = "N/A" # <-- ¡AJUSTA EXTRACCION REAL si puedes!


            # --- **FILTRAR RESULTADOS RELEVANTES (OPCIONAL pero recomendado)** ---
            # El selector 'result-item' podria traer cosas que no son normas.
            # Puedes añadir aqui una verificacion si el 'full_link' apunta a una pagina de norma real (ej: contiene "/leychile/filtrar?id=")
            es_norma_relevante = ("/leychile/filtrar?" in full_link) or ("/leychile/navegar?" in full_link) # <-- ¡Ajusta este filtro si es necesario!


            if es_norma_relevante and nombre_norma != "Nombre no encontrado": # Solo añadir si parece una norma y tiene nombre
                 normativas_encontradas.append({
                     "nombre": nombre_norma,
                     "tipo": tipo_norma,
                     "numero": numero_norma,
                     "fecha": fecha_publicacion,
                     "link": full_link,
                 })

        if not normativas_encontradas:
            print("No se encontraron resultados de normativa relevantes.")

    except requests.exceptions.RequestException as e:
        print(f"Error de solicitud HTTP en busqueda BCN para '{consulta}': {e}")
        return []
    except Exception as e:
        print(f"Error general en buscar_normativa_bcn: {e}")
        return []

    print(f"Busqueda en BCN completada. Normativas encontradas: {len(normativas_encontradas)}")
    return normativas_encontradas
