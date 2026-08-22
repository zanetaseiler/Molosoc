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
 * Lays out the headline + supporting line (and, when the post opts in, a
 * divider rule + small wordmark below it) inside the post's configured
 * safe-zone box, shrinking to fit (width first, then height) using real
 * font metrics. Returns a transparent-background SVG overlay to composite
 * over the master photo — this module never touches the photo itself.
 */
export function buildOverlaySvg({ post, template, canvasWidth, canvasHeight, socialDir }) {
  const colors = template.colors;
  const resolveColor = (c) => colors[c] ?? c;

  const hDef = template.defaults.headline;
  const sDef = template.defaults.supporting;
  const dDef = template.defaults.divider;
  const wDef = template.defaults.wordmark;
  const showBrandMark = post.brandMark !== false && Boolean(dDef) && Boolean(wDef);

  const serifPath = path.join(socialDir, template.fonts.serif.files[0]);
  const sansFiles = template.fonts.sans.files.map((f) => path.join(socialDir, f));

  const layout = post.layout;
  const boxX = layout.xFrac * canvasWidth;
  const boxY = layout.yFrac * canvasHeight;
  const boxWidth = layout.widthFrac * canvasWidth;
  const boxHeight = layout.heightFrac * canvasHeight;

  const headlineLines = post.headline;
  const accentIndex = Number.isInteger(post.accentLineIndex) ? post.accentLineIndex : -1;

  // 1) Preferred sizes, in px, before any shrink-to-fit.
  let headlineSize = hDef.fontSizeFrac * canvasWidth;
  let supportingSize = sDef.fontSizeFrac * canvasWidth;

  // 2) Shrink to fit box width (widest headline line wins).
  const maxLineWidthAt = (size) =>
    Math.max(...headlineLines.map((l) => measureWidth(serifPath, l, size, hDef.letterSpacing)));
  const widthScale = Math.min(1, boxWidth / maxLineWidthAt(headlineSize));
  headlineSize *= widthScale;
  supportingSize *= widthScale;

  // 3) Shrink further to fit box height — headline block + gap + support
  // line, plus the divider + wordmark when the post uses a brand mark. The
  // divider/wordmark are sized as factors of the headline size so they scale
  // together with it rather than needing their own independent fit pass.
  const brandMarkHeightAt = (hSize) => {
    if (!showBrandMark) return 0;
    const dividerBlock = hSize * (dDef.marginTopFactor + dDef.thicknessFactor + dDef.marginBottomFactor);
    const wordmarkLine = hSize * wDef.sizeFactor * 1.1;
    return dividerBlock + wordmarkLine;
  };
  const blockHeightAt = (hSize, sSize) => {
    const lineHeight = hSize * hDef.lineHeightFactor;
    const gap = hSize * sDef.gapFactor;
    const supportLineHeight = sSize * sDef.lineHeightFactor;
    return headlineLines.length * lineHeight + gap + supportLineHeight + brandMarkHeightAt(hSize);
  };
  const naturalHeight = blockHeightAt(headlineSize, supportingSize);
  const heightScale = Math.min(1, boxHeight / naturalHeight);
  headlineSize *= heightScale;
  supportingSize *= heightScale;

  // 4) Position elements top-down from the box origin.
  const lineHeight = headlineSize * hDef.lineHeightFactor;
  const gap = headlineSize * sDef.gapFactor;
  const supportLineHeight = supportingSize * sDef.lineHeightFactor;

  let cursorY = boxY;
  const textEls = [];
  headlineLines.forEach((line, i) => {
    const baseline = cursorY + headlineSize * BASELINE_OFFSET_FACTOR;
    const color = i === accentIndex ? resolveColor(hDef.accentColor) : resolveColor(hDef.color);
    textEls.push(
      `<text x="${boxX.toFixed(2)}" y="${baseline.toFixed(2)}" font-family="${hDef.fontFamily}" font-weight="${hDef.fontWeight}" font-size="${headlineSize.toFixed(2)}" fill="${color}">${escapeXml(line)}</text>`,
    );
    cursorY += lineHeight;
  });
  cursorY += gap;
  const supportBaseline = cursorY + supportingSize * BASELINE_OFFSET_FACTOR;
  textEls.push(
    `<text x="${boxX.toFixed(2)}" y="${supportBaseline.toFixed(2)}" font-family="${sDef.fontFamily}" font-weight="${sDef.fontWeight}" font-size="${supportingSize.toFixed(2)}" letter-spacing="${sDef.letterSpacing}em" fill="${resolveColor(sDef.color)}">${escapeXml(post.supporting)}</text>`,
  );
  cursorY += supportLineHeight;

  if (showBrandMark) {
    cursorY += headlineSize * dDef.marginTopFactor;
    const dividerThickness = headlineSize * dDef.thicknessFactor;
    const dividerWidth = headlineSize * dDef.widthFactor;
    const dividerY = cursorY + dividerThickness / 2;
    textEls.push(
      `<line x1="${boxX.toFixed(2)}" y1="${dividerY.toFixed(2)}" x2="${(boxX + dividerWidth).toFixed(2)}" y2="${dividerY.toFixed(2)}" stroke="${resolveColor(dDef.color)}" stroke-width="${dividerThickness.toFixed(2)}"/>`,
    );
    cursorY += dividerThickness + headlineSize * dDef.marginBottomFactor;

    const wordmarkSize = headlineSize * wDef.sizeFactor;
    const wordmarkBaseline = cursorY + wordmarkSize * BASELINE_OFFSET_FACTOR;
    textEls.push(
      `<text x="${boxX.toFixed(2)}" y="${wordmarkBaseline.toFixed(2)}" font-family="${wDef.fontFamily}" font-weight="${wDef.fontWeight}" font-size="${wordmarkSize.toFixed(2)}" letter-spacing="${wDef.letterSpacing}em" fill="${resolveColor(wDef.color)}">${escapeXml(wDef.text)}</text>`,
    );
    cursorY += wordmarkSize * 1.1;
  }

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${canvasWidth}" height="${canvasHeight}" viewBox="0 0 ${canvasWidth} ${canvasHeight}">
${textEls.join('\n')}
</svg>`;

  return {
    svg,
    fontFiles: [serifPath, ...sansFiles],
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
