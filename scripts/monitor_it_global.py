import json
import os
import re
import unicodedata
from datetime import datetime, date
from urllib.parse import quote_plus

import requests

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None


ARCHIVO_IT = os.path.join("data", "it.json")
MAX_ITEMS_IT = 260
MAX_ITEMS_POR_BUSQUEDA = 30


BUSQUEDAS_GLOBALES = [
    {
        "categoria": "Analista Funcional / BA Senior",
        "terminos": [
            "senior business analyst",
            "senior functional analyst",
            "business systems analyst",
            "functional analyst",
        ],
    },
    {
        "categoria": "Analista de Negocio Senior",
        "terminos": [
            "senior business analyst",
            "senior business process analyst",
            "business process analyst",
            "business analyst",
        ],
    },
    {
        "categoria": "DBA Senior",
        "terminos": [
            "senior database administrator",
            "senior dba",
            "database administrator",
            "postgresql dba",
            "sql server dba",
            "oracle dba",
        ],
    },
]


CARDS_BUSQUEDA_DIRECTA = [
    {
        "titulo": "Senior Business Analyst - LinkedIn Worldwide",
        "fuente": "LinkedIn Global",
        "categoria": "Analista Funcional / BA Senior",
        "url": "https://www.linkedin.com/jobs/search/?keywords=Senior%20Business%20Analyst&location=Worldwide",
    },
    {
        "titulo": "Senior Functional Analyst - LinkedIn Worldwide",
        "fuente": "LinkedIn Global",
        "categoria": "Analista Funcional / BA Senior",
        "url": "https://www.linkedin.com/jobs/search/?keywords=Senior%20Functional%20Analyst&location=Worldwide",
    },
    {
        "titulo": "Senior Business Analyst - Indeed Remote",
        "fuente": "Indeed Remote",
        "categoria": "Analista de Negocio Senior",
        "url": "https://www.indeed.com/jobs?q=Senior+Business+Analyst&l=Remote",
    },
    {
        "titulo": "Senior Business Analyst - Glassdoor Remote",
        "fuente": "Glassdoor Remote",
        "categoria": "Analista de Negocio Senior",
        "url": "https://www.glassdoor.com/Job/remote-senior-business-analyst-jobs-SRCH_IL.0,6_IS11047_KO7,30.htm",
    },
    {
        "titulo": "Senior DBA - LinkedIn Worldwide",
        "fuente": "LinkedIn Global",
        "categoria": "DBA Senior",
        "url": "https://www.linkedin.com/jobs/search/?keywords=Senior%20Database%20Administrator%20OR%20Senior%20DBA&location=Worldwide",
    },
    {
        "titulo": "Senior Database Administrator - Indeed Remote",
        "fuente": "Indeed Remote",
        "categoria": "DBA Senior",
        "url": "https://www.indeed.com/q-senior-database-administrator-l-remote-jobs.html",
    },
    {
        "titulo": "Remote Analyst Jobs - RemoteOK",
        "fuente": "RemoteOK",
        "categoria": "Analista Funcional / BA Senior",
        "url": "https://remoteok.com/remote-analyst-jobs",
    },
    {
        "titulo": "Remote Business Analyst Jobs - Remote.com",
        "fuente": "Remote.com",
        "categoria": "Analista de Negocio Senior",
        "url": "https://remote.com/jobs/types-of-remote-jobs/remote-business-analyst-jobs",
    },
]


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


def cargar_json(ruta):
    if not os.path.exists(ruta):
        return []

    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
            return datos if isinstance(datos, list) else []
    except json.JSONDecodeError:
        return []


def guardar_json(ruta, datos):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)

    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, indent=2, ensure_ascii=False)


def crear_id(prefijo, titulo, url):
    base = f"{prefijo}-{titulo}-{url}"
    base = normalizar_texto(base)
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    return base[:180]


def limpiar_html(texto):
    texto = re.sub(r"<[^>]+>", "", texto or "")
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def es_senior(texto):
    texto = normalizar_texto(texto)

    palabras_senior = [
        "senior",
        "sr",
        "lead",
        "principal",
        "staff",
    ]

    return any(palabra in texto for palabra in palabras_senior)


def detectar_categoria(titulo, descripcion, categoria_base):
    texto = normalizar_texto(f"{titulo} {descripcion}")

    if (
        "dba" in texto
        or "database administrator" in texto
        or "sql server" in texto
        or "oracle" in texto
        or "postgresql" in texto
    ):
        return "DBA Senior"

    if (
        "functional analyst" in texto
        or "business systems analyst" in texto
        or "systems analyst" in texto
    ):
        return "Analista Funcional / BA Senior"

    if (
        "business analyst" in texto
        or "business process analyst" in texto
        or "business analysis" in texto
    ):
        return "Analista de Negocio Senior"

    return categoria_base


def titulo_valido(titulo, descripcion):
    texto = normalizar_texto(f"{titulo} {descripcion}")

    terminos_objetivo = [
        "business analyst",
        "functional analyst",
        "business systems analyst",
        "business process analyst",
        "database administrator",
        "dba",
        "sql server",
        "oracle",
        "postgresql",
    ]

    if not any(termino in texto for termino in terminos_objetivo):
        return False

    # Como estas búsquedas son para senior, filtramos fuerte.
    if not es_senior(texto):
        return False

    descartes = [
        "intern",
        "internship",
        "trainee",
        "junior",
        "entry level",
        "graduate",
        "student",
    ]

    if any(descarte in texto for descarte in descartes):
        return False

    return True


