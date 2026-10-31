/* Markdown mínimo e seguro: TUDO é escapado antes de virar HTML,
   então um <script> na resposta do modelo aparece como texto e não executa. */

const ESCAPES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
export const escapeHtml = (s) => s.replace(/[&<>"']/g, (c) => ESCAPES[c]);

const inline = (s) =>
  escapeHtml(s)
    .replace(/`([^`\n]+)`/g, '<code class="inline">$1</code>')
    .replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>");

/* O modelo escreve títulos como "DIAGNÓSTICO". Mostramos em frase: "Diagnóstico". */
const sentenceCase = (s) => s.charAt(0) + s.slice(1).toLowerCase();

const FENCE = /^\s*```([\w+-]*)\s*$/;
const FENCE_END = /^\s*```\s*$/;
const HEADING = /^(#{1,4})\s+(.*)$/;
const BULLET = /^\s*[-*]\s+(.*)$/;
const NUMBERED = /^\s*\d+[.)]\s+(.*)$/;
const SHOUTING_TITLE = /^[A-ZÀ-Ú][A-ZÀ-Ú /çÇ]{3,}:?$/;

function codeBlock(lang, lines) {
  return (
    '<div class="code"><div class="code__bar"><span>' + escapeHtml(lang || "código") +
    '</span><button type="button" class="code__copy" data-copy>Copiar</button></div>' +
    '<pre class="scroll"><code>' + escapeHtml(lines.join("\n")) + "</code></pre></div>"
  );
}

export function renderMarkdown(source) {
  const out = [];
  const lines = source.replace(/\r/g, "").split("\n");
  let paragraph = [];
  let list = null;

  const flushParagraph = () => {
    if (paragraph.length) out.push("<p>" + paragraph.map(inline).join("<br>") + "</p>");
    paragraph = [];
  };
  const flushList = () => {
    if (list) {
      const items = list.items.map((t) => "<li>" + inline(t) + "</li>").join("");
      out.push(`<${list.tag}>${items}</${list.tag}>`);
    }
    list = null;
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    const fence = line.match(FENCE);
    if (fence) {
      flushParagraph(); flushList();
      const code = [];
      i++;
      while (i < lines.length && !FENCE_END.test(lines[i])) code.push(lines[i++]);
      out.push(codeBlock(fence[1], code)); // bloco ainda abrindo (streaming) também funciona
      continue;
    }

    const heading = line.match(HEADING);
    const bullet = line.match(BULLET);
    const numbered = line.match(NUMBERED);

    if (heading) {
      flushParagraph(); flushList();
      out.push("<h4>" + inline(heading[2]) + "</h4>");
    } else if (bullet || numbered) {
      flushParagraph();
      const tag = bullet ? "ul" : "ol";
      if (!list || list.tag !== tag) { flushList(); list = { tag, items: [] }; }
      list.items.push((bullet || numbered)[1]);
    } else if (!line.trim()) {
      flushParagraph(); flushList();
    } else if (SHOUTING_TITLE.test(line.trim())) {
      flushParagraph(); flushList();
      out.push("<h4>" + escapeHtml(sentenceCase(line.trim().replace(/:$/, ""))) + "</h4>");
    } else {
      flushList();
      paragraph.push(line);
    }
  }
  flushParagraph(); flushList();
  return out.join("");
}
