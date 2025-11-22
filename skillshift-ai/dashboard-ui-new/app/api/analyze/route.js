import { NextResponse } from "next/server";
import FormData from "form-data";
import fetch from "node-fetch";
import http from "node:http";
import https from "node:https";

// Configuration for the skillshift-ai backend
const SKILLSHIFT_AI_BASE_URL =
  process.env.SKILLSHIFT_AI_URL || "http://localhost:8000";
const DEFAULT_IGN = process.env.DEFAULT_IGN || "";
// MANUS-AI FIX: Force use of session analysis service (never use fast analysis)
const USE_FAST_ANALYSIS = false; // MANUS: Always use session analysis for 90% confidence
const ANALYZE_TIMEOUT_MS = Number(process.env.ANALYZE_TIMEOUT_MS || "240000"); // 4 minutes default
const ANALYZE_ENDPOINT = "/api/analyze"; // MANUS: Always use session analysis endpoint

// Experience stage configurations for enhanced feedback
const EXPERIENCE_STAGES = {
  first_upload: {
    anticipationMessage: "🧠 Decoding your first gameplay DNA...",
    revelationPrefix: "🎯 Your gameplay soul revealed:",
    focusAreas: ["mvp_detection", "basic_performance", "potential_discovery"],
  },
  mvp_revealed: {
    anticipationMessage: "🎮 Analyzing your tactical instincts...",
    revelationPrefix: "⚡ Your decision patterns unlocked:",
    focusAreas: ["decision_making", "positioning", "team_coordination"],
  },
  deeper_insights: {
    anticipationMessage: "📈 Mapping your growth trajectory...",
    revelationPrefix: "🚀 Your mastery evolution:",
    focusAreas: ["consistency", "improvement_trends", "advanced_tactics"],
  },
  mastery_journey: {
    anticipationMessage: "🏆 Revealing your competitive edge...",
    revelationPrefix: "⭐ Elite insights unlocked:",
    focusAreas: ["meta_adaptation", "strategic_depth", "leadership_potential"],
  },
};

