import { BriefcaseBusiness, LockKeyhole } from "lucide-react";

import { login } from "@/app/login/actions";

type Props = {
  searchParams: Promise<{ error?: string; message?: string }>;
};

export default async function LoginPage({ searchParams }: Props) {
  const params = await searchParams;
  const notice = params.error ?? params.message;

  return (
    <main className="grid min-h-screen bg-paper px-5 py-10 text-ink lg:grid-cols-[minmax(0,1.05fr)_minmax(420px,.95fr)] lg:p-5">
      <section className="hidden min-h-[calc(100vh-2.5rem)] flex-col justify-between overflow-hidden rounded-3xl bg-ink p-12 text-white lg:flex">
        <div className="flex items-center gap-3 text-sm font-bold">
          <span className="grid size-9 place-items-center border border-slate-500"><BriefcaseBusiness size={18} aria-hidden /></span>
          PFE Job Copilot
        </div>
        <div className="max-w-2xl">
          <p className="mb-5 text-xs font-extrabold uppercase tracking-[.16em] text-blue-300">Private search dossier</p>
          <h1 className="text-[clamp(3.5rem,7vw,7rem)] font-semibold leading-[.88] tracking-[-.055em]">One queue.<br />Better moves.</h1>
          <p className="mt-8 max-w-lg text-lg leading-8 text-slate-300">Collect, rank, and advance the PFE opportunities that deserve your time.</p>
        </div>
        <p className="text-xs text-slate-400">Protected by your Supabase account</p>
      </section>

      <section className="grid place-items-center py-8 lg:py-0">
        <div className="w-full max-w-[440px]">
          <div className="mb-12 flex items-center gap-3 font-bold lg:hidden"><BriefcaseBusiness size={22} />PFE Job Copilot</div>
          <span className="grid size-12 place-items-center rounded-2xl bg-cobalt-wash text-cobalt-dark"><LockKeyhole size={21} aria-hidden /></span>
          <h2 className="mt-7 text-4xl font-semibold tracking-[-.04em]">Open your dossier</h2>
          <p className="mt-3 text-sm leading-6 text-muted">Use the account you created in your Supabase project.</p>

          <form action={login} className="mt-9 grid gap-5">
            <label className="grid gap-2 text-xs font-bold text-muted">
              Email
              <input name="email" type="email" autoComplete="email" required className="h-12 rounded-xl border border-rule-dark bg-white px-4 text-base text-ink" />
            </label>
            <label className="grid gap-2 text-xs font-bold text-muted">
              Password
              <input name="password" type="password" autoComplete="current-password" required className="h-12 rounded-xl border border-rule-dark bg-white px-4 text-base text-ink" />
            </label>
            {notice && <p role="alert" className={`rounded-xl px-4 py-3 text-sm ${params.error ? "bg-red-50 text-danger" : "bg-emerald-50 text-success"}`}>{notice}</p>}
            <button className="mt-2 h-12 rounded-xl bg-cobalt px-5 font-bold text-white transition-colors hover:bg-cobalt-dark">Sign in</button>
          </form>
          <p className="mt-7 text-xs leading-5 text-muted">No public registration is exposed. Add the owner account from Supabase Authentication → Users.</p>
        </div>
      </section>
    </main>
  );
}
