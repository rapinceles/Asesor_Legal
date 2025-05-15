import requests
from bs4 import BeautifulSoup
import time # Importar time para posibles pausas entre solicitudes

# URL para la busqueda inicial de proyectos
BUSQUEDA_PROYECTO_URL = "https://seia.sea.gob.cl/busqueda/buscarProyectoAction.php"
# Base URL del SEIA, necesaria para construir URLs completas si los enlaces son relativos
BASE_SEIA_URL = "https://seia.sea.gob.cl"

# Función auxiliar para raspar los datos de las RCA desde la página de detalle de un proyecto
def _scrape_rcas_from_project_page(project_url: str) -> list:
    """
    Raspa la página de detalle de un proyecto del SEIA para extraer la información de las RCA.
    """
    rcas_encontradas = []
    full_project_url = project_url # Asumimos que la URL del proyecto ya es completa

    # Si el enlace del proyecto en la tabla de busqueda fuera relativo, construir la URL completa:
    # if project_url.startswith('/'):
    #     full_project_url = BASE_SEIA_URL + project_url
    # else:
    #     full_project_url = project_url # O manejar otros casos

    print(f"Scraping RCA de: {full_project_url}") # Log para ver a que URL estamos yendo

    try:
        # Realizar la solicitud GET a la página de detalle del proyecto
        # Aumentar timeout por si la pagina tarda en cargar
        response = requests.get(full_project_url, timeout=20)
        response.raise_for_status() # Lanzar excepcion para códigos de estado de error (4xx o 5xx)

        soup = BeautifulSoup(response.content, 'html.parser')

        # --- PARTE CRUCIAL: Localizar la tabla o sección de RCA ---
        # ESTO REQUIERE INSPECCIONAR EL HTML DE UNA PAGINA DE PROYECTO REAL
        # POSIBLES SELECTORES (NECESITA AJUSTE):
        # - Una tabla con un ID específico: rca_table = soup.find('table', id='tablaRcas')
        # - Una tabla con una clase específica: rca_table = soup.find('table', class_='tablaRCA')
        # - Una tabla que esté después de un encabezado específico (ej. <h2>Resoluciones</h2>)

        # Ejemplo hipotético: buscar una tabla con una clase 'tablaRCA'
        rca_table = soup.find('table', class_='tabla') # Usamos 'tabla' como en la busqueda, podria ser diferente
        # Si la tabla de RCA tiene una estructura diferente, ajusta el selector
        # rca_table = soup.select_one('selector_css_correcto_aqui')

        if rca_table:
            # Asumimos que las filas de RCA son <tr> dentro del <tbody> (excluyendo thead si existe)
            # Podria ser necesario ajustar el selector de filas si la estructura es diferente
            rca_rows = rca_table.find_all('tr')[1:] # Saltar la fila de encabezado si la hay

            print(f"Filas de RCA encontradas: {len(rca_rows)}") # Log

            for row in rca_rows:
                # Asumimos que las columnas de la RCA son <td>
                columns = row.find_all(['td', 'th']) # A veces thead tiene th, tbody tiene td

                if len(columns) >= 4: # Asegurarse de que hay suficientes columnas
                    try:
                        # --- EXTRACCION DE DATOS DE COLUMNAS (NECESITA AJUSTE) ---
                        # Asumimos un orden de columnas basico: N° RCA, Fecha, Tipo, Link
                        # Tienes que inspeccionar la pagina real para saber que columna es cual (indice 0, 1, 2, ...)
                        numero_rca = columns[0].get_text(strip=True)
                        fecha_rca = columns[1].get_text(strip=True)
                        tipo_rca = columns[2].get_text(strip=True)
                        # Intentar encontrar el enlace al documento si existe en alguna columna
                        link_elemento = columns[3].find('a', href=True) # Asumimos el link esta en la 4ta columna
                        link_rca = BASE_SEIA_URL + link_elemento['href'] if link_elemento else "No disponible"

                        rcas_encontradas.append({
                            "numero_rca": numero_rca,
                            "fecha": fecha_rca,
                            "tipo": tipo_rca,
                            "link_documento": link_rca
                        })
                    except IndexError as ie:
                         print(f"Error de indice al procesar fila RCA: {ie} - Fila: {row}")
                    except Exception as ex:
                         print(f"Error al extraer datos de fila RCA: {ex} - Fila: {row}")
        else:
            print("Tabla de RCA no encontrada en la página del proyecto con el selector asumido.") # Log

    except requests.exceptions.RequestException as e:
        print(f"Error al acceder a la página del proyecto {full_project_url}: {e}")
    except Exception as e:
        print(f"Error al parsear la página del proyecto {full_project_url}: {e}")

    return rcas_encontradas

