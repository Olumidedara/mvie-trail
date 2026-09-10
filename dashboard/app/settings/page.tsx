"use client";

import { useEffect, useState } from "react";

import { saveSchedule } from "@/lib/client";
import { DAYS } from "@/lib/types";
import type { Schedule } from "@/lib/types";

const DAY_LABELS: Record<string, string> = {
  mon: "Mon",
  tue: "Tue",
  wed: "Wed",
  thu: "Thu",
  fri: "Fri",
  sat: "Sat",
  sun: "Sun",
};

export default function SettingsPage() {
  const [schedule, setSchedule] = useState<Schedule | null>(null);
  const [genres, setGenres] = useState<string[]>([]);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    (async () => {
      const s = await fetch("/api/schedule").then((r) => r.json());
      setSchedule(s);
      const lib = await fetch("/api/library").then((r) => r.json()).catch(() => null);
      setGenres(lib?.config?.source?.genres ?? []);
    })();
  }, []);

  if (!schedule) return <p className="text-sm text-zinc-500">Loading…</p>;

  function toggleDay(d: string) {
    if (!schedule) return;
    const days = schedule.days.includes(d)
      ? schedule.days.filter((x) => x !== d)
      : [...schedule.days, d].sort((a, b) => DAYS.indexOf(a) - DAYS.indexOf(b));
    setSchedule({ ...schedule, days });
    setSaved(false);
  }

  async function onSave() {
    await saveSchedule({ ...schedule });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  const inputCls =
    "mt-1 rounded-lg bg-ink border border-line px-3 py-2 text-sm outline-none focus:border-accent";

  return (
    <div className="space-y-8 max-w-2xl">
      <header>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-sm text-zinc-400">Automation schedule. Vercel Cron polls this and triggers the pipeline.</p>
      </header>

      <section className="rounded-2xl border border-line bg-panel p-6 space-y-5">
        <h2 className="font-semibold">Schedule</h2>

        <label className="flex items-center justify-between text-sm">
          <span>Automatic generation</span>
          <input
            type="checkbox"
            checked={schedule.enabled}
            onChange={(e) => {
              setSchedule({ ...schedule, enabled: e.target.checked });
              setSaved(false);
            }}
            className="h-4 w-4 accent-accent"
          />
        </label>

        <div className="grid grid-cols-2 gap-3">
          <label className="block text-xs text-zinc-400">
            Time (HH:MM)
            <input
              className={inputCls + " w-full"}
              type="time"
              value={schedule.time}
              onChange={(e) => {
                setSchedule({ ...schedule, time: e.target.value });
                setSaved(false);
              }}
            />
          </label>
          <label className="block text-xs text-zinc-400">
            Timezone (IANA)
            <input
              className={inputCls + " w-full"}
              value={schedule.timezone}
              placeholder="UTC"
              onChange={(e) => {
                setSchedule({ ...schedule, timezone: e.target.value });
                setSaved(false);
              }}
            />
          </label>
        </div>

        <label className="block text-xs text-zinc-400">
          Videos per run
          <select
            className={inputCls + " w-full"}
            value={schedule.max_videos_per_run}
            onChange={(e) => {
              setSchedule({ ...schedule, max_videos_per_run: Number(e.target.value) });
              setSaved(false);
            }}
          >
            {[1, 2, 3, 4].map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </label>

        <div>
          <p className="text-xs text-zinc-400 mb-2">Days of the week</p>
          <div className="flex flex-wrap gap-1.5">
            {DAYS.map((d) => (
              <button
                key={d}
                type="button"
                onClick={() => toggleDay(d)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
                  schedule.days.includes(d)
                    ? "bg-accent text-ink border-accent"
                    : "bg-ink border-line text-zinc-400"
                }`}
              >
                {DAY_LABELS[d]}
              </button>
            ))}
          </div>
        </div>

        {genres.length > 0 && (
          <div>
            <p className="text-xs text-zinc-400">Source genres (from repo config.json)</p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {genres.map((g) => (
                <span key={g} className="text-xs px-2 py-1 rounded-full bg-line/50 text-zinc-300">
                  {g}
                </span>
              ))}
            </div>
          </div>
        )}

        <button
          onClick={onSave}
          className="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-ink hover:opacity-90"
        >
          Save schedule
        </button>
        {saved && <span className="ml-3 text-sm text-emerald-400">Saved ✓</span>}
      </section>

      <section className="rounded-2xl border border-line bg-panel p-6 text-sm text-zinc-400 space-y-2">
        <h2 className="font-semibold text-zinc-200">How it works</h2>
        <p>1 · Vercel Cron hits /api/cron every 15 minutes.</p>
        <p>2 · If the day + time matches your schedule, it dispatches a GitHub Actions run.</p>
        <p>3 · The runner generates videos, uploads them to GitHub Releases, and commits the manifest.</p>
        <p>4 · Download from Library and post manually (YouTube / TikTok / Instagram).</p>
      </section>
    </div>
  );
}