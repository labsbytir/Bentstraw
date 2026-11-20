import { PGlite } from '@electric-sql/pglite';
import { create, insertMultiple, save } from '@orama/orama';
import { writeFile, mkdir } from 'node:fs/promises';

// Orama schema: full-text + tags; vector added when embedding dims lock (384 gte-small).
const db = new PGlite('./data/bentstraw/');
const { rows } = await db.query(`SELECT id,kind,name,blurb,tags,past FROM items`);
const odx = create({ schema: { id: 'string', kind: 'string', name: 'string', blurb: 'string', tags: 'string[]' } });
await insertMultiple(odx, (rows as any[]).map(r => ({ id: r.id, kind: r.kind, name: r.name, blurb: r.blurb, tags: Array.isArray(r.tags) ? r.tags : JSON.parse(r.tags) })));
await mkdir('./public', { recursive: true });
await writeFile('./public/orama.json', JSON.stringify(await save(odx)));
console.log('orama docs', rows.length);
