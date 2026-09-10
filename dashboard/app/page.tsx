"use client";

import { useEffect, useState } from "react";

import { dispatchRun } from "@/lib/client";
import type { LibraryEntry, Schedule, WorkflowRun } from "@/lib/types";

type LibraryData = {
  entries: LibraryEntry[];
  runs: WorkflowRun[];
  config: { source?: { genres?: string[] }; schedule?: Partial<Schedule> } | null;
  configured: boolean;
};

export default function HomePage() {
  const [data, setData] = useState<LibraryData | null>(null);
  const [schedule, setSchedule] = useState<Schedule | null>(null);
  const [genre, setGenre] = useState("");
  const [topic, setTopic] = useState("");
  const [count, setCount] = useState(3);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetch("/api/library")
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setData);
    fetch("/api/schedule")
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setSchedule);
  }, []);

  useEffect(() => {
    if (data?.config?.source?.genres?.length && !genre) {
      setGenre(data.config.source.genres[0]);
    }
  }, [data, genre]);

  async function onRun(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      await dispatchRun({ genre, topic, count });
      setMessage("Pipeline dispatched. Check GitHub Actions for progress.");
    } catch (err: any) {
      setMessage(`Failed: ${err?.message ?? "unknown error"}`);
    } finally {
      setBusy(false);
      setTimeout(() => refresh(), 1500);
    }
  }

  async function refresh() {
    const r = await fetch("/api/library");
    if (r.ok) setData(await r.json());
  }

  const latestRun = data?.runs?.[0];
  const videos = data?.entries?.length ?? 0;

  return (
    <div className="space-y-8">
      <section className="rounded-2xl border border-line bg-panel p-6">
        <h1 className="text-2xl font-bold">Generate story videos</h1>
        <p className="text-sm text-zinc-400 mt-1">
          Picks royalty-free footage, writes a dramatic voiceover, renders vertical + landscape, and publishes to GitHub Releases. You post manually.
        </p>
        <form onSubmit={onRun} className="mt-5 grid gap-3 sm:grid-cols-4">
          <label className="block text-xs text-zinc-400 sm:col-span-1">
            Genre
            <input
              className="mt-1 w-full rounded-lg bg-ink border border-line px-3 py-2 text-sm outline-none focus:border-accent"
              value={genre}
              onChange={(e) => setGenre(e.target.value)}
              placeholder="vintage sci-fi"
            />
          </label>
          <label className="block text-xs text-zinc-400 sm:col-span-1">
            Topic (optional)
            <input
              className="mt-1 w-full rounded-lg bg-ink border border-line px-3 py-2 text-sm outline-none focus:border-accent"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="optional"
            />
          </label>
          <label className="block text-xs text-zinc-400 sm:col-span-1">
            Count
            <select
              className="mt-1 w-full rounded-lg bg-ink border border-line px-3 py-2 text-sm outline-none focus:border-accent"
              value={count}
              onChange={(e) => setCount(Number(e.target.value))}
            >
              {[1, 2, 3, 4].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </label>
          <div className="sm:col-span-1 flex items-end">
            <button
              type="submit"
              disabled={busy || !data?.configured}
              className="w-full rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-ink hover:opacity-90 disabled:opacity-40"
            >
              {busy ? "Dispatching…" : "Run now"}
            </button>
          </div>
        </form>
        {message && <p className="mt-3 text-sm text-accent">{message}</p>}
        {!data?.configured && (
          <p className="mt-3 text-sm text-red-400">
            GitHub repo not configured. Set NEXT_PUBLIC_GITHUB_OWNER / NEXT_PUBLIC_GITHUB_REPO.
          </p>
        )}
      </section>

      <section className="grid gap-4 sm:grid-cols-3">
        <Stat label="Videos generated" value={String(videos)} />
        <Stat
          label="Latest run"
          value={
            latestRun
              ? latestRun.conclusion ?? latestRun.status ?? "queued"
              : "no runs yet"
          }
          valueClass={
            latestRun?.conclusion === "success"
              ? "text-emerald-400"
              : latestRun?.conclusion
                ? "text-red-400"
                : ""
          }
        />
        <Stat
          label="Schedule"
          value={
            schedule
              ? schedule.enabled
                ? `${schedule.time} ${schedule.timezone} · ${schedule.days.length}d/wk`
                : "paused"
              : "…"
          }
        />
      </section>

      <section className="rounded-2xl border border-line bg-panel overflow-hidden">
        <div className="px-5 py-4 border-b border-line flex items-center justify-between">
          <h2 className="font-semibold">Recent pipeline runs</h2>
          <button onClick={refresh} className="text-xs text-zinc-400 hover:text-accent">
            Refresh
          </button>
        </div>
        <ul className="divide-y divide-line">
          {(data?.runs ?? []).length === 0 && (
            <li className="px-5 py-4 text-sm text-zinc-500">Nothing yet. Kick off a run above.</li>
          )}
          {(data?.runs ?? []).slice(0, 8).map((r) => (
            <li key={r.id} className="px-5 py-3 flex items-center justify-between gap-4">
              <div className="min-w-0">
                <p className="text-sm truncate">
                  <a
                    className="hover:text-accent"
                    href={r.html_url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    #{r.run_number} · {r.event}
                  </a>
                </p>
                <p className="text-xs text-zinc-500">{new Date(r.created_at).toLocaleString()}</p>
              </div>
              <span
                className={`text-xs font-medium px-2 py-1 rounded-full ${
                  r.conclusion === "success"
                    ? "bg-emerald-500/15 text-emerald-400"
                    : r.conclusion
                      ? "bg-red-500/15 text-red-400"
                      : "bg-zinc-500/15 text-zinc-300"
                }`}
              >
                {r.conclusion ?? r.status}
              </span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

function Stat({ label, value, valueClass = "" }: { label: string; value: string; valueClass?: string }) {
  return (
    <div className="rounded-2xl border border-line bg-panel px-5 py-4">
      <p className="text-xs text-zinc-500 uppercase tracking-wide">{label}</p>
      <p className={`mt-1 text-lg font-semibold capitalize ${valueClass}`}>{value}</p>
    </div>
  );
}