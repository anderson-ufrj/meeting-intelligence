import { NextRequest, NextResponse } from "next/server";

const API_URL =
  process.env.API_URL || "http://localhost:8000";

async function proxy(req: NextRequest) {
  const path = req.nextUrl.pathname;
  const search = req.nextUrl.search;
  const target = `${API_URL}${path}${search}`;

  const contentType = req.headers.get("content-type") || "application/json";
  const isMultipart = contentType.includes("multipart/form-data");

  const headers: Record<string, string> = {
    "content-type": contentType,
  };

  const init: RequestInit = {
    method: req.method,
    headers,
  };

  if (req.method !== "GET" && req.method !== "HEAD") {
    if (isMultipart) {
      init.body = Buffer.from(await req.arrayBuffer());
    } else {
      init.body = await req.text();
    }
  }

  const upstream = await fetch(target, init);

  return new NextResponse(upstream.body, {
    status: upstream.status,
    headers: {
      "content-type": upstream.headers.get("content-type") || "application/json",
    },
  });
}

export const GET = proxy;
export const POST = proxy;
export const DELETE = proxy;