# Función principal para buscar proyectos y sus RCAs
def buscar_empresa(nombre_empresa: str) -> dict:
    """
    Busca proyectos en el SEIA por nombre y, si encuentra, intenta raspar sus RCA.
    """
    proyectos_encontrados = []
    search_url = BUSQUEDA_PROYECTO_URL

    payload = {
        "NOMBRE_EMPRESA": nombre_empresa,
        "TIPO_PROYECTO": "", # Dejar vacio o usar valor del formulario si aplica
        "REGION": "",       # Dejar vacio
        "ESTADO": "",       # Dejar vacio
        "EVALUACION": "",   # Dejar vacio
        "RCA": "",          # Dejar vacio
        "CODIGO": "",       # Dejar vacio
        "submit": "Buscar"
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    print(f"Buscando proyectos para: {nombre_empresa}") # Log

    try:
        response = requests.post(search_url, data=payload, headers=headers, timeout=10)
        response.raise_for_status() # Lanzar excepcion para códigos de estado de error (4xx o 5xx)

        soup = BeautifulSoup(response.content, 'html.parser')

        # --- PARTE 1: Raspar la tabla de resultados de la búsqueda ---
        table = soup.find('table', class_='tabla') # Buscar la tabla principal de resultados

        if not table:
            print("Tabla de resultados de búsqueda no encontrada.") # Log
            return {"nombre_empresa": nombre_empresa, "proyectos": [], "error": "No se encontraron resultados o la tabla de busqueda cambió"}

        # Asumimos que las filas de resultados son <tr> dentro del <tbody> (excluyendo thead)
        # Asegúrate de que este selector capture correctamente las filas de resultados
        rows = table.find_all('tr')
        if len(rows) > 1: # Si hay mas de 1 fila (la primera suele ser el encabezado)
             result_rows = rows[1:] # Saltar la fila de encabezado
        else:
             print("Solo fila de encabezado o tabla vacía.") # Log
             return {"nombre_empresa": nombre_empresa, "proyectos": [], "error": "No se encontraron proyectos"}


        print(f"Proyectos encontrados en resultados de busqueda: {len(result_rows)}") # Log

        # Limitar a los primeros N resultados para evitar demasiadas solicitudes
        # Considera si necesitas procesar mas o tener una logica para seleccionar el proyecto correcto
        for i, row in enumerate(result_rows[:5]): # Procesar solo los primeros 5 proyectos encontrados
            # --- PARTE 2: Extraer datos basicos del proyecto Y EL ENLACE ---
            columns = row.find_all(['td', 'th']) # Columnas de la fila del resultado de busqueda

            if len(columns) >= 6: # Asegurarse de que hay suficientes columnas para los datos basicos + link
                try:
                    nombre_proyecto = columns[0].get_text(strip=True)
                    link_elemento_proyecto = columns[0].find('a', href=True) # Asumimos que el link esta en la primera columna

                    if link_elemento_proyecto:
                         project_detail_url = link_elemento_proyecto['href'] # Obtener el href
                         # Construir la URL completa si el link es relativo
                         if project_detail_url.startswith('/'):
                             project_detail_url = BASE_SEIA_URL + project_detail_url
                    else:
                         print(f"No se encontró enlace de detalle para el proyecto: {nombre_proyecto}") # Log
                         project_detail_url = None # No hay enlace para raspar RCA

                    proyecto_data = {
                        "nombre_proyecto": nombre_proyecto,
                        "link_detalle": project_detail_url, # Guardar el link
                        "region": columns[1].get_text(strip=True),
                        "tipo": columns[2].get_text(strip=True),
                        "fecha_ingreso": columns[3].get_text(strip=True),
                        "tipo_presentacion": columns[4].get_text(strip=True),
                        "codigo": columns[5].get_text(strip=True),
                        "rcas_asociadas": [] # Lista para guardar las RCAs que encontraremos
                    }

                    # --- PARTE 3: Si hay enlace de detalle, raspar las RCA ---
                    if project_detail_url:
                        # Pausa pequeña para no sobrecargar el servidor del SEIA
                        time.sleep(1)
                        rcas = _scrape_rcas_from_project_page(project_detail_url)
                        proyecto_data["rcas_asociadas"] = rcas

                    proyectos_encontrados.append(proyecto_data)

                except IndexError as ie:
                    print(f"Error de indice al procesar fila de resultado de busqueda {i}: {ie} - Fila: {row}")
                except Exception as ex:
                    print(f"Error al extraer datos basicos o enlace de fila {i}: {ex} - Fila: {row}")
            else:
                 print(f"Fila de resultado de busqueda {i} no tiene suficientes columnas.") # Log


    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la solicitud de busqueda SEIA para {nombre_empresa}: {e}")
        return {"nombre_empresa": nombre_empresa, "proyectos": [], "error": f"Error de conexión o solicitud: {e}"}
    except Exception as e:
        print(f"Error general en buscar_empresa para {nombre_empresa}: {e}")
        return {"nombre_empresa": nombre_empresa, "proyectos": [], "error": f"Error inesperado: {e}"}

    # Retornar la lista de proyectos encontrados, incluyendo sus RCAs si se pudieron raspar
    # Solo retornamos la lista de proyectos, puedes ajustar si necesitas la empresa_nombre tambien
    # return {"nombre_empresa": nombre_empresa, "proyectos": proyectos_encontrados}
    # Retornamos la lista de proyectos directamente, que es lo que se usara en main.py
    # Asegúrate de ajustar como usas esto en main.py si la estructura de retorno anterior era necesaria
    # En main.py, datos_seia ahora será la lista de proyectos
    return proyectos_encontrados # Retorna la lista de diccionarios de proyectos, cada uno con su lista 'rcas_asociadas'
