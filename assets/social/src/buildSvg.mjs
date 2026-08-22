import path from 'node:path';
import { measureWidth } from './textMetrics.mjs';

const BASELINE_OFFSET_FACTOR = 0.82; // approximate ascent-to-em ratio shared by both faces

function escapeXml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

/**
 * Lays out the headline + supporting line for one post inside its configured
 * safe-zone box, shrinking to fit (width first, then height) using real font
 * metrics, and returns the transparent-background SVG overlay to composite
 * over the master photo. Never touches the photo itself.
 */
export function buildOverlaySvg({ post, template, canvasWidth, canvasHeight, socialDir }) {
  const colors = template.colors;
  const resolveColor = (c) => colors[c] ?? c;

  const hDef = template.defaults.headline;
  const sDef = template.defaults.supporting;
  const serifPath = path.join(socialDir, template.fonts.serif.files[0]);

  const layout = post.layout;
  const boxX = layout.xFrac * canvasWidth;
  const boxY = layout.yFrac * canvasHeight;
  const boxWidth = layout.widthFrac * canvasWidth;
  const boxHeight = layout.heightFrac * canvasHeight;

  const headlineLines = post.headline;

  // 1) Preferred sizes, in px, before any shrink-to-fit.
  let headlineSize = hDef.fontSizeFrac * canvasWidth;
  let supportingSize = sDef.fontSizeFrac * canvasWidth;

  // 2) Shrink to fit box width (widest headline line wins).
  const maxLineWidthAt = (size) =>
    Math.max(...headlineLines.map((l) => measureWidth(serifPath, l, size, hDef.letterSpacing)));
  const widthScale = Math.min(1, boxWidth / maxLineWidthAt(headlineSize));
  headlineSize *= widthScale;
  supportingSize *= widthScale;

  // 3) Shrink further to fit box height (headline block + gap + support line).
  const blockHeightAt = (hSize, sSize) => {
    const lineHeight = hSize * hDef.lineHeightFactor;
    const gap = hSize * sDef.gapFactor;
    const supportLineHeight = sSize * sDef.lineHeightFactor;
    return headlineLines.length * lineHeight + gap + supportLineHeight;
  };
  const naturalHeight = blockHeightAt(headlineSize, supportingSize);
  const heightScale = Math.min(1, boxHeight / naturalHeight);
  headlineSize *= heightScale;
  supportingSize *= heightScale;

  // 4) Position lines top-down from the box origin.
  const lineHeight = headlineSize * hDef.lineHeightFactor;
  const gap = headlineSize * sDef.gapFactor;
  const supportLineHeight = supportingSize * sDef.lineHeightFactor;

  let cursorY = boxY;
  const textEls = [];
  for (const line of headlineLines) {
    const baseline = cursorY + headlineSize * BASELINE_OFFSET_FACTOR;
    textEls.push(
      `<text x="${boxX.toFixed(2)}" y="${baseline.toFixed(2)}" font-family="${hDef.fontFamily}" font-weight="${hDef.fontWeight}" font-size="${headlineSize.toFixed(2)}" fill="${resolveColor(hDef.color)}">${escapeXml(line)}</text>`,
    );
    cursorY += lineHeight;
  }
  cursorY += gap;
  const supportBaseline = cursorY + supportingSize * BASELINE_OFFSET_FACTOR;
  textEls.push(
    `<text x="${boxX.toFixed(2)}" y="${supportBaseline.toFixed(2)}" font-family="${sDef.fontFamily}" font-weight="${sDef.fontWeight}" font-size="${supportingSize.toFixed(2)}" letter-spacing="${sDef.letterSpacing}em" fill="${resolveColor(sDef.color)}">${escapeXml(post.supporting)}</text>`,
  );
  cursorY += supportLineHeight;

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${canvasWidth}" height="${canvasHeight}" viewBox="0 0 ${canvasWidth} ${canvasHeight}">
${textEls.join('\n')}
</svg>`;

  return {
    svg,
    fontFiles: [
      serifPath,
      ...template.fonts.sans.files.map((f) => path.join(socialDir, f)),
    ],
    meta: {
      headlineSize,
      supportingSize,
      widthScale,
      heightScale,
      blockHeightUsed: cursorY - boxY,
      blockHeightAvailable: boxHeight,
    },
  };
}
