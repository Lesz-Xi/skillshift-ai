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
    hero,
    kda,
    gpm,
    role,
    coaching_feedback,
    __raw,
  } = analysisResult;

  // Extract damage statistics with backend-first binding
  const getDamageStatistics = () => {
    // First check for direct backend damage_stats field
    if (analysisResult.damage_stats) {
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

    // Fallback to __raw.damage_stats
    const raw = __raw ?? {};
    if (raw.damage_stats) {
      return {
        hero_damage: raw.damage_stats.hero_damage ?? null,
        tower_damage: raw.damage_stats.turret_damage ?? null,
        damage_taken: raw.damage_stats.damage_taken ?? null,
        teamfight_participation:
          raw.damage_stats.teamfight_participation ?? null,
      };
    }

    // Final fallback to legacy format and session-based fusion data
    const match = raw.match_data ?? {};
    const data = raw.data ?? {};
    return {
      hero_damage:
        raw.hero_damage ?? match.hero_damage ?? data.hero_damage ?? null,
      tower_damage:
        raw.tower_damage ??
        raw.turret_damage ??
        match.tower_damage ??
        match.turret_damage ??
        data.tower_damage ??
        data.turret_damage ??
        null,
      damage_taken:
        raw.damage_taken ?? match.damage_taken ?? data.damage_taken ?? null,
      teamfight_participation:
        raw.teamfight_participation ??
        raw.teamfight_participation_pct ??
        match.teamfight_participation ??
        data.teamfight_participation ??
        null,
    };
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

  // Check if damage statistics are available
  const hasDamageStats =
    damageStats.hero_damage !== null ||
    damageStats.damage_taken !== null ||
    damageStats.tower_damage !== null ||
    damageStats.teamfight_participation !== null;

  // Check fusion status from backend
  const fusionStatus =
    __raw?.data?.fusion_status || __raw?.fusion_status || "unknown";
  const sessionComplete =
    __raw?.session_complete || __raw?.data?.session_status === "complete";
  const needsBothScreenshots =
    fusionStatus.includes("Awaiting") || (!hasDamageStats && !sessionComplete);

  // Prepare data for components
  const overviewData = {
    hero,
    kda,
    role,
    duration,
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
      <Card
        className={
          success
            ? "bg-green-50/50 border-green-200"
            : "bg-red-50/50 border-red-200"
        }
      >
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {success ? (
                <CheckCircle className="w-6 h-6 text-green-600" />
              ) : (
                <AlertCircle className="w-6 h-6 text-red-600" />
              )}
              <div>
                <h3
                  className={`font-semibold ${
                    success ? "text-green-800" : "text-red-800"
                  }`}
                >
                  {success ? "Analysis Complete" : "Analysis Failed"}
                </h3>
                <p
                  className={`text-sm ${
                    success ? "text-green-700" : "text-red-700"
                  }`}
                >
                  {success
                    ? `Analysis completed with ${Math.round(
                        confidence_score * 100
                      )}% confidence`
                    : analysisResult.error || "Unknown error occurred"}
                </p>
              </div>
            </div>
            <Badge
              variant="outline"
              className={
                success
                  ? confidence_score >= 0.8
                    ? "bg-green-50 text-green-700 border-green-200"
                    : confidence_score >= 0.6
                    ? "bg-yellow-50 text-yellow-700 border-yellow-200"
                    : "bg-red-50 text-red-700 border-red-200"
                  : "bg-gray-50 text-gray-700 border-gray-200"
              }
            >
              Confidence: {Math.round(confidence_score * 100)}%
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
              ) : needsBothScreenshots ? (
                <Card className="bg-yellow-50/50 border-yellow-200">
                  <CardContent className="p-4 text-center">
                    <AlertCircle className="w-8 h-8 text-yellow-600 mx-auto mb-2" />
                    <p className="text-yellow-800 font-medium">
                      ⚠️{" "}
                      {fusionStatus === "Awaiting KDA stats"
                        ? "Awaiting KDA screenshot"
                        : fusionStatus === "Awaiting damage stats"
                        ? "Awaiting damage screenshot"
                        : "Stats not fused — upload both KDA and Damage screenshots."}
                    </p>
                    <p className="text-yellow-700 text-sm mt-1">
                      Upload screenshots from both the KDA view and damage stats
                      view to see complete analysis.
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <Card className="bg-gray-50/50 border-gray-200">
                  <CardContent className="p-4 text-center">
                    <AlertCircle className="w-8 h-8 text-gray-600 mx-auto mb-2" />
                    <p className="text-gray-800 font-medium">
                      Damage statistics not available
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
          <InsightsList
            insights={coaching_feedback}
            confidence={confidence_score}
          />

          {/* Debug info for development (remove in production) */}
          {process.env.NODE_ENV === "development" && (
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