export async function POST(request) {
  try {
    // MANUS-AI FIX: Parse query parameters for IGN and session_id
    const url = new URL(request.url);
    const queryIgn = url.searchParams.get("ign") || "";
    const querySessionId = url.searchParams.get("session_id") || "";

    const formData = await request.formData();
    const file = formData.get("file");
    const allowDefaultIGN = process.env.ALLOW_DEFAULT_IGN === "true";

    // MANUS-AI FIX: Check both query parameters and form data for IGN and hero override
    const ignInput = (queryIgn || formData.get("ign") || "").toString().trim();
    const heroOverride = (formData.get("hero") || formData.get("hero_override") || "").toString().trim();
    const ign = ignInput || (allowDefaultIGN ? DEFAULT_IGN : "");
    if (!ign) {
      return NextResponse.json(
        {
          success: false,
          error: "IGN is required",
          details:
            "Please enter your in-game name (IGN) to anchor row parsing. Set ALLOW_DEFAULT_IGN=true to permit a default in development.",
          stage: "validation",
        },
        { status: 400 }
      );
    }
    const analysisType = formData.get("analysisType") || "general";
    const experienceStage = formData.get("experienceStage") || "first_upload";
    // MANUS-AI FIX: Generate session_id if not provided to ensure session-based fusion
    let sessionId = (querySessionId || formData.get("session_id") || "").toString().trim();
    if (!sessionId) {
      // Generate UUID for session-based analysis (required for 90% confidence)
      sessionId = 'session_' + Math.random().toString(36).substring(2, 11) + '_' + Date.now();
    }

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

    // DISABLED: Health check before processing - causes timeouts during analysis
    // try {
    //   const healthResponse = await fetch(
    //     `${SKILLSHIFT_AI_BASE_URL}/api/health-isolated`,
    //     {
    //       method: "GET",
    //       signal: AbortSignal.timeout(1000), // 1 second timeout for isolated health
    //     }
    //   );

    //   if (!healthResponse.ok) {
    //     console.error("Backend health check failed:", healthResponse.status);
    //     return NextResponse.json(
    //       {
    //         success: false,
    //         error: "Analysis service is currently unavailable",
    //         details: "Backend health check failed",
    //         stage: "health_check",
    //         backend_status: "degraded",
    //       },
    //       { status: 503 }
    //     );
    //   }
    // } catch (healthError) {
    //   console.error("Backend connection failed:", healthError);
    //   return NextResponse.json(
    //     {
    //       success: false,
    //       error: "Cannot connect to analysis service",
    //       details: "Please ensure the backend is running on port 8000",
    //       stage: "connection",
    //       backend_status: "offline",
    //     },
    //     { status: 503 }
    //   );
    // }

    // Get experience stage configuration
    const stageConfig =
      EXPERIENCE_STAGES[experienceStage] || EXPERIENCE_STAGES.first_upload;

    // Convert file once and reuse the buffer for any retries/fallback
    const fileBuffer = Buffer.from(await file.arrayBuffer());

    // Helper to build fresh FormData from buffer (avoids reusing consumed streams)
    const buildBackendFormData = () => {
      const fd = new FormData();
      fd.append("file", fileBuffer, {
        filename: file.name,
        contentType: file.type,
      });
      return fd;
    };

    // Choose endpoint based on configuration - use env var or default to heavy analysis
    const endpoint = USE_FAST_ANALYSIS
      ? "/api/analyze-instant"
      : ANALYZE_ENDPOINT;
    const timeout = USE_FAST_ANALYSIS ? 5000 : ANALYZE_TIMEOUT_MS; // 5s for instant, env-tunable for heavy

    // Prefer direct heavy analysis first; on timeout or socket errors, fall back to async jobs
    let analysisResult;
    try {
      const backendFormData = buildBackendFormData();
      const qp = new URLSearchParams();
      qp.set("ign", ign);
      if (sessionId) qp.set("session_id", sessionId);
      // MANUS-AI FIX: Pass hero override to backend for manual hero selection
      if (heroOverride) qp.set("hero_override", heroOverride);
      // CRITICAL FIX: Add extract_options to enable damage statistics extraction
      qp.set("extract_options", JSON.stringify({ with_damage: true }));
      const url = `${SKILLSHIFT_AI_BASE_URL}${endpoint}?${qp.toString()}`;
      const agent = url.startsWith("https")
        ? new https.Agent({ keepAlive: true })
        : new http.Agent({ keepAlive: true });

      const doFetch = async () =>
        fetch(url, {
          method: "POST",
          body: backendFormData,
          headers: backendFormData.getHeaders(),
          signal: AbortSignal.timeout(timeout),
          agent,
        });

      let analysisResponse = await doFetch();

      // Retry once if we hit a transient socket reset/hang-up during long processing
      if (!analysisResponse.ok) {
        const text = await analysisResponse.text();
        console.error("Analysis backend non-OK:", text);
        // For non-OK status, throw to trigger fallback logic below
        throw new Error(`Backend returned ${analysisResponse.status}: ${text}`);
      }

      analysisResult = await analysisResponse.json();
    } catch (err) {
      const msg = String(err?.message || err);
      const isAbort = err?.name === "AbortError" || msg.toLowerCase().includes("aborted");
      const isTransient = msg.includes("socket hang up") || msg.includes("ECONNRESET");

      // Retry once for transient errors before falling back
      if (!USE_FAST_ANALYSIS && isTransient) {
        console.warn("Transient error, retrying direct analysis once...", msg);
        try {
          const backendFormData2 = buildBackendFormData();
          const qp2 = new URLSearchParams();
          qp2.set("ign", ign);
          if (sessionId) qp2.set("session_id", sessionId);
          if (heroOverride) qp2.set("hero_override", heroOverride);
          // CRITICAL FIX: Add extract_options to enable damage statistics extraction
          qp2.set("extract_options", JSON.stringify({ with_damage: true }));
          const url2 = `${SKILLSHIFT_AI_BASE_URL}${endpoint}?${qp2.toString()}`;
          const agent2 = url2.startsWith("https")
            ? new https.Agent({ keepAlive: true })
            : new http.Agent({ keepAlive: true });
          const res2 = await fetch(url2, {
            method: "POST",
            body: backendFormData2,
            headers: backendFormData2.getHeaders(),
            signal: AbortSignal.timeout(timeout),
            agent: agent2,
          });
          if (res2.ok) {
            analysisResult = await res2.json();
          } else {
            throw new Error(`Retry returned ${res2.status}: ${await res2.text()}`);
          }
        } catch (retryErr) {
          console.warn("Retry failed, will attempt async fallback...", retryErr?.message || retryErr);
        }
      }

      // If still no result and error indicates timeout/reset, fall back to async job API
      if (!analysisResult && (isAbort || isTransient)) {
        console.warn("Falling back to async job pipeline due to:", msg);

        const asyncResult = await runAsyncFallback({
          fileBuffer,
          file,
          ign,
          pollTimeoutMs: ANALYZE_TIMEOUT_MS, // respect server timeout budget
          extractOptions: { with_damage: true }, // FIXED: Add extract_options for damage stats
        });
        analysisResult = asyncResult;
      }

      // If still no result, rethrow to outer error handler
      if (!analysisResult) {
        throw err;
      }
    }

    // CRITICAL FIX: Validate backend response structure - support both session-based and direct responses
    if (!analysisResult) {
      console.error("Invalid backend response structure: null/undefined response");
      return NextResponse.json(
        {
          success: false,
          error: "Invalid analysis response",
          details: "Backend returned null/undefined response",
          stage: "response_validation",
        },
        { status: 502 }
      );
    }

    // Check for valid session-based response (has session_id, screen_type, or data properties)
    const isSessionResponse = analysisResult.session_id ||
                             analysisResult.screen_type ||
                             analysisResult.data ||
                             analysisResult.session_complete !== undefined;

    // Check for valid direct response (has match_data or parsed_data)
    const isDirectResponse = analysisResult.match_data || analysisResult.parsed_data;

    // Ensure we have either type of valid response
    if (!isSessionResponse && !isDirectResponse) {
      console.error("Invalid backend response structure:", analysisResult);
      return NextResponse.json(
        {
          success: false,
          error: "Invalid analysis response",
          details: "Backend returned malformed data - missing required properties",
          stage: "response_validation",
        },
        { status: 502 }
      );
    }

    // Enhanced analysis with experience-aware insights
    const enhancedInsights = generateExperienceAwareInsights(
      analysisResult,
      experienceStage,
      stageConfig
    );

    // MANUS-AI FIX: Use the isSessionResponse from validation above (no redeclaration needed)

    // MANUS-AI FIX: Handle confidence score extraction from session-based responses
    let rawConfidence = 0;
    let sessionData = {};

    if (isSessionResponse) {
      // MANUS-AI: Session responses have confidence at the top level, not in .data
      sessionData = analysisResult; // Use the full response as session data
      // MANUS FIX: Check data.overall_confidence first (where backend puts fused confidence)
      rawConfidence = analysisResult.data?.overall_confidence ||
                     analysisResult.__raw?.data?.overall_confidence ||
                     analysisResult.confidence_score ||
                     analysisResult.__raw?.confidence_score ||
                     analysisResult.overall_confidence ||
                     analysisResult.analysis?.quality?.overall_confidence ||
                     analysisResult.quality?.overall_confidence ||
                     0;
    } else {
      // Extract confidence from direct response
      rawConfidence = analysisResult.confidence_scores?.overall_confidence ||
                     analysisResult.overall_confidence ||
                     analysisResult.diagnostics?.confidence_score ||
                     analysisResult.confidence_score ||
                     0;
    }

    // Normalize confidence to 0-100 range (percentage)
    const normalizedConfidence =
      rawConfidence > 1 ? rawConfidence : rawConfidence * 100;

    // MANUS-AI FIX: Validate data based on response type (hero-independent validation)
    let hasValidData;
    if (isSessionResponse) {
      // MANUS FIX: Validate based on fusion status and numeric data, NOT hero name
      // MANUS FIX: Validate based on fusion status and numeric data, NOT hero name
      const fusionComplete = sessionData.fusion_status === "Stats fused" ||
                            sessionData.data?.fusion_status === "Stats fused" ||
                            sessionData.__raw?.data?.fusion_status === "Stats fused";

      const sessionComplete = sessionData.session_status === "complete" ||
                             sessionData.session_complete === true ||
                             sessionData.data?.session_status === "complete" ||
                             sessionData.__raw?.data?.session_status === "complete";

      
      // Check for KDA data - support both enriched schema and legacy format
      const hasKDA = (
        // Enriched schema format (kda.k, kda.d, kda.a)
        (sessionData.kda?.k !== null && sessionData.kda?.k !== undefined) ||
        (sessionData.data?.kda?.k !== null && sessionData.data?.kda?.k !== undefined) ||  // MANUS FIX: Added nested check
        (sessionData.__raw?.kda?.k !== null && sessionData.__raw?.kda?.k !== undefined) ||
        // Legacy format (data.kills, data.deaths)
        (sessionData.data?.kills !== null && sessionData.data?.kills !== undefined) ||
        (sessionData.__raw?.data?.kills !== null && sessionData.__raw?.data?.kills !== undefined)
      );
      
      // Check for damage data - support enriched schema percentages and legacy format
      const hasDamageData = (
        // Enriched schema format (damage.hero_pct) - check if defined, even if 0
        (sessionData.damage?.hero_pct !== null && sessionData.damage?.hero_pct !== undefined) ||
        (sessionData.data?.damage?.hero_pct !== null && sessionData.data?.damage?.hero_pct !== undefined) || // MANUS FIX: Added nested check
        (sessionData.__raw?.damage?.hero_pct !== null && sessionData.__raw?.damage?.hero_pct !== undefined) ||
        // Legacy format (data.hero_damage) - must be finite number
        Number.isFinite(sessionData.data?.hero_damage) ||
        Number.isFinite(sessionData.data?.damage_taken) ||
        Number.isFinite(sessionData.__raw?.data?.hero_damage)
      );

      // CRITICAL FIX: Valid if we have BOTH KDA and damage (complete fusion), OR complete data from one view
      // Hero detection is OPTIONAL and does NOT affect validation
      const hasCompleteFusion = hasKDA && hasDamageData;
      const hasCompleteKDA = hasKDA && (sessionData.data?.deaths !== null || sessionData.__raw?.data?.deaths !== null);
      const hasCompleteDamage = hasDamageData && Number.isFinite(sessionData.data?.damage_taken || sessionData.__raw?.data?.damage_taken);
      
      hasValidData = hasCompleteFusion || hasCompleteKDA || hasCompleteDamage;
      
      console.log("Data validation:", {
        fusionComplete,
        sessionComplete,
        hasKDA,
        hasDamageData,
        hasCompleteFusion,
        hasValidData
      });
    } else {
      // Validate direct response data - focus on KDA/damage, not hero
      const hasKDA = analysisResult.parsed_data?.kda && analysisResult.parsed_data?.kda !== "N/A";
      const hasDamage = Number.isFinite(analysisResult.parsed_data?.hero_damage);
      hasValidData = hasKDA || hasDamage;
    }

    // MANUS-AI FIX: Trust backend confidence when we have valid stats (no capping)
    // Hero detection does NOT affect confidence - only statistical completeness matters
    const actualConfidence = hasValidData
      ? normalizedConfidence  // Trust backend confidence for valid data
      : Math.min(normalizedConfidence, 50);  // Only cap for truly incomplete data

    // MANUS-AI FIX: Pull performance data based on response type
    let perfSrc;
    if (isSessionResponse) {
      // MANUS FIX: Check sessionData.data first (where backend puts fused data)
      perfSrc = sessionData.data ||
               sessionData.__raw?.data ||
               sessionData.match_data ||
               sessionData.parsed_data ||
               sessionData.__raw ||
               sessionData.analysis?.performance ||
               {};
    } else {
      // Direct response uses parsed_data or match_data
      perfSrc = analysisResult.parsed_data || analysisResult.match_data || {};
    }
    const hero = perfSrc.hero || analysisResult.hero || "Unknown";
    // Build KDA from components if missing
    const kKills = perfSrc.kills ?? analysisResult.kills;
    const kDeaths = perfSrc.deaths ?? analysisResult.deaths;
    const kAssists = perfSrc.assists ?? analysisResult.assists;
    // KDA: require all three numeric components; otherwise prefer a parsed string containing '/'
    const hasAllKDA =
      Number.isFinite(kKills) && Number.isFinite(kDeaths) && Number.isFinite(kAssists);
    const parsedKdaStr =
      typeof perfSrc.kda === "string" && perfSrc.kda.includes("/")
        ? perfSrc.kda
        : typeof analysisResult.kda === "string" && analysisResult.kda.includes("/")
        ? analysisResult.kda
        : null;
    const kda = hasAllKDA ? `${kKills}/${kDeaths}/${kAssists}` : parsedKdaStr || "N/A";
    const damage = perfSrc.damage || perfSrc.hero_damage || analysisResult.damage || "N/A";
    let gpm =
      perfSrc.gpm ||
      perfSrc.gold_per_min ||
      analysisResult.gpm ||
      analysisResult.gold_per_min ||
      "N/A";
    // Fallback compute GPM if missing but gold(+_earned) + duration available
    if (
      (gpm === "N/A" || gpm === 0) &&
      (Number.isFinite(perfSrc.gold) || Number.isFinite(perfSrc.gold_earned) || Number.isFinite(analysisResult.gold) || Number.isFinite(analysisResult.gold_earned)) &&
      Number.isFinite(perfSrc.match_duration || analysisResult.match_duration) &&
      perfSrc.match_duration > 0
    ) {
      try {
        const goldVal = Number(perfSrc.gold ?? perfSrc.gold_earned ?? analysisResult.gold ?? analysisResult.gold_earned);
        const durVal = Number(perfSrc.match_duration ?? analysisResult.match_duration);
        if (Number.isFinite(goldVal) && Number.isFinite(durVal) && durVal > 0) {
          gpm = Math.round(goldVal / durVal);
        }
      } catch {}
    }
    const match_duration =
      perfSrc.match_duration || analysisResult.match_duration || "N/A";
    const rank = perfSrc.rank || analysisResult.rank || "Unknown";

    // CRITICAL FIX: Include raw backend response with damage_stats for frontend compatibility
    const dashboardResponse = {
      success: true,
      message: "Analysis completed successfully",
      // MANUS-AI FIX: Handle coaching feedback based on response type
      coaching_feedback: isSessionResponse ?
        (sessionData.coaching_feedback || sessionData.__raw?.coaching_feedback || []) :
        (analysisResult.coaching_feedback || []),
      // MANUS-AI FIX: Include appropriate raw data based on response type
      __raw: isSessionResponse ? sessionData : analysisResult, // Include raw backend response for damage_stats access
      analysis: {
        // Core analysis results
        statistical_feedback: enhancedInsights.statistical_feedback,
        mental_feedback: enhancedInsights.mental_feedback,

        // Player performance data
        performance: {
          hero,
          kda,
          damage,
          gpm,
          match_duration,
          rank,
          role: analysisResult.role || perfSrc.role || "Unknown",
          // MANUS FIX: Include damage statistics from perfSrc
          hero_damage: perfSrc.hero_damage || "N/A",
          damage_taken: perfSrc.damage_taken || "N/A",
          turret_damage: perfSrc.turret_damage || "N/A",
          teamfight_participation: perfSrc.teamfight_participation || "N/A",
        },

        // Confidence and quality metrics with validation
        quality: {
          overall_confidence: actualConfidence,
          confidence_category:
            actualConfidence >= 80
              ? "high"
              : actualConfidence >= 60
              ? "medium"
              : "low",
          component_scores:
            analysisResult.confidence_scores?.component_scores || {},
          warnings: analysisResult.parsing_warnings || analysisResult.warnings || [],
          data_validation_passed: hasValidData,
        },

        // Enhanced insights with experience progression
        insights: {
          processing_time:
            analysisResult.processing_time ||
            analysisResult.ultimate_analysis?.processing_time ||
            0,
          success_factors: enhancedInsights.success_factors || [],
          improvement_roadmap: enhancedInsights.improvement_roadmap || [],
          data_completeness:
            analysisResult.data_completeness ||
            analysisResult.ultimate_analysis?.data_completeness ||
            0,
          experience_progression: enhancedInsights.experience_progression,
        },
      },
      experience: {
        stage: experienceStage,
        stage_config: stageConfig,
        progression_detected: enhancedInsights.progression_detected,
        unlocked_features: enhancedInsights.unlocked_features,
        next_invitation: enhancedInsights.next_invitation,
      },
      metadata: {
        ign: ign,
        analysisType: analysisType,
        filename: file.name,
        fileSize: file.size,
        timestamp: new Date().toISOString(),
        backend_url: SKILLSHIFT_AI_BASE_URL,
        experienceStage: experienceStage,
      },
    };

    return NextResponse.json(dashboardResponse);
  } catch (error) {
    console.error("Analysis API error:", error);

    return NextResponse.json(
      {
        success: false,
        error: "Analysis pipeline failed",
        details: error.message,
        stage: "api_processing",
      },
      { status: 500 }
    );
  }
}

