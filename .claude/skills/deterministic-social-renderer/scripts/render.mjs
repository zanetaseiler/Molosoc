import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';
import { Resvg } from '@resvg/resvg-js';
import { buildOverlaySvg } from './buildOverlay.mjs';

// Expects to live at <project>/src/render.mjs (or wherever you place it) —
// walks up one directory to find config/, masters/, output/. Adjust this
// line if you nest it differently.
const rootDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const readJson = (p) => JSON.parse(fs.readFileSync(path.join(rootDir, p), 'utf8'));

const designSystem = readJson('config/design-system.json');
const layoutsConfig = readJson('config/layouts.json');
const manifest = readJson('masters/MANIFEST.json');

// Locale copy file: defaults to config/copy.json. Pass --copy=<path> once,
// before any IMG:VARIANT:output args, to render a translated set (e.g.
// --copy=config/copy_fr.json) — layout/template/crop are untouched, only
// which copy file supplies headline/supporting text. See
// references/localization.md before adding a second locale.
const copyFlagIndex = process.argv.findIndex((a) => a.startsWith('--copy='));
const copyPath = copyFlagIndex === -1 ? 'config/copy.json' : process.argv[copyFlagIndex].slice('--copy='.length);
const copyConfig = readJson(copyPath);

function assertFontFilesExist() {
  const files = [
    designSystem.fonts.headline.file,
    ...designSystem.fonts.support.files,
    designSystem.fonts.wordmark.file,
  ];
  for (const f of files) {
    const full = path.join(rootDir, f);
    if (!fs.existsSync(full)) {
      throw new Error(
        `Locked font file missing on disk: ${f}. Refusing to render — this system never falls back to a ` +
          `system font substitute.`,
      );
    }
  }
}

function checkMasterIntegrity(filename, buffer) {
  const entry = manifest.files.find((f) => f.filename === filename);
  if (!entry) {
    throw new Error(`No MANIFEST.json entry for master "${filename}" — add its sha256 before rendering (see scripts/add_master.mjs).`);
  }
  const actualSha256 = crypto.createHash('sha256').update(buffer).digest('hex');
  if (actualSha256 !== entry.sha256) {
    throw new Error(
      `Master "${filename}" does not match MANIFEST.json (expected sha256 ${entry.sha256}, got ${actualSha256}). ` +
        `Masters are read-only — re-acquire from the original source rather than editing the file in place.`,
    );
  }
}

function checkAspect(label, width, height) {
  const [aw, ah] = designSystem.canvas.aspect;
  const actual = width / height;
  const expected = aw / ah;
  const drift = Math.abs(actual - expected) / expected;
  if (drift > designSystem.canvas.aspectTolerance) {
    throw new Error(
      `${label} is ${width}x${height} (ratio ${actual.toFixed(4)}), which drifts ${(drift * 100).toFixed(1)}% ` +
        `from the required ${aw}:${ah}.`,
    );
  }
}

/** Confirms the rasterized overlay actually has ink in each expected region —
 * catches a silently-blank render (e.g. a font that "loaded" but was missing
 * the glyphs for this text — see references/localization.md) that would
 * otherwise pass every geometric boundary check. */
async function assertInkPresent(postId, overlayPng, canvasWidth, inkRegions) {
  const { data, info } = await sharp(overlayPng).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  const channels = info.channels;
  for (const region of inkRegions) {
    const x0 = Math.max(0, Math.floor(region.x));
    const y0 = Math.max(0, Math.floor(region.y));
    const x1 = Math.min(canvasWidth, Math.ceil(region.x + region.width));
    const y1 = Math.min(info.height, Math.ceil(region.y + region.height));
    let opaquePixels = 0;
    for (let y = y0; y < y1; y++) {
      for (let x = x0; x < x1; x++) {
        const alpha = data[(y * info.width + x) * channels + 3];
        if (alpha > 10) opaquePixels++;
      }
    }
    if (opaquePixels === 0) {
      throw new Error(
        `${postId}: expected text at (${region.x.toFixed(0)},${region.y.toFixed(0)}) drew zero visible pixels — ` +
          `the font likely failed to load/match, or is missing glyphs for this text. Refusing to ship a silently ` +
          `blank render.`,
      );
    }
  }
}

