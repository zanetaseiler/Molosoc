#!/usr/bin/env node
// Adds (or verifies) one master image's entry in masters/MANIFEST.json:
// computes its sha256 + dimensions and either appends a new manifest entry
// or, if one already exists for that filename, confirms it still matches.
//
// Usage:
//   node add_master.mjs masters/PRODUCT_042_kitchen-scene.png
//   node add_master.mjs masters/PRODUCT_042_kitchen-scene.png --source="https://drive.google.com/..." --note="from Q3 shoot"
//
// Run this once per new master, right after you copy it into masters/ —
// never hand-edit MANIFEST.json's sha256 field.

import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import sharp from 'sharp';

const args = process.argv.slice(2);
const filePathArg = args.find((a) => !a.startsWith('--'));
if (!filePathArg) {
  console.error('Usage: node add_master.mjs <path-to-master> [--source=<url-or-note>] [--note=<free-text>]');
  process.exit(1);
}
const sourceArg = args.find((a) => a.startsWith('--source='))?.slice('--source='.length);
const noteArg = args.find((a) => a.startsWith('--note='))?.slice('--note='.length);

const rootDir = process.cwd();
const filePath = path.resolve(filePathArg);
const filename = path.basename(filePath);
const manifestPath = path.join(rootDir, 'masters', 'MANIFEST.json');

if (!fs.existsSync(filePath)) {
  console.error(`File not found: ${filePath}`);
  process.exit(1);
}
if (!fs.existsSync(manifestPath)) {
  console.error(`No masters/MANIFEST.json found at ${manifestPath}. Create one first (see assets/manifest.example.json).`);
  process.exit(1);
}

const buffer = fs.readFileSync(filePath);
const sha256 = crypto.createHash('sha256').update(buffer).digest('hex');
const meta = await sharp(buffer).metadata();

const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
const existing = manifest.files.find((f) => f.filename === filename);

if (existing) {
  if (existing.sha256 === sha256) {
    console.log(`${filename}: already in manifest, sha256 matches. No change.`);
  } else {
    console.error(
      `${filename}: already in manifest but sha256 DIFFERS (manifest=${existing.sha256}, file=${sha256}). ` +
        `The file on disk has changed since it was added — masters are supposed to be read-only. ` +
        `If this is intentional (re-acquiring a corrected master), update the entry by hand and note why.`,
    );
    process.exit(1);
  }
} else {
  manifest.files.push({
    filename,
    sha256,
    width: meta.width,
    height: meta.height,
    importedAt: new Date().toISOString().slice(0, 10),
    ...(sourceArg ? { source: sourceArg } : {}),
    ...(noteArg ? { note: noteArg } : {}),
  });
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n');
  console.log(`${filename}: added to manifest (${meta.width}x${meta.height}, sha256 ${sha256.slice(0, 12)}...).`);
}
