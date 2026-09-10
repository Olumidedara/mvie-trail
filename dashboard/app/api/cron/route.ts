import { NextRequest, NextResponse } from "next/server";

import { CRON_SECRET } from "@/lib/config";
import { dispatchRun } from "@/lib/github";
import { getSchedule, markDispatched, wasDispatched } from "@/lib/schedule";

export const dynamic = "force-dynamic";

// Vercel Hobby crons may fire at most once per day, so the route decides the
// exact time. It dispatches once when "now" is within this many minutes after
// the configured schedule time.
const DISPATCH_WINDOW_MIN = 60;

function localParts(
  now: Date,
  timeZone: string
): { hour: number; minute: number; dayKey: string; weekday: string } {
  try {
    const fmt = new Intl.DateTimeFormat("en-US", {
      timeZone,
      hour: "2-digit",
      minute: "2-digit",
      weekday: "short",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour12: false,
    });
    const parts = fmt.formatToParts(now);
    const get = (t: string) => parts.find((p) => p.type === t)?.value ?? "";
    const hour = String(Number(get("hour")) % 24).padStart(2, "0");
    const minute = get("minute").padStart(2, "0");
    return {
      hour: Number(hour),
      minute: Number(minute),
      dayKey: `${get("year")}-${get("month")}-${get("day")}`,
      weekday: get("weekday").toLowerCase(),
    };
  } catch {
    const u = now.getUTCHours();
    const m = now.getUTCMinutes();
    return {
      hour: u,
      minute: m,
      dayKey: now.toISOString().slice(0, 10),
      weekday: ["sun", "mon", "tue", "wed", "thu", "fri", "sat"][now.getUTCDay()],
    };
  }
}

export async function GET(req: NextRequest) {
  if (CRON_SECRET) {
    const auth = req.headers.get("authorization") ?? "";
    if (auth !== `Bearer ${CRON_SECRET}` && req.headers.get("x-vercel-cron") !== "1") {
      return NextResponse.json({ error: "unauthorized" }, { status: 401 });
    }
  }
  const schedule = await getSchedule();
  if (!schedule.enabled) {
    return NextResponse.json({ ok: true, action: "disabled" });
  }
  const target = schedule.time.trim();
  if (target === "") return NextResponse.json({ ok: true, action: "no-time" });

  const [th, tm] = target.split(":").map((s) => Number(s));
  if (Number.isNaN(th) || Number.isNaN(tm)) {
    return NextResponse.json({ ok: true, action: "bad-time" });
  }

  const now = new Date();
  const { hour, minute, dayKey, weekday } = localParts(now, schedule.timezone);
  if (!schedule.days.includes(weekday)) {
    return NextResponse.json({ ok: true, action: "not-day" });
  }

  const targetMins = th * 60 + tm;
  const nowMins = hour * 60 + minute;
  if (nowMins < targetMins || nowMins >= targetMins + DISPATCH_WINDOW_MIN) {
    return NextResponse.json({ ok: true, action: "out-of-window" });
  }

  const slot = `${dayKey}-${target}`;
  if (await wasDispatched(slot)) {
    return NextResponse.json({ ok: true, action: "already" });
  }

  try {
    await dispatchRun({ count: schedule.max_videos_per_run });
    await markDispatched(slot);
    return NextResponse.json({ ok: true, action: "dispatched", slot });
  } catch (err: any) {
    return NextResponse.json(
      { ok: false, action: "error", error: err?.message ?? "dispatch failed" },
      { status: 500 }
    );
  }
}