// Normalize various backend feedback shapes into unified objects
function normalizeFeedback(analysisResult) {
  if (!analysisResult) return [];

  // Priority order: backend coaching_feedback > statistical_feedback > feedback
  let items =
    analysisResult.coaching_feedback ||
    analysisResult.statistical_feedback ||
    analysisResult.feedback ||
    null;

  if (!items) return [];

  // Handle unified coaching feedback from backend session analysis
  if (Array.isArray(items)) {
    return items.map((item) => {
      if (typeof item === "string") {
        return { message: item, severity: "info", category: "coaching" };
      }
      if (typeof item === "object" && item !== null) {
        const message = item.message ?? item.feedback ?? String(item);
        const severity = item.severity ?? item.type ?? "info";
        const category = item.category ?? "coaching";
        return { message, severity, category };
      }
      return { message: String(item), severity: "info", category: "coaching" };
    });
  }

  return [];
}

async function runAsyncFallback({ fileBuffer, file, ign, pollTimeoutMs, extractOptions }) {
  // Build a fresh FormData for job creation
  const fd = new FormData();
  fd.append("file", fileBuffer, { filename: file.name, contentType: file.type });

  // Create the job on backend with extract_options
  const createUrl = `${SKILLSHIFT_AI_BASE_URL}/api/jobs?ign=${encodeURIComponent(ign)}${extractOptions ? `&extract_options=${encodeURIComponent(JSON.stringify(extractOptions))}` : ''}`;
  const createRes = await fetch(createUrl, {
    method: "POST",
    body: fd,
    headers: fd.getHeaders(),
    signal: AbortSignal.timeout(15000),
  });
  if (!createRes.ok) {
    const t = await createRes.text();
    throw new Error(`Async job creation failed: ${t}`);
  }
  const createJson = await createRes.json();
  const jobId = createJson.job_id;
  if (!jobId) throw new Error("Async job creation did not return job_id");

  // Poll for completion
  const start = Date.now();
  const pollInterval = 2000;
  while (Date.now() - start < pollTimeoutMs) {
    const statusUrl = `${SKILLSHIFT_AI_BASE_URL}/api/jobs/${jobId}`;
    try {
      const statusRes = await fetch(statusUrl, {
        method: "GET",
        signal: AbortSignal.timeout(8000),
      });
      if (statusRes.ok) {
        const status = await statusRes.json();
        if (status.state === "finished") {
          if (status.result) return status.result;
          throw new Error("Async job finished without result payload");
        }
        if (status.state === "failed") {
          throw new Error(status.error || "Async job failed");
        }
      }
    } catch (e) {
      // swallow transient polling errors and continue until timeout
      const m = String(e?.message || e);
      if (!(m.includes("timeout") || m.includes("ECONNRESET") || m.includes("socket hang up"))) {
        // non-transient: rethrow
        throw e;
      }
    }
    await new Promise((r) => setTimeout(r, pollInterval));
  }
  throw new Error("Async job polling timed out");
}

