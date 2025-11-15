import { NextResponse } from "next/server";

const BACKEND_API_BASE_URL =
  process.env.BACKEND_API_BASE_URL ?? "http://localhost:8000";

export async function POST(request: Request) {
  try {
    const payload = await request.json().catch(() => null);
    const text = typeof payload?.text === "string" ? payload.text.trim() : "";

    if (!text) {
      return NextResponse.json(
        { detail: "Text to analyze cannot be empty." },
        { status: 400 }
      );
    }

    const backendResponse = await fetch(`${BACKEND_API_BASE_URL}/analyze/text`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
      cache: "no-store",
    });

    const data = await backendResponse.json().catch(() => null);

    if (!backendResponse.ok) {
      return NextResponse.json(
        data ?? { detail: "Backend error" },
        { status: backendResponse.status }
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error while proxying to backend:", error);
    return NextResponse.json(
      { detail: "Unexpected error while contacting backend." },
      { status: 500 }
    );
  }
}
