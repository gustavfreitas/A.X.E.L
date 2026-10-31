/* Componentes de interface: cada função cria ou atualiza um pedaço do DOM. */
import { escapeHtml, renderMarkdown } from "./markdown.js";

const INTENT_LABELS = {
  CODE_DEBUG: "Debug de código",
  CODE_OPTIMIZATION: "Otimização de código",
  SQL_OPTIMIZATION: "Otimização de SQL",
  ERROR_ANALYSIS: "Análise de erro",
  EXPLANATION: "Explicação",
  GENERAL_QUERY: "Pergunta geral",
  OUT_OF_SCOPE: "Fora do escopo",
};
export const intentLabel = (intent) => INTENT_LABELS[intent] || "";

const $ = (id) => document.getElementById(id);
export const els = {
  app: $("app"), hero: $("hero"), thread: $("thread"), inner: $("threadInner"),
  form: $("form"), input: $("input"), send: $("send"), clear: $("clear"),
  badge: $("badge"), badgeText: $("badgeText"), chips: $("chips"),
};

/* ---- Estado da tela: boas-vindas ou conversa ---- */
export function showChat() {
  els.app.dataset.state = "chat";
  els.hero.hidden = true;
  els.thread.hidden = false;
  els.clear.hidden = false;
}

export const scrollThreadToEnd = () => { els.thread.scrollTop = els.thread.scrollHeight; };

/* ---- Mensagens ---- */
export function addUserMessage(text) {
  showChat();
  const wrap = document.createElement("div");
  wrap.className = "msg msg--user";
  const bubble = document.createElement("div");
  bubble.className = "msg__bubble";
  bubble.textContent = text; // textContent: nunca interpreta HTML
  wrap.appendChild(bubble);
  els.inner.appendChild(wrap);
  scrollThreadToEnd();
}

export function addAnswer() {
  showChat();
  const card = document.createElement("article");
  card.className = "answer";
  els.inner.appendChild(card);
  scrollThreadToEnd();
  return card;
}

export function showStatus(card, label) {
  card.innerHTML =
    '<div class="answer__status"><span class="spinner" aria-hidden="true"></span>' +
    escapeHtml(label) + "</div>";
}

export function showError(card, message) {
  card.innerHTML = '<div class="answer__error">' + escapeHtml(message) + "</div>";
}

export function setAnswer(card, { text, intent = "", streaming = false }) {
  let body = card.querySelector(".answer__body");
  if (!body) {
    const tag = intentLabel(intent);
    card.innerHTML =
      (tag ? `<div class="answer__head"><span class="answer__tag">${escapeHtml(tag)}</span></div>` : "") +
      '<div class="answer__body scroll"></div>';
    body = card.querySelector(".answer__body");
  }
  const atEnd = body.scrollHeight - body.scrollTop - body.clientHeight < 40;
  body.innerHTML = renderMarkdown(text);
  body.classList.toggle("is-streaming", streaming);
  if (atEnd) body.scrollTop = body.scrollHeight; // acompanha enquanto escreve
}

/* ---- Cabeçalho ---- */
export function setBadge(state, text, title = "") {
  els.badge.dataset.state = state;
  els.badgeText.textContent = text;
  els.badge.title = title;
}

/* ---- Entrada ---- */
export function setBusy(busy) {
  els.app.dataset.busy = String(busy); // o ícone pulsa mais rápido enquanto o modelo trabalha
  els.send.disabled = busy;
  els.input.disabled = busy;
  els.chips.querySelectorAll("button").forEach((b) => (b.disabled = busy));
  if (!busy) els.input.focus();
}

export function autosizeInput() {
  els.input.style.height = "auto";
  els.input.style.height = Math.min(els.input.scrollHeight, 180) + "px";
}
