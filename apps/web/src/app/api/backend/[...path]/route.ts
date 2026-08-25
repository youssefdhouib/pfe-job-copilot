import { NextRequest, NextResponse } from "next/server";

const backendUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const target = new URL(path.join("/"), `${backendUrl}/`);
  target.search = request.nextUrl.search;

  try {
    const response = await fetch(target, {
      method: request.method,
      headers: { "content-type": request.headers.get("content-type") ?? "application/json" },
      body: request.method === "GET" || request.method === "HEAD" ? undefined : await request.text(),
      cache: "no-store",
      signal: AbortSignal.timeout(90_000),
    });
    const body = await response.text();
    const contentType = response.headers.get("content-type") ?? "application/json";
    return new NextResponse(body, { status: response.status, headers: { "content-type": contentType } });
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Backend request failed";
    return NextResponse.json({ detail }, { status: 502 });
  }
}

export const dynamic = "force-dynamic";
export const maxDuration = 120;

export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
