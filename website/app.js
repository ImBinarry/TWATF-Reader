"use strict";
const $ = (s) => document.querySelector(s);
let catalog,
  version = "revised",
  current = null,
  onlyBookmarks = false,
  loadId = 0,
  restoring = false;
let state = {
  version: "revised",
  progress: {},
  bookmarks: [],
  theme: "oled",
  size: 20,
  font: "serif",
};
try {
  Object.assign(
    state,
    JSON.parse(localStorage.getItem("twatf-reader") || "{}"),
  );
} catch {}
version = ["first", "revised"].includes(state.version)
  ? state.version
  : "revised";
function save() {
  try {
    localStorage.setItem("twatf-reader", JSON.stringify(state));
  } catch {}
}
function toast(text) {
  $("#toast").textContent = text;
  $("#toast").classList.add("show");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => $("#toast").classList.remove("show"), 2500);
}
const fonts = {
  serif: "Georgia, serif",
  palatino: 'Palatino, "Palatino Linotype", "Book Antiqua", serif',
  times: '"Times New Roman", Times, serif',
  "sans-serif": "system-ui, sans-serif",
  arial: "Arial, Helvetica, sans-serif",
  verdana: "Verdana, Geneva, sans-serif",
  mono: 'ui-monospace, "Courier New", monospace',
};
const covers = {
  first: "assets/first_upscaled.png",
  revised: "assets/revised_upscaled_2.png",
};
const epubs = {
  first: "assets/The_World_After_The_Fall_First_Edition.epub",
  revised: "assets/The_World_After_The_Fall_Revised.epub",
};
const checkIsIndex = () =>
  /(?:^|\/)chapters(?:\.html)?\/?$/i.test(location.pathname) ||
  location.hash === "#chapters";