function generateExperienceAwareInsights(
  analysisResult,
  experienceStage,
  stageConfig
) {
  const baseStatistical = normalizeFeedback(analysisResult);
  const baseMental = analysisResult.mental_feedback || analysisResult.mental_boost || "";
  const baseSuccessFactors =
    analysisResult.ultimate_analysis?.success_factors || [];
  const baseRoadmap =
    analysisResult.ultimate_analysis?.improvement_roadmap || [];

  // Detect meaningful progressions based on stage
  const progressionDetected = detectProgression(
    analysisResult,
    experienceStage
  );
  const unlockedFeatures = determineUnlockedFeatures(
    analysisResult,
    experienceStage
  );
  const nextInvitation = generateNextInvitation(
    analysisResult,
    experienceStage
  );

  // Experience-aware enhancements
  let enhancedStatistical = [...baseStatistical];
  let enhancedMental = baseMental;
  let enhancedSuccessFactors = [...baseSuccessFactors];
  let enhancedRoadmap = [...baseRoadmap];

  switch (experienceStage) {
    case "first_upload":
      enhancedStatistical.unshift({
        message:
          "🎯 Welcome to your coaching journey! This analysis reveals your baseline gameplay DNA.",
        severity: "info",
        category: "experience_intro",
      });

      if (analysisResult.parsed_data?.rank?.includes("MVP")) {
        enhancedStatistical.push({
          message:
            "🏆 MVP performance detected! You have the potential for tactical leadership.",
          severity: "positive",
          category: "mvp_discovery",
        });
      }

      enhancedMental = `🧠 First Revelation: ${enhancedMental}\n\n🎯 This is just the beginning. Your gameplay patterns show ${getPersonalityHint(
        analysisResult
      )}. Ready to go deeper?`;
      break;

    case "mvp_revealed":
      enhancedStatistical.unshift({
        message:
          "⚡ Tactical Analysis: Your decision-making patterns are emerging from the data.",
        severity: "info",
        category: "tactical_focus",
      });

      enhancedMental = `🎮 Decision Pattern Analysis: ${enhancedMental}\n\n🧠 Your instincts are becoming visible. Each choice reveals your strategic DNA.`;
      break;

    case "deeper_insights":
      enhancedStatistical.unshift({
        message:
          "📈 Growth Trajectory: Analyzing consistency and improvement patterns across matches.",
        severity: "info",
        category: "growth_analysis",
      });

      enhancedMental = `🚀 Mastery Evolution: ${enhancedMental}\n\n📊 Your growth path is becoming clear. Patterns reveal your learning velocity.`;
      break;

    case "mastery_journey":
      enhancedStatistical.unshift({
        message:
          "⭐ Elite Analysis: Unlocking advanced strategic insights and meta adaptation patterns.",
        severity: "info",
        category: "elite_insights",
      });

      enhancedMental = `🏆 Competitive Edge: ${enhancedMental}\n\n⚡ You're operating at advanced levels. Time to explore leadership dynamics.`;
      break;
  }

  return {
    statistical_feedback: enhancedStatistical,
    mental_feedback: enhancedMental,
    success_factors: enhancedSuccessFactors,
    improvement_roadmap: enhancedRoadmap,
    progression_detected: progressionDetected,
    unlocked_features: unlockedFeatures,
    next_invitation: nextInvitation,
    experience_progression: {
      stage: experienceStage,
      insights_unlocked: enhancedStatistical.length,
      personality_hint: getPersonalityHint(analysisResult),
      mastery_indicators: getMasteryIndicators(analysisResult),
    },
  };
}

