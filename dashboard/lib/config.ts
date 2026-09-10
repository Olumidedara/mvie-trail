export const GITHUB_OWNER = process.env.NEXT_PUBLIC_GITHUB_OWNER ?? "";
export const GITHUB_REPO = process.env.NEXT_PUBLIC_GITHUB_REPO ?? "";
export const GH_PAT = process.env.GH_PAT ?? "";
export const CRON_SECRET = process.env.CRON_SECRET ?? "";

export function repoFull(): string {
  return `${GITHUB_OWNER}/${GITHUB_REPO}`;
}

export function configured(): boolean {
  return Boolean(GITHUB_OWNER && GITHUB_REPO);
}