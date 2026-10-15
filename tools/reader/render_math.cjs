const fs = require("node:fs");

function normalizeLatexmlTex(tex) {
  let clean = "";
  for (let i = 0; i < tex.length; i++) {
    if (tex[i] === "\\") {
      clean += tex[i];
      if (i + 1 < tex.length) clean += tex[++i];
    } else if (tex[i] === "%") {
      while (i < tex.length && tex[i] !== "\n") i++;
    } else {
      clean += tex[i];
    }
  }
  return clean.replace(
    /(\\(?:big|Big|bigg|Bigg)[lrm]?)\s*\{\s*(\\(?:[{}|]|langle\b|rangle\b|lvert\b|rvert\b|lVert\b|rVert\b|vert\b|Vert\b|lfloor\b|rfloor\b|lceil\b|rceil\b|lbrace\b|rbrace\b)|[()[\]|.])\s*\}/g,
    (_, size, delimiter) =>
      size + delimiter + (/^\\[A-Za-z]+$/.test(delimiter) ? " " : ""),
  );
}

function renderMath(katex, items) {
  return items.map(({ id, tex, display }) => {
    if (typeof tex !== "string" || !tex.trim()) {
      throw new Error(`${id}: missing LaTeX formula`);
    }
    try {
      const html = katex.renderToString(normalizeLatexmlTex(tex), {
        displayMode: Boolean(display),
        throwOnError: true,
        strict: "error",
        trust: false,
        output: "htmlAndMathml",
        macros: {
          "\\leavevmode": "",
          "\\nobreak": "",
        },
      });
      return { id, html };
    } catch (error) {
      throw new Error(`${id}: ${error.message}`);
    }
  });
}

module.exports = { normalizeLatexmlTex, renderMath };

if (require.main === module) {
  try {
    const katex = require(process.argv[2]);
    const items = JSON.parse(fs.readFileSync(0, "utf8"));
    process.stdout.write(JSON.stringify(renderMath(katex, items)));
  } catch (error) {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  }
}
