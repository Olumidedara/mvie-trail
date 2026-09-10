export async function dispatchRun(args: { genre?: string; topic?: string; count?: number }): Promise<void> {
  const res = await fetch("/api/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(args),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error ?? "dispatch failed");
  }
}

export async function saveSchedule(patch: Record<string, unknown>): Promise<any> {
  const res = await fetch("/api/schedule", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });
  if (!res.ok) throw new Error("failed to save schedule");
  return res.json();
}