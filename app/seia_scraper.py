# app/seia_scraper.py
import requests
from bs4 import BeautifulSoup
import time
import re # Importar re para usar expresiones regulares si es necesario

BUSQUEDA_PROYECTO_URL = "https://seia.sea.gob.cl/busqueda/buscarProyectoAction.php"
BASE_SEIA_URL = "https://seia.sea.gob.cl"


# --- FUNCIÓN AUXILIAR para raspar la tabla de documentos del expediente ---
# ESTA FUNCIÓN REQUIERE AJUSTES FINOS DE SELECTORES BASADOS EN EL HTML REAL
def _scrape_expediente_documents(expediente_url: str) -> list:
    """
    Raspa la página expedienteEvaluacion.php para extraer información de los documentos,
    identificando especialmente las RCAs.
    """
    documentos_encontrados = []
    full_expediente_url = expediente_url

    print(f"Scraping documentos del expediente desde: {full_expediente_url}")

    try:
        response = requests.get(full_expediente_url, timeout=20)
        response.raise_for_status() # Lanzar excepción para códigos de estado de error

        soup = BeautifulSoup(response.content, 'html.parser')

        # --- LOCALIZAR LA TABLA PRINCIPAL DE DOCUMENTOS EN expedienteEvaluacion.php ---
        # Basado en las capturas, parece ser una tabla con class='tabla'
        # AJUSTA ESTE SELECTOR SI ES NECESARIO para encontrar la tabla correcta
        # Podria ser soup.find('table', {'class': 'tabla'}) o un selector CSS mas especifico
        document_table = soup.find('table', class_='tabla')


        if not document_table:
            print("Tabla de documentos del expediente no encontrada.")
            return []


        # Asumimos que las filas de documentos son <tr> dentro del <tbody> (excluyendo thead)
        # AJUSTA ESTO si la estructura es diferente
        document_rows = document_table.find_all('tr')
        if len(document_rows) > 1:
            document_rows = document_rows[1:] # Saltar la fila de encabezado si existe
        else:
             print("Tabla de documentos vacía o solo con encabezado.")
             return []


        print(f"Filas de documentos encontradas: {len(document_rows)}")

        # Iterar sobre las filas de la tabla de documentos
        for i, row in enumerate(document_rows):
             # Asumimos que las columnas son <td>
             columns = row.find_all(['td', 'th'])

             # --- EXTRACCION DE DATOS DE COLUMNAS DE DOCUMENTO (AJUSTA INDICES) ---
             # Asegurarse de que hay suficientes columnas ANTES de intentar acceder a ellas
             # Los indices [0], [1], etc. dependen del orden REAL de las columnas en la tabla.
             # Basado en las capturas, parece haber al menos 5 columnas relevantes al inicio.
             if len(columns) >= 5:
                 try:
                     # Extraer texto y enlaces. AJUSTA LOS INDICES [0], [1], [2], etc.
                     folio = columns[0].get_text(strip=True) if len(columns) > 0 else "N/A"
                     documento_texto = columns[1].get_text(strip=True) if len(columns) > 1 else "N/A"
                     emitido_por = columns[2].get_text(strip=True) if len(columns) > 2 else "N/A"
                     destinado_a = columns[3].get_text(strip=True) if len(columns) > 3 else "N/A"
                     fecha = columns[4].get_text(strip=True) if len(columns) > 4 else "N/A" # Puede ser fecha de recepcion o similar

                     # --- IDENTIFICAR SI ES UNA RCA Y EXTRAER EL ENLACE PDF ---
                     # Busca si el texto del documento indica que es una RCA. AJUSTA EL TEXTO A BUSCAR.
                     is_rca = "resolución de calificación ambiental" in documento_texto.lower() or \
                              "rca n°" in documento_texto.lower() # Ejemplo: buscar N° RCA tambien

                     link_documento = None
                     # Busca el enlace (<a> tag) dentro de la columna "Documento" (indice 1)
                     if len(columns) > 1:
                        link_elemento = columns[1].find('a', href=True)

                        if link_elemento:
                            href = link_elemento['href']
                            # Construir URL completa si es relativa y verificar si es un PDF (opcional)
                            if href.startswith('/'):
                                full_href = BASE_SEIA_URL + href
                            else:
                                full_href = href # Ya es una URL completa

                            # Opcional: Puedes añadir una verificación si el enlace apunta a un PDF
                            # if full_href.lower().endswith('.pdf'):
                            link_documento = full_href
                            # else:
                            #     print(f"Enlace encontrado no parece un PDF para {documento_texto}: {full_href}") # Log

                     # Solo añadimos el documento si logramos identificarlo como una RCA
                     if is_rca:
                         documentos_encontrados.append({
                             "folio": folio,
                             "documento_tipo": documento_texto,
                             "emitido_por": emitido_por,
                             "destinado_a": destinado_a,
                             "fecha": fecha,
                             "link_pdf": link_documento if link_documento else "No disponible",
                             "fuente_expediente": full_expediente_url # Opcional: URL del expediente
                         })
                     # O podrías añadir todos los documentos si el modelo necesita ver el expediente completo
                     # else:
                     #     # Añadir otros documentos aunque no sean RCA si es util para el analisis
                     #     documentos_encontrados.append({
                     #         "folio": folio, "documento_tipo": documento_texto, "fecha": fecha,
                     #         "link_pdf": link_documento if link_documento else "No disponible", "es_rca": False
                     #     })


                 except IndexError as ie:
                      print(f"Error de indice al procesar fila de documento {i}: {ie}")
                 except Exception as ex:
                      print(f"Error al extraer datos de fila de documento {i}: {ex}")
             else:
                  print(f"Fila de documento {i} no tiene suficientes columnas (esperadas >=5).")


    except requests.exceptions.RequestException as e:
        print(f"Error al acceder a la página del expediente {full_expediente_url}: {e}")
        return []
    except Exception as e:
        print(f"Error general al raspar documentos del expediente {full_expediente_url}: {e}")
        return []

    print(f"Raspado de documentos del expediente completado. Documentos (posibles RCAs) identificados: {len(documentos_encontrados)}")
    return documentos_encontrados


