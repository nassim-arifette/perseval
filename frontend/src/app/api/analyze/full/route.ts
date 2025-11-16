import { NextResponse } from "next/server";

const BACKEND_API_BASE_URL =
  process.env.BACKEND_API_BASE_URL ?? "http://localhost:8000";

export async function POST(request: Request) {
  try {
    const payload = await request.json().catch(() => null);
    const text =
      typeof payload?.text === "string" ? payload.text.trim() : undefined;
    const instagramUrl =
      typeof payload?.instagram_url === "string"
        ? payload.instagram_url.trim()
        : undefined;
    const influencerHandle =
      typeof payload?.influencer_handle === "string"
        ? payload.influencer_handle.trim()
        : undefined;
    const companyName =
      typeof payload?.company_name === "string"
        ? payload.company_name.trim()
        : undefined;
    const maxPosts =
      typeof payload?.max_posts === "number" && Number.isFinite(payload.max_posts)
        ? Math.min(Math.max(Math.trunc(payload.max_posts), 1), 20)
        : 5;
    const companyMaxResults =
      typeof payload?.company_max_results === "number" &&
      Number.isFinite(payload.company_max_results)
        ? Math.min(Math.max(Math.trunc(payload.company_max_results), 1), 20)
        : 8;

    if (!text && !instagramUrl) {
      return NextResponse.json(
        { detail: "Provide text or an Instagram URL to analyze." },
        { status: 400 },
      );
    }

    const backendResponse = await fetch(
      `${BACKEND_API_BASE_URL}/analyze/full`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text,
          instagram_url: instagramUrl,
          influencer_handle: influencerHandle,
          company_name: companyName,
          max_posts: maxPosts,
          company_max_results: companyMaxResults,
        }),
        cache: "no-store",
      },
    );

    const data = await backendResponse.json().catch(() => null);
    if (!backendResponse.ok) {
      return NextResponse.json(
        data ?? { detail: "Backend error" },
        { status: backendResponse.status },
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error while running full analysis:", error);
    return NextResponse.json(
      { detail: "Unexpected error while contacting backend." },
      { status: 500 },
    );
  }
}
