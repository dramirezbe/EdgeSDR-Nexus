#!/usr/bin/env node

/**
 * verify-scaffold.js
 *
 * Validates scaffold integrity against manifest.json:
 *   1. Every path in manifest.json exists on disk
 *   2. Every section in INDEX.md has a matching manifest entry
 *   3. No orphan scaffold files (files in scaffold/ not in manifest)
 *
 * Usage: node scaffold/_meta/verify-scaffold.js
 *
 * Output: JSON { valid: boolean, errors: string[], warnings: string[] }
 */

const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "../..");
const MANIFEST_PATH = path.join(ROOT, "scaffold/_meta/manifest.json");
const INDEX_PATH = path.join(ROOT, "scaffold/INDEX.md");

function loadManifest() {
  const raw = fs.readFileSync(MANIFEST_PATH, "utf-8");
  return JSON.parse(raw);
}

function readIndexSections() {
  const raw = fs.readFileSync(INDEX_PATH, "utf-8");
  const sections = [];
  // Match markdown table rows: | section | ... | [link](path) |
  const tableRowRegex = /^\|\s*\[?(\w+)\]?\s*\|[^|]*\|\s*\[.*?\]\(([^)]+)\)/gm;
  let match;
  while ((match = tableRowRegex.exec(raw)) !== null) {
    sections.push(match[2].trim());
  }
  return sections;
}

function getAllScaffoldFiles(dir) {
  const files = [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === "node_modules" || entry.name === ".git") continue;
      files.push(...getAllScaffoldFiles(fullPath));
    } else {
      files.push(fullPath);
    }
  }
  return files;
}

function main() {
  const errors = [];
  const warnings = [];

  // Load manifest
  let manifest;
  try {
    manifest = loadManifest();
  } catch (e) {
    errors.push(`Failed to parse manifest.json: ${e.message}`);
    console.log(JSON.stringify({ valid: false, errors, warnings }, null, 2));
    process.exit(1);
  }

  const manifestPaths = manifest.sections.map((s) => s.path);

  // Check 1: Every manifest path exists on disk
  for (const relPath of manifestPaths) {
    const fullPath = path.join(ROOT, relPath);
    if (!fs.existsSync(fullPath)) {
      errors.push(`Manifest path does not exist: ${relPath}`);
    }
  }

  // Check 2: Every INDEX.md section has a manifest entry
  let indexSections = [];
  try {
    indexSections = readIndexSections();
  } catch (e) {
    warnings.push(`Could not parse INDEX.md sections: ${e.message}`);
  }

  for (const sectionPath of indexSections) {
    if (!manifestPaths.includes(sectionPath)) {
      errors.push(`INDEX.md section not in manifest: ${sectionPath}`);
    }
  }

  // Check 3: No orphan scaffold files
  const scaffoldDir = path.join(ROOT, "scaffold");
  const allFiles = getAllScaffoldFiles(scaffoldDir);

  // Normalize manifest paths to absolute
  const manifestAbsPaths = new Set(
    manifestPaths.map((p) => path.join(ROOT, p))
  );

  for (const file of allFiles) {
    const relFromRoot = path.relative(ROOT, file);
    if (!manifestAbsPaths.has(file)) {
      // Skip _meta files (they are meta, not scaffold sections)
      if (relFromRoot.startsWith("scaffold/_meta/")) continue;
      warnings.push(`Orphan file not in manifest: ${relFromRoot}`);
    }
  }

  const valid = errors.length === 0;
  const result = { valid, errors, warnings };

  console.log(JSON.stringify(result, null, 2));

  if (!valid) {
    process.exit(1);
  }
}

main();
