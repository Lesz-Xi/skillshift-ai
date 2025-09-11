import { NextResponse } from "next/server";
import fetch from "node-fetch";

// Configuration for the skillshift-ai backend
const SKILLSHIFT_AI_BASE_URL =
  process.env.SKILLSHIFT_AI_URL || "http://localhost:8000";

export async function GET(request) {
  try {
    const url = new URL(request.url);
    const limit = url.searchParams.get("limit") || "10";

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
            error: "Meta analysis service is currently unavailable",
            details: "Backend health check failed",
          },
          { status: 503 }
        );
      }
    } catch (healthError) {
      return NextResponse.json(
        {
          success: false,
          error: "Cannot connect to meta analysis service",
          details: "Please ensure the backend is running on port 8000",
        },
        { status: 503 }
      );
    }

    // Call the top meta heroes endpoint
    const metaResponse = await fetch(
      `${SKILLSHIFT_AI_BASE_URL}/api/meta-analysis/top-heroes?limit=${limitNum}`,
      {
        method: "GET",
        signal: AbortSignal.timeout(10000), // 10 second timeout
      }
    );

    if (!metaResponse.ok) {
      const errorText = await metaResponse.text();
      return NextResponse.json(
        {
          success: false,
          error: "Top heroes meta analysis failed",
          details: errorText,
        },
        { status: metaResponse.status }
      );
    }

    const metaResult = await metaResponse.json();

    // Transform response for frontend
    const dashboardResponse = {
      success: true,
      message: "Top meta heroes retrieved successfully",
      meta_analysis: {
        top_heroes: (metaResult.top_heroes || []).map((heroData, index) => {
          const [hero, win_rate] = Array.isArray(heroData) ? heroData : [heroData.hero, heroData.win_rate];
          return {
            rank: index + 1,
            hero: hero,
            win_rate: win_rate,
            win_rate_percentage: Math.round(win_rate * 100),
            tier: getTierFromWinRate(win_rate),
            recommendation: getRecommendationFromRank(index + 1)
          };
        }),
        total_count: metaResult.top_heroes?.length || 0,
        limit: limitNum
      },
      insights: {
        meta_trends: generateMetaTrends(metaResult.top_heroes || []),
        tier_distribution: generateTierDistribution(metaResult.top_heroes || []),
        recommendations: generateRecommendations(metaResult.top_heroes || [], limitNum)
      },
      metadata: {
        limit: limitNum,
        timestamp: new Date().toISOString(),
        backend_url: SKILLSHIFT_AI_BASE_URL,
        meta_version: "2.0.0",
        data_source: "hero_database"
      },
    };

    return NextResponse.json(dashboardResponse);

  } catch (error) {
    console.error("Top heroes meta analysis API error:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Top heroes meta analysis failed",
        details: error.message,
      },
      { status: 500 }
    );
  }
}

// Helper functions
function getTierFromWinRate(win_rate) {
  if (win_rate >= 0.65) return "S";
  if (win_rate >= 0.60) return "A";
  if (win_rate >= 0.55) return "B";
  if (win_rate >= 0.50) return "C";
  return "D";
}

function getRecommendationFromRank(rank) {
  if (rank <= 3) return "Must pick/ban";
  if (rank <= 5) return "Priority pick";
  if (rank <= 10) return "Strong pick";
  return "Viable option";
}

function generateMetaTrends(topHeroes) {
  if (!topHeroes || topHeroes.length === 0) return {};
  
  const avgWinRate = topHeroes.reduce((sum, heroData) => {
    const winRate = Array.isArray(heroData) ? heroData[1] : heroData.win_rate;
    return sum + winRate;
  }, 0) / topHeroes.length;

  return {
    average_win_rate: Math.round(avgWinRate * 100),
    meta_strength: avgWinRate >= 0.55 ? "strong" : avgWinRate >= 0.50 ? "balanced" : "weak",
    top_performer: topHeroes[0] ? (Array.isArray(topHeroes[0]) ? topHeroes[0][0] : topHeroes[0].hero) : "Unknown"
  };
}

function generateTierDistribution(topHeroes) {
  const tiers = { S: 0, A: 0, B: 0, C: 0, D: 0 };
  
  topHeroes.forEach(heroData => {
    const winRate = Array.isArray(heroData) ? heroData[1] : heroData.win_rate;
    const tier = getTierFromWinRate(winRate);
    tiers[tier]++;
  });
  
  return tiers;
}

function generateRecommendations(topHeroes, limit) {
  const recommendations = [];
  
  if (topHeroes.length === 0) return recommendations;
  
  // Add general recommendations based on meta
  const topPerformer = Array.isArray(topHeroes[0]) ? topHeroes[0][0] : topHeroes[0].hero;
  recommendations.push(`${topPerformer} is dominating the current meta`);
  
  const sTierCount = topHeroes.filter(heroData => {
    const winRate = Array.isArray(heroData) ? heroData[1] : heroData.win_rate;
    return winRate >= 0.65;
  }).length;
  
  if (sTierCount > 0) {
    recommendations.push(`${sTierCount} S-tier heroes available for priority picks`);
  }
  
  if (limit >= 10) {
    recommendations.push("Consider diversifying your hero pool from the top 10");
  }
  
  return recommendations;
}

export async function POST(request) {
  return NextResponse.json(
    { 
      success: false, 
      error: "POST method not supported. Use GET to retrieve top meta heroes." 
    },
    { status: 405 }
  );
}