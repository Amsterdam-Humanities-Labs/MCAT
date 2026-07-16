import { readdir, readFile, writeFile, mkdir, rm } from 'node:fs/promises';
import { join } from 'node:path';
import { splitBlocks } from '../src/lib/data/policies/blocks';
import { diffVersions, countWords } from '../src/lib/data/policies/diff';
import type {
  Block,
  BlockContent,
  ChangeStat,
  PlatformGroup,
  PolicyDetail,
  PolicyIndexEntry,
  PolicyManifest,
  VersionRef,
} from '../src/lib/types/policies';

const CONTENT = 'src/content/policies';
const OUT = 'static/policies';

const slugify = (s: string) =>
  s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

// Folder: '<Platform> - <qualifier?> - <Policy Title>'
function parseFolder(name: string) {
  const parts = name.split(' - ').map((s) => s.trim());
  const platformLabel = parts[0];
  const title = parts.length > 2 ? parts.slice(2).join(' - ') : parts[parts.length - 1];
  return { platformId: slugify(platformLabel), platformLabel, title };
}

// Filename: '<stamp>_<platform>_<name>.md', stamp = 'YYYY-MM-DD' or 'YYYY-MM-DDTHH-MM-SSZ'
function parseVersion(filename: string) {
  const stamp = filename.split('_')[0];
  const date = stamp.slice(0, 10);
  const label = stamp.includes('T')
    ? `${date} ${stamp.slice(11, 19).replace(/-/g, ':')}`
    : date;
  return { date: stamp, label };
}

// Stores each unique block once; versions reference blocks by index.
function dedupe(parsed: { date: string; label: string; blocks: Block[] }[]) {
  const blocks: BlockContent[] = [];
  const seen = new Map<string, number>();
  const versions: VersionRef[] = parsed.map((v) => ({
    date: v.date,
    label: v.label,
    refs: v.blocks.map((b) => {
      const key = `${b.type}|${b.depth ?? 0}|${b.text}`;
      let id = seen.get(key);
      if (id === undefined) {
        id = blocks.length;
        blocks.push({ type: b.type, depth: b.depth, text: b.text });
        seen.set(key, id);
      }
      return id;
    }),
  }));
  return { blocks, versions };
}

async function main() {
  await rm(OUT, { recursive: true, force: true });
  await mkdir(OUT, { recursive: true });

  const folders = (await readdir(CONTENT, { withFileTypes: true })).filter((d) =>
    d.isDirectory(),
  );
  const groups = new Map<string, PlatformGroup>();

  console.log('Generated policies:');
  for (const folder of folders) {
    const { platformId, platformLabel, title } = parseFolder(folder.name);
    const slug = `${platformId}/${slugify(title)}`;

    // 1. Parse every snapshot into blocks.
    const files = (await readdir(join(CONTENT, folder.name))).filter((f) => f.endsWith('.md'));
    const parsed: { date: string; label: string; blocks: Block[] }[] = [];
    for (const file of files) {
      const { date, label } = parseVersion(file);
      const raw = await readFile(join(CONTENT, folder.name, file), 'utf8');
      parsed.push({ date, label, blocks: splitBlocks(raw) });
    }
    parsed.sort((a, b) => (a.date < b.date ? -1 : 1));

    // 2. Change stats from consecutive diffs.
    const changes: ChangeStat[] = [];
    for (let i = 1; i < parsed.length; i++) {
      const { added, removed } = countWords(diffVersions(parsed[i - 1].blocks, parsed[i].blocks));
      changes.push({ date: parsed[i].date, label: parsed[i].label, added, removed });
    }

    // 3. Dedupe into a dictionary + ref lists, then write the policy file.
    const { blocks, versions } = dedupe(parsed);
    const detail: PolicyDetail = { slug, title, platform: platformId, blocks, versions, changes };
    await mkdir(join(OUT, platformId), { recursive: true });
    await writeFile(join(OUT, `${slug}.json`), JSON.stringify(detail));

    const entry: PolicyIndexEntry = {
      slug,
      title,
      platform: platformId,
      versionCount: versions.length,
      firstDate: versions[0]?.label ?? '',
      lastDate: versions[versions.length - 1]?.label ?? '',
    };
    const group = groups.get(platformId) ?? { id: platformId, label: platformLabel, policies: [] };
    group.policies.push(entry);
    groups.set(platformId, group);

    const instances = parsed.reduce((n, v) => n + v.blocks.length, 0);
    console.log(
      `  ${slug} — ${versions.length} versions, ${blocks.length} unique blocks ` +
        `(${instances} instances, ${(instances / blocks.length).toFixed(1)}x deduped)`,
    );
  }

  const manifest: PolicyManifest = [...groups.values()];
  await writeFile(join(OUT, 'manifest.json'), JSON.stringify(manifest));
}

main();
