#!/usr/bin/env node
// Copies the canonical AGENTS.md ruleset into each host's rule file.
// Run after editing AGENTS.md:   node scripts/sync-rules.js
// Check only (used by CI/tests): node scripts/sync-rules.js --check
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const body = fs.readFileSync(path.join(root, 'AGENTS.md'), 'utf8').replace(/\r\n/g, '\n').trim() + '\n';

const targets = {
  '.cursor/rules/lld.mdc':
    '---\ndescription: Low-level design rules (classes, APIs, patterns, concurrency, tests)\nalwaysApply: true\n---\n\n' + body,
  '.windsurf/rules/lld.md': body,
  '.clinerules/lld.md': body,
  '.agents/rules/lld.md': body,
  '.kiro/steering/lld.md': '---\ntitle: Low-level design rules\ninclusion: always\n---\n\n' + body,
  '.github/copilot-instructions.md': body,
};

const check = process.argv.includes('--check');
let drift = [];
for (const [rel, content] of Object.entries(targets)) {
  const file = path.join(root, rel);
  const current = fs.existsSync(file) ? fs.readFileSync(file, 'utf8') : null;
  if (current === content) continue;
  if (check) drift.push(rel);
  else {
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, content);
    console.log('wrote ' + rel);
  }
}
if (drift.length) {
  console.error('Out of sync with AGENTS.md: ' + drift.join(', ') + '\nRun: node scripts/sync-rules.js');
  process.exit(1);
}

module.exports = { targets };
