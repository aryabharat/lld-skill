// Structural checks for the plugin: manifests, skills, rule copies, links.
// Run: npm test   (node --test)
const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const root = path.join(__dirname, '..');
const read = (rel) => fs.readFileSync(path.join(root, rel), 'utf8');
const pkg = JSON.parse(read('package.json'));

const manifests = [
  '.claude-plugin/plugin.json',
  '.claude-plugin/marketplace.json',
  '.codex-plugin/plugin.json',
  '.github/plugin/plugin.json',
  '.github/plugin/marketplace.json',
  'gemini-extension.json',
  'plugin.json',
];

test('every manifest is valid JSON and versions match package.json', () => {
  for (const m of manifests) {
    const json = JSON.parse(read(m));
    if (json.version) assert.strictEqual(json.version, pkg.version, `${m} version`);
    if (json.plugins) for (const p of json.plugins) if (p.version) assert.strictEqual(p.version, pkg.version, `${m} plugin version`);
  }
});

function frontmatter(text) {
  const m = text.match(/^---\n([\s\S]*?)\n---\n/);
  assert.ok(m, 'missing frontmatter');
  const out = {};
  let key = null;
  for (const line of m[1].split('\n')) {
    const kv = line.match(/^([a-z_-]+):\s*(.*)$/);
    if (kv) { key = kv[1]; out[key] = kv[2].replace(/^>\s*$/, '').trim(); }
    else if (key) out[key] = (out[key] + ' ' + line.trim()).trim();
  }
  return out;
}

const skillDirs = fs.readdirSync(path.join(root, 'skills')).filter((d) =>
  fs.existsSync(path.join(root, 'skills', d, 'SKILL.md')));

test('each skill has name matching its folder and a useful description', () => {
  assert.ok(skillDirs.length >= 4, 'expected at least 4 skills');
  for (const d of skillDirs) {
    const fm = frontmatter(read(`skills/${d}/SKILL.md`));
    assert.strictEqual(fm.name, d, `skills/${d} name`);
    assert.ok(fm.description && fm.description.length > 80, `skills/${d} description too short`);
    assert.ok(fm.description.length <= 1024, `skills/${d} description over 1024 chars`);
  }
});

test('agents have frontmatter with name and description', () => {
  for (const f of fs.readdirSync(path.join(root, 'agents'))) {
    const fm = frontmatter(read(`agents/${f}`));
    assert.strictEqual(fm.name + '.md', f);
    assert.ok(fm.description);
  }
});

test('host rule files are in sync with AGENTS.md', () => {
  execFileSync(process.execPath, [path.join(root, 'scripts/sync-rules.js'), '--check'], { stdio: 'pipe' });
});

function mdFiles(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) return e.name === 'node_modules' || e.name.startsWith('.git') ? [] : mdFiles(p);
    return e.name.endsWith('.md') ? [p] : [];
  });
}

test('relative markdown links resolve', () => {
  const broken = [];
  for (const file of mdFiles(root)) {
    const text = fs.readFileSync(file, 'utf8').replace(/```[\s\S]*?```/g, '');
    for (const m of text.matchAll(/\]\(([^)\s#]+)(#[^)]*)?\)/g)) {
      const target = m[1];
      if (/^[a-z]+:/i.test(target)) continue;
      if (!fs.existsSync(path.resolve(path.dirname(file), target))) broken.push(`${path.relative(root, file)} -> ${target}`);
    }
  }
  assert.deepStrictEqual(broken, []);
});

test('gemini commands are valid toml-ish with description and prompt', () => {
  for (const f of fs.readdirSync(path.join(root, 'commands'))) {
    const t = read(`commands/${f}`);
    assert.match(t, /^description = ".+"$/m, f);
    assert.match(t, /^prompt = """[\s\S]+"""\s*$/m, f);
  }
});
