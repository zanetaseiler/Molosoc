import * as fontkitNS from 'fontkit';

const fontkit = fontkitNS.default ?? fontkitNS;
const cache = new Map();

function loadFont(path) {
  if (!cache.has(path)) cache.set(path, fontkit.openSync(path));
  return cache.get(path);
}

/**
 * Width of `text` in px at `fontSize`, including tracking, using real glyph
 * advances (kerning-aware) from the actual font file — not an estimate.
 */
export function measureWidth(fontPath, text, fontSize, letterSpacingEm = 0) {
  const font = loadFont(fontPath);
  const run = font.layout(text);
  const advance = (run.advanceWidth / font.unitsPerEm) * fontSize;
  const tracking = letterSpacingEm * fontSize * Math.max(0, text.length - 1);
  return advance + tracking;
}
