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

const ITEMS_PER_PAGE = 9;

const homeSection = document.getElementById("homeSection");
const resultsSection = document.getElementById("resultsSection");
const sectionTitle = document.getElementById("sectionTitle");
const sectionDescription = document.getElementById("sectionDescription");
const cardsContainer = document.getElementById("cardsContainer");
const filtersContainer = document.getElementById("filtersContainer");
const statusSummary = document.getElementById("statusSummary");
const paginationContainer = document.getElementById("paginationContainer");
const lastUpdate = document.getElementById("lastUpdate");

const backButton = document.getElementById("backButton");
const homeLink = document.getElementById("homeLink");
const themeToggle = document.getElementById("themeToggle");

let currentItems = [];
let currentFilteredItems = [];
let currentFilter = "Todos";
let currentAreaKey = "";
let currentPage = 1;

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
  currentPage = 1;

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

  paginationContainer.innerHTML = "";

  try {
    const response = await fetch(area.file);

    if (!response.ok) {
      throw new Error("No se pudo cargar el archivo JSON.");
    }

    const data = await response.json();

    currentItems = Array.isArray(data) ? data : [];
    currentFilteredItems = currentItems;

    renderSummary(currentItems);
    renderFilters(currentItems);
    renderCards(currentFilteredItems);
  } catch (error) {
    cardsContainer.innerHTML = `
      <div class="col-12">
        <div class="empty-state">
          No se pudieron cargar los datos. Revisá que el archivo JSON exista y esté bien escrito.
        </div>
      </div>
    `;

    paginationContainer.innerHTML = "";
    console.error(error);
  }
}

function showHome() {
  resultsSection.classList.add("d-none");
  homeSection.classList.remove("d-none");

  currentItems = [];
  currentFilteredItems = [];
  currentFilter = "Todos";
  currentAreaKey = "";
  currentPage = 1;

  cardsContainer.innerHTML = "";
  filtersContainer.innerHTML = "";
  statusSummary.innerHTML = "";
  paginationContainer.innerHTML = "";

  window.scrollTo({
    top: 0,
    behavior: "smooth",
  });
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
      currentPage = 1;

      currentFilteredItems =
        currentFilter === "Todos"
          ? currentItems
          : currentItems.filter((item) => item.categoria === currentFilter);

      renderFilters(currentItems);
      renderCards(currentFilteredItems);
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

    paginationContainer.innerHTML = "";
    return;
  }

  const totalPages = Math.ceil(items.length / ITEMS_PER_PAGE);

  if (currentPage > totalPages) {
    currentPage = totalPages;
  }

  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = startIndex + ITEMS_PER_PAGE;
  const paginatedItems = items.slice(startIndex, endIndex);

  cardsContainer.innerHTML = paginatedItems
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

  renderPagination(items.length);
}

function renderPagination(totalItems) {
  const totalPages = Math.ceil(totalItems / ITEMS_PER_PAGE);

  if (totalPages <= 1) {
    paginationContainer.innerHTML = "";
    return;
  }

  const pages = getVisiblePages(totalPages);

  paginationContainer.innerHTML = `
    <div class="pagination-card">
      <button 
        class="pagination-btn" 
        data-page-action="prev"
        ${currentPage === 1 ? "disabled" : ""}
      >
        ← Anterior
      </button>

      <div class="pagination-pages">
        ${pages
          .map((page) => {
            if (page === "...") {
              return `<span class="pagination-dots">...</span>`;
            }

            const activeClass = page === currentPage ? "active" : "";

            return `
              <button class="pagination-number ${activeClass}" data-page="${page}">
                ${page}
              </button>
            `;
          })
          .join("")}
      </div>

      <button 
        class="pagination-btn" 
        data-page-action="next"
        ${currentPage === totalPages ? "disabled" : ""}
      >
        Siguiente →
      </button>
    </div>

    <p class="pagination-info">
      Página ${currentPage} de ${totalPages} · ${totalItems} publicaciones
    </p>
  `;

  const prevButton = paginationContainer.querySelector('[data-page-action="prev"]');
  const nextButton = paginationContainer.querySelector('[data-page-action="next"]');
  const pageButtons = paginationContainer.querySelectorAll("[data-page]");

  prevButton.addEventListener("click", () => {
    if (currentPage > 1) {
      currentPage--;
      renderCards(currentFilteredItems);
      scrollToResultsTop();
    }
  });

  nextButton.addEventListener("click", () => {
    if (currentPage < totalPages) {
      currentPage++;
      renderCards(currentFilteredItems);
      scrollToResultsTop();
    }
  });

  pageButtons.forEach((button) => {
    button.addEventListener("click", () => {
      currentPage = Number(button.dataset.page);
      renderCards(currentFilteredItems);
      scrollToResultsTop();
    });
  });
}

function getVisiblePages(totalPages) {
  if (totalPages <= 5) {
    return Array.from({ length: totalPages }, (_, index) => index + 1);
  }

  const pages = [1];

  if (currentPage > 3) {
    pages.push("...");
  }

  const start = Math.max(2, currentPage - 1);
  const end = Math.min(totalPages - 1, currentPage + 1);

  for (let page = start; page <= end; page++) {
    pages.push(page);
  }

  if (currentPage < totalPages - 2) {
    pages.push("...");
  }

  pages.push(totalPages);

  return pages;
}

function scrollToResultsTop() {
  resultsSection.scrollIntoView({
    behavior: "smooth",
    block: "start",
  });
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