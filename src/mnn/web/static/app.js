"use strict";

const I18N = {
  en: {
    brand: "Vocab",
    search_ph: "Search kanji / kana / meaning…",
    f_kanji: "has kanji",
    f_sentence: "has sentence",
    f_mnemonic: "has mnemonic",
    f_learned: "hide learned",
    start_here: "📖 Start Here",
    all_lessons: "All lessons",
    lesson_prefix: "Lesson",
    cards_suffix: "cards",
    no_matches: "No matches.",
    by: "by",
    word_audio: "🔊 word",
    sentence_audio: "🔊 sentence",
    learned: "✓ learned",
    mark_learned: "mark learned",
    about: "About this deck",
  },
  bn: {
    brand: "শব্দভান্ডার",
    search_ph: "কাঞ্জি / কানা / অর্থ খুঁজুন…",
    f_kanji: "কাঞ্জি আছে",
    f_sentence: "বাক্য আছে",
    f_mnemonic: "mnemonic আছে",
    f_learned: "শেখা হয়েছে লুকান",
    start_here: "📖 শুরু এখান থেকে",
    all_lessons: "সব পাঠ",
    lesson_prefix: "পাঠ",
    cards_suffix: "টি কার্ড",
    no_matches: "কিছু পাওয়া যায়নি।",
    by: "তৈরি করেছেন",
    word_audio: "🔊 শব্দ",
    sentence_audio: "🔊 বাক্য",
    learned: "✓ শেখা হয়েছে",
    mark_learned: "শেখা হয়েছে চিহ্নিত করুন",
    about: "এই deck সম্পর্কে",
  },
};

let lang = localStorage.getItem("mnn-lang") || "en";
const t = (key) => I18N[lang][key] ?? I18N.en[key] ?? key;

let DATA = null;
let state = {
  lesson: null,    // null = "all"; 0 = intro; 1..50
  query: "",
  filters: { kanji: false, sentence: false, mnemonic: false, learned: false },
  expanded: null,
};
const learnedKey = "mnn-learned";
let learned = new Set(JSON.parse(localStorage.getItem(learnedKey) || "[]"));

const $ = (sel) => document.querySelector(sel);
const el = (tag, props = {}, ...children) => {
  const e = document.createElement(tag);
  Object.assign(e, props);
  for (const c of children) {
    if (c == null) continue;
    e.append(typeof c === "string" ? document.createTextNode(c) : c);
  }
  return e;
};

function applyI18n() {
  document.documentElement.lang = lang;
  $("#search").placeholder = t("search_ph");
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.dataset.i18n);
  });
}

async function boot() {
  const res = await fetch("data/vocab.json");
  DATA = await res.json();
  applyI18n();
  renderLessons();
  renderIntro();
  bindUi();
  applyTheme();
  render();
}

function bindUi() {
  $("#search").addEventListener("input", (e) => {
    state.query = e.target.value.trim().toLowerCase();
    state.expanded = null;
    render();
  });
  for (const id of ["kanji", "sentence", "mnemonic", "learned"]) {
    $("#f-" + id).addEventListener("change", (e) => {
      state.filters[id] = e.target.checked;
      render();
    });
  }
  $("#menu-btn").addEventListener("click", () => $("#sidebar").classList.toggle("open"));
  $("#lang-btn").addEventListener("click", () => {
    lang = lang === "en" ? "bn" : "en";
    localStorage.setItem("mnn-lang", lang);
    applyI18n();
    document.querySelector("#lessons").innerHTML = "";
    renderLessons();
    renderIntro();
    render();
  });
  $("#theme-btn").addEventListener("click", () => {
    const root = document.documentElement;
    const cur = root.classList.contains("dark") ? "dark" : root.classList.contains("light") ? "light" : "";
    const next = cur === "" ? "light" : cur === "light" ? "dark" : "";
    root.classList.remove("light", "dark");
    if (next) root.classList.add(next);
    localStorage.setItem("mnn-theme", next);
  });
}

function applyTheme() {
  const t = localStorage.getItem("mnn-theme");
  if (t) document.documentElement.classList.add(t);
}

function renderLessons() {
  const ul = $("#lessons");
  const make = (id, label, count) => {
    const li = el("li", {}, label, el("span", { className: "count" }, count + ""));
    li.dataset.id = id;
    li.addEventListener("click", () => {
      state.lesson = id;
      state.expanded = null;
      document.querySelectorAll("#lessons li").forEach((x) => x.classList.toggle("active", x.dataset.id == id));
      if (window.innerWidth <= 720) $("#sidebar").classList.remove("open");
      render();
    });
    return li;
  };
  ul.append(make(0, t("start_here"), "1"));
  ul.append(make(-1, t("all_lessons"), DATA.cards.length + ""));
  for (const lesson of DATA.lessons) {
    ul.append(make(lesson.n, t("lesson_prefix") + " " + String(lesson.n).padStart(2, "0"), lesson.count + ""));
  }
  state.lesson = -1;
  document.querySelectorAll("#lessons li").forEach((x) => x.classList.toggle("active", x.dataset.id == -1));
}

