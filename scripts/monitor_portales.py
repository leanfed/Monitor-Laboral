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


ARCHIVOS_SALIDA = {
    "salud_privada": os.path.join("data", "salud.json"),
    "quimica": os.path.join("data", "quimica.json"),
    "it": os.path.join("data", "it.json"),
}

MAX_ITEMS_POR_AREA = 180

FUENTES = [
    # ============================================================
    # SALUD PRIVADA - TÉCNICO/A EN ESTERILIZACIÓN
    # ============================================================

    {
        "area": "salud_privada",
        "categoria": "Técnico/a en Esterilización",
        "fuente": "Hospital Alemán",
        "url": "https://www.hospitalaleman.org.ar/nuestro-hospital/trabajar-en-ha/trabajarenha/",
        "keywords": [
            "tecnico de esterilizacion",
            "tecnico en esterilizacion",
            "tecnica en esterilizacion",
            "esterilizacion",
        ],
        "exclude": ["farmaceutico dt", "bioquimico", "bioquimica"],
        "fallback": True,
        "force_fallback": True,
        "fallback_titulo": "Técnico/a en Esterilización - Hospital Alemán",
    },
    {
        "area": "salud_privada",
        "categoria": "Técnico/a en Esterilización",
        "fuente": "Hospital Italiano",
        "url": "https://www.hospitalitaliano.org.ar/hiba/es/news/tecnicoa-esterilizacion",
        "keywords": [
            "tecnico/a en esterilizacion",
            "tecnico en esterilizacion",
            "tecnica en esterilizacion",
            "esterilizacion",
        ],
        "exclude": ["bioquimico", "bioquimica"],
        "fallback": True,
        "force_fallback": True,
        "fallback_titulo": "Técnico/a en Esterilización - Hospital Italiano",
    },
    {
        "area": "salud_privada",
        "categoria": "Técnico/a en Esterilización",
        "fuente": "Hospital Italiano",
        "url": "https://www.hospitalitaliano.org.ar/hiba/es/news/preparadora-de-materiales-quirofano-central",
        "keywords": [
            "tecnico/a en esterilizacion",
            "tecnico en esterilizacion",
            "tecnica en esterilizacion",
            "esterilizacion",
            "preparador de materiales",
            "quirofano central",
        ],
        "exclude": ["bioquimico", "bioquimica"],
        "fallback": True,
        "force_fallback": True,
        "fallback_titulo": "Preparador/a de materiales - Quirófano Central - Hospital Italiano",
    },
    {
        "area": "salud_privada",
        "categoria": "Técnico/a en Esterilización",
        "fuente": "DOS Argentina",
        "url": "https://ar.linkedin.com/jobs/view/tecnico-de-esterilizacion-at-dos-argentina-4295813980",
        "keywords": [
            "tecnico de esterilizacion",
            "tecnicos/as en esterilizacion",
            "esterilizacion",
        ],
        "exclude": [],
        "fallback": True,
        "force_fallback": True,
        "fallback_titulo": "Técnico de Esterilización - DOS Argentina",
    },
    {
        "area": "salud_privada",
        "categoria": "Técnico/a en Esterilización",
        "fuente": "Computrabajo",
        "url": "https://ar.computrabajo.com/trabajo-de-tecnico-en-esterilizacion",
        "keywords": [
            "esterilizacion",
            "tecnico en esterilizacion",
            "tecnica en esterilizacion",
            "tecnico/a en esterilizacion",
            "central de esterilizacion",
            "supervisor de esterilizacion",
            "supervisora de esterilizacion",
        ],
        "exclude": ["farmaceutico dt", "bioquimico", "bioquimica"],
        "fallback": True,
        "fallback_titulo": "Técnico/a en Esterilización - Computrabajo",
    },
    {
        "area": "salud_privada",
        "categoria": "Técnico/a en Esterilización",
        "fuente": "LinkedIn",
        "url": "https://ar.linkedin.com/jobs/t%C3%A9cnico-en-esterilizaci%C3%B3n-empleos",
        "keywords": ["esterilizacion", "tecnico", "tecnica"],
        "exclude": [],
        "fallback": True,
        "force_fallback": True,
        "fallback_titulo": "Técnico/a en Esterilización - LinkedIn",
    },
    {
        "area": "salud_privada",
        "categoria": "Central de Esterilización",
        "fuente": "Computrabajo",
        "url": "https://ar.computrabajo.com/trabajo-de-personal-de-esterilizacion",
        "keywords": [
            "esterilizacion",
            "central de esterilizacion",
            "personal de esterilizacion",
            "supervisor de esterilizacion",
            "supervisora de esterilizacion",
        ],
        "exclude": ["farmaceutico dt", "bioquimico", "bioquimica"],
        "fallback": True,
        "fallback_titulo": "Personal / Central de Esterilización - Computrabajo",
    },
    {
        "area": "salud_privada",
        "categoria": "Central de Esterilización",
        "fuente": "Jooble",
        "url": "https://ar.jooble.org/trabajo-central-de-esterilizacion/Buenos-Aires",
        "keywords": [
            "esterilizacion",
            "central de esterilizacion",
            "tecnico en esterilizacion",
            "tecnica en esterilizacion",
        ],
        "exclude": ["farmaceutico dt", "bioquimico", "bioquimica"],
        "fallback": True,
        "fallback_titulo": "Central de Esterilización - Jooble",
    },
    {
        "area": "salud_privada",
        "categoria": "Técnico/a en Esterilización",
        "fuente": "OpciónEmpleo",
        "url": "https://www.opcionempleo.com.ar/trabajo-tecnico-en-esterilizacion",
        "keywords": [
            "esterilizacion",
            "tecnico en esterilizacion",
            "tecnica en esterilizacion",
        ],
        "exclude": ["farmaceutico dt", "bioquimico", "bioquimica"],
        "fallback": True,
        "fallback_titulo": "Técnico/a en Esterilización - OpciónEmpleo",
    },

    # ============================================================
    # QUÍMICA PRIVADA
    # ============================================================

    {
        "area": "quimica",
        "categoria": "Técnico químico",
        "fuente": "Computrabajo",
        "url": "https://ar.computrabajo.com/trabajo-de-tecnico-quimico",
        "keywords": ["tecnico quimico", "tecnica quimica", "quimico", "quimica"],
        "exclude": ["bioquimico", "bioquimica", "farmaceutico", "farmaceutica"],
        "fallback": True,
        "fallback_titulo": "Técnico químico - Computrabajo",
    },
    {
        "area": "quimica",
        "categoria": "Técnico químico",
        "fuente": "LinkedIn",
        "url": "https://ar.linkedin.com/jobs/tecnico-quimico-empleos",
        "keywords": ["tecnico quimico", "tecnica quimica", "quimico", "quimica"],
        "exclude": [],
        "fallback": True,
        "force_fallback": True,
        "fallback_titulo": "Técnico químico - LinkedIn",
    },
    {
        "area": "quimica",
        "categoria": "Técnico químico",
        "fuente": "Jooble",
        "url": "https://ar.jooble.org/trabajo-tecnico-quimico",
        "keywords": ["tecnico quimico", "tecnica quimica", "quimico", "quimica"],
        "exclude": ["bioquimico", "bioquimica", "farmaceutico", "farmaceutica"],
        "fallback": True,
        "fallback_titulo": "Técnico químico - Jooble",
    },
    {
        "area": "quimica",
        "categoria": "Operario",
        "fuente": "Computrabajo",
        "url": "https://ar.computrabajo.com/trabajo-de-operario-produccion",
        "keywords": ["operario", "produccion", "planta", "industria"],
        "exclude": ["chofer", "vendedor", "comercial"],
        "fallback": True,
        "fallback_titulo": "Operario de producción - Computrabajo",
    },
    {
        "area": "quimica",
        "categoria": "Control de calidad",
        "fuente": "Computrabajo",
        "url": "https://ar.computrabajo.com/trabajo-de-control-de-calidad",
        "keywords": [
            "control de calidad",
            "calidad",
            "analista de calidad",
            "inspector de calidad",
        ],
        "exclude": ["software", "qa automation", "qa manual"],
        "fallback": True,
        "fallback_titulo": "Control de calidad - Computrabajo",
    },

    # ============================================================
    # IT PRIVADA - TRAINEE / JUNIOR
    # ============================================================

    {
        "area": "it",
        "categoria": "QA Manual",
        "fuente": "Computrabajo",
        "url": "https://ar.computrabajo.com/trabajo-de-tester-qa",
        "keywords": ["qa", "tester", "testing", "manual", "junior", "trainee", "jr"],
        "exclude": ["senior", "sr", "ssr", "semi senior", "lead"],
        "fallback": True,
        "fallback_titulo": "QA Manual / Tester Junior - Computrabajo",
    },
    {
        "area": "it",
        "categoria": "QA Manual",
        "fuente": "LinkedIn",
        "url": "https://www.linkedin.com/jobs/search/?keywords=QA%20Manual%20Junior&location=Argentina",
        "keywords": ["qa manual", "tester manual", "junior", "trainee", "jr"],
        "exclude": ["senior", "sr", "ssr", "lead"],
        "fallback": True,
        "force_fallback": True,
        "fallback_titulo": "QA Manual Junior - LinkedIn",
    },
    {
        "area": "it",
        "categoria": "QA Automation",
        "fuente": "Computrabajo",
        "url": "https://ar.computrabajo.com/trabajo-de-qa-automation",
        "keywords": [
            "qa automation",
            "automation",
            "automatizacion",
            "selenium",
            "cypress",
            "playwright",
            "junior",
            "trainee",
            "jr",
        ],
        "exclude": ["senior", "sr", "ssr", "semi senior", "lead"],
        "fallback": True,
        "fallback_titulo": "QA Automation Junior - Computrabajo",
    },
    {
        "area": "it",
        "categoria": "QA Automation",
        "fuente": "LinkedIn",
        "url": "https://www.linkedin.com/jobs/search/?keywords=QA%20Automation%20Junior&location=Argentina",
        "keywords": ["qa automation", "junior", "trainee", "selenium", "cypress", "playwright"],
        "exclude": ["senior", "sr", "ssr", "lead"],
        "fallback": True,
        "force_fallback": True,
        "fallback_titulo": "QA Automation Junior - LinkedIn",
    },
    {
        "area": "it",
        "categoria": "Desarrollo",
        "fuente": "Computrabajo",
        "url": "https://ar.computrabajo.com/trabajo-de-programador-junior",
        "keywords": ["programador", "desarrollador", "developer", "junior", "trainee", "jr"],
        "exclude": ["senior", "sr", "ssr", "semi senior", "lead"],
        "fallback": True,
        "fallback_titulo": "Programador Junior - Computrabajo",
    },
    {
        "area": "it",
        "categoria": "Desarrollo",
        "fuente": "LinkedIn",
        "url": "https://www.linkedin.com/jobs/search/?keywords=Desarrollador%20Junior%20OR%20Frontend%20Junior%20OR%20React%20Junior&location=Argentina",
        "keywords": [
            "programador",
            "desarrollador",
            "developer",
            "frontend",
            "backend",
            "junior",
            "trainee",
            "jr",
        ],
        "exclude": ["senior", "sr", "ssr", "lead"],
        "fallback": True,
        "force_fallback": True,
        "fallback_titulo": "Desarrollo Junior / Frontend / React - LinkedIn",
    },

    # ============================================================
    # IT GLOBAL / SENIOR - BÚSQUEDAS DIRECTAS
    # ============================================================

    {
        "area": "it",
        "categoria": "Analista Funcional / BA Senior",
        "fuente": "LinkedIn Global",
        "url": "https://www.linkedin.com/jobs/search/?keywords=Senior%20Functional%20Analyst%20OR%20Senior%20Business%20Analyst&location=Worldwide",
        "keywords": [
            "senior functional analyst",
            "senior business analyst",
            "business analyst",
            "functional analyst",
        ],
        "exclude": [],
        "force_fallback": True,
        "fallback": True,
        "fallback_titulo": "Analista Funcional / Business Analyst Senior - LinkedIn Global",
    },
    {
        "area": "it",
        "categoria": "Analista de Negocio Senior",
        "fuente": "LinkedIn Global",
        "url": "https://www.linkedin.com/jobs/search/?keywords=Senior%20Business%20Analyst%20OR%20Senior%20Business%20Process%20Analyst&location=Worldwide",
        "keywords": [
            "senior business analyst",
            "senior business process analyst",
            "analista de negocio",
        ],
        "exclude": [],
        "force_fallback": True,
        "fallback": True,
        "fallback_titulo": "Analista de Negocio Senior - LinkedIn Global",
    },
    {
        "area": "it",
        "categoria": "DBA Senior",
        "fuente": "Indeed Remote",
        "url": "https://www.indeed.com/q-senior-database-administrator-l-remote-jobs.html",
        "keywords": [
            "senior database administrator",
            "dba senior",
            "database administrator",
            "sql server",
            "oracle",
            "postgresql",
        ],
        "exclude": [],
        "force_fallback": True,
        "fallback": True,
        "fallback_titulo": "Senior Database Administrator / DBA Senior - Indeed Remote",
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


def obtener_html(url):
    headers = {
        "User-Agent": "Mozilla/5.0 MonitorLaboral/1.0"
    }

    respuesta = requests.get(url, headers=headers, timeout=30)
    respuesta.raise_for_status()
    return respuesta.text


def texto_valido(texto, keywords, exclude):
    texto_normalizado = normalizar_texto(texto)

    if not texto_normalizado:
        return False

    for palabra in exclude:
        if normalizar_texto(palabra) in texto_normalizado:
            return False

    for palabra in keywords:
        if normalizar_texto(palabra) in texto_normalizado:
            return True

    return False


def titulo_no_util(titulo):
    titulo_normalizado = normalizar_texto(titulo)

    bloqueados = [
        "crear alerta",
        "mis alertas",
        "postularme",
        "ingresar",
        "registrarme",
        "empresas",
        "salarios",
        "blog",
        "ayuda",
        "condiciones",
        "privacidad",
        "ver ofertas",
        "buscar empleo",
        "cargar cv",
        "guardar",
        "denunciar empleo",
        "ocultar aviso",
        "mostrar oferta",
        "recibe nuevas ofertas",
    ]

    return any(palabra in titulo_normalizado for palabra in bloqueados)


def crear_id(area, titulo, url):
    base = f"portal-{area}-{titulo}-{url}"
    base = normalizar_texto(base)
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    return base[:180]


def limpiar_titulo(titulo):
    titulo = re.sub(r"\s+", " ", titulo or "").strip()
    titulo = titulo.replace("Postulado", "").replace("Vista", "").strip()
    return titulo


def extraer_descripcion_cercana(link):
    contenedor = link

    for _ in range(4):
        if contenedor.parent:
            contenedor = contenedor.parent

    texto = contenedor.get_text(" ", strip=True)
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto[:260]


def descripcion_default(area):
    if area == "salud_privada":
        return (
            "Acceso directo a búsqueda u oferta privada relacionada con Técnico/a "
            "en Esterilización, central de esterilización, clínicas, sanatorios u hospitales privados."
        )

    if area == "quimica":
        return (
            "Acceso directo a búsqueda u oferta relacionada con Técnico Químico, "
            "operario, calidad, producción o industria."
        )

    if area == "it":
        return (
            "Acceso directo a búsqueda laboral IT: QA, desarrollo, análisis funcional, "
            "Business Analyst, Analista de Negocio o DBA."
        )

    return "Oferta detectada automáticamente."


def crear_item_fallback(fuente_config, anteriores_por_id):
    titulo = fuente_config.get("fallback_titulo") or fuente_config["categoria"]
    url = fuente_config["url"]
    area = fuente_config["area"]

    id_item = crear_id(area, titulo, url)
    item_anterior = anteriores_por_id.get(id_item)

    estado = "vigente"
    fecha_detectada = hoy_argentina().isoformat()

    if not item_anterior:
        estado = "nuevo"
    else:
        fecha_detectada = item_anterior.get("fechaDetectada", fecha_detectada)

    return {
        "id": id_item,
        "titulo": titulo,
        "fuente": fuente_config["fuente"],
        "categoria": fuente_config["categoria"],
        "estado": estado,
        "fechaDetectada": fecha_detectada,
        "fechaCierre": "",
        "url": url,
        "descripcion": descripcion_default(area),
        "origen": "Búsqueda directa",
    }


def extraer_items_fuente(fuente_config, anteriores_por_id):
    print(
        f"[{fuente_config['area']}] Revisando portal: "
        f"{fuente_config['fuente']} - {fuente_config['url']}"
    )

    if fuente_config.get("force_fallback"):
        item = crear_item_fallback(fuente_config, anteriores_por_id)
        print(f"[{fuente_config['area']}] Fuente configurada como búsqueda directa.")
        return [item]

    html = obtener_html(fuente_config["url"])
    soup = BeautifulSoup(html, "html.parser")

    items = []
    links = soup.find_all("a", href=True)

    for link in links:
        titulo = limpiar_titulo(link.get_text(" ", strip=True))
        href = link.get("href", "")

        if not titulo or len(titulo) < 5:
            continue

        if titulo_no_util(titulo):
            continue

        descripcion = extraer_descripcion_cercana(link)
        texto_para_filtrar = f"{titulo} {descripcion}"

        if not texto_valido(
            texto_para_filtrar,
            fuente_config["keywords"],
            fuente_config["exclude"],
        ):
            continue

        url_final = urljoin(fuente_config["url"], href)

        if not url_final.startswith("http"):
            continue

        id_item = crear_id(fuente_config["area"], titulo, url_final)
        item_anterior = anteriores_por_id.get(id_item)

        estado = "vigente"
        fecha_detectada = hoy_argentina().isoformat()

        if not item_anterior:
            estado = "nuevo"
        else:
            fecha_detectada = item_anterior.get("fechaDetectada", fecha_detectada)

        item = {
            "id": id_item,
            "titulo": titulo,
            "fuente": fuente_config["fuente"],
            "categoria": fuente_config["categoria"],
            "estado": estado,
            "fechaDetectada": fecha_detectada,
            "fechaCierre": "",
            "url": url_final,
            "descripcion": descripcion if descripcion else descripcion_default(fuente_config["area"]),
            "origen": "Privado",
        }

        items.append(item)

    items = quitar_duplicados(items)

    if not items and fuente_config.get("fallback"):
        items.append(crear_item_fallback(fuente_config, anteriores_por_id))

    print(f"[{fuente_config['area']}] Encontrados en portal: {len(items)}")

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
            item.get("categoria", ""),
            item.get("fechaDetectada", ""),
            item.get("titulo", ""),
        ),
    )


