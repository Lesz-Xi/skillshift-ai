import { NextResponse } from "next/server";
import fetch from "node-fetch";

// Configuration for the skillshift-ai backend
const SKILLSHIFT_AI_BASE_URL =
  process.env.SKILLSHIFT_AI_URL || "http://localhost:8000";

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const limit = searchParams.get("limit") || "50";
    const offset = searchParams.get("offset") || "0";
    const analysisType = searchParams.get("type") || "all";
    const userId = searchParams.get("user_id") || "default_user";

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
            error: "Analysis history service is currently unavailable",
            details: "Backend health check failed",
          },
          { status: 503 }
        );
      }
    } catch (healthError) {
      return NextResponse.json(
        {
          success: false,
          error: "Cannot connect to analysis history service",
          details: "Please ensure the backend is running on port 8000",
        },
        { status: 503 }
      );
    }

    // Fetch analysis history from backend
    const historyResponse = await fetch(
      `${SKILLSHIFT_AI_BASE_URL}/api/analysis-history?limit=${limit}&offset=${offset}&type=${analysisType}&user_id=${userId}`,
      {
        method: "GET",
        signal: AbortSignal.timeout(10000), // 10 second timeout
      }
    );

    if (!historyResponse.ok) {
      // If endpoint doesn't exist, return mock data for now
      if (historyResponse.status === 404) {
        return NextResponse.json(getMockAnalysisHistory());
      }

      const errorText = await historyResponse.text();
      return NextResponse.json(
        {
          success: false,
          error: "Failed to retrieve analysis history",
          details: errorText,
        },
        { status: historyResponse.status }
      );
    }

    const historyResult = await historyResponse.json();

    // Transform response for frontend
    const dashboardResponse = {
      success: true,
      message: "Analysis history retrieved successfully",
      data: {
        analyses: historyResult.analyses || [],
        total_count: historyResult.total_count || 0,
        summary: {
          total_analyses: historyResult.total_count || 0,
          avg_score: calculateAverageScore(historyResult.analyses || []),
          recent_count: countRecentAnalyses(historyResult.analyses || []),
          improvement_rate: calculateImprovementRate(
            historyResult.analyses || []
          ),
        },
        filters: {
          available_types: ["screenshot", "video", "all"],
          date_range: {
            earliest: getEarliestDate(historyResult.analyses || []),
            latest: getLatestDate(historyResult.analyses || []),
          },
        },
      },
      metadata: {
        timestamp: new Date().toISOString(),
        backend_url: SKILLSHIFT_AI_BASE_URL,
        version: "1.0.0",
      },
    };

    return NextResponse.json(dashboardResponse);
  } catch (error) {
    console.error("Analysis history API error:", error);

    // Return mock data on error for development
    return NextResponse.json(getMockAnalysisHistory());
  }
}

