"use server";

import { redirect } from "next/navigation";

import { createClient } from "@/lib/supabase/server";

function loginUrl(key: "error" | "message", value: string) {
  return `/login?${key}=${encodeURIComponent(value)}`;
}

export async function login(formData: FormData) {
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");

  if (!email || !password) redirect(loginUrl("error", "Enter your email and password."));

  const supabase = await createClient();
  const { error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) redirect(loginUrl("error", "The email or password is incorrect."));

  redirect("/");
}
