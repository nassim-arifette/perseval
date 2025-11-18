import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_API_BASE_URL || 'http://localhost:5371';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Forward the request to the backend
    const response = await fetch(`${BACKEND_URL}/feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Forward the session ID header
        'X-Session-ID': request.headers.get('X-Session-ID') || 'unknown',
        // Forward the real IP address for rate limiting
        'X-Forwarded-For': request.headers.get('x-forwarded-for') ||
                           request.headers.get('x-real-ip') ||
                           'unknown',
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { error: data.detail || 'Failed to submit feedback' },
        { status: response.status }
      );
    }

    return NextResponse.json(data);
  } catch (error: any) {
    console.error('Feedback API error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
