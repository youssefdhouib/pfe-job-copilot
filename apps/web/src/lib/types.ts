export const JOB_STATUSES = [
  "new", "shortlisted", "preparing", "ready", "applied", "interview", "rejected", "offer", "ignored",
] as const;

export type JobStatus = (typeof JOB_STATUSES)[number];
export type Job = {
  id: number; title: string; company: string; location: string; url: string; source: string;
  description: string; score: number; status: JobStatus; created_at: string; updated_at: string;
};
export type JobStats = Partial<Record<JobStatus, number>> & { total: number };
export type CollectionResult = { source: string; query: string; saved: number };
export type PortfolioCollectionResult = { targets: number; saved: number; skipped: number };