function detectProgression(analysisResult, experienceStage) {
  const confidence =
    analysisResult.confidence_scores?.overall_confidence ||
    analysisResult.diagnostics?.confidence_score ||
    0;
  const P = analysisResult.parsed_data || analysisResult.match_data || {};
  const hasMVP = typeof P.rank === "string" && P.rank.includes("MVP");
  const hasGoodKDA = parseFloat((P.kda || "0/0/0").split("/")[0]) > 5;

  switch (experienceStage) {
    case "first_upload":
      return hasMVP || confidence > 0.8;
    case "mvp_revealed":
      return hasGoodKDA && confidence > 0.7;
    case "deeper_insights":
      return confidence > 0.85;
    default:
      return false;
  }
}

function determineUnlockedFeatures(analysisResult, experienceStage) {
  const features = [];
  const P = analysisResult.parsed_data || analysisResult.match_data || {};
  const hasMVP = typeof P.rank === "string" && P.rank.includes("MVP");
  const confidence =
    analysisResult.confidence_scores?.overall_confidence ||
    analysisResult.diagnostics?.confidence_score ||
    0;

  if (experienceStage === "first_upload" && hasMVP) {
    features.push("video_analysis", "decision_tracking");
  }

  if (experienceStage === "mvp_revealed" && confidence > 0.7) {
    features.push("trend_analysis", "consistency_tracking");
  }

  if (experienceStage === "deeper_insights") {
    features.push("team_synergy", "meta_analysis");
  }

  return features;
}