async function renderPost(imgId, variantId, outputName) {
  const baseCopy = copyConfig[imgId];
  if (!baseCopy) {
    throw new Error(`${imgId}: no entry in ${copyPath}. Every post must use its own assigned copy.`);
  }
  const imageLayouts = layoutsConfig[imgId];
  if (!imageLayouts) {
    throw new Error(
      `${imgId}: no entry in config/layouts.json. Layout is never calculated automatically — add a manually ` +
        `authored entry before rendering this post.`,
    );
  }
  const layout = imageLayouts[variantId];
  if (!layout) {
    throw new Error(`${imgId}: no variant "${variantId}" in config/layouts.json (have: ${Object.keys(imageLayouts).filter((k) => !k.startsWith('_') && k !== 'master').join(', ')}).`);
  }
  // A variant may test a different line-break of the SAME assigned copy (not
  // different words) — e.g. comparing a 4-line stacked treatment against the
  // 3-line default. The copy file stays the one source of truth for the words.
  const copy = {
    ...baseCopy,
    headline: layout.headlineLinesOverride ?? baseCopy.headline,
    accentLineIndex: layout.accentLineIndexOverride ?? baseCopy.accentLineIndex,
  };

  assertFontFilesExist();

  const postId = `${imgId}:${variantId}`;
  const masterPath = path.join(rootDir, 'masters', imageLayouts.master);
  const masterBuffer = fs.readFileSync(masterPath);
  checkMasterIntegrity(imageLayouts.master, masterBuffer);
  const masterMeta = await sharp(masterBuffer).metadata();
  checkAspect('Master', masterMeta.width, masterMeta.height);

  // TEMPLATE_FULL ("B", default, for a photo with genuinely large clean
  // negative space): the derived canvas IS a lossless in-memory crop of the
  // master — full-bleed photo, text composited straight on top of it.
  // TEMPLATE_SIDE ("A") / TEMPLATE_BOTTOM ("C"): the derived canvas is a
  // flat, brand-color rectangle with a lossless in-memory crop of the
  // master composited into ONLY its photo region (left panel for A, top
  // band for C) — text never touches that photo region at all (enforced by
  // buildOverlay's textAreaBounds check, not just by visual convention).
  // Either way, the master file on disk is never written to. See
  // references/templates.md for when to choose which.
  const template = layout.template ?? 'B';
  let baseBuffer;
  let canvasWidth;
  let canvasHeight;
  let cropLog;

  if (template === 'B') {
    const { x: cx, y: cy, width: cw, height: ch } = layout.crop;
    if (cx < 0 || cy < 0 || cx + cw > masterMeta.width || cy + ch > masterMeta.height) {
      throw new Error(
        `${postId}: crop {x:${cx},y:${cy},w:${cw},h:${ch}} falls outside the master's ${masterMeta.width}x${masterMeta.height} bounds.`,
      );
    }
    checkAspect(`${postId} crop`, cw, ch);
    // .png() here is load-bearing: without it, sharp re-encodes the extracted
    // buffer in the SOURCE format (a master can be baseline JPEG despite its
    // .png filename), silently reintroducing lossy compression across the
    // whole derived crop before text is even composited onto it.
    baseBuffer = await sharp(masterBuffer)
      .extract({ left: cx, top: cy, width: cw, height: ch })
      .png({ compressionLevel: 9 })
      .toBuffer();
    canvasWidth = cw;
    canvasHeight = ch;
    cropLog = `crop: x=${cx} y=${cy} w=${cw} h=${ch} -> derived canvas ${cw}x${ch}`;
  } else {
    const tmpl = designSystem.templates[template];
    if (!tmpl) throw new Error(`${postId}: unknown template "${template}" (expected A, B, or C).`);
    // The canvas is always the master's own dimensions — a real photo set
    // often has more than one native size, so panel/band geometry is stored
    // as a RATIO of that size, computed fresh per master, never a fixed
    // pixel value assumed from one size.
    canvasWidth = masterMeta.width;
    canvasHeight = masterMeta.height;
    const photoPanelWidth = template === 'A' ? Math.round(canvasWidth * tmpl.photoPanelWidthRatio) : undefined;
    const photoPanelX = template === 'A' ? canvasWidth - photoPanelWidth : undefined;
    const photoBandHeight = template === 'C' ? Math.round(canvasHeight * tmpl.photoBandHeightRatio) : undefined;
    const { x: px, y: py, width: pw, height: ph } = layout.photoCrop;
    if (px < 0 || py < 0 || px + pw > masterMeta.width || py + ph > masterMeta.height) {
      throw new Error(
        `${postId}: photoCrop {x:${px},y:${py},w:${pw},h:${ph}} falls outside the master's ${masterMeta.width}x${masterMeta.height} bounds.`,
      );
    }
    const expectedW = template === 'A' ? photoPanelWidth : canvasWidth;
    const expectedH = template === 'A' ? canvasHeight : photoBandHeight;
    if (pw !== expectedW || ph !== expectedH) {
      throw new Error(
        `${postId}: template ${template}'s photoCrop must be exactly ${expectedW}x${expectedH} for this master's own ` +
          `${canvasWidth}x${canvasHeight} size (so it composites with zero scaling) — got ${pw}x${ph}.`,
      );
    }
    const photoBuffer = await sharp(masterBuffer)
      .extract({ left: px, top: py, width: pw, height: ph })
      .png({ compressionLevel: 9 })
      .toBuffer();
    const photoOffset = template === 'A' ? { left: photoPanelX, top: 0 } : { left: 0, top: 0 };
    baseBuffer = await sharp({
      create: {
        width: canvasWidth,
        height: canvasHeight,
        channels: 3,
        background: designSystem.colors.panelBackground,
      },
    })
      .composite([{ input: photoBuffer, ...photoOffset }])
      .png({ compressionLevel: 9 })
      .toBuffer();
    cropLog =
      `template ${template}: photoCrop x=${px} y=${py} w=${pw} h=${ph} -> placed at (${photoOffset.left},${photoOffset.top}) ` +
      `on a ${canvasWidth}x${canvasHeight} ${designSystem.colors.panelBackground} canvas`;
  }

  const { svg, fontFiles, report, inkRegions } = buildOverlaySvg({
    postId,
    copy,
    layout,
    designSystem,
    canvasWidth,
    canvasHeight,
    socialDir: rootDir,
  });

  const resvg = new Resvg(svg, {
    font: {
      fontFiles,
      loadSystemFonts: false,
      defaultFontFamily: designSystem.fonts.headline.family,
    },
    background: 'rgba(0,0,0,0)',
  });
  const overlayPng = resvg.render().asPng();

  await assertInkPresent(postId, overlayPng, canvasWidth, inkRegions);

  // Rounded outer corners (optional — set cornerRadius: 0 in design-system.json
  // to skip): a white rounded-rect mask clipped onto the final composite via
  // 'dest-in' (keep pixels where the mask is opaque, make transparent where
  // it isn't) — the corners themselves, not a border drawn on top, so
  // nothing is added over the photo/text.
  const composited = await sharp(baseBuffer)
    .composite([{ input: overlayPng, left: 0, top: 0 }])
    .png({ compressionLevel: 9 })
    .toBuffer();

  const outPath = path.join(rootDir, 'output', outputName);
  const r = designSystem.cornerRadius ?? 0;
  let finalImage = sharp(composited);
  if (r > 0) {
    const cornerMaskSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="${canvasWidth}" height="${canvasHeight}"><rect x="0" y="0" width="${canvasWidth}" height="${canvasHeight}" rx="${r}" ry="${r}" fill="#fff"/></svg>`;
    finalImage = finalImage.composite([{ input: Buffer.from(cornerMaskSvg), blend: 'dest-in' }]);
  }
  await finalImage.png({ compressionLevel: 9 }).withMetadata().toFile(outPath);

  console.log(`\n${postId} -> ${outputName}`);
  console.log(`  master: ${imageLayouts.master} (untouched on disk, sha256 verified)`);
  console.log(`  ${cropLog}`);
  console.log(
    `  headline: [${report.headlineLineSizes.join('/')}]px / lineHeight ${report.headlineLineHeight} ` +
      `-> block ${report.headlineBlockWidth.toFixed(1)}x${report.headlineBlockHeight.toFixed(1)}px ` +
      `at (${report.textBox.x}, ${report.textBox.y}), box ${report.textBox.width}x${report.textBox.maxHeight}px`,
  );
  console.log(
    `  supporting: ${report.supportFontSize}px, ${report.supportWidth.toFixed(1)}px wide, at ` +
      `(${report.supportPosition.x}, ${report.supportPosition.y})`,
  );
  console.log(`  divider: ${report.dividerWidth}px wide, at (${report.dividerPosition.x}, ${report.dividerPosition.y})`);
  console.log(
    `  brand: ${report.wordmarkFontSize}px, ${report.wordmarkWidth.toFixed(1)}px wide, at ` +
      `(${report.brandPosition.x}, ${report.brandPosition.y})`,
  );
  console.log(`  boundary checks: PASSED (min ${designSystem.minEdgePadding}px edge padding, headline within textBox)`);
  console.log(`  -> ${outPath}`);
}

const requested = process.argv.slice(2).filter((a) => !a.startsWith('--copy='));
if (!requested.length) {
  console.error('Usage: node render.mjs [--copy=config/copy_XX.json] <IMG_ID>:<VARIANT>:<output.png> [...]');
  process.exit(1);
}

for (const arg of requested) {
  const [imgId, variantId, outputName] = arg.split(':');
  if (!imgId || !variantId || !outputName) {
    console.error(`Bad argument "${arg}" — expected IMG_ID:VARIANT:output.png`);
    process.exit(1);
  }
  await renderPost(imgId, variantId, outputName);
}
