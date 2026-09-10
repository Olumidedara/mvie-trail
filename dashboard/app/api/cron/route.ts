import { NextRequest, NextResponse } from "next/server";

import { CRON_SECRET } from "@/lib/config";
import { dispatchRun } from "@/lib/github";
import { getSchedule, markDispatched, wasDispatched } from "@/lib/schedule";

export const dynamic = "force-dynamic";

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
  const now = new Date();
  let minute: string;
  let hour: string;
  try {
    const parts = new Intl.DateTimeFormat("en-US", {
      timeZone: schedule.timezone,
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).formatToParts(now);
    const get = (t: string) => parts.find((p) => p.type === t)?.value ?? "0";
    hour = String(Number(get("hour")) % 24).padStart(2, "0");
    minute = get("minute").padStart(2, "0");
  } catch {
    hour = String(now.getUTCHours()).padStart(2, "0");
    minute = String(now.getUTCMinutes()).padStart(2, "0");
  }
  const day = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"][now.getUTCDay()];
  const target = schedule.time.trim();
  if (target === "") return NextResponse.json({ ok: true, action: "no-time" });
  if (hour !== target.slice(0, 2)) return NextResponse.json({ ok: true, action: "not-hour" });
  if (minute.length < 2 || Number(minute) % 15 !== 0) {
    return NextResponse.json({ ok: true, action: "not-slot" });
  }
  if (!schedule.days.includes(day)) return NextResponse.json({ ok: true, action: "not-day" });
  const slot = `${now.toISOString().slice(0, 10)}-${hour}:${minute}`;
  if (await wasDispatched(slot)) return NextResponse.json({ ok: true, action: "already" });

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