let reverseIndex = false;
function indexRender() {
  if (!catalog) return;
  $("#index-cover").src = covers[version];
  $("#index-version").value = version;
  $("#index-download").href = epubs[version];
  const p = state.progress[version];
  $("#index-resume").href = `index.html#read/${version}/${p?.number || 1}`;
  $("#index-resume").textContent = p
    ? `Continue · Chapter ${p.number} →`
    : "Start reading →";
  $("#index-description").textContent =
    `${version === "first" ? "First edition" : "Revised edition"} · ${catalog[version].length} chapters`;
  const q = $("#index-search").value.trim().toLowerCase();
  let rows = catalog[version].filter(
    (c) => c.title.toLowerCase().includes(q) || String(c.number) === q,
  );
  if (reverseIndex) rows = rows.slice().reverse();
  $("#index-count").textContent = rows.length + " chapters";
  $("#index-results").replaceChildren();
  if (!rows.length) {
    const p = document.createElement("p");
    p.className = "summary";
    p.textContent = "No chapters match your search.";
    $("#index-results").append(p);
  }
  rows.forEach((c) => {
    const a = document.createElement("a");
    a.className = "chapter-card";
    a.href = `index.html#read/${version}/${c.number}`;
    if (p?.number === c.number) {
      a.classList.add("last-read");
      a.setAttribute("aria-current", "true");
    }
    const label = document.createElement("small");
    label.textContent = `CHAPTER ${c.number}`;
    const h = document.createElement("h3");
    h.textContent = c.title.replace(/^Chapter \d+\s*[-:]?\s*/, "") || c.title;
    const badge = document.createElement("span");
    badge.className = "chapter-badge";
    badge.textContent =
      p?.number === c.number
        ? "LAST READ"
        : `${Math.max(1, Math.round(c.words / 220))} MIN`;
    a.append(label, h, badge);
    $("#index-results").append(a);
  });
}
function goIndex() {
  storePosition();
  location.href = `chapters.html?edition=${version}`;
}
function support(kind) {
  const donations = kind === "donations";
  const cfg = window.READER_CONFIG || {};
  const url = donations ? cfg.donationUrl : cfg.contributionUrl;
  $("#support-title").textContent = donations
    ? "Support Home"
    : "Contribute to Home";
  $("#support-copy").textContent = donations
    ? "Enjoying the reader? Support helps keep this Home available."
    : "Help improve the reading experience. Report a typo, suggest an improvement, or contribute to the website.";
  const valid = typeof url === "string" && /^https:\/\//i.test(url);
  $("#support-link").hidden = !valid;
  $("#support-link").href = valid ? url : "#";
  $("#support-link").textContent = donations
    ? "Make a donation ↗"
    : "Contribute ↗";
  $("#support-status").textContent = valid
    ? "Thank you for helping this Home grow."
    : donations
      ? "Donations are not available yet."
      : "A contribution link will be added soon.";
  $("#support").showModal();
}
function settings() {
  document.body.dataset.theme = state.theme;
  document.documentElement.style.setProperty("--size", state.size + "px");
  document.documentElement.style.setProperty(
    "--font",
    fonts[state.font] || fonts.serif,
  );
  $("#theme").value = state.theme;
  $("#size").textContent = state.size + " px";
  $("#size-down").disabled = state.size <= 16;
  $("#size-up").disabled = state.size >= 30;
  $("#font").value = state.font;
  window.readerComments?.theme();
}
function choose(v) {
  version = v;
  state.version = v;
  save();
  document.querySelectorAll("[data-version]").forEach((b) => {
    b.classList.toggle("selected", b.dataset.version === v);
    b.setAttribute("aria-pressed", b.dataset.version === v);
  });
  $("#cover").src = covers[v];
  $("#download").href = epubs[v];
  $("#list-version").value = v;
  const p = state.progress[v];
  $("#start").innerHTML = "Chapters <span>↗</span>";
  $("#resume-note").textContent = p
    ? `Continue ${v} edition · Chapter ${p.number}. Your place is saved on this device.`
    : "Your place is saved automatically on this device.";
}
function list() {
  if (!catalog) return;
  const selected = $("#list-version").value;
  const q = $("#search").value.toLowerCase().trim();
  const rows = catalog[selected].filter(
    (c) =>
      (!onlyBookmarks || state.bookmarks.includes(selected + ":" + c.number)) &&
      `${c.number} ${c.title}`.toLowerCase().includes(q),
  );
  $("#chapter-results").replaceChildren();
  $("#count").textContent = rows.length
    ? `${rows.length} ${onlyBookmarks ? "bookmarks" : "chapters"} · ${selected} edition`
    : onlyBookmarks
      ? "No bookmarks here yet. Save one while reading."
      : "No chapters match your search.";
  const reading = location.hash.match(/^#read\/(first|revised)\/(\d+)$/);
  rows.forEach((c) => {
    const button = document.createElement("button");
    button.className = "popup-chapter";
    const number = document.createElement("span");
    number.className = "popup-number";
    number.textContent = "#" + c.number;
    const title = document.createElement("span");
    title.className = "popup-title";
    title.textContent =
      c.title.replace(/^Chapter \d+\s*[-:]?\s*/, "") || c.title;
    button.append(number, title);
    if (reading && reading[1] === selected && Number(reading[2]) === c.number) {
      button.classList.add("current-chapter");
      button.setAttribute("aria-current", "page");
    }
    if (state.bookmarks.includes(selected + ":" + c.number)) {
      const star = document.createElement("span");
      star.className = "popup-star";
      star.textContent = "★";
      star.setAttribute("aria-label", "Bookmarked");
      button.append(star);
    }
    button.onclick = () => {
      storePosition();
      $("#contents").close();
      const hash = `#read/${selected}/${c.number}`;
      if (checkIsIndex()) location.href = "index.html" + hash;
      else location.hash = hash;
    };
    $("#chapter-results").append(button);
  });
}
function openList(bookmarks = false) {
  storePosition();
  onlyBookmarks = bookmarks;
  $("#list-title").textContent = bookmarks ? "Your bookmarks" : "Chapters";
  $("#search").value = "";
  $("#list-version").value = version;
  list();
  $("#contents").showModal();
  document.body.classList.add("chapter-popup-open");
  $("#search").focus({ preventScroll: true });
  const active = $("#chapter-results .current-chapter");
  $("#chapter-results").scrollTop = active
    ? active.offsetTop - $("#chapter-results").offsetTop - 80
    : 0;
}
function mark() {
  if (!current) return;
  const on = state.bookmarks.includes(version + ":" + current.number);
  $("#bookmark").textContent = on ? "★ Bookmarked" : "☆ Bookmark";
  $("#bookmark").setAttribute("aria-pressed", on);
}
function storePosition() {
  if (!current || restoring || $("#reader").hidden) return;
  const max = Math.max(1, document.documentElement.scrollHeight - innerHeight);
  const activeVersion = location.hash.split("/")[1];
  if (!["first", "revised"].includes(activeVersion)) return;
  state.progress[activeVersion] = {
    number: current.number,
    ratio: Math.min(1, scrollY / max),
  };
  save();
}
async function route() {
  const id = ++loadId;
  window.readerComments.clear();
  if (checkIsIndex()) {
    current = null;
    $("#home").hidden = true;
    $("#reader").hidden = true;
    $("#chapter-index").hidden = false;
    const v = new URLSearchParams(location.search).get("edition");
    if (["first", "revised"].includes(v)) choose(v);
    indexRender();
    return;
  }
  const match = location.hash.match(/^#read\/(first|revised)\/(\d+)$/);
  if (!match) {
    current = null;
    $("#home").hidden = false;
    $("#chapter-index").hidden = true;
    $("#reader").hidden = true;
    choose(version);
    document.title = "The World After the Fall — Reader";
    scrollTo(0, 0);
    return;
  }
  const v = match[1],
    n = Number(match[2]),
    entry = catalog[v].find((c) => c.number === n);
  if (!entry) {
    toast("This chapter does not exist.");
    location.hash = "";
    return;
  }
  choose(v);
  current = entry;
  $("#home").hidden = true;
  $("#chapter-index").hidden = true;
  $("#reader").hidden = false;
  $("#chapter").textContent = "Opening chapter…";
  $("#edition-label").textContent =
    `${v === "first" ? "First Edition" : "Revised"} / ${n} of ${catalog[v].length}`;
  const idx = catalog[v].indexOf(entry);
  $("#prev").disabled = idx === 0;
  $("#next").disabled = idx === catalog[v].length - 1;
  $("#prev").onclick = () => navigate(-1);
  $("#next").onclick = () => navigate(1);
  mark();
  restoring = true;
  try {
    const res = await fetch(entry.path);
    if (!res.ok) throw Error();
    const data = await res.json();
    if (id !== loadId) return;
    $("#chapter").innerHTML = data.html;
    window.readerComments.show(v, n);
    document.title = data.title + " — " + v + " · TWATF";
    $("#end-note").textContent =
      idx === catalog[v].length - 1
        ? "You have reached the end of this edition."
        : "";
    const prior = state.progress[v];
    const ratio = prior?.number === n ? prior.ratio || 0 : 0;
    state.progress[v] = { number: n, ratio };
    save();
    requestAnimationFrame(() => {
      if (id !== loadId) return;
      scrollTo(
        0,
        ratio *
          Math.max(0, document.documentElement.scrollHeight - innerHeight),
      );
      restoring = false;
    });
  } catch {
    restoring = false;
    $("#chapter").textContent =
      "This chapter could not load. Check your connection and reload the page.";
  }
}
function navigate(delta) {
  storePosition();
  const a = catalog[version],
    i = a.findIndex((c) => c.number === current.number),
    c = a[i + delta];
  if (c) location.hash = `read/${version}/${c.number}`;
}
$("#start").onclick = goIndex;
document
  .querySelectorAll("[data-version]")
  .forEach((b) => (b.onclick = () => choose(b.dataset.version)));
$("#chapter-list").onclick = () => openList();
$("#bookmarks").onclick = () => openList(true);
$("#back").onclick = () => {
  storePosition();
  location.hash = "";
};
$(".brand").href = "index.html";
$(".brand").onclick = storePosition;
$("#settings").onclick = () => $("#preferences").showModal();
document
  .querySelectorAll("[data-close]")
  .forEach((b) => (b.onclick = () => $("#" + b.dataset.close).close()));
$("#search").oninput = list;
$("#list-version").onchange = () => {
  list();
  $("#chapter-results").scrollTop = 0;
};
$("#bookmark").onclick = () => {
  const key = version + ":" + current.number;
  state.bookmarks = state.bookmarks.includes(key)
    ? state.bookmarks.filter((x) => x !== key)
    : [...state.bookmarks, key];
  save();
  mark();
};
["theme", "font"].forEach(
  (k) =>
    ($("#" + k).oninput = (e) => {
      state[k] = k === "size" ? Number(e.target.value) : e.target.value;
      settings();
      save();
    }),
);
$("#contents").addEventListener("close", () =>
  document.body.classList.remove("chapter-popup-open"),
);
addEventListener("hashchange", () => {
  if (catalog) route();
});
let timer;
addEventListener(
  "scroll",
  () => {
    clearTimeout(timer);
    timer = setTimeout(storePosition, 150);
  },
  { passive: true },
);
addEventListener("pagehide", storePosition);
addEventListener("keydown", (e) => {
  if (
    !current ||
    document.querySelector("dialog[open]") ||
    /INPUT|SELECT|TEXTAREA/.test(e.target.tagName)
  )
    return;
  if (e.key === "ArrowRight") navigate(1);
  if (e.key === "ArrowLeft") navigate(-1);
});
$("#index-search").oninput = indexRender;
$("#index-sort").onclick = () => {
  reverseIndex = !reverseIndex;
  $("#index-sort").setAttribute(
    "aria-label",
    reverseIndex ? "Sort chapters ascending" : "Sort chapters descending",
  );
  indexRender();
};
$("#index-version").onchange = (e) => {
  choose(e.target.value);
  history.replaceState(null, "", `chapters.html?edition=${version}`);
  indexRender();
};
settings();
choose(version);
fetch("data/catalog.json")
  .then((r) => {
    if (!r.ok) throw Error();
    return r.json();
  })
  .then((c) => {
    catalog = c;
    route();
  })
  .catch(() => {
    $("#start").disabled = true;
    $("#resume-note").textContent =
      "Unable to load the library. Please reload when your connection returns.";
  });

function resizeText(delta) {
  state.size = Math.max(16, Math.min(30, Number(state.size) + delta));
  settings();
  save();
}
$("#size-down").onclick = () => resizeText(-1);
$("#size-up").onclick = () => resizeText(1);