function renderIntro() {
  $("#intro").innerHTML = (lang === "bn" && DATA.intro_html_bn) ? DATA.intro_html_bn : DATA.intro_html;
}

function matchCard(c) {
  if (state.filters.kanji && !c.kanji) return false;
  if (state.filters.sentence && !c.sentence_jp) return false;
  if (state.filters.mnemonic && !c.mnemonic && !c.mnemonic_bn) return false;
  if (state.filters.learned && learned.has(c.guid)) return false;
  if (state.query) {
    const q = state.query;
    const hay = (c.kanji + " " + c.kana + " " + c.meaning + " " + (c.meaning_bn || "") + " " + (c.mnemonic || "") + " " + (c.mnemonic_bn || "")).toLowerCase();
    if (!hay.includes(q)) return false;
  }
  return true;
}

function render() {
  const intro = $("#intro");
  const cards = $("#cards");
  const empty = $("#empty");
  cards.innerHTML = "";
  intro.style.display = state.lesson === 0 ? "block" : "none";
  if (state.lesson === 0) {
    empty.hidden = true;
    $("#stats").textContent = t("about");
    return;
  }

  let list = DATA.cards;
  if (state.lesson > 0) list = list.filter((c) => c.lesson === state.lesson);
  list = list.filter(matchCard);

  $("#stats").textContent = `${list.length} ${t("cards_suffix")}`;
  empty.hidden = list.length > 0;
  empty.textContent = t("no_matches");

  for (const c of list) cards.append(renderCard(c));
}

function pitchHtml(c) {
  return c.kana_pitch || c.kana;
}

function renderCard(c) {
  const expanded = state.expanded === c.guid;
  const wrap = el("div", { className: "card" + (expanded ? " expanded" : "") + (learned.has(c.guid) ? " learned" : "") });
  const theme = el("div", { className: "theme" });
  theme.style.background = c.theme;
  wrap.append(theme);
  wrap.append(el("div", { className: "lesson-tag" }, `${t("lesson_prefix")} ${c.lesson} ${c.emoji}`));
  if (c.kanji) wrap.append(el("div", { className: "jp" }, c.kanji));
  const kana = el("div", { className: "kana" });
  kana.innerHTML = pitchHtml(c);
  wrap.append(kana);
  const meaningText = (lang === "bn" && c.meaning_bn) ? c.meaning_bn : c.meaning;
  wrap.append(el("div", { className: "meaning" }, meaningText));
  if (lang === "bn" && c.meaning_bn && c.meaning) {
    wrap.append(el("div", { className: "meaning meaning-secondary" }, c.meaning));
  } else if (lang === "en" && c.meaning_bn) {
    wrap.append(el("div", { className: "meaning meaning-secondary" }, c.meaning_bn));
  }

  if (expanded) {
    if (c.kanji_svgs.length) {
      const svgs = el("div", { className: "kanji-svgs" });
      for (const fn of c.kanji_svgs) svgs.append(el("img", { src: "svg/" + fn, alt: "" }));
      wrap.append(svgs);
    }
    if (c.sentence_jp) {
      const s = el("div", { className: "sentence" });
      s.append(el("div", { className: "sentence-jp" }, c.sentence_jp));
      const trans = (lang === "bn" && c.sentence_bn) ? c.sentence_bn : c.sentence_en;
      if (trans) s.append(el("div", { className: "sentence-en" }, trans));
      wrap.append(s);
    }
    const mnemoText = (lang === "bn" && c.mnemonic_bn) ? c.mnemonic_bn : c.mnemonic;
    if (mnemoText) wrap.append(el("div", { className: "mnemonic" }, mnemoText));
  }

  const actions = el("div", { className: "actions" });
  if (c.audio) actions.append(audioBtn(t("word_audio"), "audio/" + c.audio));
  if (c.sentence_audio) actions.append(audioBtn(t("sentence_audio"), "audio_sent/" + c.sentence_audio));
  const learn = el("button", { className: "learn" + (learned.has(c.guid) ? " on" : "") }, learned.has(c.guid) ? t("learned") : t("mark_learned"));
  learn.addEventListener("click", (e) => {
    e.stopPropagation();
    if (learned.has(c.guid)) learned.delete(c.guid);
    else learned.add(c.guid);
    localStorage.setItem(learnedKey, JSON.stringify([...learned]));
    render();
  });
  actions.append(learn);
  wrap.append(actions);

  wrap.addEventListener("click", (e) => {
    if (e.target.closest("button")) return;
    state.expanded = expanded ? null : c.guid;
    render();
  });
  return wrap;
}

function audioBtn(label, src) {
  const btn = el("button", {}, label);
  btn.addEventListener("click", (e) => {
    e.stopPropagation();
    const a = new Audio(src);
    a.play();
  });
  return btn;
}

boot().catch((e) => {
  console.error(e);
  document.body.innerText = "Failed to load: " + e.message;
});
