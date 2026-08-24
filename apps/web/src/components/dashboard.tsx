"use client";

import {
  ArrowUpRight, BriefcaseBusiness, ChevronDown, CircleAlert, FileSearch, Filter,
  LoaderCircle, LogOut, MapPin, Plus, RefreshCw, Search, Sparkles, X,
} from "lucide-react";
import { FormEvent, useCallback, useMemo, useState } from "react";
import Link from "next/link";

import { logout } from "@/app/actions";
import type { CollectionResult, Job, JobStats, JobStatus, PortfolioCollectionResult } from "@/lib/types";
import { JOB_STATUSES } from "@/lib/types";

type Props = { initialJobs: Job[]; initialStats: JobStats; online: boolean; authEnabled: boolean };
type Sort = "score" | "newest" | "company";

const stages: Array<{ key: "all" | JobStatus; label: string }> = [
  { key: "all", label: "All offers" }, { key: "new", label: "New" },
  { key: "shortlisted", label: "Shortlist" }, { key: "preparing", label: "Preparing" },
  { key: "applied", label: "Applied" }, { key: "interview", label: "Interview" },
];
const statusLabels: Record<JobStatus, string> = {
  new: "New", shortlisted: "Shortlisted", preparing: "Preparing", ready: "Ready",
  applied: "Applied", interview: "Interview", rejected: "Rejected", offer: "Offer", ignored: "Ignored",
};

function dateLabel(value: string) {
  const date = new Date(value.replace(" ", "T") + (value.includes("Z") ? "" : "Z"));
  return Number.isNaN(date.valueOf()) ? "Date unknown" : new Intl.DateTimeFormat("en", { month: "short", day: "numeric" }).format(date);
}

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`/api/backend${path}`, { cache: "no-store", ...options });
  const payload = await response.json();
  if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : "The request failed");
  return payload as T;
}

