import json
import os
import re
import unicodedata
from datetime import datetime, date
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None


URL_BASE = "https://buenosaires.gob.ar"

URL_ESTERILIZACION = (
    "https://buenosaires.gob.ar/gcaba_historico/salud/recursos-humanos/"
    "tecnicoa-en-esterilizacion"
)

URL_CONCURSOS_ACTIVOS = (
    "https://buenosaires.gob.ar/gcaba_historico/"
    "concursos-de-la-carrera-profesional-de-la-salud/concursos-publicos-abiertos"
)

ARCHIVO_SALIDA = os.path.join("data", "concursos_caba.json")

PALABRAS_ESTERILIZACION = [
    "esterilizacion",
    "central de esterilizacion",
    "tecnico en esterilizacion",
    "tecnica en esterilizacion",
    "tecnico/a en esterilizacion",
]

PALABRAS_TECNICO_QUIMICO = [
    "tecnico quimico",
    "tecnica quimica",
    "tecnico/a quimico",
    "tecnico/a quimica",
    "perito quimico",
]

PALABRAS_DESCARTAR = [
    "tecnico en laboratorio",
    "tecnica en laboratorio",
    "tecnico/a en laboratorio",
    "bioquimico",
    "bioquimica",
]

MESES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


def hoy_argentina():
    if ZoneInfo:
        return datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()

    return date.today()


def normalizar_texto(texto):
    texto = texto or ""
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def contiene_alguna(texto_normalizado, palabras):
    return any(palabra in texto_normalizado for palabra in palabras)


def obtener_html(url):
    headers = {
        "User-Agent": "Mozilla/5.0 MonitorLaboral/1.0"
    }

    respuesta = requests.get(url, headers=headers, timeout=30)
    respuesta.raise_for_status()
    return respuesta.text


def cargar_json():
    if not os.path.exists(ARCHIVO_SALIDA):
        return []

    try:
        with open(ARCHIVO_SALIDA, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
            return datos if isinstance(datos, list) else []
    except json.JSONDecodeError:
        return []


def guardar_json(datos):
    os.makedirs(os.path.dirname(ARCHIVO_SALIDA), exist_ok=True)

    with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, indent=2, ensure_ascii=False)


def convertir_fecha(texto):
    texto_normalizado = normalizar_texto(texto)

    patron_largo = r"(\d{1,2})\s+de\s+([a-z]+)(?:\s+de)?\s+(\d{4})"
    coincidencia = re.search(patron_largo, texto_normalizado)

    if coincidencia:
        dia = int(coincidencia.group(1))
        mes_nombre = coincidencia.group(2)
        anio = int(coincidencia.group(3))
        mes = MESES.get(mes_nombre)

        if mes:
            return date(anio, mes, dia).isoformat()

    patron_corto = r"(\d{1,2})/(\d{1,2})/(\d{4})"
    coincidencia = re.search(patron_corto, texto_normalizado)

    if coincidencia:
        dia = int(coincidencia.group(1))
        mes = int(coincidencia.group(2))
        anio = int(coincidencia.group(3))

        return date(anio, mes, dia).isoformat()

    return ""


def buscar_fecha(texto, etiquetas):
    lineas = texto.split("\n")

    for indice, linea in enumerate(lineas):
        linea_normalizada = normalizar_texto(linea)

        for etiqueta in etiquetas:
            if etiqueta in linea_normalizada:
                bloque = linea

                if indice + 1 < len(lineas):
                    bloque += " " + lineas[indice + 1]

                if indice + 2 < len(lineas):
                    bloque += " " + lineas[indice + 2]

                fecha = convertir_fecha(bloque)

                if fecha:
                    return fecha

    return ""


def esta_vigente(fecha_inicio, fecha_cierre):
    if not fecha_cierre:
        return False

    hoy = hoy_argentina()
    cierre = date.fromisoformat(fecha_cierre)

    if cierre < hoy:
        return False

    if fecha_inicio:
        inicio = date.fromisoformat(fecha_inicio)

        if hoy < inicio:
            return False

    return True


