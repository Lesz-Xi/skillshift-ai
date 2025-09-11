import { NextResponse } from "next/server";
import fetch from "node-fetch";

// Configuration for the skillshift-ai backend
const SKILLSHIFT_AI_BASE_URL =
  process.env.SKILLSHIFT_AI_URL || "http://localhost:8000";

export async function POST(request) {
  try {
    const requestBody = await request.json();
    const { enemy_heroes, allied_heroes = [], match_result = null } = requestBody;

    // Validate required fields
    if (!enemy_heroes || !Array.isArray(enemy_heroes) || enemy_heroes.length === 0) {
      return NextResponse.json(
        { 
          success: false, 
          error: "Enemy heroes list is required and cannot be empty" 
        },
        { status: 400 }
      );
    }

    // Validate hero names (basic validation)
    if (enemy_heroes.some(hero => !hero || typeof hero !== 'string')) {
      return NextResponse.json(
        { 
          success: false, 
          error: "All enemy hero names must be valid strings" 
        },
        { status: 400 }
      );
    }

    if (allied_heroes.some(hero => !hero || typeof hero !== 'string')) {
      return NextResponse.json(
        { 
          success: false, 
          error: "All allied hero names must be valid strings" 
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

    // Call the counter-pick analysis endpoint
    const analysisResponse = await fetch(
      `${SKILLSHIFT_AI_BASE_URL}/api/counter-pick-analysis/`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          enemy_heroes: enemy_heroes,
          allied_heroes: allied_heroes,
          match_result: match_result
        }),
        signal: AbortSignal.timeout(30000), // 30 second timeout
      }
    );

    if (!analysisResponse.ok) {
      const errorText = await analysisResponse.text();
      return NextResponse.json(
        {
          success: false,
          error: "Counter-pick analysis failed",
          details: errorText,
        },
        { status: analysisResponse.status }
      );
    }

    const analysisResult = await analysisResponse.json();

    // Transform response for frontend
    const dashboardResponse = {
      success: true,
      message: "Counter-pick analysis completed successfully",
      analysis_type: "counter_pick",
      analysis: {
        // Enemy team analysis
        enemy_team: {
          heroes: enemy_heroes,
          team_composition: analysisResult.counter_pick_analysis?.enemy_composition || {},
          threats: analysisResult.counter_pick_analysis?.primary_threats || [],
          weaknesses: analysisResult.counter_pick_analysis?.team_weaknesses || [],
          synergy_score: analysisResult.counter_pick_analysis?.enemy_synergy_score || 0
        },

        // Allied team analysis
        allied_team: {
          heroes: allied_heroes,
          team_composition: analysisResult.counter_pick_analysis?.allied_composition || {},
          current_synergy: analysisResult.counter_pick_analysis?.current_synergy || 0,
          missing_roles: analysisResult.counter_pick_analysis?.missing_roles || []
        },

        // Counter-pick recommendations
        recommendations: {
          priority_picks: analysisResult.counter_pick_analysis?.priority_counters || [],
          situational_picks: analysisResult.counter_pick_analysis?.situational_counters || [],
          ban_suggestions: analysisResult.counter_pick_analysis?.ban_suggestions || [],
          avoid_picks: analysisResult.counter_pick_analysis?.avoid_picks || []
        },

        // Strategic analysis
        strategy: {
          win_conditions: analysisResult.counter_pick_analysis?.win_conditions || [],
          team_fight_analysis: analysisResult.counter_pick_analysis?.teamfight_analysis || {},
          laning_phase: analysisResult.counter_pick_analysis?.laning_recommendations || {},
          late_game_scaling: analysisResult.counter_pick_analysis?.scaling_analysis || {}
        },

        // Meta considerations
        meta_analysis: {
          meta_tier_scores: analysisResult.counter_pick_analysis?.meta_scores || {},
          pick_ban_priority: analysisResult.counter_pick_analysis?.draft_priority || {},
          matchup_advantages: analysisResult.counter_pick_analysis?.lane_matchups || {}
        }
      },
      metadata: {
        enemy_heroes: enemy_heroes,
        allied_heroes: allied_heroes,
        match_result: match_result,
        timestamp: new Date().toISOString(),
        backend_url: SKILLSHIFT_AI_BASE_URL,
        analysis_version: "2.0.0"
      },
    };

    return NextResponse.json(dashboardResponse);

  } catch (error) {
    console.error("Counter-pick analysis API error:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Counter-pick analysis failed",
        details: error.message,
      },
      { status: 500 }
    );
  }
}

export async function GET() {
  return NextResponse.json({
    message: "Counter-Pick Analysis Endpoint",
    status: "operational",
    backend_url: SKILLSHIFT_AI_BASE_URL,
    supported_methods: ["POST"],
    required_fields: ["enemy_heroes"],
    optional_fields: ["allied_heroes", "match_result"],
    description: "Comprehensive counter-pick analysis for team compositions",
    features: [
      "Enemy team composition analysis",
      "Counter-pick recommendations",
      "Ban suggestions",
      "Strategic win conditions",
      "Laning phase recommendations", 
      "Team fight analysis",
      "Meta tier considerations"
    ],
    example_request: {
      enemy_heroes: ["Alice", "Tigreal", "Eudora", "Layla", "Nana"],
      allied_heroes: ["Hayabusa", "Johnson"],
      match_result: "win" // optional: "win", "loss", null
    }
  });
}