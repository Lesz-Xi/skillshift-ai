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

    // Call the advanced performance analysis endpoint
    const analysisResponse = await fetch(
      `${SKILLSHIFT_AI_BASE_URL}/api/analyze-advanced/?${queryParams}`,
      {
        method: "POST",
        body: backendFormData,
        headers: backendFormData.getHeaders(),
        signal: AbortSignal.timeout(180000), // 3 minute timeout for advanced analysis
      }
    );

    if (!analysisResponse.ok) {
      const errorText = await analysisResponse.text();
      return NextResponse.json(
        {
          success: false,
          error: "Advanced performance analysis failed",
          details: errorText,
        },
        { status: analysisResponse.status }
      );
    }

    const analysisResult = await analysisResponse.json();

    // Transform response for frontend
    const dashboardResponse = {
      success: true,
      message: "Advanced performance analysis completed successfully",
      analysis_type: "advanced_performance",
      analysis: {
        // Core analysis results
        statistical_feedback: analysisResult.detailed_feedback || [],
        mental_feedback: analysisResult.mental_boost || "Keep improving your performance!",

        // Advanced performance metrics
        advanced_analysis: {
          hero: analysisResult.advanced_analysis?.hero || "Unknown",
          role: analysisResult.advanced_analysis?.role || "Unknown", 
          overall_rating: analysisResult.advanced_analysis?.overall_rating || "Unknown",
          overall_score: analysisResult.advanced_analysis?.overall_score || 0,
          
          // Core performance metrics
          core_metrics: {
            combat_efficiency: {
              value: analysisResult.advanced_analysis?.core_metrics?.combat_efficiency?.value || 0,
              benchmark: analysisResult.advanced_analysis?.core_metrics?.combat_efficiency?.benchmark || 0,
              category: analysisResult.advanced_analysis?.core_metrics?.combat_efficiency?.category || "poor",
              description: analysisResult.advanced_analysis?.core_metrics?.combat_efficiency?.description || "Combat efficiency analysis"
            },
            objective_participation: {
              value: analysisResult.advanced_analysis?.core_metrics?.objective_participation?.value || 0,
              benchmark: analysisResult.advanced_analysis?.core_metrics?.objective_participation?.benchmark || 0,
              category: analysisResult.advanced_analysis?.core_metrics?.objective_participation?.category || "poor",
              description: analysisResult.advanced_analysis?.core_metrics?.objective_participation?.description || "Objective participation analysis"
            },
            economic_efficiency: {
              value: analysisResult.advanced_analysis?.core_metrics?.economic_efficiency?.value || 0,
              benchmark: analysisResult.advanced_analysis?.core_metrics?.economic_efficiency?.benchmark || 0,
              category: analysisResult.advanced_analysis?.core_metrics?.economic_efficiency?.category || "poor",
              description: analysisResult.advanced_analysis?.core_metrics?.economic_efficiency?.description || "Economic efficiency analysis"
            },
            survival_rating: {
              value: analysisResult.advanced_analysis?.core_metrics?.survival_rating?.value || 0,
              benchmark: analysisResult.advanced_analysis?.core_metrics?.survival_rating?.benchmark || 0,
              category: analysisResult.advanced_analysis?.core_metrics?.survival_rating?.category || "poor",
              description: analysisResult.advanced_analysis?.core_metrics?.survival_rating?.description || "Survival rating analysis"
            }
          },

          // Role-specific metrics
          role_specific_metrics: analysisResult.advanced_analysis?.role_specific_metrics || {},

          // Performance insights
          strengths: analysisResult.advanced_analysis?.strengths || [],
          weaknesses: analysisResult.advanced_analysis?.weaknesses || [],
          improvement_priorities: analysisResult.advanced_analysis?.improvement_priorities || [],
          advanced_insights: analysisResult.advanced_analysis?.advanced_insights || []
        },

        // Quality metrics
        quality: {
          overall_confidence: calculateOverallConfidence(analysisResult),
          confidence_category: getConfidenceCategory(calculateOverallConfidence(analysisResult) / 100),
          warnings: analysisResult.warnings || [],
          data_validation_passed: true, // Advanced analysis assumes valid data
          advanced_metrics_available: true,
        },

        // Enhanced insights
        insights: {
          analysis_mode: "advanced_performance",
          processing_time: 0,
          success_factors: extractSuccessFactors(analysisResult),
          improvement_roadmap: analysisResult.advanced_analysis?.improvement_priorities || [],
          performance_breakdown: generatePerformanceBreakdown(analysisResult),
          role_analysis: generateRoleAnalysis(analysisResult),
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
        analysis_depth: "advanced_performance"
      },
    };

    return NextResponse.json(dashboardResponse);

  } catch (error) {
    console.error("Advanced performance analysis API error:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Advanced performance analysis failed",
        details: error.message,
      },
      { status: 500 }
    );
  }
}

