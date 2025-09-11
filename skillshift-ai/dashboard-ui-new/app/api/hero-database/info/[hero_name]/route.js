import { NextResponse } from "next/server";
import fetch from "node-fetch";

// Configuration for the skillshift-ai backend
const SKILLSHIFT_AI_BASE_URL =
  process.env.SKILLSHIFT_AI_URL || "http://localhost:8000";

export async function GET(request, { params }) {
  try {
    const hero_name = params.hero_name;

    // Validate hero_name parameter
    if (!hero_name || hero_name.trim().length === 0) {
      return NextResponse.json(
        { 
          success: false, 
          error: "Hero name is required" 
        },
        { status: 400 }
      );
    }

    // Decode and sanitize hero name
    const decodedHeroName = decodeURIComponent(hero_name).trim();

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
            error: "Hero database service is currently unavailable",
            details: "Backend health check failed",
          },
          { status: 503 }
        );
      }
    } catch (healthError) {
      return NextResponse.json(
        {
          success: false,
          error: "Cannot connect to hero database service",
          details: "Please ensure the backend is running on port 8000",
        },
        { status: 503 }
      );
    }

    // Call the hero info endpoint
    const infoResponse = await fetch(
      `${SKILLSHIFT_AI_BASE_URL}/api/hero-database/info/${encodeURIComponent(decodedHeroName)}`,
      {
        method: "GET",
        signal: AbortSignal.timeout(10000), // 10 second timeout
      }
    );

    if (!infoResponse.ok) {
      if (infoResponse.status === 404) {
        const errorData = await infoResponse.json();
        
        // Return suggestions if available
        if (errorData.suggestions) {
          return NextResponse.json({
            success: false,
            error: "Hero not found",
            hero_name: decodedHeroName,
            suggestions: errorData.suggestions.map(suggestion => ({
              hero: suggestion.hero,
              confidence: suggestion.confidence,
              relevance_score: Math.round(suggestion.confidence * 100)
            })),
            metadata: {
              hero_name: decodedHeroName,
              timestamp: new Date().toISOString(),
              backend_url: SKILLSHIFT_AI_BASE_URL,
            },
          });
        }
        
        return NextResponse.json(
          {
            success: false,
            error: "Hero not found",
            hero_name: decodedHeroName,
          },
          { status: 404 }
        );
      }

      const errorText = await infoResponse.text();
      return NextResponse.json(
        {
          success: false,
          error: "Hero info lookup failed",
          details: errorText,
        },
        { status: infoResponse.status }
      );
    }

    const infoResult = await infoResponse.json();

    // Transform response for frontend
    const dashboardResponse = {
      success: true,
      message: "Hero information retrieved successfully",
      hero_info: {
        basic: {
          name: infoResult.hero?.name || decodedHeroName,
          role: infoResult.hero?.role || "Unknown",
          aliases: infoResult.hero?.aliases || [],
          detection_keywords: infoResult.hero?.detection_keywords || [],
        },
        abilities: {
          skill_names: infoResult.hero?.skill_names || [],
        },
        meta: {
          meta_tier: infoResult.hero?.meta_tier || "Unknown",
          win_rate: infoResult.hero?.win_rate || 0,
          pick_rate: infoResult.hero?.pick_rate || 0,
          ban_rate: infoResult.hero?.ban_rate || 0,
        },
        relationships: {
          counters: infoResult.hero?.counters || [],
          countered_by: infoResult.hero?.countered_by || [],
          synergies: infoResult.hero?.synergies || [],
        },
        resources: {
          image_url: infoResult.hero?.image_url || null,
          wiki_url: infoResult.hero?.wiki_url || null,
        }
      },
      metadata: {
        hero_name: decodedHeroName,
        timestamp: new Date().toISOString(),
        backend_url: SKILLSHIFT_AI_BASE_URL,
        info_version: "2.0.0"
      },
    };

    return NextResponse.json(dashboardResponse);

  } catch (error) {
    console.error("Hero info API error:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Hero info lookup failed",
        details: error.message,
        hero_name: params.hero_name,
      },
      { status: 500 }
    );
  }
}

export async function POST(request) {
  return NextResponse.json(
    { 
      success: false, 
      error: "POST method not supported. Use GET to retrieve hero information." 
    },
    { status: 405 }
  );
}