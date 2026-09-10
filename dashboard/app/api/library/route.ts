import { NextResponse } from "next/server";

import { configured } from "@/lib/config";
import { getManifest, getReleases, getRepositoryConfig, getWorkflowRuns } from "@/lib/github";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const [entries, releases, runs, config] = await Promise.all([
      getManifest(),
      getReleases(),
      getWorkflowRuns(),
      getRepositoryConfig(),
    ]);
    return NextResponse.json({ entries, releases, runs, config, configured: configured() });
  } catch (err: any) {
    return NextResponse.json({ error: err?.message ?? "failed" }, { status: 500 });
  }
}