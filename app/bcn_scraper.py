# app/bcn_scraper.py
import requests
from bs4 import BeautifulSoup
import time

# URL base del sitio de la BCN o Ley Chile
BASE_BCN_URL = "https://www.bcn.cl" # O revisa si es https://www.leychile.cl

# **NECESITAS ENCONTRAR ESTA URL**
# Esta es la dirección web donde haces la busqueda de normativa.
# Ve a la pagina de la BCN, busca normativa, y mira la barra de direcciones
# después de buscar. Copia esa URL base de busqueda.
BUSQUEDA_NORMATIVA_URL = "PON_AQUI_LA_URL_DE_BUSQUEDA_DE_NORMATIVA_DE_LA_BCN" # <-- ¡AJUSTA ESTO!


def buscar_normativa_bcn(consulta: str) -> list:
    """
    Intenta buscar normativa legal en el sitio de la BCN (Ley Chile).
    Necesita que BUSQUEDA_NORMATIVA_URL y el payload esten correctos.
    """
    normativas_encontradas = []
    search_url = BUSQUEDA_NORMATIVA_URL

    # --- **IDENTIFICA EL FORMULARIO DE BUSQUEDA** ---
    # Ve a la pagina donde buscas normativa en la BCN.
    # Haz clic derecho en el campo donde escribes la consulta, selecciona "Inspeccionar".
    # Busca el atributo 'name' de ese campo (ej: name="texto", name="q"). PONLO ABAJO.
    # Si hay otros campos ocultos o necesarios en el formulario, identificalos e incluyelos.
    payload = {
        "NOMBRE_DEL_CAMPO_DE_CONSULTA": consulta, # <-- ¡AJUSTA "NOMBRE_DEL_CAMPO_DE_CONSULTA"!
        # **AÑADE AQUI OTROS CAMPOS DEL FORMULARIO SI SON NECESARIOS**
        # ej: "campo_fecha_desde": "", "campo_tipo_norma": "ley", etc.
    }

    headers = {
        "User-Agent": "Mozilla/5.0" # Simula un navegador
    }

    print(f"Intentando buscar normativa en BCN para: {consulta}")

    try:
        # --- **IDENTIFICA EL METODO DE ENVIO DEL FORMULARIO** ---
        # En la misma herramienta de inspeccion (pestaña Network o mirando el tag <form>),
        # mira si el formulario se envia por GET o POST.
        # Descomenta la linea correcta y comenta la otra.
        # response = requests.get(search_url, params=payload, headers=headers, timeout=15) # Si es GET
        response = requests.post(search_url, data=payload, headers=headers, timeout=15) # Si es POST <-- ¡AJUSTA AQUI (GET o POST)!

        response.raise_for_status() # Lanza error si la solicitud falla

        soup = BeautifulSoup(response.content, 'html.parser')

        # --- **PUNTO CLAVE: RASCAR LOS RESULTADOS DE LA BUSQUEDA** ---
        # **AHORA NECESITAS MIRAR LA PAGINA DE RESULTADOS DE BUSQUEDA EN TU NAVEGADOR**
        # Busca donde aparece la lista de normas encontradas.
        # ¿Es una tabla? ¿Son divs? ¿Tienen alguna clase CSS o ID especial?

        # **EJEMPLOS HIPOTETICOS DE COMO ENCONTRAR LOS RESULTADOS (AJUSTA ESTO COMPLETAMENTE):**
        # Si cada resultado esta en un div con clase "resultado-busqueda":
        # resultado_items = soup.find_all('div', class_='resultado-busqueda')

        # Si los resultados estan en una tabla con id "tabla-resultados":
        # tabla_resultados = soup.find('table', id='tabla-resultados')
        # resultado_items = tabla_resultados.find_all('tr')[1:] if tabla_resultados else [] # Saltar encabezado

        # Si son enlaces directos dentro de alguna seccion:
        # resultado_items = soup.select('#id_de_la_lista a')


        # **POR AHORA, USARE UN SELECTOR MUY GENERICO COMO MARCADOR. ESTO SEGURO FALLARÁ HASTA QUE LO AJUSTES.**
        # NECESITAS REEMPLAZAR COMPLETAMENTE LAS LINEAS ABAJO POR LA LOGICA CORRECTA PARA ENCONTRAR CADA RESULTADO
        resultado_items = soup.find_all('a', href=True) # <-- ¡AJUSTA ESTO TOTALMENTE!


        print(f"Elementos potenciales encontrados en resultados de BCN: {len(resultado_items)}")

        # --- **EXTRAER INFORMACION DE CADA RESULTADO** ---
        # Ahora itera sobre los resultados encontrados (resultado_items) y extrae los datos de cada norma.
        # ¿Como obtienes el nombre, numero, fecha, tipo y el ENLACE completo de cada norma en el HTML?

        # **EJEMPLO HIPOTETICO DE EXTRACCION (AJUSTA ESTO COMPLETAMENTE):**
        count = 0
        for item in resultado_items: # Itera sobre los resultados que encontraste arriba
            # **PON AQUI LA LOGICA PARA EXTRAER LOS DATOS DE ESTE 'item'**
            # Por ejemplo, si 'item' es un enlace <a>, obtienes el link con item['href']
            # y el texto con item.get_text()

            link = item.get('href', '#') # Obtiene el enlace
            if link.startswith('/'):
                 full_link = BASE_BCN_URL + link # Construye URL completa si es relativa

            nombre_norma = item.get_text(strip=True) # Obtiene el texto del enlace/item

            # **NECESITAS LOGICA COMPLEJA AQUI para obtener tipo, numero, fecha, etc.**
            # Pueden estar en elementos HTML cercanos al enlace, o parseando el texto del nombre.
            tipo_norma = "???" # <-- ¡AJUSTA EXTRACCION REAL!
            numero_norma = "???" # <-- ¡AJUSTA EXTRACCION REAL!
            fecha_publicacion = "???" # <-- ¡AJUSTA EXTRACCION REAL!

            # **AÑADE LOGICA PARA FILTRAR SOLO RESULTADOS DE NORMATIVA REALES**
            # El selector inicial puede traer otros enlaces. Verifica el link o el texto.
            es_norma_relevante = True # <-- ¡AÑADE LOGICA DE FILTRO!


            if es_norma_relevante and len(nombre_norma) > 5: # Filtro basico, mejora esto
                 normativas_encontradas.append({
                     "nombre": nombre_norma,
                     "tipo": tipo_norma,
                     "numero": numero_norma,
                     "fecha": fecha_publicacion,
                     "link": full_link,
                 })
                 count += 1
                 if count >= 15: # Limitar a los primeros 15 resultados encontrados (AJUSTA LIMITE)
                     break


        if not normativas_encontradas:
            print("No se encontraron resultados de normativa relevantes.")

    except requests.exceptions.RequestException as e:
        print(f"Error de solicitud en busqueda BCN para '{consulta}': {e}")
        return []
    except Exception as e:
        print(f"Error general en buscar_normativa_bcn para '{consulta}': {e}")
        return []

    print(f"Busqueda en BCN completada. Normativas encontradas (potenciales): {len(normativas_encontradas)}")
    return normativas_encontradas
