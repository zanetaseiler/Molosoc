import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';
import { Resvg } from '@resvg/resvg-js';
import { buildOverlaySvg } from './buildSvg.mjs';

const socialDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const template = JSON.parse(fs.readFileSync(path.join(socialDir, 'config/template.json'), 'utf8'));
const posts = JSON.parse(fs.readFileSync(path.join(socialDir, 'config/posts.json'), 'utf8'));
const manifest = JSON.parse(fs.readFileSync(path.join(socialDir, 'masters/MANIFEST.json'), 'utf8'));

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

function checkAspect(width, height) {
  const [aw, ah] = template.canvas.aspect;
  const actual = width / height;
  const expected = aw / ah;
  const drift = Math.abs(actual - expected) / expected;
  if (drift > template.canvas.aspectTolerance) {
    throw new Error(
      `Master is ${width}x${height} (ratio ${actual.toFixed(4)}), which drifts ${(drift * 100).toFixed(1)}% ` +
        `from the required ${aw}:${ah}. Refusing to crop or stretch a master — fix the source or its ` +
        `aspect tolerance instead.`,
    );
  }
}

async function renderPost(post) {
  const masterPath = path.join(socialDir, 'masters', post.master);
  const masterBuffer = fs.readFileSync(masterPath);
  checkMasterIntegrity(post.master, masterBuffer);
  const metadata = await sharp(masterBuffer).metadata();
  checkAspect(metadata.width, metadata.height);

  const { svg, fontFiles, meta } = buildOverlaySvg({
    post,
    template,
    canvasWidth: metadata.width,
    canvasHeight: metadata.height,
    socialDir,
  });

  const resvg = new Resvg(svg, {
    font: {
      fontFiles,
      loadSystemFonts: false,
      defaultFontFamily: template.fonts.serif.family,
    },
    background: 'rgba(0,0,0,0)',
  });
  const overlayPng = resvg.render().asPng();

  const outPath = path.join(socialDir, 'output', `${post.id}.png`);
  await sharp(masterBuffer)
    .composite([{ input: overlayPng, left: 0, top: 0 }])
    .png({ compressionLevel: 9 })
    .withMetadata()
    .toFile(outPath);

  console.log(`${post.id}: ${metadata.width}x${metadata.height} <- ${post.master}`);
  console.log(
    `  headline ${meta.headlineSize.toFixed(1)}px / supporting ${meta.supportingSize.toFixed(1)}px ` +
      `-> ${outPath}`,
  );
  console.log(
    `  headline block ${meta.headlineBlockWidth.toFixed(1)}x${meta.headlineBlockHeight.toFixed(1)}px ` +
      `(guard: >= ${template.guards?.minHeadlineBlockWidth ?? 0}x${template.guards?.minHeadlineBlockHeight ?? 0}px)`,
  );
  console.log(
    `  full lockup ${meta.lockupWidth.toFixed(1)}x${meta.lockupHeight.toFixed(1)}px ` +
      `within safe zone ${meta.boxWidth.toFixed(1)}x${meta.boxHeight.toFixed(1)}px`,
  );
}

const requestedIds = process.argv.slice(2);
const toRender = requestedIds.length ? posts.filter((p) => requestedIds.includes(p.id)) : posts;

if (!toRender.length) {
  console.error('No matching post ids in config/posts.json for:', requestedIds.join(', '));
  process.exit(1);
}

for (const post of toRender) {
  await renderPost(post);
}
