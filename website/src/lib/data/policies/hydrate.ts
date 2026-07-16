import type { Block, PolicyDetail } from '../../types/policies';

// Resolves a version's block ids against the policy's dictionary into its
// ordered Block[]. Blocks are shared by reference across versions.
export function getVersion(detail: PolicyDetail, date: string): Block[] {
  const version = detail.versions.find((v) => v.date === date);
  if (!version) return [];
  return version.refs.map((ref, i) => ({ id: `${i}-${ref}`, ...detail.blocks[ref] }));
}
