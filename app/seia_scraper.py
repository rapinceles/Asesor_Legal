import requests
from bs4 import BeautifulSoup

def buscar_empresa(nombre_empresa):
    url = "https://seia.sea.gob.cl/busqueda/buscarProyectoAction.php"
    payload = {
        "NOMBRE": nombre_empresa,
        "tipoproyecto": "",
        "region": "",
        "comuna": "",
        "estado": "",
        "tipopresentacion": "",
        "evaluacion": "",
        "RCA": "",
        "codigo": "",
        "submit": "Buscar"
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.post(url, data=payload, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")
    tabla = soup.find("table", class_="tabla")

    if not tabla:
        return {"empresa": nombre_empresa, "proyectos": [], "error": "No se encontraron resultados"}

    proyectos = []
    for fila in tabla.find_all("tr")[1:6]:  # Solo los primeros 5
        columnas = fila.find_all("td")
        if len(columnas) >= 7:
            proyectos.append({
                "nombre_proyecto": columnas[0].text.strip(),
                "region": columnas[1].text.strip(),
                "tipo": columnas[2].text.strip(),
                "estado": columnas[3].text.strip(),
                "fecha_ingreso": columnas[4].text.strip(),
                "tipo_presentacion": columnas[5].text.strip(),
                "codigo": columnas[6].text.strip()
            })

    return {"empresa": nombre_empresa, "proyectos": proyectos}
