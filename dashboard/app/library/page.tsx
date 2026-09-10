"use client";

import { useEffect, useState } from "react";

import type { LibraryEntry, Release } from "@/lib/types";

type LibraryData = {
  entries: LibraryEntry[];
  releases: Release[];
  configured: boolean;
};

const TAGS: Record<string, string> = {
  vertical: "Vertical 9:16",
  landscape: "Landscape 16:9",
};

export default function LibraryPage() {
  const [data, setData] = useState<LibraryData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("/api/library")
      .then((r) => {
        if (!r.ok) throw new Error("failed to load");
        return r.json();
      })
      .then(setData)
      .catch((e) => setError(String(e?.message ?? e)));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Library</h1>
          <p className="text-sm text-zinc-400">Ready-to-post videos with captions.</p>
        </div>
        <span className="text-sm text-zinc-500">{data?.entries?.length ?? 0} videos</span>
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}
      {data && data.entries.length === 0 && (
        <div className="rounded-2xl border border-dashed border-line p-10 text-center text-zinc-500 text-sm">
          No videos yet. Trigger a run from Home.
        </div>
      )}

      <div className="space-y-4">
        {(data?.entries ?? []).map((entry) => (
          <article key={entry.id} className="rounded-2xl border border-line bg-panel overflow-hidden">
            <div className="px-5 py-4 flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <h2 className="font-semibold text-lg">{entry.title}</h2>
                  {entry.release && (
                    <a
                      href={entry.release.html_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs text-accent hover:underline"
                    >
                      release ↗
                    </a>
                  )}
                </div>
                <p className="text-xs text-zinc-500 mt-1">
                  {new Date(entry.created_at).toLocaleString()} · {entry.genre}
                </p>
              </div>
              <div className="flex gap-2">
                {["vertical", "landscape"].map((k) => {
                  const url = entry.videos?.[k]?.browser_download_url;
                  return (
                    <a
                      key={k}
                      href={url ?? "#"}
                      target="_blank"
                      rel="noreferrer"
                      className={`rounded-lg px-3 py-1.5 text-xs font-medium ${
                        url
                          ? "bg-accent text-ink hover:opacity-90"
                          : "bg-line/40 text-zinc-500 cursor-not-allowed"
                      }`}
                    >
                      {TAGS[k]}
                    </a>
                  );
                })}
              </div>
            </div>
            <div className="px-5 pb-4">
              <div className="flex flex-wrap gap-1.5">
                {(entry.tags ?? []).slice(0, 6).map((t) => (
                  <span key={t} className="text-[11px] px-2 py-0.5 rounded-full bg-line/50 text-zinc-300">
                    #{t}
                  </span>
                ))}
              </div>
              {entry.hook && (
                <p className="mt-3 text-sm italic text-zinc-300">“{entry.hook}”</p>
              )}
              <details className="mt-3 group">
                <summary className="cursor-pointer text-xs text-accent">Captions / narration script</summary>
                <pre className="mt-2 whitespace-pre-wrap text-xs text-zinc-300 bg-ink/60 rounded-lg p-3">
                  {entry.captions}
                </pre>
              </details>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}