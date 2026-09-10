import { NextResponse } from "next/server";

import { GH_PAT } from "@/lib/config";
import { dispatchRun } from "@/lib/github";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  if (!GH_PAT) {
    return NextResponse.json({ error: "GH_PAT not configured on server" }, { status: 401 });
  }
  try {
    const body = await req.json();
    await dispatchRun({
      genre: body.genre ?? "",
      topic: body.topic ?? "",
      count: Number(body.count) || 3,
    });
    return NextResponse.json({ ok: true });
  } catch (err: any) {
    return NextResponse.json({ error: err?.message ?? "dispatch failed" }, { status: 500 });
  }
}