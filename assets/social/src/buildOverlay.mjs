import path from 'node:path';
import { measureWidth } from './textMetrics.mjs';

// Approximate ascent-to-em ratio shared by DM Serif Display and Mulish — used
// only to convert a "top of visual box" y-coordinate (how every position in
// layouts.json is authored) into the SVG baseline the renderer actually draws
// at. This is not a layout decision; every text box position in this module
// comes verbatim from config.
const BASELINE_OFFSET_FACTOR = 0.82;

function escapeXml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

class LayoutViolation extends Error {}

function fail(postId, message) {
  throw new LayoutViolation(`${postId}: ${message}`);
}

/**
 * Builds the transparent-background SVG overlay for one post, using ONLY
 * fixed values from config/design-system.json (fonts/colors/weights, locked
 * globally) and config/layouts.json (position/size, authored per image).
 *
 * There is no shrink-to-fit, no automatic safe-zone calculation, and no
 * color/font derived from the photo anywhere in this module. Every
 * measurement is checked against hard boundaries — the moment any of them is
 * violated, this throws instead of adjusting anything. That is the point:
 * a layout that doesn't fit is a layout to fix by hand in config, not a
 * render to quietly degrade.
 */
export function buildOverlaySvg({ postId, copy, layout, designSystem, canvasWidth, canvasHeight, socialDir }) {
  const pad = designSystem.minEdgePadding;
  const colors = designSystem.colors;
  const headlineFontPath = path.join(socialDir, designSystem.fonts.headline.file);
  const supportFontPaths = designSystem.fonts.support.files.map((f) => path.join(socialDir, f));
  const wordmarkFontPath = path.join(socialDir, designSystem.fonts.wordmark.file);

  const { headline, accentLineIndex, supporting } = copy;
  const { textBox, headlineFontSize, headlineLineHeight, supportFontSize, supportPosition, dividerPosition, brandPosition } =
    layout;

  // ---- 1. Headline must fit inside its own configured text box. ----
  const lineHeight = headlineFontSize * headlineLineHeight;
  const headlineBlockHeight = headline.length * lineHeight;
  const headlineLineWidths = headline.map((l) => measureWidth(headlineFontPath, l, headlineFontSize, 0));
  const headlineBlockWidth = Math.max(...headlineLineWidths);

  headline.forEach((line, i) => {
    if (headlineLineWidths[i] > textBox.width) {
      fail(
        postId,
        `headline line ${i + 1} ("${line}") is ${headlineLineWidths[i].toFixed(1)}px wide, wider than its ` +
          `configured text box (${textBox.width}px). No glyph may extend outside its text box — widen textBox.width ` +
          `or shorten the copy/font size in layouts.json.`,
      );
    }
  });
  if (headlineBlockHeight > textBox.maxHeight) {
    fail(
      postId,
      `headline block is ${headlineBlockHeight.toFixed(1)}px tall, taller than its configured maxHeight ` +
        `(${textBox.maxHeight}px). Increase maxHeight or reduce headlineFontSize/headlineLineHeight in layouts.json ` +
        `— never silently shrink the headline to make this pass.`,
    );
  }

  // ---- 2. The text box itself, and every other element, must clear the ----
  // ---- global minimum edge padding on all four sides of the canvas. ----
  const checkPadding = (label, left, top, right, bottom) => {
    if (left < pad) fail(postId, `${label} is ${(pad - left).toFixed(1)}px inside the left ${pad}px padding limit.`);
    if (top < pad) fail(postId, `${label} is ${(pad - top).toFixed(1)}px inside the top ${pad}px padding limit.`);
    if (right > canvasWidth - pad)
      fail(postId, `${label} overflows the right edge by ${(right - (canvasWidth - pad)).toFixed(1)}px (min ${pad}px padding).`);
    if (bottom > canvasHeight - pad)
      fail(postId, `${label} overflows the bottom edge by ${(bottom - (canvasHeight - pad)).toFixed(1)}px (min ${pad}px padding).`);
  };

  checkPadding('headline text box', textBox.x, textBox.y, textBox.x + textBox.width, textBox.y + headlineBlockHeight);

  const supportWidth = measureWidth(supportFontPaths[0], supporting, supportFontSize, designSystem.supportLetterSpacing);
  const supportHeight = supportFontSize; // single line, no internal leading needed
  checkPadding(
    'supporting text',
    supportPosition.x,
    supportPosition.y,
    supportPosition.x + supportWidth,
    supportPosition.y + supportHeight,
  );

  const dividerWidth = designSystem.dividerWidth;
  const dividerThickness = designSystem.dividerThickness;
  checkPadding(
    'divider',
    dividerPosition.x,
    dividerPosition.y,
    dividerPosition.x + dividerWidth,
    dividerPosition.y + dividerThickness,
  );

  const wordmarkFontSize = designSystem.wordmarkFontSize;
  const wordmarkWidth = measureWidth(wordmarkFontPath, designSystem.wordmarkText, wordmarkFontSize, designSystem.wordmarkLetterSpacing);
  const wordmarkHeight = wordmarkFontSize * 1.1;
  checkPadding(
    'brand wordmark',
    brandPosition.x,
    brandPosition.y,
    brandPosition.x + wordmarkWidth,
    brandPosition.y + wordmarkHeight,
  );

  // ---- 3. Render. Every position below is the config value verbatim. ----
  const textEls = [];
  let cursorY = textBox.y;
  headline.forEach((line, i) => {
    const baseline = cursorY + headlineFontSize * BASELINE_OFFSET_FACTOR;
    const color = i === accentLineIndex ? colors.accent : colors.headline;
    textEls.push(
      `<text x="${textBox.x}" y="${baseline.toFixed(2)}" font-family="${designSystem.fonts.headline.family}" font-weight="${designSystem.headlineFontWeight}" font-size="${headlineFontSize}" fill="${color}">${escapeXml(line)}</text>`,
    );
    cursorY += lineHeight;
  });

  const supportBaseline = supportPosition.y + supportFontSize * BASELINE_OFFSET_FACTOR;
  textEls.push(
    `<text x="${supportPosition.x}" y="${supportBaseline.toFixed(2)}" font-family="${designSystem.fonts.support.family}" font-weight="${designSystem.supportFontWeight}" font-size="${supportFontSize}" letter-spacing="${designSystem.supportLetterSpacing}em" fill="${colors.support}">${escapeXml(supporting)}</text>`,
  );

  const dividerY = dividerPosition.y + dividerThickness / 2;
  textEls.push(
    `<line x1="${dividerPosition.x}" y1="${dividerY.toFixed(2)}" x2="${dividerPosition.x + dividerWidth}" y2="${dividerY.toFixed(2)}" stroke="${colors.divider}" stroke-width="${dividerThickness}"/>`,
  );

  const wordmarkBaseline = brandPosition.y + wordmarkFontSize * BASELINE_OFFSET_FACTOR;
  textEls.push(
    `<text x="${brandPosition.x}" y="${wordmarkBaseline.toFixed(2)}" font-family="${designSystem.fonts.wordmark.family}" font-weight="${designSystem.wordmarkFontWeight}" font-size="${wordmarkFontSize}" letter-spacing="${designSystem.wordmarkLetterSpacing}em" fill="${colors.wordmark}">${escapeXml(designSystem.wordmarkText)}</text>`,
  );

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${canvasWidth}" height="${canvasHeight}" viewBox="0 0 ${canvasWidth} ${canvasHeight}">
${textEls.join('\n')}
</svg>`;

  return {
    svg,
    fontFiles: [headlineFontPath, ...supportFontPaths, wordmarkFontPath],
    report: {
      headlineFontSize,
      headlineLineHeight,
      headlineBlockWidth,
      headlineBlockHeight,
      textBox,
      supportFontSize,
      supportPosition,
      supportWidth,
      dividerPosition,
      brandPosition,
      wordmarkWidth,
    },
    // Regions with actual ink, for the post-render "did our font really draw
    // something" sanity check in render.mjs (guards against a silent font
    // substitution/load failure producing blank text that would otherwise
    // pass every geometric check above).
    inkRegions: [
      { x: textBox.x, y: textBox.y, width: headlineBlockWidth, height: headlineBlockHeight },
      { x: supportPosition.x, y: supportPosition.y, width: supportWidth, height: supportHeight },
      { x: brandPosition.x, y: brandPosition.y, width: wordmarkWidth, height: wordmarkHeight },
    ],
  };
}
