import { readdir, readFile } from 'node:fs/promises';
import { join } from 'node:path';

export const KINDS = ['prompts', 'skills', 'repos', 'models', 'mcp', 'icons'] as const;
export type Kind = (typeof KINDS)[number];

export type Item = {
  id: string;
  kind: string;
  name: string;
  blurb: string;
  url?: string;
  install?: string;
  tags?: string[];
  past?: boolean;
};

let cache: Item[] | null = null;

export function isKind(value: string): value is Kind {
  return (KINDS as readonly string[]).includes(value);
}

export async function loadItems(): Promise<Item[]> {
  if (cache) return cache;
  const dir = join(process.cwd(), 'data/seed');
  const files = (await readdir(dir)).filter((f) => f.endsWith('.json')).sort();
  const rows: Item[] = [];
  for (const file of files) {
    rows.push(...JSON.parse(await readFile(join(dir, file), 'utf8')));
  }
  cache = rows;
  return rows;
}

export async function itemsByKind(kind: string): Promise<Item[]> {
  return (await loadItems()).filter((row) => row.kind === kind);
}

export async function findItem(kind: string, slug: string): Promise<Item | undefined> {
  const id = `${kind}/${slug}`;
  return (await loadItems()).find((row) => row.id === id);
}