def item_desde_datos(titulo, empresa, fuente, categoria, url, descripcion):
    hoy = hoy_argentina().isoformat()

    return {
        "id": crear_id(fuente, titulo, url),
        "titulo": titulo,
        "fuente": f"{fuente} - {empresa}" if empresa else fuente,
        "categoria": categoria,
        "estado": "nuevo",
        "fechaDetectada": hoy,
        "fechaCierre": "",
        "url": url,
        "descripcion": descripcion[:260] if descripcion else "Oferta global/remota detectada automáticamente para perfil IT senior.",
        "origen": "Global / remoto",
    }


def obtener_json(url):
    headers = {
        "User-Agent": "Mozilla/5.0 MonitorLaboral/1.0",
        "Accept": "application/json",
    }

    respuesta = requests.get(url, headers=headers, timeout=30)
    respuesta.raise_for_status()
    return respuesta.json()


def buscar_remotive(termino, categoria_base):
    resultados = []
    url = f"https://remotive.com/api/remote-jobs?search={quote_plus(termino)}"

    try:
        data = obtener_json(url)
        jobs = data.get("jobs", [])

        for job in jobs[:MAX_ITEMS_POR_BUSQUEDA]:
            titulo = job.get("title", "")
            empresa = job.get("company_name", "")
            descripcion = limpiar_html(job.get("description", ""))
            url_job = job.get("url", "")

            if not titulo or not url_job:
                continue

            if not titulo_valido(titulo, descripcion):
                continue

            categoria = detectar_categoria(titulo, descripcion, categoria_base)

            resultados.append(
                item_desde_datos(
                    titulo=titulo,
                    empresa=empresa,
                    fuente="Remotive",
                    categoria=categoria,
                    url=url_job,
                    descripcion=descripcion,
                )
            )

    except Exception as error:
        print(f"[it-global] Error Remotive '{termino}': {error}")

    return resultados


def buscar_remoteok_todo():
    resultados = []

    try:
        data = obtener_json("https://remoteok.com/api")

        for job in data:
            if not isinstance(job, dict):
                continue

            titulo = job.get("position", "") or job.get("title", "")
            empresa = job.get("company", "")
            descripcion = limpiar_html(job.get("description", ""))
            url_job = job.get("url", "") or job.get("apply_url", "")

            if not titulo or not url_job:
                continue

            if not titulo_valido(titulo, descripcion):
                continue

            categoria = detectar_categoria(titulo, descripcion, "Analista de Negocio Senior")

            resultados.append(
                item_desde_datos(
                    titulo=titulo,
                    empresa=empresa,
                    fuente="RemoteOK",
                    categoria=categoria,
                    url=url_job,
                    descripcion=descripcion,
                )
            )

    except Exception as error:
        print(f"[it-global] Error RemoteOK API: {error}")

    return resultados[:90]


def crear_cards_busqueda_directa():
    items = []
    hoy = hoy_argentina().isoformat()

    for card in CARDS_BUSQUEDA_DIRECTA:
        items.append(
            {
                "id": crear_id("busqueda-directa-global", card["titulo"], card["url"]),
                "titulo": card["titulo"],
                "fuente": card["fuente"],
                "categoria": card["categoria"],
                "estado": "nuevo",
                "fechaDetectada": hoy,
                "fechaCierre": "",
                "url": card["url"],
                "descripcion": (
                    "Búsqueda global/remota preconfigurada. Abre el portal directamente "
                    "con la búsqueda armada, sin escribir nada manualmente."
                ),
                "origen": "Búsqueda directa global",
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


def conservar_fecha_y_estado(items, anteriores_por_id):
    resultado = []

    for item in items:
        anterior = anteriores_por_id.get(item["id"])

        if anterior:
            item["estado"] = "vigente"
            item["fechaDetectada"] = anterior.get(
                "fechaDetectada",
                item["fechaDetectada"],
            )

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
            item.get("categoria", ""),
            item.get("fechaDetectada", ""),
            item.get("titulo", ""),
        ),
    )


def main():
    print("Iniciando revisión IT global...")

    existentes = cargar_json(ARCHIVO_IT)

    anteriores_por_id = {
        item.get("id"): item
        for item in existentes
        if item.get("id")
    }

    nuevos_globales = []

    for busqueda in BUSQUEDAS_GLOBALES:
        categoria = busqueda["categoria"]

        for termino in busqueda["terminos"]:
            print(f"[it-global] Remotive: {termino}")
            nuevos_globales.extend(buscar_remotive(termino, categoria))

    print("[it-global] RemoteOK API")
    nuevos_globales.extend(buscar_remoteok_todo())

    print("[it-global] Agregando búsquedas directas globales")
    nuevos_globales.extend(crear_cards_busqueda_directa())

    nuevos_globales = quitar_duplicados(nuevos_globales)
    nuevos_globales = conservar_fecha_y_estado(nuevos_globales, anteriores_por_id)

    combinado = existentes + nuevos_globales
    combinado = quitar_duplicados(combinado)
    combinado = ordenar_items(combinado)
    combinado = combinado[:MAX_ITEMS_IT]

    guardar_json(ARCHIVO_IT, combinado)

    total_global = len([
        item for item in combinado
        if item.get("categoria") in [
            "Analista Funcional / BA Senior",
            "Analista de Negocio Senior",
            "DBA Senior",
        ]
    ])

    print("Revisión IT global finalizada.")
    print(f"Archivo actualizado: {ARCHIVO_IT}")
    print(f"Total IT: {len(combinado)}")
    print(f"Total categorías global/senior: {total_global}")


if __name__ == "__main__":
    main()