def obtener_links_desde_esterilizacion():
    html = obtener_html(URL_ESTERILIZACION)
    soup = BeautifulSoup(html, "html.parser")

    links = []

    for a in soup.find_all("a", href=True):
        texto = normalizar_texto(a.get_text(" ", strip=True))
        href = a.get("href")

        if "datos del concurso" in texto:
            links.append(urljoin(URL_BASE, href))

    return links


def obtener_links_desde_concursos_activos():
    html = obtener_html(URL_CONCURSOS_ACTIVOS)
    soup = BeautifulSoup(html, "html.parser")

    links = []

    for a in soup.find_all("a", href=True):
        href = a.get("href")
        url = urljoin(URL_BASE, href)
        url_normalizada = normalizar_texto(url)

        if "concursos-publicos-abiertos" in url_normalizada:
            continue

        if "/node/" in url_normalizada or "/salud/recursos-humanos/" in url_normalizada:
            links.append(url)

    return links


def obtener_hospital(soup):
    h1 = soup.find("h1")

    if h1:
        return h1.get_text(" ", strip=True)

    return "Hospital GCBA"


def extraer_bloques(soup):
    bloques = []
    encabezados = soup.find_all(["h2", "h3", "h4", "h5"])

    for encabezado in encabezados:
        partes = [encabezado.get_text(" ", strip=True)]

        for hermano in encabezado.find_next_siblings():
            if hermano.name in ["h2", "h3", "h4", "h5"]:
                break

            texto = hermano.get_text("\n", strip=True)

            if texto:
                partes.append(texto)

        bloque = "\n".join(partes).strip()

        if bloque:
            bloques.append(bloque)

    if not bloques:
        texto_completo = soup.get_text("\n", strip=True)

        if texto_completo:
            bloques.append(texto_completo)

    return bloques


def es_concurso_buscado(bloque):
    bloque_normalizado = normalizar_texto(bloque)

    es_esterilizacion = contiene_alguna(
        bloque_normalizado,
        PALABRAS_ESTERILIZACION,
    )

    es_tecnico_quimico = contiene_alguna(
        bloque_normalizado,
        PALABRAS_TECNICO_QUIMICO,
    )

    if not es_esterilizacion and not es_tecnico_quimico:
        return False

    for palabra in PALABRAS_DESCARTAR:
        if palabra in bloque_normalizado:
            return False

    return True


def clasificar_categoria(bloque):
    bloque_normalizado = normalizar_texto(bloque)

    if contiene_alguna(bloque_normalizado, PALABRAS_TECNICO_QUIMICO):
        return "Técnico químico GCBA"

    if contiene_alguna(bloque_normalizado, PALABRAS_ESTERILIZACION):
        return "Esterilización GCBA"

    return "Concursos CABA"


def obtener_titulo(bloque):
    lineas = [linea.strip() for linea in bloque.split("\n") if linea.strip()]

    for linea in lineas:
        linea_normalizada = normalizar_texto(linea)

        if linea_normalizada.startswith("cargo:"):
            titulo = linea.split(":", 1)[1].strip()

            if titulo:
                return titulo

    for linea in lineas:
        linea_normalizada = normalizar_texto(linea)

        if contiene_alguna(linea_normalizada, PALABRAS_TECNICO_QUIMICO):
            return linea

        if contiene_alguna(linea_normalizada, PALABRAS_ESTERILIZACION):
            return linea

    for linea in lineas:
        if "concurso" in normalizar_texto(linea):
            return linea

    return "Concurso CABA"


def crear_id(url, titulo, fecha_inicio, fecha_cierre):
    base = f"concursos-caba-{url}-{titulo}-{fecha_inicio}-{fecha_cierre}"
    base = normalizar_texto(base)
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    return base[:180]


