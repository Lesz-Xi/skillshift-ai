import { NextResponse } from "next/server";
import fetch from "node-fetch";

// Configuration for the skillshift-ai backend
const SKILLSHIFT_AI_BASE_URL =
  process.env.SKILLSHIFT_AI_URL || "http://localhost:8000";

export async function GET(request) {
  try {
    const url = new URL(request.url);
    const query = url.searchParams.get("query");
    const limit = url.searchParams.get("limit") || "10";

    // Validate query parameter
    if (!query || query.trim().length === 0) {
      return NextResponse.json(
        { 
          success: false, 
          error: "Query parameter is required" 
        },
        { status: 400 }
      );
    }

    // Validate limit parameter
    const limitNum = parseInt(limit);
    if (isNaN(limitNum) || limitNum < 1 || limitNum > 50) {
      return NextResponse.json(
        { 
          success: false, 
          error: "Limit must be a number between 1 and 50" 
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

    // Call the hero search endpoint
    const searchResponse = await fetch(
      `${SKILLSHIFT_AI_BASE_URL}/api/hero-database/search/${encodeURIComponent(query)}?limit=${limitNum}`,
      {
        method: "GET",
        signal: AbortSignal.timeout(10000), // 10 second timeout
      }
    );

    if (!searchResponse.ok) {
      const errorText = await searchResponse.text();
      return NextResponse.json(
        {
          success: false,
          error: "Hero search failed",
          details: errorText,
        },
        { status: searchResponse.status }
      );
    }

    const searchResult = await searchResponse.json();

    // Transform response for frontend
    const dashboardResponse = {
      success: true,
      message: "Hero search completed successfully",
      search: {
        query: query,
        limit: limitNum,
        total_results: searchResult.results?.length || 0,
        results: (searchResult.results || []).map(result => ({
          hero: result.hero,
          confidence: result.confidence,
          match_type: result.match_type,
          source: result.source,
          relevance_score: Math.round(result.confidence * 100)
        }))
      },
      metadata: {
        query: query,
        limit: limitNum,
        timestamp: new Date().toISOString(),
        backend_url: SKILLSHIFT_AI_BASE_URL,
        search_version: "2.0.0"
      },
    };

    return NextResponse.json(dashboardResponse);

  } catch (error) {
    console.error("Hero search API error:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Hero search failed",
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
      error: "POST method not supported. Use GET with query parameter." 
    },
    { status: 405 }
  );
}