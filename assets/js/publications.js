/**
 * Publications renderer.
 *
 * Data lives in /publications.json (repo root). To add a paper, add one object
 * there. Fields:
 *   category : "journal" | "conference" | "manuscript"  (required)
 *   title    : string   (required)
 *   url      : string   (title link; defaults to "#")
 *   authors  : string[] (your name "Kishen N Gowda" is auto-bolded)
 *   year     : number   (required; used for sorting, newest first)
 *   selected : boolean  (optional; if true, shown on the homepage)
 *   venue    : string   (optional; e.g. "NeurIPS, 2024")
 *   venueUrl : string   (optional; makes the venue text a link)
 *   links    : { label, url }[]  (optional; e.g. { label: "ArXiv", url: "..." })
 *
 * Ordering: newest year first; ties broken by position in the file, where an
 * entry appearing LATER in the file has higher priority (shown first).
 *
 * Pages opt in via container ids:
 *   #pubs-selected                         -> selected entries, all categories
 *   #pubs-journal / -conference / -manuscript -> all entries of that category
 */

const SELF_NAME = "Kishen N Gowda";
const LINK_SEPARATOR = "&nbsp;&nbsp;&nbsp; ";
const DATA_URL = "publications.json";
const CATEGORIES = ["journal", "conference", "manuscript"];

function renderAuthors(authors) {
  return authors
    .map((name) => (name === SELF_NAME ? `<span class="self">${name}</span>` : name))
    .join(", ");
}

function renderVenue(pub) {
  if (!pub.venue) return "";
  const venueText = pub.venueUrl
    ? `<a href="${pub.venueUrl}">${pub.venue}</a>`
    : pub.venue;
  return `    <p class="card-text">${venueText}</p>\n`;
}

function renderLinks(pub) {
  if (!pub.links || pub.links.length === 0) return "";
  const linksText = pub.links
    .map((link) => `${link.label}: <a href="${link.url}"><u>Link</u></a>`)
    .join(LINK_SEPARATOR);
  return `    <p class="card-text">${linksText} </p>\n`;
}

function renderCard(pub) {
  const url = pub.url || "#";
  return (
    `<div class="card w-100 mb-2">\n` +
    `  <div class="card-body">\n` +
    `    <h4 class="card-title"><a href="${url}">${pub.title}</a></h4>\n` +
    `    <h6 class="card-title">${renderAuthors(pub.authors)}</h6>\n` +
    renderVenue(pub) +
    renderLinks(pub) +
    `  </div>\n` +
    `</div>`
  );
}

// Newest year first; ties: later position in the source file wins (shown first).
function sortForDisplay(list) {
  return list
    .slice()
    .sort((a, b) => (b.year || 0) - (a.year || 0) || b._index - a._index);
}

function fillContainer(container, pubs) {
  if (!container) return;
  if (pubs.length === 0) {
    const box = container.closest(".post-box") || container;
    box.style.display = "none";
    return;
  }
  sortForDisplay(pubs).forEach((pub) => {
    container.insertAdjacentHTML("beforeend", renderCard(pub));
  });
}

function renderPublications(publications) {
  publications.forEach((pub, i) => {
    pub._index = i;
  });

  const selectedContainer = document.getElementById("pubs-selected");
  if (selectedContainer) {
    fillContainer(
      selectedContainer,
      publications.filter((pub) => pub.selected === true)
    );
  }

  CATEGORIES.forEach((category) => {
    const container = document.getElementById("pubs-" + category);
    fillContainer(
      container,
      publications.filter((pub) => pub.category === category)
    );
  });
}

document.addEventListener("DOMContentLoaded", function () {
  fetch(DATA_URL)
    .then((response) => {
      if (!response.ok) throw new Error("HTTP " + response.status);
      return response.json();
    })
    .then(renderPublications)
    .catch((err) => {
      console.error("Could not load " + DATA_URL + ":", err);
    });
});
