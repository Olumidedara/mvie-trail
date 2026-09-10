import { getSchedule, saveSchedule } from "@/lib/schedule";
import type { Schedule } from "@/lib/types";

export const dynamic = "force-dynamic";

export async function GET() {
  return Response.json(await getSchedule());
}

export async function PUT(req: Request) {
  try {
    const body = (await req.json()) as Partial<Schedule>;
    const saved = await saveSchedule(body);
    return Response.json(saved);
  } catch {
    return Response.json({ error: "invalid schedule" }, { status: 400 });
  }
}