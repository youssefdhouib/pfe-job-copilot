import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

import { getSupabaseConfigStatus, getSupabasePublicConfig } from "@/lib/supabase/config";

export async function updateSession(request: NextRequest) {
  const configStatus = getSupabaseConfigStatus();
  if (configStatus === "disabled") return NextResponse.next({ request });
  if (configStatus === "invalid") {
    return NextResponse.json(
      { detail: "Supabase configuration is incomplete." },
      { status: 500 },
    );
  }

  const { url, key } = getSupabasePublicConfig();
  let response = NextResponse.next({ request });
  const supabase = createServerClient(url, key, {
    cookies: {
      getAll: () => request.cookies.getAll(),
      setAll(items) {
        items.forEach(({ name, value }) => request.cookies.set(name, value));
        response = NextResponse.next({ request });
        items.forEach(({ name, value, options }) => response.cookies.set(name, value, options));
      },
    },
  });

  const { data, error } = await supabase.auth.getClaims();
  const authenticated = !error && Boolean(data?.claims?.sub);
  const isLogin = request.nextUrl.pathname === "/login";

  if (!authenticated && !isLogin) {
    if (request.nextUrl.pathname.startsWith("/api/")) {
      return NextResponse.json({ detail: "Authentication required." }, { status: 401 });
    }
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = "/login";
    loginUrl.searchParams.set("next", request.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  if (authenticated && isLogin) {
    return NextResponse.redirect(new URL("/", request.url));
  }

  return response;
}
