"use server";

import { redirect } from "next/navigation";

import { getSupabaseConfigStatus } from "@/lib/supabase/config";
import { createClient } from "@/lib/supabase/server";

export async function logout() {
  if (getSupabaseConfigStatus() === "ready") {
    const supabase = await createClient();
    await supabase.auth.signOut();
  }
  redirect("/login");
}
