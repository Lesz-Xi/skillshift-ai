import { NextResponse } from "next/server";
import fetch from "node-fetch";

// Configuration for the skillshift-ai backend
const SKILLSHIFT_AI_BASE_URL =
  process.env.SKILLSHIFT_AI_URL || "http://localhost:8000";

export async function GET(request) {
  try {
    // Health check before processing
    try {
      const healthResponse = await fetch(
        `${SKILLSHIFT_AI_BASE_URL}/api/health-isolated`,
        {
          method: "GET",
          signal: AbortSignal.timeout(2000),
        }
      );

      if (!healthResponse.ok) {
        return NextResponse.json(
          {
            success: false,
            error: "Session management service is currently unavailable",
            details: "Backend health check failed",
          },
          { status: 503 }
        );
      }
    } catch (healthError) {
      return NextResponse.json(
        {
          success: false,
          error: "Cannot connect to session management service",
          details: "Please ensure the backend is running on port 8000",
        },
        { status: 503 }
      );
    }

    // Call the list active sessions endpoint
    const sessionsResponse = await fetch(
      `${SKILLSHIFT_AI_BASE_URL}/api/sessions/`,
      {
        method: "GET",
        signal: AbortSignal.timeout(10000), // 10 second timeout
      }
    );

    if (!sessionsResponse.ok) {
      const errorText = await sessionsResponse.text();
      return NextResponse.json(
        {
          success: false,
          error: "Failed to retrieve active sessions",
          details: errorText,
        },
        { status: sessionsResponse.status }
      );
    }

    const sessionsResult = await sessionsResponse.json();

    // Transform response for frontend
    const dashboardResponse = {
      success: true,
      message: "Active sessions retrieved successfully",
      sessions: {
        active_sessions: sessionsResult.active_sessions || [],
        total_count: sessionsResult.count || 0,
        session_details: (sessionsResult.active_sessions || []).map(
          (session) => ({
            session_id: session.session_id || session,
            status: session.status || "active",
            created_at: session.created_at || null,
            last_activity: session.last_activity || null,
            screenshot_count: session.screenshot_count || 0,
            analysis_type: session.analysis_type || "unknown",
            ign: session.ign || null,
          })
        ),
      },
      metadata: {
        timestamp: new Date().toISOString(),
        backend_url: SKILLSHIFT_AI_BASE_URL,
        session_version: "2.0.0",
      },
    };

    return NextResponse.json(dashboardResponse);
  } catch (error) {
    console.error("Sessions API error:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Failed to retrieve sessions",
        details: error.message,
      },
      { status: 500 }
    );
  }
}

export async function POST(request) {
  return NextResponse.json(
    {
      success: false,
      error: "POST method not supported. Use GET to retrieve active sessions.",
    },
    { status: 405 }
  );
}

export async function DELETE(request) {
  // Optional: Implement session cleanup
  try {
    const url = new URL(request.url);
    const sessionId = url.searchParams.get("session_id");

    if (!sessionId) {
      return NextResponse.json(
        {
          success: false,
          error: "Session ID is required for deletion",
        },
        { status: 400 }
      );
    }

    // Note: Backend doesn't have explicit session deletion, but we can provide a stub
    return NextResponse.json({
      success: true,
      message: "Session cleanup requested",
      session_id: sessionId,
      note: "Session will be automatically cleaned up by backend",
    });
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: "Session cleanup failed",
        details: error.message,
      },
      { status: 500 }
    );
  }
}