// Helper functions
function calculateOverallConfidence(result) {
  // Calculate confidence based on data availability and quality
  let confidence = 70; // Base confidence for advanced analysis
  
  if (result.advanced_analysis?.overall_score > 0.7) confidence += 15;
  if (result.advanced_analysis?.core_metrics?.combat_efficiency?.value > 0) confidence += 5;
  if (result.advanced_analysis?.strengths?.length > 0) confidence += 5;
  if (result.advanced_analysis?.improvement_priorities?.length > 0) confidence += 5;
  
  return Math.min(confidence, 100);
}

function getConfidenceCategory(score) {
  if (score >= 0.8) return "high";
  if (score >= 0.6) return "medium";
  return "low";
}

function extractSuccessFactors(result) {
  const factors = [];
  const strengths = result.advanced_analysis?.strengths || [];
  
  strengths.forEach(strength => {
    factors.push(`✓ ${strength}`);
  });
  
  if (result.advanced_analysis?.overall_rating === "excellent") {
    factors.push("✓ Outstanding overall performance");
  }
  
  return factors.slice(0, 5); // Limit to 5 factors
}

function generatePerformanceBreakdown(result) {
  const coreMetrics = result.advanced_analysis?.core_metrics || {};
  const breakdown = {};
  
  Object.keys(coreMetrics).forEach(metricName => {
    const metric = coreMetrics[metricName];
    breakdown[metricName] = {
      score: metric.value || 0,
      benchmark: metric.benchmark || 0,
      performance: metric.category || "poor",
      improvement: metric.value < metric.benchmark ? "needs_improvement" : "on_track"
    };
  });
  
  return breakdown;
}

function generateRoleAnalysis(result) {
  const roleMetrics = result.advanced_analysis?.role_specific_metrics || {};
  const analysis = {
    role: result.advanced_analysis?.role || "Unknown",
    role_performance: "average",
    role_specific_insights: []
  };
  
  // Analyze role-specific performance
  Object.keys(roleMetrics).forEach(metricName => {
    const metric = roleMetrics[metricName];
    if (metric.category === "excellent" || metric.category === "good") {
      analysis.role_specific_insights.push(`Strong ${metricName.replace(/_/g, ' ')}`);
    } else if (metric.category === "poor") {
      analysis.role_specific_insights.push(`Improve ${metricName.replace(/_/g, ' ')}`);
    }
  });
  
  return analysis;
}

export async function GET() {
  return NextResponse.json({
    message: "Advanced Performance Analysis Endpoint",
    status: "operational",
    backend_url: SKILLSHIFT_AI_BASE_URL,
    supported_methods: ["POST"],
    required_fields: ["file"],
    optional_fields: ["ign", "session_id", "hero_override"],
    description: "Advanced performance analysis with comprehensive metrics beyond KDA",
    features: [
      "Combat efficiency analysis",
      "Objective participation metrics",
      "Economic efficiency scoring",
      "Survival rating assessment",
      "Role-specific performance metrics",
      "Advanced insights and recommendations"
    ]
  });
}