function generateNextInvitation(analysisResult, experienceStage) {
  const P = analysisResult.parsed_data || analysisResult.match_data || {};
  const hasMVP = typeof P.rank === "string" && P.rank.includes("MVP");
  const hero = P.hero || "your hero";

  switch (experienceStage) {
    case "first_upload":
      if (hasMVP) {
        return {
          title: "🎮 Ready to see your instincts in action?",
          subtitle: `Your ${hero} shows MVP potential. Upload a gameplay video to see your real-time decision patterns.`,
          cta: "Analyze Decision-Making",
        };
      }
      return {
        title: "🧠 Want to understand your tactical mind?",
        subtitle:
          "Upload another match to reveal how your gameplay adapts under different conditions.",
        cta: "Continue Discovery",
      };

    case "mvp_revealed":
      return {
        title: "📈 Ready to map your growth journey?",
        subtitle:
          "Upload more matches to unlock your historical performance patterns and consistency metrics.",
        cta: "Unlock Growth Map",
      };

    case "deeper_insights":
      return {
        title: "⭐ Time for advanced mastery tools?",
        subtitle:
          "Access team synergy analysis, meta adaptation insights, and leadership potential assessment.",
        cta: "Explore Elite Features",
      };

    default:
      return {
        title: "🚀 Your journey continues...",
        subtitle: "Each upload reveals new layers of your competitive DNA.",
        cta: "Next Revelation",
      };
  }
}

