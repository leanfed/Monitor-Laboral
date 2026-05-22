# Monitor Laboral

Monitor Laboral es una página web pensada para consultar oportunidades laborales y concursos públicos de forma rápida, ordenada y desde el celular.

El objetivo principal del proyecto es evitar tener que entrar manualmente a varios portales, escribir búsquedas repetidas o revisar muchos enlaces uno por uno. La aplicación organiza la información por áreas de interés y muestra cada resultado como una tarjeta clickeable que lleva directamente a la publicación original.

## Sitio publicado

https://leanfed.github.io/Monitor-Laboral/

## ¿Qué busca la página?

La página está organizada en cuatro secciones principales:

### Salud

Ofertas privadas relacionadas con:

- Técnico/a en Esterilización
- Central de esterilización
- Clínicas
- Sanatorios
- Hospitales privados
- Portales laborales con búsquedas ya preparadas

Esta sección está enfocada únicamente en el ámbito privado para no mezclarla con los concursos públicos.

### Química

Ofertas relacionadas con:

- Técnico químico
- Operario de producción
- Control de calidad
- Packaging
- Industria alimenticia
- Industria farmacéutica
- Producción industrial

### IT

Ofertas relacionadas con:

- QA Manual trainee / junior
- QA Automation trainee / junior
- Tester QA
- Desarrollo trainee / junior
- Programador junior
- Frontend junior
- React junior
- Analista Funcional / Business Analyst Senior
- Analista de Negocio Senior
- DBA Senior
- Búsquedas globales y remotas

### Concursos CABA

Concursos públicos de hospitales del Gobierno de la Ciudad de Buenos Aires.

Actualmente contempla:

- Técnico/a en Esterilización
- Técnico Químico en hospitales GCBA

Los concursos solo se muestran si tienen fecha de cierre conocida y todavía están vigentes. Cuando no hay concursos activos, la sección muestra el mensaje correspondiente.

## ¿Cómo se usa?

1. Entrar a la página.
2. Elegir una de las áreas principales:
   - Salud
   - Química
   - IT
   - Concursos CABA
3. Revisar las tarjetas disponibles.
4. Tocar una tarjeta para abrir la publicación original.
5. Usar los filtros internos para ver una categoría específica.

No hace falta escribir búsquedas manuales. Las búsquedas ya están definidas dentro del proyecto.

## Características principales

- Diseño responsive.
- Optimizado para celular.
- Modo claro y modo oscuro.
- Interfaz limpia y moderna.
- Tarjetas clickeables.
- Filtros por categoría.
- Datos cargados desde archivos JSON.
- Scripts en Python para actualizar la información.
- Compatible con GitHub Pages.
- Preparado para automatizar revisiones con GitHub Actions.

## Tecnologías utilizadas

- HTML
- CSS
- JavaScript
- Bootstrap
- Python
- BeautifulSoup
- Requests
- GitHub Pages
- GitHub Actions

## Estructura del proyecto

```text
monitor-laboral/
│
├── index.html
├── style.css
├── app.js
├── requirements.txt
│
├── data/
│   ├── salud.json
│   ├── quimica.json
│   ├── it.json
│   └── concursos_caba.json
│
├── config/
│   └── fuentes_alertas.json
│
├── scripts/
│   ├── monitor_gcba.py
│   ├── monitor_alertas.py
│   ├── monitor_portales.py
│   └── monitor_it_global.py
│
└── .github/
    └── workflows/
        └── monitor.yml