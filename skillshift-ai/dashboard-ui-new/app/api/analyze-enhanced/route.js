import { NextResponse } from "next/server";
import FormData from "form-data";
import fetch from "node-fetch";

// Configuration for the skillshift-ai backend
const SKILLSHIFT_AI_BASE_URL =
  process.env.SKILLSHIFT_AI_URL || "http://localhost:8000";
const DEFAULT_IGN = process.env.DEFAULT_IGN || "Lesz XVII";

export async function POST(request) {
  try {
    const formData = await request.formData();
    const file = formData.get("file");
    const ign = formData.get("ign") || DEFAULT_IGN;
    const session_id = formData.get("session_id") || null;
    const hero_override = formData.get("hero_override") || "";

    if (!file) {
      return NextResponse.json(
        { success: false, error: "No file provided for analysis" },
        { status: 400 }
      );
    }

    // Validate file type - should be image
    if (!file.type.startsWith("image/")) {
      return NextResponse.json(
        {
          success: false,
          error: "Only image files are supported for analysis",
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
            error: "Analysis service is currently unavailable",
            details: "Backend health check failed",
          },
          { status: 503 }
        );
      }
    } catch (healthError) {
      return NextResponse.json(
        {
          success: false,
          error: "Cannot connect to analysis service",
          details: "Please ensure the backend is running on port 8000",
        },
        { status: 503 }
      );
    }

    // Create FormData for skillshift-ai backend
    const backendFormData = new FormData();
    const fileBuffer = Buffer.from(await file.arrayBuffer());
    backendFormData.append("file", fileBuffer, {
      filename: file.name,
      contentType: file.type,
    });

    // Build query params
    const queryParams = new URLSearchParams({
      ign: ign,
    });

    if (session_id) queryParams.append("session_id", session_id);
    if (hero_override) queryParams.append("hero_override", hero_override);

    // Call the enhanced analysis endpoint
    const analysisResponse = await fetch(
      `${SKILLSHIFT_AI_BASE_URL}/api/analyze-enhanced/?${queryParams}`,
      {
        method: "POST",
        body: backendFormData,
        headers: backendFormData.getHeaders(),
        signal: AbortSignal.timeout(120000), // 2 minute timeout
      }
    );

    if (!analysisResponse.ok) {
      const errorText = await analysisResponse.text();
      return NextResponse.json(
        {
          success: false,
          error: "Enhanced analysis failed",
          details: errorText,
        },
        { status: analysisResponse.status }
      );
    }

    const analysisResult = await analysisResponse.json();

    // Transform response for frontend
    const dashboardResponse = {
      success: true,
      message: "Enhanced analysis completed successfully",
      analysis_type: "enhanced",
      analysis: {
        // Core analysis results
        statistical_feedback: analysisResult.feedback || [],
        mental_feedback: analysisResult.mental_boost || "Keep improving!",

        // Player performance data
        performance: {
          hero: extractHeroName(analysisResult),
          kda: extractKDA(analysisResult),
          damage: extractDamage(analysisResult),
          gold: extractGold(analysisResult),
          match_duration: extractDuration(analysisResult),
          rank: extractRank(analysisResult),
        },

        // Enhanced quality metrics
        quality: {
          overall_confidence:
            (analysisResult.diagnostics?.confidence_score || 0) * 100,
          confidence_category: getConfidenceCategory(
            analysisResult.diagnostics?.confidence_score || 0
          ),
          warnings: analysisResult.warnings || [],
          data_validation_passed:
            analysisResult.diagnostics?.validation_passed || false,
          hero_detected: analysisResult.diagnostics?.hero_detected || false,
          kda_complete: analysisResult.diagnostics?.kda_data_complete || false,
          gold_valid: analysisResult.diagnostics?.gold_data_valid || false,
        },

        // Enhanced insights
        insights: {
          analysis_mode: "enhanced",
          session_complete:
            analysisResult.session_info?.session_complete || false,
          screenshot_type:
            analysisResult.session_info?.screenshot_type || "unknown",
          data_completeness: analysisResult.diagnostics?.data_completeness || 0,
          hero_suggestions: analysisResult.diagnostics?.hero_suggestions || [],
          improvement_roadmap: extractImprovementPoints(
            analysisResult.feedback
          ),
        },
      },
      session_info: analysisResult.session_info || {},
      debug_info: analysisResult.debug_info || {},
      metadata: {
        ign: ign,
        filename: file.name,
        fileSize: file.size,
        timestamp: new Date().toISOString(),
        backend_url: SKILLSHIFT_AI_BASE_URL,
        session_id: session_id,
        hero_override: hero_override,
      },
    };

    return NextResponse.json(dashboardResponse);
  } catch (error) {
    console.error("Enhanced analysis API error:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Enhanced analysis failed",
        details: error.message,
      },
      { status: 500 }
    );
  }
}

// Helper functions
function extractHeroName(result) {
  return (
    result.analysis?.performance?.hero ||
    result.match_data?.hero ||
    result.diagnostics?.hero_name ||
    "Unknown"
  );
}

function extractKDA(result) {
  const matchData = result.match_data || {};
  if (
    matchData.kills !== undefined &&
    matchData.deaths !== undefined &&
    matchData.assists !== undefined
  ) {
    return `${matchData.kills}/${matchData.deaths}/${matchData.assists}`;
  }
  return result.analysis?.performance?.kda || "N/A";
}

function extractDamage(result) {
  return (
    result.match_data?.hero_damage ||
    result.analysis?.performance?.damage ||
    "N/A"
  );
}

function extractGold(result) {
  return result.match_data?.gold || result.analysis?.performance?.gold || "N/A";
}

function extractDuration(result) {
  return (
    result.match_data?.match_duration ||
    result.analysis?.performance?.match_duration ||
    "N/A"
  );
}

function extractRank(result) {
  return (
    result.match_data?.rank || result.analysis?.performance?.rank || "Unknown"
  );
}

function getConfidenceCategory(score) {
  const percentage = score * 100;
  if (percentage >= 80) return "high";
  if (percentage >= 60) return "medium";
  return "low";
}

function extractImprovementPoints(feedback) {
  if (!Array.isArray(feedback)) return [];

  return feedback
    .filter((item) => item.type === "warning" || item.type === "critical")
    .map((item) => item.message)
    .slice(0, 5); // Top 5 improvement points
}

export async function GET() {
  return NextResponse.json({
    message: "Enhanced Analysis Endpoint",
    status: "operational",
    backend_url: SKILLSHIFT_AI_BASE_URL,
    supported_methods: ["POST"],
    required_fields: ["file"],
    optional_fields: ["ign", "session_id", "hero_override"],
    description:
      "Enhanced screenshot analysis with session management and improved hero detection",
    features: [
      "Session-based analysis",
      "Hero detection improvements",
      "Advanced diagnostics",
      "Multi-screenshot processing",
    ],
  });
}