function getPersonalityHint(analysisResult) {
  const P = analysisResult.parsed_data || analysisResult.match_data || {};
  const kda = P.kda || "0/0/0";
  const [kills, deaths, assists] = kda.split("/").map((x) => parseInt(x) || 0);

  if (kills > deaths * 2) {
    return "aggressive excellence - you strike decisively";
  } else if (assists > kills) {
    return "strategic support - you enable team victories";
  } else if (deaths < kills) {
    return "calculated aggression - you balance risk and reward";
  }
  return "adaptive potential - your style is emerging";
}

function getMasteryIndicators(analysisResult) {
  const indicators = [];
  const confidence =
    analysisResult.confidence_scores?.overall_confidence ||
    analysisResult.diagnostics?.confidence_score ||
    0;

  if (confidence > 0.9) indicators.push("elite_confidence");
  const P = analysisResult.parsed_data || analysisResult.match_data || {};
  if (typeof P.rank === "string" && P.rank.includes("MVP"))
    indicators.push("mvp_performance");
  if (P.damage) indicators.push("damage_dealing");

  return indicators;
}

export async function GET() {
  return NextResponse.json({
    message: "MLBB Coach AI Sequential Experience Analysis Endpoint",
    status: "operational",
    backend_url: SKILLSHIFT_AI_BASE_URL,
    supported_methods: ["POST"],
    required_fields: ["file"],
    optional_fields: ["ign", "analysisType", "experienceStage"],
    experience_stages: Object.keys(EXPERIENCE_STAGES),
  });
}
