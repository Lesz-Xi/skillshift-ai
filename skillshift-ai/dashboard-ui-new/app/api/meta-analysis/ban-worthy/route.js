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
    if (isNaN(limitNum) || limitNum < 1 || limitNum > 20) {
      return NextResponse.json(
        { 
          success: false, 
          error: "Limit must be a number between 1 and 20" 
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

    // Call the ban worthy heroes endpoint
    const banResponse = await fetch(
      `${SKILLSHIFT_AI_BASE_URL}/api/meta-analysis/ban-worthy?limit=${limitNum}`,
      {
        method: "GET",
        signal: AbortSignal.timeout(10000), // 10 second timeout
      }
    );

    if (!banResponse.ok) {
      const errorText = await banResponse.text();
      return NextResponse.json(
        {
          success: false,
          error: "Ban-worthy heroes analysis failed",
          details: errorText,
        },
        { status: banResponse.status }
      );
    }

    const banResult = await banResponse.json();

    // Transform response for frontend
    const dashboardResponse = {
      success: true,
      message: "Ban-worthy heroes analysis completed successfully",
      ban_analysis: {
        ban_worthy_heroes: (banResult.ban_worthy_heroes || []).map((heroData, index) => {
          // Handle different response formats from backend
          if (typeof heroData === 'string') {
            // Simple string format
            return {
              rank: index + 1,
              hero: heroData,
              ban_priority: getBanPriorityFromRank(index + 1),
              reason: "High meta presence"
            };
          } else if (typeof heroData === 'object' && heroData.hero) {
            // Object format with detailed info
            return {
              rank: index + 1,
              hero: heroData.hero,
              ban_priority: getBanPriorityFromRank(index + 1),
              win_rate: heroData.win_rate || null,
              pick_rate: heroData.pick_rate || null,
              ban_rate: heroData.ban_rate || null,
              threat_level: heroData.threat_level || getThreatLevel(index + 1),
              reason: heroData.reason || generateBanReason(heroData, index + 1)
            };
          } else {
            // Fallback for other formats
            return {
              rank: index + 1,
              hero: String(heroData),
              ban_priority: getBanPriorityFromRank(index + 1),
              reason: "Meta consideration"
            };
          }
        }),
        total_count: banResult.ban_worthy_heroes?.length || 0,
        limit: limitNum
      },
      ban_strategy: {
        priority_bans: generatePriorityBans(banResult.ban_worthy_heroes || []),
        situational_bans: generateSituationalBans(banResult.ban_worthy_heroes || []),
        flex_bans: generateFlexBans(banResult.ban_worthy_heroes || [])
      },
      meta_insights: {
        ban_meta_summary: generateBanMetaSummary(banResult.ban_worthy_heroes || []),
        draft_recommendations: generateDraftRecommendations(banResult.ban_worthy_heroes || []),
        counter_strategies: generateCounterStrategies(banResult.ban_worthy_heroes || [])
      },
      metadata: {
        limit: limitNum,
        timestamp: new Date().toISOString(),
        backend_url: SKILLSHIFT_AI_BASE_URL,
        ban_analysis_version: "2.0.0",
        data_source: "hero_database"
      },
    };

    return NextResponse.json(dashboardResponse);

  } catch (error) {
    console.error("Ban-worthy heroes analysis API error:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Ban-worthy heroes analysis failed",
        details: error.message,
      },
      { status: 500 }
    );
  }
}

// Helper functions
function getBanPriorityFromRank(rank) {
  if (rank <= 2) return "Must ban";
  if (rank <= 4) return "High priority";
  if (rank <= 7) return "Situational";
  return "Consider";
}

function getThreatLevel(rank) {
  if (rank <= 3) return "Critical";
  if (rank <= 6) return "High";
  if (rank <= 10) return "Moderate";
  return "Low";
}

function generateBanReason(heroData, rank) {
  const reasons = [];
  
  if (heroData.win_rate && heroData.win_rate > 0.65) {
    reasons.push("Extremely high win rate");
  } else if (heroData.win_rate && heroData.win_rate > 0.60) {
    reasons.push("High win rate");
  }
  
  if (heroData.pick_rate && heroData.pick_rate > 0.30) {
    reasons.push("Very popular pick");
  } else if (heroData.pick_rate && heroData.pick_rate > 0.20) {
    reasons.push("Popular pick");
  }
  
  if (heroData.ban_rate && heroData.ban_rate > 0.40) {
    reasons.push("Commonly banned");
  }
  
  if (reasons.length === 0) {
    if (rank <= 3) reasons.push("Meta dominant");
    else if (rank <= 6) reasons.push("Strong meta presence");
    else reasons.push("Situational threat");
  }
  
  return reasons.join(", ");
}

function generatePriorityBans(banWorthyHeroes) {
  return banWorthyHeroes.slice(0, 3).map(hero => {
    const heroName = typeof hero === 'string' ? hero : hero.hero;
    return heroName;
  });
}

function generateSituationalBans(banWorthyHeroes) {
  return banWorthyHeroes.slice(3, 7).map(hero => {
    const heroName = typeof hero === 'string' ? hero : hero.hero;
    return heroName;
  });
}

function generateFlexBans(banWorthyHeroes) {
  return banWorthyHeroes.slice(7, 10).map(hero => {
    const heroName = typeof hero === 'string' ? hero : hero.hero;
    return heroName;
  });
}

function generateBanMetaSummary(banWorthyHeroes) {
  if (banWorthyHeroes.length === 0) return "No dominant meta threats identified";
  
  const topThreat = typeof banWorthyHeroes[0] === 'string' ? banWorthyHeroes[0] : banWorthyHeroes[0].hero;
  return `${topThreat} leads the ban priority list. ${banWorthyHeroes.length} heroes require ban consideration.`;
}

function generateDraftRecommendations(banWorthyHeroes) {
  const recommendations = [];
  
  if (banWorthyHeroes.length >= 3) {
    recommendations.push("Focus first 2 bans on top priority threats");
  }
  
  if (banWorthyHeroes.length >= 6) {
    recommendations.push("Consider team composition when selecting situational bans");
  }
  
  if (banWorthyHeroes.length >= 10) {
    recommendations.push("Prepare counter-picks for heroes you can't ban");
  }
  
  return recommendations;
}

function generateCounterStrategies(banWorthyHeroes) {
  const strategies = [];
  
  if (banWorthyHeroes.length > 0) {
    strategies.push("Ban phase: Target the most oppressive meta picks first");
  }
  
  if (banWorthyHeroes.length >= 5) {
    strategies.push("Pick phase: Secure counters to unbanned threats");
  }
  
  strategies.push("Team strategy: Coordinate bans with your team composition");
  
  return strategies;
}

export async function POST(request) {
  return NextResponse.json(
    { 
      success: false, 
      error: "POST method not supported. Use GET to retrieve ban-worthy heroes analysis." 
    },
    { status: 405 }
  );
}