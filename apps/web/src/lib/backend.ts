import "server-only";
import type { Job, JobStats } from "@/lib/types";

const backendUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";

export async function getDashboardData(): Promise<{ jobs: Job[]; stats: JobStats; online: boolean }> {
  try {
    const [jobsResponse, statsResponse] = await Promise.all([
      fetch(`${backendUrl}/jobs?limit=200`, { cache: "no-store" }),
      fetch(`${backendUrl}/stats`, { cache: "no-store" }),
    ]);
    if (!jobsResponse.ok || !statsResponse.ok) throw new Error("Backend response failed");
    return { jobs: await jobsResponse.json(), stats: await statsResponse.json(), online: true };
  } catch {
    return { jobs: [], stats: { total: 0 }, online: false };
  }
}