def actualizar_area(area):
    archivo_salida = ARCHIVOS_SALIDA[area]
    existentes = cargar_json(archivo_salida)

    anteriores_por_id = {
        item.get("id"): item
        for item in existentes
        if item.get("id")
    }

    resultados_portales = []

    for fuente_config in FUENTES:
        if fuente_config["area"] != area:
            continue

        try:
            items = extraer_items_fuente(fuente_config, anteriores_por_id)
            resultados_portales.extend(items)

        except Exception as error:
            print(f"[{area}] Error revisando {fuente_config['url']}: {error}")

            if fuente_config.get("fallback"):
                item = crear_item_fallback(fuente_config, anteriores_por_id)
                resultados_portales.append(item)
                print(f"[{area}] Se agregó búsqueda directa por fallback.")

    combinado = existentes + resultados_portales
    combinado = quitar_duplicados(combinado)
    combinado = ordenar_items(combinado)
    combinado = combinado[:MAX_ITEMS_POR_AREA]

    guardar_json(archivo_salida, combinado)

    nuevos = [item for item in combinado if item.get("estado") == "nuevo"]

    print(f"[{area}] Archivo actualizado: {archivo_salida}")
    print(f"[{area}] Total: {len(combinado)}")
    print(f"[{area}] Nuevos: {len(nuevos)}")


def main():
    print("Iniciando revisión de portales laborales...")

    actualizar_area("salud_privada")
    actualizar_area("quimica")
    actualizar_area("it")

    print("Revisión de portales finalizada.")


if __name__ == "__main__":
    main()