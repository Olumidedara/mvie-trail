import "server-only";

import { GH_PAT, configured, repoFull } from "./config";
import type { LibraryEntry, Release, WorkflowRun } from "./types";

const API = "https://api.github.com";

async function getJson(url: string, token?: string): Promise<any> {
  const headers: Record<string, string> = {
    Accept: "application/vnd.github+json",
    "User-Agent": "movie-storybot",
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(url, { headers, next: { revalidate: 60 } });
  if (!res.ok) throw new Error(`GitHub API ${res.status}: ${url}`);
  return res.json();
}

export async function getManifest(): Promise<LibraryEntry[]> {
  if (!configured()) return [];
  const url = `https://raw.githubusercontent.com/${repoFull()}/main/output/manifest.json`;
  const res = await fetch(url, { next: { revalidate: 60 } });
  if (!res.ok) return [];
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

export async function getReleases(): Promise<Release[]> {
  if (!configured()) return [];
  const data = await getJson(`${API}/repos/${repoFull()}/releases?per_page=50`);
  return Array.isArray(data) ? data : [];
}

export async function getWorkflowRuns(): Promise<WorkflowRun[]> {
  if (!configured()) return [];
  const data = await getJson(`${API}/repos/${repoFull()}/actions/runs?per_page=10`);
  return Array.isArray(data?.workflow_runs) ? data.workflow_runs : [];
}

export async function getRepositoryConfig(): Promise<any> {
  if (!configured()) return null;
  const url = `https://raw.githubusercontent.com/${repoFull()}/main/config.json`;
  const res = await fetch(url, { next: { revalidate: 300 } });
  if (!res.ok) return null;
  return res.json();
}

export async function dispatchRun(payload: { genre?: string; topic?: string; count?: number }): Promise<void> {
  if (!configured() || !GH_PAT) throw new Error("Missing GH_PAT or repo config");
  const body = {
    event_type: "run-pipeline",
    client_payload: {
      genre: payload.genre ?? "",
      topic: payload.topic ?? "",
      count: (payload.count ?? 3).toString(),
    },
  };
  const res = await fetch(`${API}/repos/${repoFull()}/dispatches`, {
    method: "POST",
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${GH_PAT}`,
      "User-Agent": "movie-storybot",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Dispatch failed ${res.status}: ${text}`);
  }
}