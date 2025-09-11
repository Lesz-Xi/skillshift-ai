import { NextResponse } from "next/server";
import fetch from "node-fetch";

// Configuration for the skillshift-ai backend
const SKILLSHIFT_AI_BASE_URL =
  process.env.SKILLSHIFT_AI_URL || "http://localhost:8000";

export async function GET(request, { params }) {
  try {
    const sessionId = params.sessionId;

    // Validate session ID parameter
    if (!sessionId || sessionId.trim().length === 0) {
      return NextResponse.json(
        { 
          success: false, 
          error: "Session ID is required" 
        },
        { status: 400 }
      );
    }

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

    // Call the session info endpoint
    const sessionResponse = await fetch(
      `${SKILLSHIFT_AI_BASE_URL}/api/session/${encodeURIComponent(sessionId)}`,
      {
        method: "GET",
        signal: AbortSignal.timeout(10000), // 10 second timeout
      }
    );

    if (!sessionResponse.ok) {
      if (sessionResponse.status === 404) {
        return NextResponse.json(
          {
            success: false,
            error: "Session not found",
            session_id: sessionId,
          },
          { status: 404 }
        );
      }

      const errorText = await sessionResponse.text();
      return NextResponse.json(
        {
          success: false,
          error: "Failed to retrieve session information",
          details: errorText,
        },
        { status: sessionResponse.status }
      );
    }

    const sessionResult = await sessionResponse.json();

    // Transform response for frontend
    const dashboardResponse = {
      success: true,
      message: "Session information retrieved successfully",
      session: {
        session_id: sessionId,
        status: sessionResult.status || "active",
        created_at: sessionResult.created_at || null,
        last_activity: sessionResult.last_activity || null,
        screenshot_count: sessionResult.screenshot_count || 0,
        analysis_type: sessionResult.analysis_type || "unknown",
        ign: sessionResult.ign || null,
        total_analyses: sessionResult.total_analyses || 0,
        successful_analyses: sessionResult.successful_analyses || 0,
        average_confidence: sessionResult.average_confidence || 0,
        last_hero_detected: sessionResult.last_hero_detected || null,
        session_complete: sessionResult.session_complete || false,
      },
      session_history: {
        analyses: sessionResult.analyses || [],
        screenshots: sessionResult.screenshots || [],
        recent_activity: sessionResult.recent_activity || []
      },
      session_insights: {
        performance_trend: calculatePerformanceTrend(sessionResult),
        data_quality: calculateDataQuality(sessionResult),
        recommendations: generateSessionRecommendations(sessionResult)
      },
      metadata: {
        session_id: sessionId,
        timestamp: new Date().toISOString(),
        backend_url: SKILLSHIFT_AI_BASE_URL,
        session_version: "2.0.0"
      },
    };

    return NextResponse.json(dashboardResponse);

  } catch (error) {
    console.error("Session info API error:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Failed to retrieve session information",
        details: error.message,
        session_id: params.sessionId,
      },
      { status: 500 }
    );
  }
}

// Helper functions
function calculatePerformanceTrend(sessionResult) {
  const analyses = sessionResult.analyses || [];
  if (analyses.length < 2) return "insufficient_data";
  
  // Simple trend calculation based on confidence scores
  const recent = analyses.slice(-3);
  const older = analyses.slice(0, Math.max(1, analyses.length - 3));
  
  const recentAvg = recent.reduce((sum, analysis) => sum + (analysis.confidence || 0), 0) / recent.length;
  const olderAvg = older.reduce((sum, analysis) => sum + (analysis.confidence || 0), 0) / older.length;
  
  if (recentAvg > olderAvg + 0.1) return "improving";
  if (recentAvg < olderAvg - 0.1) return "declining";
  return "stable";
}

function calculateDataQuality(sessionResult) {
  const successRate = sessionResult.total_analyses > 0 
    ? (sessionResult.successful_analyses || 0) / sessionResult.total_analyses 
    : 0;
    
  const avgConfidence = sessionResult.average_confidence || 0;
  
  if (successRate >= 0.8 && avgConfidence >= 0.7) return "excellent";
  if (successRate >= 0.6 && avgConfidence >= 0.5) return "good";
  if (successRate >= 0.4 && avgConfidence >= 0.3) return "fair";
  return "poor";
}

function generateSessionRecommendations(sessionResult) {
  const recommendations = [];
  
  const successRate = sessionResult.total_analyses > 0 
    ? (sessionResult.successful_analyses || 0) / sessionResult.total_analyses 
    : 0;
    
  if (successRate < 0.5) {
    recommendations.push("Consider using higher quality screenshots for better analysis results");
  }
  
  if (sessionResult.screenshot_count && sessionResult.screenshot_count >= 5) {
    recommendations.push("Multiple screenshots detected - session analysis will improve");
  }
  
  if (sessionResult.average_confidence && sessionResult.average_confidence < 0.5) {
    recommendations.push("Try providing hero override for more accurate analysis");
  }
  
  if (!sessionResult.session_complete) {
    recommendations.push("Continue adding screenshots to complete your analysis session");
  }
  
  return recommendations;
}

export async function POST(request) {
  return NextResponse.json(
    { 
      success: false, 
      error: "POST method not supported. Use GET to retrieve session information." 
    },
    { status: 405 }
  );
}