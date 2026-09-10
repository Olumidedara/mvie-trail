import { kv } from "@vercel/kv";

import { DAYS } from "./types";
import type { Schedule } from "./types";

const KEY = "schedule";
const DISPATCH_KEY = "schedule:last_dispatch";

const DEFAULT_SCHEDULE: Schedule = {
  enabled: true,
  time: "09:00",
  days: [...DAYS],
  max_videos_per_run: 3,
  timezone: "UTC",
};

let memory: Schedule | null = null;
const memorySlots = new Set<string>();

export async function getSchedule(): Promise<Schedule> {
  try {
    const stored = await kv.get<Schedule>(KEY);
    if (stored) return { ...DEFAULT_SCHEDULE, ...stored };
  } catch {
    // KV unavailable (e.g. local dev) — fall through
  }
  return memory ?? DEFAULT_SCHEDULE;
}

export async function saveSchedule(patch: Partial<Schedule>): Promise<Schedule> {
  const current = await getSchedule();
  const merged: Schedule = {
    ...DEFAULT_SCHEDULE,
    ...current,
    ...patch,
    days: patch.days?.length ? patch.days : current.days,
  };
  try {
    await kv.set(KEY, merged);
  } catch {
    memory = merged;
  }
  return merged;
}

export async function wasDispatched(slot: string): Promise<boolean> {
  if (memorySlots.has(slot)) return true;
  try {
    return (await kv.get<string>(DISPATCH_KEY)) === slot;
  } catch {
    return memorySlots.has(slot);
  }
}

export async function markDispatched(slot: string): Promise<void> {
  memorySlots.add(slot);
  try {
    await kv.set(DISPATCH_KEY, slot);
  } catch {
    // best effort
  }
}