def extraer_items_de_pagina(url, anteriores_por_id):
    html = obtener_html(url)
    soup = BeautifulSoup(html, "html.parser")

    hospital = obtener_hospital(soup)
    bloques = extraer_bloques(soup)

    items = []

    for bloque in bloques:
        if not es_concurso_buscado(bloque):
            continue

        fecha_inicio = buscar_fecha(
            bloque,
            [
                "fecha de inscripcion",
                "fecha de inicio inscripcion",
                "fecha inicio inscripcion",
                "fecha de apertura",
                "apertura de inscripcion",
            ],
        )

        fecha_cierre = buscar_fecha(
            bloque,
            [
                "fecha de cierre",
                "fecha de cierre inscripcion",
                "cierre de la inscripcion",
                "cierre de inscripcion",
            ],
        )

        # Regla principal:
        # Solo se muestran concursos con fecha de cierre conocida y vigente.
        if not fecha_cierre:
            continue

        if not esta_vigente(fecha_inicio, fecha_cierre):
            continue

        titulo = obtener_titulo(bloque)
        categoria = clasificar_categoria(bloque)
        id_item = crear_id(url, titulo, fecha_inicio, fecha_cierre)

        item_anterior = anteriores_por_id.get(id_item)

        estado = "vigente"
        fecha_detectada = hoy_argentina().isoformat()

        if not item_anterior:
            estado = "nuevo"
        else:
            fecha_detectada = item_anterior.get("fechaDetectada", fecha_detectada)

        if categoria == "Esterilización GCBA":
            descripcion = (
                "Concurso vigente de hospitales GCBA para Técnico/a en "
                "Esterilización o central de esterilización."
            )
        elif categoria == "Técnico químico GCBA":
            descripcion = (
                "Concurso vigente de hospitales GCBA para Técnico Químico."
            )
        else:
            descripcion = "Concurso vigente de hospitales del Gobierno de la Ciudad."

        items.append(
            {
                "id": id_item,
                "titulo": titulo,
                "fuente": hospital,
                "categoria": categoria,
                "estado": estado,
                "fechaDetectada": fecha_detectada,
                "fechaInscripcion": fecha_inicio,
                "fechaCierre": fecha_cierre,
                "url": url,
                "descripcion": descripcion,
                "origen": "Concursos CABA",
            }
        )

    return items


def quitar_duplicados(items):
    vistos = set()
    resultado = []

    for item in items:
        clave = item.get("id") or item.get("url")

        if clave in vistos:
            continue

        vistos.add(clave)
        resultado.append(item)

    return resultado


def ordenar_items(items):
    prioridad_estado = {
        "nuevo": 0,
        "vigente": 1,
    }

    return sorted(
        items,
        key=lambda item: (
            prioridad_estado.get(item.get("estado"), 9),
            item.get("fechaCierre") or "9999-12-31",
            item.get("categoria", ""),
            item.get("titulo", ""),
        ),
    )


def main():
    print("Iniciando revisión de Concursos CABA...")

    anteriores = cargar_json()
    anteriores_por_id = {
        item.get("id"): item
        for item in anteriores
        if item.get("id")
    }

    links = []

    try:
        links_esterilizacion = obtener_links_desde_esterilizacion()
        print(f"Links de índice Esterilización: {len(links_esterilizacion)}")
        links.extend(links_esterilizacion)
    except Exception as error:
        print(f"Error revisando índice de Esterilización: {error}")

    try:
        links_activos = obtener_links_desde_concursos_activos()
        print(f"Links de Concursos CABA activos: {len(links_activos)}")
        links.extend(links_activos)
    except Exception as error:
        print(f"Error revisando Concursos CABA activos: {error}")

    links = list(dict.fromkeys(links))

    print(f"Total de páginas a revisar: {len(links)}")

    resultados = []

    for link in links:
        try:
            items = extraer_items_de_pagina(link, anteriores_por_id)
            resultados.extend(items)

            for item in items:
                print(
                    f"Detectado vigente: {item['titulo']} | "
                    f"{item['categoria']} | cierre {item['fechaCierre']}"
                )

        except Exception as error:
            print(f"Error revisando {link}: {error}")

    resultados = quitar_duplicados(resultados)
    resultados = ordenar_items(resultados)

    guardar_json(resultados)

    print("Revisión finalizada.")
    print(f"Concursos vigentes encontrados: {len(resultados)}")
    print(f"Archivo actualizado: {ARCHIVO_SALIDA}")

    if not resultados:
        print("No hay concursos CABA vigentes para Esterilización o Técnico Químico.")


if __name__ == "__main__":
    main()