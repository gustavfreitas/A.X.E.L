/* Ponto de entrada: liga os componentes à API. */
import { clearHistory, getHealth, getHistory, streamChat } from "./api.js";
import {
  addAnswer, addUserMessage, autosizeInput, els, scrollThreadToEnd,
  setAnswer, setBadge, setBusy, showError, showStatus,
} from "./ui.js";

let controller = null;
let busy = false;

async function ask(text) {
  text = text.trim();
  if (busy || !text) return;
  busy = true;
  setBusy(true);
  addUserMessage(text);
  const card = addAnswer();
  showStatus(card, "Entendendo o seu pedido…");

  controller = new AbortController();
  let acc = "";
  let intent = "";
  try {
    for await (const ev of streamChat(text, controller.signal)) {
      if (ev.type === "status") {
        showStatus(card, ev.stage === "generating" ? "Escrevendo o diagnóstico…" : "Entendendo o seu pedido…");
      } else if (ev.type === "intent") {
        intent = ev.intent;
      } else if (ev.type === "token") {
        acc += ev.text;
        setAnswer(card, { text: acc, intent, streaming: true });
        scrollThreadToEnd();
      } else if (ev.type === "done") {
        setAnswer(card, { text: ev.text, intent: ev.intent || intent });
      } else if (ev.type === "error") {
        showError(card, ev.message);
      }
    }
  } catch (err) {
    if (err.name === "AbortError") {
      acc ? setAnswer(card, { text: acc, intent }) : showError(card, "Interrompido.");
    } else {
      showError(card, "Não consegui falar com o servidor do A.X.E.L. Ele ainda está rodando?");
    }
  } finally {
    controller = null;
    busy = false;
    setBusy(false);
    scrollThreadToEnd();
  }
}

/* ---- Eventos ---- */
els.form.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = els.input.value;
  els.input.value = "";
  autosizeInput();
  ask(text);
});

els.input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
    e.preventDefault();
    els.form.requestSubmit();
  }
});
els.input.addEventListener("input", autosizeInput);

els.chips.addEventListener("click", (e) => {
  const chip = e.target.closest("[data-prompt]");
  if (chip) ask(chip.dataset.prompt);
});

els.inner.addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-copy]");
  if (!btn) return;
  const code = btn.closest(".code").querySelector("code").textContent;
  try {
    await navigator.clipboard.writeText(code);
    btn.textContent = "Copiado";
  } catch {
    btn.textContent = "Selecione e copie";
  }
  setTimeout(() => (btn.textContent = "Copiar"), 1500);
});

els.clear.addEventListener("click", async () => {
  if (controller) controller.abort();
  await clearHistory().catch(() => {});
  location.reload();
});

/* ---- Início: estado do Ollama e histórico salvo ---- */
getHealth()
  .then((h) => setBadge(h.ok ? "ok" : "bad", h.ok ? h.model : "Ollama indisponível", h.message))
  .catch(() => setBadge("bad", "Servidor offline"));

getHistory()
  .then((turns) => {
    turns.forEach((t) => {
      addUserMessage(t.user);
      setAnswer(addAnswer(), { text: t.response, intent: t.intent });
    });
    scrollThreadToEnd();
  })
  .catch(() => {});

els.input.focus();
