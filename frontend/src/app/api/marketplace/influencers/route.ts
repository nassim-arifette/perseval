import { NextResponse } from "next/server";

const BACKEND_API_BASE_URL =
  process.env.BACKEND_API_BASE_URL ?? "http://localhost:5371";

export async function GET(request: Request) {
  try {
    const url = new URL(request.url);
    const search = url.searchParams.toString();
    const backendUrl = `${BACKEND_API_BASE_URL}/marketplace/influencers${
      search ? `?${search}` : ""
    }`;

    const backendResponse = await fetch(backendUrl, { cache: "no-store" });
    const data = await backendResponse.json().catch(() => null);

    if (!backendResponse.ok) {
      return NextResponse.json(
        data ?? { detail: "Backend error" },
        { status: backendResponse.status },
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error while fetching marketplace influencers:", error);
    return NextResponse.json(
      { detail: "Unexpected error while contacting backend." },
      { status: 500 },
    );
  }
}

