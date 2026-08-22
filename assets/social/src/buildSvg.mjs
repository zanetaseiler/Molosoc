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
 * small wordmark below it) inside the post's configured safe-zone box.
 *
 * Sizes are FIXED from config (fontSizeFrac * canvasWidth) — there is no
 * shrink-to-fit here. A too-small safe zone, or copy that doesn't fit it,
 * is a config bug and must fail the render loudly (see the guard checks
 * below), not silently produce a smaller headline than the brief calls for.
 * Returns a transparent-background SVG overlay to composite over the
 * master photo — this module never touches the photo itself.
 */
export function buildOverlaySvg({ post, template, canvasWidth, canvasHeight, socialDir }) {
  const colors = template.colors;
  const resolveColor = (c) => colors[c] ?? c;

  const hDef = template.defaults.headline;
  const sDef = template.defaults.supporting;
  const dDef = template.defaults.divider;
  const wDef = template.defaults.wordmark;
  const showBrandMark = post.brandMark !== false;
  const showDivider = showBrandMark && Boolean(dDef);
  const showWordmark = showBrandMark && Boolean(wDef);

  const serifPath = path.join(socialDir, template.fonts.serif.files[0]);
  const sansFiles = template.fonts.sans.files.map((f) => path.join(socialDir, f));

  const layout = post.layout;
  const boxX = layout.xFrac * canvasWidth;
  const boxY = layout.yFrac * canvasHeight;
  const boxWidth = layout.widthFrac * canvasWidth;
  const boxHeight = layout.heightFrac * canvasHeight;

  const headlineLines = post.headline;
  const accentIndex = Number.isInteger(post.accentLineIndex) ? post.accentLineIndex : -1;

  // Fixed sizes — driven only by config, never scaled down to fit.
  const headlineSize = hDef.fontSizeFrac * canvasWidth;
  const supportingSize = sDef.fontSizeFrac * canvasWidth;
  const lineHeight = headlineSize * hDef.lineHeightFactor;
  const supportLineHeight = supportingSize * sDef.lineHeightFactor;
  const wordmarkSize = showWordmark ? headlineSize * wDef.sizeFactor : 0;

  // --- Guard 1: headline block must clear the requested minimum size. ---
  const headlineBlockWidth = Math.max(
    ...headlineLines.map((l) => measureWidth(serifPath, l, headlineSize, hDef.letterSpacing)),
  );
  const headlineBlockHeight = headlineLines.length * lineHeight;
  const guards = template.guards ?? {};
  if (guards.minHeadlineBlockWidth && headlineBlockWidth < guards.minHeadlineBlockWidth) {
    throw new Error(
      `${post.id}: headline block is ${headlineBlockWidth.toFixed(1)}px wide, below the required minimum ` +
        `${guards.minHeadlineBlockWidth}px. Fix the safe-zone/copy/font size in config — do not let this ` +
        `silently shrink.`,
    );
  }
  if (guards.minHeadlineBlockHeight && headlineBlockHeight < guards.minHeadlineBlockHeight) {
    throw new Error(
      `${post.id}: headline block is ${headlineBlockHeight.toFixed(1)}px tall, below the required minimum ` +
        `${guards.minHeadlineBlockHeight}px. Fix the safe-zone/copy/font size in config — do not let this ` +
        `silently shrink.`,
    );
  }

  // --- Guard 2: the full lockup must not overflow the safe zone (that's ---
  // --- what would risk covering the model or the product). ---
  const gapToSupport = headlineSize * sDef.gapFactor;
  const dividerBlockHeight = showDivider
    ? headlineSize * (dDef.marginTopFactor + dDef.thicknessFactor + dDef.marginBottomFactor)
    : 0;
  const gapToWordmark = showWordmark && !showDivider ? headlineSize * wDef.gapFactor : 0;
  const naturalWidth = Math.max(
    headlineBlockWidth,
    measureWidth(sansFiles[0], post.supporting, supportingSize, sDef.letterSpacing),
    showWordmark ? measureWidth(sansFiles[0], wDef.text, wordmarkSize, wDef.letterSpacing) : 0,
  );
  const naturalHeight =
    headlineBlockHeight +
    gapToSupport +
    supportLineHeight +
    dividerBlockHeight +
    gapToWordmark +
    wordmarkSize * (showWordmark ? 1.1 : 0);
  if (naturalWidth > boxWidth) {
    throw new Error(
      `${post.id}: text lockup is ${naturalWidth.toFixed(1)}px wide, wider than its ${boxWidth.toFixed(1)}px ` +
        `safe zone — it would overflow into the rest of the photo. Narrow the copy/font size or widen the zone.`,
    );
  }
  if (naturalHeight > boxHeight) {
    throw new Error(
      `${post.id}: text lockup is ${naturalHeight.toFixed(1)}px tall, taller than its ${boxHeight.toFixed(1)}px ` +
        `safe zone — it would overflow past the zone (risking the model/product). Shorten the lockup or ` +
        `enlarge the zone.`,
    );
  }

  // --- Position elements top-down from the box origin. ---
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
  cursorY += gapToSupport;
  const supportBaseline = cursorY + supportingSize * BASELINE_OFFSET_FACTOR;
  textEls.push(
    `<text x="${boxX.toFixed(2)}" y="${supportBaseline.toFixed(2)}" font-family="${sDef.fontFamily}" font-weight="${sDef.fontWeight}" font-size="${supportingSize.toFixed(2)}" letter-spacing="${sDef.letterSpacing}em" fill="${resolveColor(sDef.color)}">${escapeXml(post.supporting)}</text>`,
  );
  cursorY += supportLineHeight;

  if (showDivider) {
    cursorY += headlineSize * dDef.marginTopFactor;
    const dividerThickness = headlineSize * dDef.thicknessFactor;
    const dividerWidth = headlineSize * dDef.widthFactor;
    const dividerY = cursorY + dividerThickness / 2;
    textEls.push(
      `<line x1="${boxX.toFixed(2)}" y1="${dividerY.toFixed(2)}" x2="${(boxX + dividerWidth).toFixed(2)}" y2="${dividerY.toFixed(2)}" stroke="${resolveColor(dDef.color)}" stroke-width="${dividerThickness.toFixed(2)}"/>`,
    );
    cursorY += dividerThickness + headlineSize * dDef.marginBottomFactor;
  }

  if (showWordmark) {
    cursorY += gapToWordmark;
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
      headlineBlockWidth,
      headlineBlockHeight,
      lockupWidth: naturalWidth,
      lockupHeight: naturalHeight,
      boxWidth,
      boxHeight,
    },
  };
}
