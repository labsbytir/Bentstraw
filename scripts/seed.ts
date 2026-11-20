import { PGlite } from '@electric-sql/pglite';
import { readdir, readFile } from 'node:fs/promises';
import legacy from '../data/seed.json' with { type: 'json' };

// shortcut: url/install stay in bundles only (search reads name/blurb/tags); add columns if pages need links.
const rows: any[] = [...(legacy as any[])];
for (const f of (await readdir('./data/seed')).filter((f) => f.endsWith('.json')).sort()) {
  rows.push(...JSON.parse(await readFile(`./data/seed/${f}`, 'utf8')));
}

// shortcut: plain tables, no pgvector yet — Orama owns vectors; add vector ext when dims lock.
const db = new PGlite('./data/bentstraw/');
await db.exec(`CREATE TABLE IF NOT EXISTS items (id TEXT PRIMARY KEY, kind TEXT, name TEXT, blurb TEXT, tags JSONB, past BOOLEAN, views INT DEFAULT 0);`);
for (const r of rows) {
  await db.query(`INSERT INTO items (id,kind,name,blurb,tags,past) VALUES ($1,$2,$3,$4,$5,$6) ON CONFLICT (id) DO UPDATE SET name=$3, blurb=$4, tags=$5`, [r.id, r.kind, r.name, r.blurb, JSON.stringify(r.tags), r.past]);
}
const n = await db.query(`SELECT count(*) FROM items`);
console.log('seeded', (n.rows[0] as any).count);
