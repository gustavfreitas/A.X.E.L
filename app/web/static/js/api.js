/* Comunicação com o servidor. Nenhum DOM aqui. */

export async function* streamChat(message, signal) {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
    signal,
  });
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let nl;
    while ((nl = buffer.indexOf("\n")) >= 0) {
      const line = buffer.slice(0, nl).trim();
      buffer = buffer.slice(nl + 1);
      if (line) yield JSON.parse(line); // um evento por linha (NDJSON)
    }
  }
}

export const getHealth = () => fetch("/api/health").then((r) => r.json());
export const getHistory = () => fetch("/api/history").then((r) => r.json());
export const clearHistory = () => fetch("/api/clear", { method: "POST" });
