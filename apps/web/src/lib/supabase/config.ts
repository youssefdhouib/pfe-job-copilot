export type SupabaseConfigStatus = "disabled" | "ready" | "invalid";

export function getSupabaseConfigStatus(): SupabaseConfigStatus {
  if (process.env.NEXT_PUBLIC_PFE_AUTH_ENABLED !== "true") return "disabled";

  const url = process.env.NEXT_PUBLIC_SUPABASE_URL?.trim();
  const key = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY?.trim();

  if (!url && !key) return "disabled";
  return url && key ? "ready" : "invalid";
}

export function getSupabasePublicConfig() {
  if (getSupabaseConfigStatus() !== "ready") {
    throw new Error("Supabase requires both its project URL and publishable key.");
  }

  return {
    url: process.env.NEXT_PUBLIC_SUPABASE_URL as string,
    key: process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY as string,
  };
}