export function Dashboard({ initialJobs, initialStats, online, authEnabled }: Props) {
  const [jobs, setJobs] = useState(initialJobs);
  const [stats, setStats] = useState(initialStats);
  const [isOnline, setOnline] = useState(online);
  const [stage, setStage] = useState<"all" | JobStatus>("all");
  const [search, setSearch] = useState("");
  const [minScore, setMinScore] = useState(0);
  const [source, setSource] = useState("all");
  const [sort, setSort] = useState<Sort>("score");
  const [collectOpen, setCollectOpen] = useState(false);
  const [collecting, setCollecting] = useState(false);
  const [collectMessage, setCollectMessage] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  const [savingId, setSavingId] = useState<number | null>(null);

  const refresh = useCallback(async () => {
    setRefreshing(true);
    try {
      const [nextJobs, nextStats] = await Promise.all([api<Job[]>("/jobs?limit=200"), api<JobStats>("/stats")]);
      setJobs(nextJobs); setStats(nextStats); setOnline(true);
    } catch { setOnline(false); }
    finally { setRefreshing(false); }
  }, []);

  const sources = useMemo(() => [...new Set(jobs.map((job) => job.source))].sort(), [jobs]);
  const visible = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return jobs.filter((job) => {
      const text = `${job.title} ${job.company} ${job.location} ${job.description}`.toLowerCase();
      return (stage === "all" || job.status === stage) && job.score >= minScore
        && (source === "all" || job.source === source) && (!needle || text.includes(needle));
    }).sort((a, b) => {
      if (sort === "newest") return b.created_at.localeCompare(a.created_at);
      if (sort === "company") return a.company.localeCompare(b.company);
      return b.score - a.score;
    });
  }, [jobs, stage, minScore, source, search, sort]);

  async function updateStatus(job: Job, status: JobStatus) {
    const previous = job.status;
    setSavingId(job.id);
    setJobs((current) => current.map((item) => item.id === job.id ? { ...item, status } : item));
    try {
      await api(`/jobs/${job.id}/status`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status }) });
      setStats(await api<JobStats>("/stats"));
    } catch {
      setJobs((current) => current.map((item) => item.id === job.id ? { ...item, status: previous } : item));
    } finally { setSavingId(null); }
  }

  async function collect(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setCollecting(true); setCollectMessage("Searching the selected source…");
    try {
      if (data.get("source") === "ats-portfolio") {
        const result = await api<PortfolioCollectionResult>("/collect/portfolio", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: "stage stagiaire internship intern pfe", location: "France", limit_per_target: Number(data.get("limit")) }),
        });
        setCollectMessage(`${result.saved} relevant offers saved from ${result.targets} startup boards; ${result.skipped} unrelated listings skipped.`);
        await refresh();
        return;
      }
      const result = await api<CollectionResult>("/collect", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: data.get("source"), query: data.get("query"), location: "France", limit: Number(data.get("limit")) }),
      });
      setCollectMessage(`${result.saved} new offer${result.saved === 1 ? "" : "s"} saved. Your queue is current.`);
      await refresh();
    } catch (error) {
      setCollectMessage(`${error instanceof Error ? error.message : "Collection failed"}. Check the source configuration and retry.`);
    } finally { setCollecting(false); }
  }

  const clearFilters = () => { setSearch(""); setMinScore(0); setSource("all"); };

  return (
    <div className="min-h-screen min-w-0 overflow-x-hidden bg-paper text-ink">
      <a href="#job-list" className="fixed left-3 top-3 z-50 -translate-y-24 bg-ink px-4 py-2 text-sm font-bold text-white focus:translate-y-0">Skip to jobs</a>
      <header className="flex h-[68px] items-center gap-6 bg-ink px-5 text-white sm:px-8 lg:px-16">
        <Link href="/" className="flex items-center gap-3 text-[15px] font-bold tracking-[-0.01em]">
          <span className="grid size-8 place-items-center border border-slate-500"><BriefcaseBusiness size={17} aria-hidden /></span>
          PFE Job Copilot
        </Link>
        <div className="ml-auto hidden items-center gap-2 text-xs text-slate-300 sm:flex">
          <span className={`size-2 rounded-full ${isOnline ? "bg-emerald-400 shadow-[0_2px_8px_rgba(52,211,153,.35)]" : "bg-rose-400"}`} />
          {isOnline ? "Pipeline online" : "Pipeline needs attention"}
        </div>
        <button onClick={refresh} disabled={refreshing} aria-label="Refresh jobs" title="Refresh jobs" className="grid size-10 place-items-center rounded-full border border-slate-600 transition-colors hover:bg-slate-700 disabled:opacity-60">
          <RefreshCw size={17} className={refreshing ? "animate-spin" : ""} aria-hidden />
        </button>
        {authEnabled && <form action={logout}><button aria-label="Sign out" title="Sign out" className="grid size-10 place-items-center rounded-full border border-slate-600 transition-colors hover:bg-slate-700"><LogOut size={17} aria-hidden /></button></form>}
      </header>

      <main className="mx-auto w-full max-w-[1460px] px-5 pb-16 sm:px-8 lg:px-16">
        <section className="flex flex-col items-start justify-between gap-8 py-11 sm:py-14 lg:flex-row lg:items-end lg:py-20">
          <div>
            <h1 className="max-w-[860px] text-balance text-[clamp(2.8rem,6vw,5.5rem)] font-semibold leading-[.96] tracking-[-.035em]">Your next application starts here.</h1>
            <p className="mt-6 text-base text-muted sm:text-lg">{stats.total ? `${stats.total} offer${stats.total === 1 ? "" : "s"} indexed. ${stats.new ?? 0} waiting for review.` : "Your pipeline is ready. Run a collection to build the first queue."}</p>
          </div>
          <button onClick={() => setCollectOpen((value) => !value)} aria-expanded={collectOpen} className="inline-flex h-12 items-center gap-2 rounded-xl bg-cobalt px-5 font-bold text-white transition-colors hover:bg-cobalt-dark">
            {collectOpen ? <X size={18} aria-hidden /> : <Plus size={18} aria-hidden />} {collectOpen ? "Close" : "Collect jobs"}
          </button>
        </section>

        {collectOpen && <CollectionPanel collecting={collecting} message={collectMessage} onSubmit={collect} />}

        <nav aria-label="Application stages" className="queue-scrollbar -mx-5 flex overflow-x-auto border-y border-rule-dark px-5 sm:mx-0 sm:grid sm:grid-cols-3 sm:px-0 lg:grid-cols-6">
          {stages.map((item) => (
            <button key={item.key} onClick={() => setStage(item.key)} className={`flex min-w-[132px] items-baseline justify-between gap-3 border-r border-rule px-4 py-4 text-left text-sm transition-colors last:border-r-0 hover:bg-white ${stage === item.key ? "bg-cobalt-wash text-cobalt-dark shadow-[inset_0_-3px_0_var(--cobalt)]" : "text-muted"}`}>
              <span>{item.label}</span><strong className="text-lg text-current">{item.key === "all" ? stats.total : stats[item.key] ?? 0}</strong>
            </button>
          ))}
        </nav>

        <section className="grid gap-10 pt-10 lg:grid-cols-[240px_minmax(0,1fr)] lg:gap-14" aria-label="Job queue">
          <aside className="self-start lg:sticky lg:top-6">
            <div className="mb-6 flex items-center justify-between"><h2 className="flex items-center gap-2 text-lg font-bold"><Filter size={17} aria-hidden />Filter the dossier</h2><button onClick={clearFilters} className="text-xs font-bold text-cobalt-dark hover:underline">Clear</button></div>
            <div className="grid gap-5 sm:grid-cols-3 lg:grid-cols-1">
              <Field label="Search"><div className="relative"><Search size={17} className="pointer-events-none absolute left-3 top-3 text-muted" aria-hidden /><Input value={search} onChange={(e) => setSearch(e.target.value)} type="search" placeholder="Role, company, location" className="pl-9" /></div></Field>
              <Field label={`Minimum match · ${minScore}`}><input value={minScore} onChange={(e) => setMinScore(Number(e.target.value))} type="range" min="0" max="100" step="5" className="h-6 w-full accent-cobalt" /></Field>
              <Field label="Source"><Select value={source} onChange={(e) => setSource(e.target.value)}><option value="all">All sources</option>{sources.map((item) => <option key={item} value={item}>{item}</option>)}</Select></Field>
            </div>
            <div className="mt-6 flex gap-3 border-t border-rule pt-5 text-xs leading-5 text-muted"><Sparkles size={18} className="shrink-0 text-cobalt" aria-hidden /><p>Higher scores mean stronger alignment with your AI, software, and PFE profile.</p></div>
          </aside>

          <div className="min-w-0">
            <div className="flex flex-col justify-between gap-4 border-b-2 border-ink pb-5 sm:flex-row sm:items-start">
              <div><h2 className="text-xl font-bold">Opportunity queue</h2><p className="mt-1 text-sm text-muted">{visible.length} offer{visible.length === 1 ? "" : "s"} shown</p></div>
              <label className="flex items-center justify-between gap-3 text-xs font-bold text-muted">Sort<Select value={sort} onChange={(e) => setSort(e.target.value as Sort)} className="w-[150px]"><option value="score">Best match</option><option value="newest">Newest first</option><option value="company">Company A–Z</option></Select></label>
            </div>
            <div id="job-list" aria-live="polite">
              {!isOnline && !jobs.length ? <StateMessage icon={<CircleAlert />} title="The job queue did not load" copy="Start the FastAPI backend, then refresh this page." />
                : !visible.length ? <StateMessage icon={<FileSearch />} title={jobs.length ? "No offers match these filters" : "The dossier is empty"} copy={jobs.length ? "Clear a filter or lower the minimum match score to widen the queue." : "Open Collect jobs and run a focused France Travail search to add the first offers."} />
                : visible.map((job) => <JobRow key={job.id} job={job} saving={savingId === job.id} onStatus={updateStatus} />)}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

function CollectionPanel({ collecting, message, onSubmit }: { collecting: boolean; message: string; onSubmit: (event: FormEvent<HTMLFormElement>) => void }) {
  return <section className="mb-8 rounded-2xl bg-cobalt-dark p-6 text-white shadow-panel lg:p-7" aria-labelledby="collect-title">
    <div><h2 id="collect-title" className="text-xl font-bold">Run a focused search</h2><p className="mt-1 text-sm text-blue-100">Use official or public sources. Keep protected-board discovery small.</p></div>
    <form onSubmit={onSubmit} className="mt-6 grid items-end gap-4 md:grid-cols-[190px_minmax(260px,1fr)_90px_auto]">
      <Field label="Source"><Select name="source" defaultValue="france-travail"><option value="france-travail">France Travail</option><option value="ats-portfolio">Startup portfolio</option><option value="jobspy-indeed">Indeed via JobSpy</option><option value="jobspy-linkedin">LinkedIn via JobSpy</option><option value="jobspy-glassdoor">Glassdoor via JobSpy</option><option value="jobspy-google">Google Jobs</option><option value="adzuna">Adzuna</option></Select></Field>
      <Field label="Keywords"><Input name="query" defaultValue="stage PFE intelligence artificielle" required /></Field>
      <Field label="Limit"><Input name="limit" type="number" min="1" max="50" defaultValue="10" required /></Field>
      <button disabled={collecting} className="inline-flex h-11 items-center justify-center gap-2 rounded-xl bg-white px-5 font-bold text-cobalt-dark transition-colors hover:bg-blue-50 disabled:opacity-70">{collecting && <LoaderCircle size={17} className="animate-spin" />}Run collection</button>
    </form>
    <p role="status" aria-live="polite" className="mt-3 min-h-5 text-sm text-blue-100">{message}</p>
  </section>;
}

function JobRow({ job, saving, onStatus }: { job: Job; saving: boolean; onStatus: (job: Job, status: JobStatus) => void }) {
  return <article className="grid gap-4 border-b border-rule py-7 transition-colors hover:bg-white/60 sm:grid-cols-[64px_minmax(0,1fr)] lg:grid-cols-[70px_minmax(0,1fr)_155px] lg:gap-6">
    <div className="relative flex min-h-32 flex-col items-center justify-center overflow-hidden rounded-xl border border-rule bg-white" style={{ "--score-scale": Math.min(100, Math.max(0, job.score)) / 100 } as React.CSSProperties}>
      <span className="score-fill absolute inset-0 bg-cobalt-wash" /><strong className="relative text-2xl font-bold text-cobalt-dark">{Math.min(100, Math.max(0, job.score))}</strong><small className="relative mt-1 text-[9px] font-bold uppercase tracking-[.09em] text-muted">match</small>
    </div>
    <div className="min-w-0">
      <div className="flex items-center justify-between gap-4"><span className="text-[11px] font-extrabold uppercase tracking-[.07em] text-cobalt-dark">{job.source.replaceAll("-", " ")}</span><time className="text-xs text-muted" dateTime={job.created_at}>{dateLabel(job.created_at)}</time></div>
      <h3 className="mt-2 text-[clamp(1.25rem,2vw,1.75rem)] font-semibold leading-tight tracking-[-.02em]"><a href={job.url} target="_blank" rel="noreferrer" className="decoration-1 underline-offset-4 hover:text-cobalt-dark hover:underline">{job.title || "Untitled offer"}</a></h3>
      <p className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted"><strong className="text-ink">{job.company || "Company not listed"}</strong><span className="inline-flex items-center gap-1"><MapPin size={13} aria-hidden />{job.location || "Location not listed"}</span></p>
      <p className="job-description mt-4 max-w-[74ch] text-sm leading-6 text-slate-600">{job.description || "Open the original offer to read the full description."}</p>
    </div>
    <div className="col-start-auto flex items-end justify-between gap-4 sm:col-start-2 lg:col-start-auto lg:flex-col lg:items-stretch">
      <Field label="Status"><Select value={job.status} disabled={saving} onChange={(e) => onStatus(job, e.target.value as JobStatus)}>{JOB_STATUSES.map((status) => <option key={status} value={status}>{statusLabels[status]}</option>)}</Select></Field>
      <a href={job.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 whitespace-nowrap text-xs font-bold text-cobalt-dark hover:underline">Open offer<ArrowUpRight size={15} aria-hidden /></a>
    </div>
  </article>;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) { return <label className="grid gap-2 text-xs font-bold text-muted">{label}{children}</label>; }
function Input({ className = "", ...props }: React.InputHTMLAttributes<HTMLInputElement>) { return <input {...props} className={`h-11 w-full rounded-xl border border-rule-dark bg-white px-3 text-sm text-ink placeholder:text-slate-400 ${className}`} />; }
function Select({ className = "", children, ...props }: React.SelectHTMLAttributes<HTMLSelectElement>) { return <span className="relative block"><select {...props} className={`h-11 w-full appearance-none rounded-xl border border-rule-dark bg-white px-3 pr-9 text-sm text-ink ${className}`}>{children}</select><ChevronDown size={15} className="pointer-events-none absolute right-3 top-3.5 text-muted" aria-hidden /></span>; }
function StateMessage({ icon, title, copy }: { icon: React.ReactNode; title: string; copy: string }) { return <div className="grid place-items-center px-6 py-20 text-center text-cobalt"><span className="[&>svg]:size-11">{icon}</span><h3 className="mt-4 text-2xl font-bold text-ink">{title}</h3><p className="mt-2 max-w-md text-sm leading-6 text-muted">{copy}</p></div>; }
