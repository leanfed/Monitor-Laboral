const areas = {
  salud: {
    title: "Salud",
    description:
      "Ofertas privadas de Técnico/a en Esterilización, central de esterilización, clínicas, sanatorios y hospitales privados.",
    file: "data/salud.json",
    emptyMessage: "No hay ofertas privadas vigentes de esterilización.",
  },
  quimica: {
    title: "Química",
    description:
      "Ofertas privadas para técnico químico, operario, producción, packaging y control de calidad.",
    file: "data/quimica.json",
    emptyMessage: "No hay ofertas vigentes para Química.",
  },
  it: {
    title: "IT",
    description:
      "Ofertas para desarrollo trainee/junior y QA manual/automation trainee-junior.",
    file: "data/it.json",
    emptyMessage: "No hay ofertas vigentes para IT.",
  },
  concursos_caba: {
    title: "Concursos CABA",
    description:
      "Concursos de hospitales del Gobierno de la Ciudad para Técnico/a en Esterilización y Técnico Químico.",
    file: "data/concursos_caba.json",
    emptyMessage: "No hay concursos CABA vigentes.",
  },
};

const homeSection = document.getElementById("homeSection");
const resultsSection = document.getElementById("resultsSection");
const sectionTitle = document.getElementById("sectionTitle");
const sectionDescription = document.getElementById("sectionDescription");
const cardsContainer = document.getElementById("cardsContainer");
const filtersContainer = document.getElementById("filtersContainer");
const statusSummary = document.getElementById("statusSummary");
const lastUpdate = document.getElementById("lastUpdate");

const backButton = document.getElementById("backButton");
const homeLink = document.getElementById("homeLink");
const themeToggle = document.getElementById("themeToggle");

let currentItems = [];
let currentFilter = "Todos";
let currentAreaKey = "";

document.addEventListener("DOMContentLoaded", () => {
  setupTheme();
  setupNavigation();

  const today = new Date().toLocaleDateString("es-AR");
  lastUpdate.textContent = today;
});

function setupNavigation() {
  const areaButtons = document.querySelectorAll(".area-card");

  areaButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const area = button.dataset.area;
      loadArea(area);
    });
  });

  backButton.addEventListener("click", showHome);

  homeLink.addEventListener("click", (event) => {
    event.preventDefault();
    showHome();
  });
}

async function loadArea(areaKey) {
  const area = areas[areaKey];

  if (!area) return;

  currentAreaKey = areaKey;
  currentFilter = "Todos";

  sectionTitle.textContent = area.title;
  sectionDescription.textContent = area.description;

  homeSection.classList.add("d-none");
  resultsSection.classList.remove("d-none");

  cardsContainer.innerHTML = `
    <div class="col-12">
      <div class="empty-state">
        Cargando publicaciones...
      </div>
    </div>
  `;

  try {
    const response = await fetch(area.file);

    if (!response.ok) {
      throw new Error("No se pudo cargar el archivo JSON.");
    }

    const data = await response.json();

    currentItems = Array.isArray(data) ? data : [];

    renderSummary(currentItems);
    renderFilters(currentItems);
    renderCards(currentItems);
  } catch (error) {
    cardsContainer.innerHTML = `
      <div class="col-12">
        <div class="empty-state">
          No se pudieron cargar los datos. Revisá que el archivo JSON exista y esté bien escrito.
        </div>
      </div>
    `;

    console.error(error);
  }
}

function showHome() {
  resultsSection.classList.add("d-none");
  homeSection.classList.remove("d-none");

  currentItems = [];
  currentFilter = "Todos";
  currentAreaKey = "";

  cardsContainer.innerHTML = "";
  filtersContainer.innerHTML = "";
  statusSummary.innerHTML = "";
}

function renderSummary(items) {
  const total = items.length;
  const nuevos = items.filter((item) => item.estado === "nuevo").length;
  const vigentes = items.filter((item) => item.estado === "vigente").length;

  statusSummary.innerHTML = `
    <div class="summary-card">
      <strong>${total}</strong>
      <span>Total</span>
    </div>

    <div class="summary-card">
      <strong>${nuevos}</strong>
      <span>Nuevos</span>
    </div>

    <div class="summary-card">
      <strong>${vigentes}</strong>
      <span>Vigentes</span>
    </div>
  `;
}

