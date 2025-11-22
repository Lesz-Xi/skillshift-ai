import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, AlertCircle, Brain } from "lucide-react";
import OverviewCard from "./OverviewCard";
import AdvancedStatsCard from "./AdvancedStatsCard";
import InsightsList from "./InsightsList";

export default function CoachingFeedback({ analysisResult }) {
  if (!analysisResult) {
    return (
      <div className="text-center py-8">
        <p className="text-muted-foreground">No analysis results available</p>
      </div>
    );
  }

  const {
    success,
    confidence_score,
    __raw,
  } = analysisResult;

  // MANUS FIX: Extract data from nested 'data' object if available (fused results)
  const fusedData = analysisResult.data || {};
  
  // Robust extraction: Check fusedData first, then analysisResult top-level
  const hero = fusedData.hero || analysisResult.hero;
  
  // KDA: Handle object or individual fields
  const kdaRaw = fusedData.kda || analysisResult.kda;
  const kda = (kdaRaw && typeof kdaRaw === 'object') ? kdaRaw : analysisResult.kda;

  const gpm = fusedData.gpm || analysisResult.gpm;
  const role = fusedData.role || analysisResult.role;
  const match_duration = fusedData.match_duration || analysisResult.match_duration;
  const fusion_status = fusedData.fusion_status || analysisResult.fusion_status;
  const confidence_breakdown = fusedData.confidence_breakdown || analysisResult.confidence_breakdown;
  const coaching_feedback = fusedData.coaching_feedback || analysisResult.coaching_feedback;

  // Enhanced unified coaching feedback binding per triage checklist
  // Priority: analysis.coaching_feedback -> data.coaching_feedback -> __raw.coaching_feedback
  const getUnifiedCoachingFeedback = () => {
    // First check direct analysis.coaching_feedback (session fusion primary)
    if (analysisResult.data?.coaching_feedback && Array.isArray(analysisResult.data.coaching_feedback)) {
      return analysisResult.data.coaching_feedback;
    }
    // Then check top-level coaching_feedback (current format)
    if (coaching_feedback && Array.isArray(coaching_feedback)) {
      return coaching_feedback;
    }
    // Fallback to __raw.coaching_feedback (legacy compatibility)
    if (__raw?.coaching_feedback && Array.isArray(__raw.coaching_feedback)) {
      return __raw.coaching_feedback;
    }
    // Final fallback to empty array
    return [];
  };

  const unifiedCoachingFeedback = getUnifiedCoachingFeedback();

  // Enhanced confidence scoring per triage checklist
  // Use analysis.overall_confidence after merge, show partial status before merge
  const getBackendConfidence = () => {
    // First check analysis.overall_confidence (session fusion primary)
    if (analysisResult.data?.overall_confidence) {
      return analysisResult.data.overall_confidence;
    }
    // Then check top-level overall_confidence (current format)
    if (analysisResult.overall_confidence) {
      return analysisResult.overall_confidence;
    }
    // Fallback to confidence_score (legacy compatibility)
    return confidence_score || 0;
  };

  const backendConfidence = getBackendConfidence();
  const confidencePercent = Math.round(backendConfidence * 100);
  const confidenceThreshold = 0.4;
  const normalizedFusionStatus = (
    fusion_status ||
    __raw?.fusion_status ||
    __raw?.data?.fusion_status ||
    ""
  ).toLowerCase();
  const awaitingDamage = normalizedFusionStatus.includes("awaiting damage");
  const awaitingKda = normalizedFusionStatus.includes("awaiting kda");
  const fusionError =
    normalizedFusionStatus.includes("failed") ||
    normalizedFusionStatus.includes("error");
  const isSessionComplete =
    analysisResult.session_complete ||
    analysisResult.data?.session_status === "complete" ||
    __raw?.session_complete;
  const isConfident = success && backendConfidence >= confidenceThreshold;
  const hasInsights = Array.isArray(unifiedCoachingFeedback) && unifiedCoachingFeedback.length > 0;
  const shouldShowInsights = success && isConfident && hasInsights;

  const statusTone = !success
    ? "error"
    : isConfident
    ? "success"
    : confidencePercent === 0 || fusionError
    ? "error"
    : "warn";

  const fusionExplanation = fusionError
    ? "Fusion error — the backend couldn't merge both screenshots. Try uploading clearer images and confirm they match the same match."
    : awaitingDamage
    ? "Fusion pending — damage stats screenshot is still missing or being processed."
    : awaitingKda
    ? "Fusion pending — scoreboard screenshot is still missing or being processed."
    : "Confidence too low to trust the extracted data. Try re-uploading clearer screenshots.";

  const statusTitle =
    statusTone === "success" ? "Analysis Complete" : "Analysis Incomplete";
  const statusMessage =
    statusTone === "success"
      ? `Analysis ready with ${confidencePercent}% confidence`
      : confidencePercent === 0
      ? fusionExplanation
      : `${confidencePercent}% confidence — ${fusionExplanation}`;

  const cardToneClass =
    statusTone === "success"
      ? "bg-green-50/50 border-green-200"
      : statusTone === "warn"
      ? "bg-yellow-50/50 border-yellow-200"
      : "bg-red-50/50 border-red-200";
  const iconToneClass =
    statusTone === "success"
      ? "text-green-600"
      : statusTone === "warn"
      ? "text-yellow-600"
      : "text-red-600";
  const badgeToneClass =
    statusTone === "success"
      ? confidence_score >= 0.8
        ? "bg-green-50 text-green-700 border-green-200"
        : "bg-green-50 text-green-700 border-green-200"
      : statusTone === "warn"
      ? "bg-yellow-50 text-yellow-700 border-yellow-200"
      : "bg-red-50 text-red-700 border-red-200";

  // Enhanced damage statistics extraction per triage checklist
  // Priority: analysis.damage_stats -> data.damage_stats -> __raw.damage_stats -> legacy formats
  const getDamageStatistics = () => {
    console.log("🔍 [DAMAGE DEBUG] Extracting damage statistics from analysis result:", {
      has_data: !!analysisResult.data,
      has_damage_stats: !!analysisResult.damage_stats,
      has_raw: !!__raw,
      has_raw_damage_stats: !!__raw?.damage_stats,
      data_keys: analysisResult.data ? Object.keys(analysisResult.data) : [],
      raw_keys: __raw ? Object.keys(__raw) : [],
    });

    // MANUS FIX: Use the extracted fusedData for damage stats
    const damageFromFusedData = fusedData.damage || {};
    
    // Check for absolute values first (from fused result)
    if (damageFromFusedData.hero_damage !== undefined || damageFromFusedData.damage_taken !== undefined) {
      console.log("✅ [DAMAGE DEBUG] Found damage stats in fusedData.damage:", damageFromFusedData);
      return {
        hero_damage: damageFromFusedData.hero_damage ?? damageFromFusedData.hero_pct ?? null,
        tower_damage: damageFromFusedData.tower_damage ?? damageFromFusedData.turret_pct ?? null,
        damage_taken: damageFromFusedData.damage_taken ?? damageFromFusedData.taken_pct ?? null,
        teamfight_participation: analysisResult.teamfight_participation ?? __raw?.teamfight_participation ?? null,
      };
    }

    // First check analysis.damage_stats (session fusion primary)
    if (analysisResult.data?.damage_stats) {
      const stats = analysisResult.data.damage_stats;
      console.log("✅ [DAMAGE DEBUG] Found damage stats in analysisResult.data.damage_stats:", stats);
      return {
        hero_damage: stats.hero_damage ?? null,
        tower_damage: stats.turret_damage ?? stats.tower_damage ?? null,
        damage_taken: stats.damage_taken ?? null,
        teamfight_participation: stats.teamfight_participation ?? null,
      };
    }

    // Second check for direct backend damage_stats field (current format)
    if (analysisResult.damage_stats) {
      console.log("✅ [DAMAGE DEBUG] Found damage stats in analysisResult.damage_stats:", analysisResult.damage_stats);
      return {
        hero_damage: analysisResult.damage_stats.hero_damage ?? null,
        tower_damage:
          analysisResult.damage_stats.turret_damage ??
          analysisResult.damage_stats.tower_damage ??
          null,
        damage_taken: analysisResult.damage_stats.damage_taken ?? null,
        teamfight_participation:
          analysisResult.damage_stats.teamfight_participation ?? null,
      };
    }

    // Third fallback to __raw.damage_stats (legacy compatibility)
    const raw = __raw ?? {};
    if (raw.damage_stats) {
      console.log("✅ [DAMAGE DEBUG] Found damage stats in __raw.damage_stats:", raw.damage_stats);
      return {
        hero_damage: raw.damage_stats.hero_damage ?? null,
        tower_damage: raw.damage_stats.turret_damage ?? null,
        damage_taken: raw.damage_stats.damage_taken ?? null,
        teamfight_participation:
          raw.damage_stats.teamfight_participation ?? null,
      };
    }

    // Check for fused response format (damage percentages)
    const damage = analysisResult.damage ?? raw.damage ?? raw?.data?.damage;
    if (damage) {
      console.log("✅ [DAMAGE DEBUG] Found damage object in fused format:", damage);
      // Fused format has percentage fields - treat any non-null value as "has stats"
      return {
        hero_damage: damage.hero_damage ?? damage.hero_pct ?? null,
        tower_damage: damage.tower_damage ?? damage.turret_pct ?? null,
        damage_taken: damage.damage_taken ?? damage.taken_pct ?? null,
        teamfight_participation: analysisResult.teamfight_participation ?? raw.teamfight_participation ?? null,
      };
    }

    // Final fallback to legacy format and session-based fusion data
    const match = raw.match_data ?? {};
    const legacyStats = {
      hero_damage:
        raw.hero_damage ?? match.hero_damage ?? analysisResult.data?.hero_damage ?? null,
      tower_damage:
        raw.tower_damage ??
        raw.turret_damage ??
        match.tower_damage ??
        match.turret_damage ??
        analysisResult.data?.tower_damage ??
        analysisResult.data?.turret_damage ??
        null,
      damage_taken:
        raw.damage_taken ?? match.damage_taken ?? analysisResult.data?.damage_taken ?? null,
      teamfight_participation:
        raw.teamfight_participation ??
        raw.teamfight_participation_pct ??
        match.teamfight_participation ??
        analysisResult.data?.teamfight_participation ??
        null,
    };
    console.log("⚠️ [DAMAGE DEBUG] Using legacy format extraction:", {
      legacyStats,
      checked_paths: {
        raw_hero_damage: raw.hero_damage,
        match_hero_damage: match.hero_damage,
        data_hero_damage: analysisResult.data?.hero_damage,
      },
    });
    return legacyStats;
  };

  // Extract MVP score and duration from raw data
  const getMVPAndDuration = () => {
    const raw = __raw ?? {};
    const match = raw.match_data ?? {};

    return {
      mvp_score:
        raw.mvp_score ?? match.mvp_score ?? raw.mvp ?? match.mvp ?? null,
      duration:
        raw.duration ??
        match.duration ??
        raw.match_duration ??
        match.match_duration ??
        null,
    };
  };

  const damageStats = getDamageStatistics();
  const { mvp_score, duration } = getMVPAndDuration();
  const displayDuration = match_duration ?? duration;

  // Check if damage statistics are available
  const hasDamageStats =
    damageStats.hero_damage !== null ||
    damageStats.damage_taken !== null ||
    damageStats.tower_damage !== null ||
    damageStats.teamfight_participation !== null;

  // Check fusion status from backend
  const effectiveFusionStatus =
    fusion_status ||
    __raw?.fusion_status ||
    __raw?.data?.fusion_status ||
    "unknown";
  const sessionComplete =
    __raw?.session_complete || __raw?.data?.session_status === "complete";
  const needsBothScreenshots = awaitingDamage || awaitingKda;
  const showFusionWarning = fusionError || needsBothScreenshots;

  const fusionWarning = fusionError
    ? {
        title: "Fusion error — unable to merge screenshots",
        body: "Both screenshots were received, but the backend could not align them. Try re-uploading clearer images from the same match.",
      }
    : awaitingDamage
    ? {
        title: "Waiting for damage stats screenshot",
        body: "We detected the scoreboard view. Upload the damage stats screen to complete the merge.",
      }
    : awaitingKda
    ? {
        title: "Waiting for scoreboard screenshot",
        body: "We detected the damage stats view. Upload the KDA/scoreboard screen to finish the analysis.",
      }
    : {
        title: "Damage statistics not available",
        body: "This screenshot doesn't contain damage statistics.",
      };

  // Prepare data for components
  const overviewData = {
    hero,
    kda,
    role,
    duration: displayDuration,
    mvpScore: mvp_score,
    confidence: confidence_score,
  };

  const advancedStatsData = {
    heroDamage: damageStats.hero_damage,
    damageTaken: damageStats.damage_taken,
    turretDamage: damageStats.tower_damage,
    teamfightParticipation: damageStats.teamfight_participation,
    gpm,
  };

  return (
    <div className="space-y-6">
      {/* Header with analysis status */}
      <Card className={cardToneClass}>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {statusTone === "success" ? (
                <CheckCircle className={`w-6 h-6 ${iconToneClass}`} />
              ) : (
                <AlertCircle className={`w-6 h-6 ${iconToneClass}`} />
              )}
              <div>
                <h3 className={`font-semibold ${
                  statusTone === "success"
                    ? "text-green-800"
                    : statusTone === "warn"
                    ? "text-yellow-800"
                    : "text-red-800"
                }`}
                >
                  {statusTitle}
                </h3>
                <p className={`text-sm ${
                  statusTone === "success"
                    ? "text-green-700"
                    : statusTone === "warn"
                    ? "text-yellow-700"
                    : "text-red-700"
                }`}
                >
                  {statusTone === "error" && !success
                    ? analysisResult.error || "Unknown error occurred"
                    : statusMessage}
                </p>
              </div>
            </div>
            <Badge variant="outline" className={badgeToneClass}>
              {isSessionComplete
                ? `Confidence: ${confidencePercent}%`
                : "Partial (waiting for second screenshot)"}
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Only show detailed analysis if successful */}
      {success && (
        <>
          {/* Two-column metrics layout */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Column: Overview & Performance Metrics */}
            <div className="space-y-4">
              <OverviewCard data={overviewData} />
            </div>

            {/* Right Column: Advanced Stats */}
            <div className="space-y-4">
              {hasDamageStats ? (
                <AdvancedStatsCard data={advancedStatsData} />
              ) : showFusionWarning ? (
                <Card
                  className={
                    fusionError
                      ? "bg-red-50/50 border-red-200"
                      : "bg-yellow-50/50 border-yellow-200"
                  }
                >
                  <CardContent className="p-4 text-center">
                    <AlertCircle
                      className={`w-8 h-8 mx-auto mb-2 ${
                        fusionError ? "text-red-600" : "text-yellow-600"
                      }`}
                    />
                    <p
                      className={`font-medium ${
                        fusionError ? "text-red-800" : "text-yellow-800"
                      }`}
                    >
                      ⚠️ {fusionWarning.title}
                    </p>
                    <p
                      className={`text-sm mt-1 ${
                        fusionError ? "text-red-700" : "text-yellow-700"
                      }`}
                    >
                      {fusionWarning.body}
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <Card className="bg-gray-50/50 border-gray-200">
                  <CardContent className="p-4 text-center">
                    <AlertCircle className="w-8 h-8 text-gray-600 mx-auto mb-2" />
                    <p className="text-gray-800 font-medium">
                      ⚠️ Stats not fused — upload both KDA and Damage screenshots.
                    </p>
                    <p className="text-gray-700 text-sm mt-1">
                      This screenshot doesn't contain damage statistics.
                    </p>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>

          {/* Full-width AI Coaching Insights */}
          {shouldShowInsights ? (
            <InsightsList
              insights={unifiedCoachingFeedback}
              confidence={confidence_score}
            />
          ) : (
            <Card className="bg-muted/30 border-dashed">
              <CardContent className="p-4 text-center">
                <Brain className="w-6 h-6 text-muted-foreground mx-auto mb-2" />
                <p className="font-medium text-foreground">
                  {hasInsights
                    ? `Insights unlock at ${Math.round(
                        confidenceThreshold * 100
                      )}% confidence`
                    : "No insights available"}
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  {hasInsights
                    ? "Re-upload clearer screenshots so we can trust the metrics."
                    : "We need reliable KDA and damage stats before generating coaching tips."}
                </p>
              </CardContent>
            </Card>
          )}

          {/* Debug info for development (remove in production) */}
          {process.env.NEXT_PUBLIC_ENABLE_DEBUG_PANEL === "true" && (
            <Card className="bg-muted/30 border-dashed">
              <CardHeader>
                <CardTitle className="text-sm text-muted-foreground flex items-center gap-2">
                  <Brain className="w-4 h-4" />
                  Debug Information (Development Only)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <details className="text-xs">
                  <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
                    Raw Analysis Data
                  </summary>
                  <pre className="mt-2 p-2 bg-muted rounded text-xs overflow-auto max-h-40">
                    {JSON.stringify(__raw, null, 2)}
                  </pre>
                </details>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
