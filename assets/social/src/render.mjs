import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';
import { Resvg } from '@resvg/resvg-js';
import { buildOverlaySvg } from './buildOverlay.mjs';

const socialDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const readJson = (p) => JSON.parse(fs.readFileSync(path.join(socialDir, p), 'utf8'));

const designSystem = readJson('config/design-system.json');
const copyConfig = readJson('config/copy.json');
const layoutsConfig = readJson('config/layouts.json');
const manifest = readJson('masters/MANIFEST.json');

function assertFontFilesExist() {
  const files = [
    designSystem.fonts.headline.file,
    ...designSystem.fonts.support.files,
    designSystem.fonts.wordmark.file,
  ];
  for (const f of files) {
    const full = path.join(socialDir, f);
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
    throw new Error(`No MANIFEST.json entry for master "${filename}" — add its sha256 before rendering.`);
  }
  const actualSha256 = crypto.createHash('sha256').update(buffer).digest('hex');
  if (actualSha256 !== entry.sha256) {
    throw new Error(
      `Master "${filename}" does not match MANIFEST.json (expected sha256 ${entry.sha256}, got ${actualSha256}). ` +
        `Masters are read-only — re-download from Drive rather than editing the file in place.`,
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
 * catches a silently-blank render (e.g. a font that "loaded" but matched no
 * glyphs) that would otherwise pass every geometric boundary check. */
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
          `the font likely failed to load/match. Refusing to ship a silently blank render.`,
      );
    }
  }
}

async function renderPost(imgId, variantId, outputName) {
  const baseCopy = copyConfig[imgId];
  if (!baseCopy) {
    throw new Error(`${imgId}: no entry in config/copy.json. Every post must use its own assigned copy.`);
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
  // 3-line default. copy.json stays the one source of truth for the words.
  const copy = {
    ...baseCopy,
    headline: layout.headlineLinesOverride ?? baseCopy.headline,
    accentLineIndex: layout.accentLineIndexOverride ?? baseCopy.accentLineIndex,
  };

  assertFontFilesExist();

  const postId = `${imgId}:${variantId}`;
  const masterPath = path.join(socialDir, 'masters', imageLayouts.master);
  const masterBuffer = fs.readFileSync(masterPath);
  checkMasterIntegrity(imageLayouts.master, masterBuffer);
  const masterMeta = await sharp(masterBuffer).metadata();
  checkAspect('Master', masterMeta.width, masterMeta.height);

  // Derived 4:5 social crop — a lossless, in-memory extract of the untouched
  // master buffer. The master file on disk is never written to; this crop
  // exists only as pixels in this process, composited straight into the
  // output file below.
  const { x: cx, y: cy, width: cw, height: ch } = layout.crop;
  if (cx < 0 || cy < 0 || cx + cw > masterMeta.width || cy + ch > masterMeta.height) {
    throw new Error(
      `${postId}: crop {x:${cx},y:${cy},w:${cw},h:${ch}} falls outside the master's ${masterMeta.width}x${masterMeta.height} bounds.`,
    );
  }
  checkAspect(`${postId} crop`, cw, ch);
  // .png() here is load-bearing: without it, sharp re-encodes the extracted
  // buffer in the SOURCE format (several masters are baseline JPEG despite
  // their .png filename), silently reintroducing lossy compression across
  // the whole derived crop before we've even composited text onto it.
  const croppedBuffer = await sharp(masterBuffer)
    .extract({ left: cx, top: cy, width: cw, height: ch })
    .png({ compressionLevel: 9 })
    .toBuffer();

  const { svg, fontFiles, report, inkRegions } = buildOverlaySvg({
    postId,
    copy,
    layout,
    designSystem,
    canvasWidth: cw,
    canvasHeight: ch,
    socialDir,
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

  await assertInkPresent(postId, overlayPng, cw, inkRegions);

  const outPath = path.join(socialDir, 'output', outputName);
  await sharp(croppedBuffer)
    .composite([{ input: overlayPng, left: 0, top: 0 }])
    .png({ compressionLevel: 9 })
    .withMetadata()
    .toFile(outPath);

  console.log(`\n${postId} -> ${outputName}`);
  console.log(`  master: ${imageLayouts.master} (untouched on disk, sha256 verified)`);
  console.log(`  crop: x=${cx} y=${cy} w=${cw} h=${ch} -> derived canvas ${cw}x${ch} (4:5)`);
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

const requested = process.argv.slice(2);
if (!requested.length) {
  console.error('Usage: node src/render.mjs <IMG_ID>:<VARIANT>:<output.png> [...]');
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