// Helper functions
function getMockAnalysisHistory() {
  return {
    success: true,
    message:
      "Analysis history retrieved successfully (using mock data - backend endpoint not yet implemented)",
    data: {
      analyses: [
        {
          id: "AH-001",
          session_id: "session_12345",
          analysis_type: "screenshot",
          title: "MVP Performance Analysis",
          timestamp: "2025-01-17T14:30:00Z",
          hero: "Ling",
          role: "Assassin",
          confidence: 94,
          status: "completed",
          match_data: {
            badges: ["MVP", "SAVAGE"],
            kda: "12/2/8",
            result: "Victory",
            duration: "18:45",
          },
          coaching_insights: [
            "Excellent positioning during team fights",
            "Consider improving early game farm efficiency",
            "Outstanding objective control timing",
          ],
          feedback: {
            strengths: ["Team fight positioning", "Objective timing"],
            improvements: ["Early game farming", "Map awareness"],
            score: 87,
            detailed_analysis: {
              mechanics: 85,
              decision_making: 90,
              teamwork: 88,
              positioning: 92,
            },
          },
          files: {
            screenshot_url: "/uploads/screenshots/session_12345_mvp.png",
            report_url: "/reports/session_12345_analysis.pdf",
          },
        },
        {
          id: "AH-002",
          session_id: "session_12344",
          analysis_type: "video",
          title: "Team Fight Analysis",
          timestamp: "2025-01-17T12:15:00Z",
          hero: "Chang'e",
          role: "Mage",
          confidence: 88,
          status: "completed",
          match_data: {
            badges: ["LEGENDARY"],
            kda: "8/3/15",
            result: "Victory",
            duration: "22:30",
          },
          coaching_insights: [
            "Good spell rotation timing",
            "Needs better positioning vs assassins",
            "Excellent team coordination",
          ],
          feedback: {
            strengths: ["Spell rotation", "Team coordination"],
            improvements: ["Positioning", "Vision control"],
            score: 79,
            detailed_analysis: {
              mechanics: 82,
              decision_making: 75,
              teamwork: 85,
              positioning: 70,
            },
          },
          files: {
            video_url: "/uploads/videos/session_12344_teamfight.mp4",
            report_url: "/reports/session_12344_analysis.pdf",
          },
        },
        {
          id: "AH-003",
          session_id: "session_12343",
          analysis_type: "screenshot",
          title: "Laning Phase Analysis",
          timestamp: "2025-01-16T20:45:00Z",
          hero: "Granger",
          role: "Marksman",
          confidence: 76,
          status: "completed",
          match_data: {
            badges: [],
            kda: "6/5/12",
            result: "Defeat",
            duration: "26:15",
          },
          coaching_insights: [
            "Improve last-hitting consistency",
            "Better warding placement needed",
            "Good item build choices",
          ],
          feedback: {
            strengths: ["Item builds", "Late game scaling"],
            improvements: ["Last-hitting", "Warding", "Lane pressure"],
            score: 64,
            detailed_analysis: {
              mechanics: 60,
              decision_making: 70,
              teamwork: 65,
              positioning: 62,
            },
          },
          files: {
            screenshot_url: "/uploads/screenshots/session_12343_lane.png",
            report_url: "/reports/session_12343_analysis.pdf",
          },
        },
      ],
      total_count: 47,
      summary: {
        total_analyses: 47,
        avg_score: 78,
        recent_count: 12,
        improvement_rate: 15,
      },
      filters: {
        available_types: ["screenshot", "video", "all"],
        date_range: {
          earliest: "2025-01-01T00:00:00Z",
          latest: "2025-01-17T14:30:00Z",
        },
      },
    },
    metadata: {
      timestamp: new Date().toISOString(),
      backend_url: SKILLSHIFT_AI_BASE_URL,
      version: "1.0.0",
      mode: "mock_data",
    },
  };
}

function calculateAverageScore(analyses) {
  if (!analyses || analyses.length === 0) return 0;
  const totalScore = analyses.reduce((sum, analysis) => {
    return sum + (analysis.feedback?.score || 0);
  }, 0);
  return Math.round(totalScore / analyses.length);
}

function countRecentAnalyses(analyses) {
  if (!analyses) return 0;
  const oneWeekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
  return analyses.filter(
    (analysis) => new Date(analysis.timestamp) > oneWeekAgo
  ).length;
}

function calculateImprovementRate(analyses) {
  if (!analyses || analyses.length < 6) return 0;

  // Compare average score of recent analyses vs older ones
  const recent = analyses.slice(0, Math.ceil(analyses.length / 3));
  const older = analyses.slice(Math.ceil((analyses.length * 2) / 3));

  const recentAvg = calculateAverageScore(recent);
  const olderAvg = calculateAverageScore(older);

  if (olderAvg === 0) return 0;
  return Math.round(((recentAvg - olderAvg) / olderAvg) * 100);
}

function getEarliestDate(analyses) {
  if (!analyses || analyses.length === 0) return null;
  return analyses.reduce((earliest, analysis) => {
    const date = new Date(analysis.timestamp);
    return date < new Date(earliest) ? analysis.timestamp : earliest;
  }, analyses[0].timestamp);
}

function getLatestDate(analyses) {
  if (!analyses || analyses.length === 0) return null;
  return analyses.reduce((latest, analysis) => {
    const date = new Date(analysis.timestamp);
    return date > new Date(latest) ? analysis.timestamp : latest;
  }, analyses[0].timestamp);
}

export async function POST(request) {
  return NextResponse.json(
    {
      success: false,
      error: "POST method not supported. Use GET to retrieve analysis history.",
    },
    { status: 405 }
  );
}
