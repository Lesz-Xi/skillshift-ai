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
          signal: AbortSignal.timeout(1000), // Quick health check for fast analysis
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

    // Call the fast analysis endpoint with shorter timeout
    const analysisResponse = await fetch(
      `${SKILLSHIFT_AI_BASE_URL}/api/analyze-fast?ign=${encodeURIComponent(ign)}`,
      {
        method: "POST",
        body: backendFormData,
        headers: backendFormData.getHeaders(),
        signal: AbortSignal.timeout(15000), // 15 second timeout for fast analysis
      }
    );

    if (!analysisResponse.ok) {
      const errorText = await analysisResponse.text();
      return NextResponse.json(
        {
          success: false,
          error: "Fast analysis failed",
          details: errorText,
        },
        { status: analysisResponse.status }
      );
    }

    const analysisResult = await analysisResponse.json();

    // Transform response for frontend
    const dashboardResponse = {
      success: true,
      message: "Fast analysis completed successfully",
      analysis_type: "fast",
      analysis: {
        // Core analysis results
        statistical_feedback: analysisResult.feedback || [],
        mental_feedback: analysisResult.mental_boost || "Keep improving!",

        // Basic performance data
        performance: {
          hero: extractHeroName(analysisResult),
          kda: extractKDA(analysisResult),
          damage: extractDamage(analysisResult),
          gold: extractGold(analysisResult),
          match_duration: extractDuration(analysisResult),
          rank: extractRank(analysisResult),
        },

        // Fast analysis quality metrics
        quality: {
          overall_confidence: (analysisResult.diagnostics?.confidence_score || 0) * 100,
          confidence_category: getConfidenceCategory(analysisResult.diagnostics?.confidence_score || 0),
          warnings: analysisResult.diagnostics?.warnings || [],
          data_validation_passed: analysisResult.diagnostics?.hero_detected || false,
          processing_mode: "fast",
        },

        // Fast analysis insights
        insights: {
          analysis_mode: "fast",
          processing_time: analysisResult.diagnostics?.processing_time || 2.0,
          success_factors: generateFastSuccessFactors(analysisResult),
          improvement_roadmap: extractImprovementPoints(analysisResult.feedback),
          data_completeness: analysisResult.diagnostics?.data_completeness || 0.8,
          speed_optimized: true,
        },
      },
      performance_metrics: {
        target_processing_time: "< 15 seconds",
        actual_processing_time: analysisResult.diagnostics?.processing_time || 2.0,
        optimization_level: "high",
        accuracy_trade_off: "balanced"
      },
      metadata: {
        ign: ign,
        filename: file.name,
        fileSize: file.size,
        timestamp: new Date().toISOString(),
        backend_url: SKILLSHIFT_AI_BASE_URL,
        analysis_mode: "fast",
      },
    };

    return NextResponse.json(dashboardResponse);

  } catch (error) {
    console.error("Fast analysis API error:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Fast analysis failed",
        details: error.message,
      },
      { status: 500 }
    );
  }
}

// Helper functions
function extractHeroName(result) {
  return result.match_data?.hero || 
         result.diagnostics?.hero_name || 
         "Unknown";
}

function extractKDA(result) {
  const matchData = result.match_data || {};
  if (matchData.kills !== undefined && matchData.deaths !== undefined && matchData.assists !== undefined) {
    return `${matchData.kills}/${matchData.deaths}/${matchData.assists}`;
  }
  return "N/A";
}

function extractDamage(result) {
  return result.match_data?.hero_damage || "N/A";
}

function extractGold(result) {
  return result.match_data?.gold || "N/A";
}

function extractDuration(result) {
  return result.match_data?.match_duration || "N/A";
}

function extractRank(result) {
  return result.match_data?.rank || "Unknown";
}

function getConfidenceCategory(score) {
  const percentage = score * 100;
  if (percentage >= 70) return "high"; // Lower threshold for fast analysis
  if (percentage >= 50) return "medium";
  return "low";
}

function generateFastSuccessFactors(result) {
  const factors = [];
  
  // Add fast analysis specific success factors
  factors.push("✓ Fast analysis completed under 15 seconds");
  
  if (result.diagnostics?.hero_detected) {
    factors.push("✓ Hero successfully detected");
  }
  
  if (result.diagnostics?.confidence_score > 0.6) {
    factors.push("✓ Good analysis confidence achieved");
  }
  
  if (result.match_data && Object.keys(result.match_data).length > 3) {
    factors.push("✓ Multiple data points extracted");
  }
  
  return factors.slice(0, 4); // Limit to 4 factors
}

function extractImprovementPoints(feedback) {
  if (!Array.isArray(feedback)) return [];
  
  return feedback
    .filter((item) => item.type === "warning" || item.type === "critical")
    .map((item) => item.message)
    .slice(0, 3); // Top 3 improvement points for fast analysis
}

export async function GET() {
  return NextResponse.json({
    message: "Fast Analysis Endpoint",
    status: "operational",
    backend_url: SKILLSHIFT_AI_BASE_URL,
    supported_methods: ["POST"],
    required_fields: ["file"],
    optional_fields: ["ign"],
    description: "Fast analysis endpoint that prioritizes speed over accuracy",
    features: [
      "Sub-15 second processing time",
      "Basic hero detection",
      "Essential KDA extraction",
      "Quick feedback generation",
      "Optimized for speed"
    ],
    performance: {
      target_time: "< 15 seconds",
      accuracy_level: "basic",
      recommended_use: "Quick analysis when speed is priority"
    }
  });
}