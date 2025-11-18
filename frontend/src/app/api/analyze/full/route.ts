import { NextResponse } from "next/server";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:5371";

export async function POST(request: Request) {
  try {
    const payload = await request.json().catch(() => null);
    const text =
      typeof payload?.text === "string" ? payload.text.trim() : undefined;
    const instagramUrl =
      typeof payload?.instagram_url === "string"
        ? payload.instagram_url.trim()
        : undefined;
    const tiktokUrl =
      typeof payload?.tiktok_url === "string"
        ? payload.tiktok_url.trim()
        : undefined;
    const influencerHandle =
      typeof payload?.influencer_handle === "string"
        ? payload.influencer_handle.trim()
        : undefined;
    const companyName =
      typeof payload?.company_name === "string"
        ? payload.company_name.trim()
        : undefined;
    const productName =
      typeof payload?.product_name === "string"
        ? payload.product_name.trim()
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
    const productMaxResults =
      typeof payload?.product_max_results === "number" &&
      Number.isFinite(payload.product_max_results)
        ? Math.min(Math.max(Math.trunc(payload.product_max_results), 1), 20)
        : 8;

    if (!text && !instagramUrl && !tiktokUrl) {
      return NextResponse.json(
        { detail: "Provide text, an Instagram URL, or a TikTok URL to analyze." },
        { status: 400 },
      );
    }

    console.log(`Calling backend at: ${BACKEND_URL}/analyze/full`);

    const backendResponse = await fetch(
      `${BACKEND_URL}/analyze/full`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text,
          instagram_url: instagramUrl,
          tiktok_url: tiktokUrl,
          influencer_handle: influencerHandle,
          company_name: companyName,
          product_name: productName,
          max_posts: maxPosts,
          company_max_results: companyMaxResults,
          product_max_results: productMaxResults,
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