# --- FUNCIÓN PRINCIPAL: buscar_empresa ---
# Busca proyectos en la busqueda inicial y luego raspa sus documentos de expediente
def buscar_empresa(nombre_empresa: str) -> list: # Retorna una lista de proyectos, cada uno con sus documentos/RCAs
    """
    Busca proyectos en el SEIA por nombre, obtiene el enlace al expediente y raspa sus documentos/RCAs.
    Retorna una lista de diccionarios de proyecto.
    """
    proyectos_encontrados = []
    search_url = BUSQUEDA_PROYECTO_URL

    payload = {
        "NOMBRE_EMPRESA": nombre_empresa,
        "TIPO_PROYECTO": "",
        "REGION": "",
        "ESTADO": "",
        "EVALUACION": "",
        "RCA": "",
        "CODIGO": "",
        "submit": "Buscar"
    }

    headers = {
        "User-Agent": "Mozilla/5.0" # Es bueno simular un navegador
    }

    print(f"Buscando proyectos para: {nombre_empresa} en {search_url}")

    try:
        response = requests.post(search_url, data=payload, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Raspar la tabla de resultados de la búsqueda (clase 'tabla')
        table = soup.find('table', class_='tabla')

        if not table:
            print("Tabla de resultados de busqueda no encontrada o vacia.")
            return []

        rows = table.find_all('tr')
        if len(rows) <= 1:
             print(f"No se encontraron proyectos en los resultados de busqueda para '{nombre_empresa}'.")
             return []

        result_rows = rows[1:] # Saltar la fila de encabezado

        print(f"Proyectos encontrados en resultados de busqueda: {len(result_rows)}")

        # Limitar a los primeros N resultados y extraer el enlace del EXPEDIENTE
        # El enlace de detalle/expediente parece estar en la primera columna (indice 0)
        for i, row in enumerate(result_rows[:5]): # Procesar solo los primeros 5 proyectos
            columns = row.find_all(['td', 'th'])

            # Extraer el enlace al expediente del <a> en la primera columna
            expediente_url = None
            if len(columns) > 0:
                 link_elemento_expediente = columns[0].find('a', href=True)

                 if link_elemento_expediente:
                      expediente_href = link_elemento_expediente['href']
                      # Construir URL completa del expediente si es relativa
                      if expediente_href.startswith('/'):
                          expediente_url = BASE_SEIA_URL + expediente_href
                      else:
                           expediente_url = expediente_href # Asumir completa o ajustar


            # Si encontramos el enlace al expediente, raspar los documentos
            documentos_rcas = []
            if expediente_url:
                print(f"Encontrado enlace de expediente: {expediente_url}. Raspando documentos...")
                time.sleep(2) # Pausa antes de ir a la pagina del expediente
                documentos_rcas = _scrape_expediente_documents(expediente_url)
            else:
                 print(f"No se encontro enlace de expediente en la primera columna para la fila {i}.")


            # Añadir los datos basicos del proyecto + los documentos/RCAs encontrados
            # Asegurarse de que las columnas existan antes de acceder a ellas
            nombre_proyecto = columns[0].get_text(strip=True) if len(columns) > 0 else "N/A"
            region = columns[1].get_text(strip=True) if len(columns) > 1 else "N/A"
            tipo = columns[2].get_text(strip=True) if len(columns) > 2 else "N/A"
            fecha_ingreso = columns[3].get_text(strip=True) if len(columns) > 3 else "N/A"
            tipo_presentacion = columns[4].get_text(strip=True) if len(columns) > 4 else "N/A"
            codigo = columns[5].get_text(strip=True) if len(columns) > 5 else "N/A"


            proyectos_encontrados.append({
                 "nombre_proyecto": nombre_proyecto,
                 "link_expediente": expediente_url if expediente_url else "No disponible",
                 "region": region,
                 "tipo": tipo,
                 "fecha_ingreso": fecha_ingreso,
                 "tipo_presentacion": tipo_presentacion,
                 "codigo": codigo,
                 "documentos_rcas": documentos_rcas # Lista de documentos/RCAs para este proyecto
            })


    except requests.exceptions.RequestException as e:
        print(f"Error de solicitud HTTP en buscar_empresa: {e}")
        return []
    except Exception as e:
        print(f"Error general en buscar_empresa: {e}")
        return []

    print(f"Busqueda de proyectos y raspado de documentos del expediente completado. Proyectos con documentos procesados: {len(proyectos_encontrados)}")
    return proyectos_encontrados
