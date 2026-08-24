import { Dashboard } from "@/components/dashboard";
import { getDashboardData } from "@/lib/backend";
import { getSupabaseConfigStatus } from "@/lib/supabase/config";
import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";

export const dynamic = "force-dynamic";

export default async function Home() {
  const authEnabled = getSupabaseConfigStatus() === "ready";
  if (authEnabled) {
    const supabase = await createClient();
    const { data, error } = await supabase.auth.getClaims();
    if (error || !data?.claims?.sub) redirect("/login");
  }
  const initial = await getDashboardData();
  return <Dashboard initialJobs={initial.jobs} initialStats={initial.stats} online={initial.online} authEnabled={authEnabled} />;
}
