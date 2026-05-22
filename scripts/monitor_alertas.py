import json
import os
import re
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime, date
from urllib.parse import urlparse, parse_qs

import requests

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None


ARCHIVO_CONFIG = os.path.join("config", "fuentes_alertas.json")

ARCHIVOS_SALIDA = {
    "salud_privada": os.path.join("data", "salud.json"),
    "quimica": os.path.join("data", "quimica.json"),
    "it": os.path.join("data", "it.json"),
}

MAX_ITEMS_POR_AREA = 100


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


def cargar_json(ruta, valor_default):
    if not os.path.exists(ruta):
        return valor_default

    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
            return datos if isinstance(datos, list) else valor_default
    except json.JSONDecodeError:
        return valor_default


def guardar_json(ruta, datos):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)

    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, indent=2, ensure_ascii=False)


def obtener_texto(elemento, nombre):
    encontrado = elemento.find(nombre)

    if encontrado is None or encontrado.text is None:
        return ""

    return encontrado.text.strip()


def limpiar_url_google_alerts(url):
    if not url:
        return ""

    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    for key in ["url", "q"]:
        if key in params and params[key]:
            posible_url = params[key][0]

            if posible_url.startswith("http"):
                return posible_url

    return url


def crear_id(area, titulo, url):
    base = f"alerta-{area}-{titulo}-{url}"
    base = normalizar_texto(base)
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    return base[:180]


def obtener_feed(rss_url):
    headers = {
        "User-Agent": "Mozilla/5.0 MonitorLaboral/1.0"
    }

    respuesta = requests.get(rss_url, headers=headers, timeout=30)
    respuesta.raise_for_status()
    return respuesta.text


def parsear_feed_google_alerts(xml_texto):
    root = ET.fromstring(xml_texto)
    items = []

    for item in root.findall(".//item"):
        titulo = obtener_texto(item, "title")
        link = limpiar_url_google_alerts(obtener_texto(item, "link"))
        resumen = obtener_texto(item, "description")
        fecha_publicacion = obtener_texto(item, "pubDate")

        if titulo and link:
            items.append(
                {
                    "titulo": titulo,
                    "url": link,
                    "resumen": resumen,
                    "fechaPublicacion": fecha_publicacion,
                }
            )

    atom_ns = "{http://www.w3.org/2005/Atom}"

    for entry in root.findall(f".//{atom_ns}entry"):
        titulo = obtener_texto(entry, f"{atom_ns}title")
        resumen = obtener_texto(entry, f"{atom_ns}content")
        fecha_publicacion = obtener_texto(entry, f"{atom_ns}updated")

        link = ""
        link_element = entry.find(f"{atom_ns}link")

        if link_element is not None:
            link = limpiar_url_google_alerts(link_element.attrib.get("href", ""))

        if titulo and link:
            items.append(
                {
                    "titulo": titulo,
                    "url": link,
                    "resumen": resumen,
                    "fechaPublicacion": fecha_publicacion,
                }
            )

    return items


def limpiar_html(texto):
    texto = re.sub(r"<[^>]+>", "", texto or "")
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def descripcion_por_area(area, categoria, resumen):
    resumen_limpio = limpiar_html(resumen)

    if resumen_limpio:
        return resumen_limpio[:220]

    if area == "salud_privada":
        return (
            "Oferta privada detectada para Técnico/a en Esterilización, "
            "central de esterilización, clínicas, sanatorios u hospitales privados."
        )

    if area == "quimica":
        return (
            "Oferta privada detectada para técnico químico, operario, "
            "producción o control de calidad."
        )

    if area == "it":
        if categoria == "QA Manual":
            return "Oferta detectada para QA Manual trainee/junior."
        if categoria == "QA Automation":
            return "Oferta detectada para QA Automation trainee/junior."
        return "Oferta detectada para desarrollo trainee/junior."

    return "Publicación detectada automáticamente."


def convertir_items(area, fuente, items_feed, anteriores_por_id):
    nuevos_items = []

    for item in items_feed:
        id_item = crear_id(area, item["titulo"], item["url"])
        item_anterior = anteriores_por_id.get(id_item)

        estado = "vigente"
        fecha_detectada = hoy_argentina().isoformat()

        if not item_anterior:
            estado = "nuevo"
        else:
            fecha_detectada = item_anterior.get("fechaDetectada", fecha_detectada)

        nuevos_items.append(
            {
                "id": id_item,
                "titulo": item["titulo"],
                "fuente": fuente["nombre"],
                "categoria": fuente["categoria"],
                "estado": estado,
                "fechaDetectada": fecha_detectada,
                "fechaCierre": "",
                "url": item["url"],
                "descripcion": descripcion_por_area(
                    area,
                    fuente["categoria"],
                    item.get("resumen", "")
                ),
                "origen": "Google Alerts",
            }
        )

    return nuevos_items


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
            item.get("fechaDetectada", ""),
            item.get("categoria", ""),
            item.get("titulo", ""),
        ),
    )


def revisar_area(area, fuentes):
    archivo_salida = ARCHIVOS_SALIDA[area]
    anteriores = cargar_json(archivo_salida, [])
    anteriores_por_id = {
        item.get("id"): item
        for item in anteriores
        if item.get("id")
    }

    resultados = []

    for fuente in fuentes:
        rss_url = fuente.get("rss", "").strip()

        if not rss_url:
            print(f"[{area}] Fuente sin RSS configurado: {fuente['nombre']}")
            continue

        print(f"[{area}] Revisando alerta: {fuente['nombre']}")

        try:
            xml_texto = obtener_feed(rss_url)
            items_feed = parsear_feed_google_alerts(xml_texto)
            items_convertidos = convertir_items(
                area,
                fuente,
                items_feed,
                anteriores_por_id,
            )

            resultados.extend(items_convertidos)

            print(f"[{area}] Items encontrados: {len(items_convertidos)}")

        except Exception as error:
            print(f"[{area}] Error revisando {fuente['nombre']}: {error}")

    combinado = anteriores + resultados
    combinado = quitar_duplicados(combinado)
    combinado = ordenar_items(combinado)
    combinado = combinado[:MAX_ITEMS_POR_AREA]

    guardar_json(archivo_salida, combinado)

    nuevos = [item for item in combinado if item.get("estado") == "nuevo"]

    print(f"[{area}] Archivo actualizado: {archivo_salida}")
    print(f"[{area}] Total: {len(combinado)}")
    print(f"[{area}] Nuevos: {len(nuevos)}")


def main():
    print("Iniciando revisión de Google Alerts...")

    config = cargar_json(ARCHIVO_CONFIG, {})

    for area in ["salud_privada", "quimica", "it"]:
        fuentes = config.get(area, [])

        if not fuentes:
            print(f"No hay fuentes configuradas para {area}.")
            continue

        revisar_area(area, fuentes)

    print("Revisión de Google Alerts finalizada.")


if __name__ == "__main__":
    main()