function renderFilters(items) {
  const categories = ["Todos", ...new Set(items.map((item) => item.categoria))];

  filtersContainer.innerHTML = categories
    .map((category) => {
      const activeClass =
        category === currentFilter ? "btn-primary" : "btn-outline-primary";

      return `
        <button class="btn ${activeClass} btn-sm filter-btn" data-filter="${category}">
          ${category}
        </button>
      `;
    })
    .join("");

  const filterButtons = document.querySelectorAll(".filter-btn");

  filterButtons.forEach((button) => {
    button.addEventListener("click", () => {
      currentFilter = button.dataset.filter;

      const filteredItems =
        currentFilter === "Todos"
          ? currentItems
          : currentItems.filter((item) => item.categoria === currentFilter);

      renderFilters(currentItems);
      renderCards(filteredItems);
    });
  });
}

function renderCards(items) {
  if (!items.length) {
    const area = areas[currentAreaKey];

    cardsContainer.innerHTML = `
      <div class="col-12">
        <div class="empty-state">
          ${area ? area.emptyMessage : "No hay publicaciones vigentes."}
        </div>
      </div>
    `;
    return;
  }

  cardsContainer.innerHTML = items
    .map((item) => {
      const badgeClass = getBadgeClass(item.estado);
      const estadoTexto = getEstadoTexto(item.estado);

      const periodoConcurso =
        item.fechaInscripcion && item.fechaCierre
          ? `<span>Inscripción: desde ${formatDate(item.fechaInscripcion)} hasta ${formatDate(item.fechaCierre)}</span>`
          : item.fechaCierre
            ? `<span>Inscripción: hasta ${formatDate(item.fechaCierre)}</span>`
            : `<span>Sin fecha de cierre informada</span>`;

      return `
        <div class="col-12 col-md-6 col-lg-4">
          <a class="job-link" href="${item.url}" target="_blank" rel="noopener noreferrer">
            <article class="job-card">
              <div class="job-card-body">
                <span class="badge-soft ${badgeClass}">
                  ${estadoTexto}
                </span>

                <h3>${item.titulo}</h3>

                <p class="mb-3">
                  ${item.descripcion || ""}
                </p>

                <div class="job-meta">
                  <span>Fuente: ${item.fuente || "Sin fuente informada"}</span>
                  <span>Categoría: ${item.categoria || "Sin categoría"}</span>
                  <span>Detectado: ${formatDate(item.fechaDetectada)}</span>
                  ${periodoConcurso}
                </div>

                <div class="job-footer">
                  <span>Abrir publicación</span>
                  <span>↗</span>
                </div>
              </div>
            </article>
          </a>
        </div>
      `;
    })
    .join("");
}

function getBadgeClass(estado) {
  if (estado === "nuevo") return "badge-new";
  if (estado === "vigente") return "badge-active";
  if (estado === "vencido") return "badge-expired";

  return "badge-active";
}

function getEstadoTexto(estado) {
  if (estado === "nuevo") return "Nuevo";
  if (estado === "vigente") return "Vigente";
  if (estado === "vencido") return "Vencido";

  return estado || "Vigente";
}

function formatDate(dateString) {
  if (!dateString) return "Sin fecha";

  const [year, month, day] = dateString.split("-");

  if (!year || !month || !day) return dateString;

  return `${day}/${month}/${year}`;
}

function setupTheme() {
  const savedTheme = localStorage.getItem("monitor-theme") || "light";

  document.documentElement.setAttribute("data-bs-theme", savedTheme);
  updateThemeButton(savedTheme);

  themeToggle.addEventListener("click", () => {
    const currentTheme = document.documentElement.getAttribute("data-bs-theme");
    const newTheme = currentTheme === "dark" ? "light" : "dark";

    document.documentElement.setAttribute("data-bs-theme", newTheme);
    localStorage.setItem("monitor-theme", newTheme);

    updateThemeButton(newTheme);
  });
}

function updateThemeButton(theme) {
  themeToggle.textContent =
    theme === "dark" ? "☀️ Modo claro" : "🌙 Modo oscuro";
}