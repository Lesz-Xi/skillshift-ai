import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Clock, User, Trophy, Target } from "lucide-react";

export default function OverviewCard({ data }) {
  const { hero, kda, role, duration, mvpScore, confidence } = data;

  // Parse KDA data
  const kdaDisplay = (() => {
    if (kda) {
      if (typeof kda === "object") {
        return `${kda.kills || 0}/${kda.deaths || 0}/${kda.assists || 0}`;
      }
      return kda;
    }
    return "N/A";
  })();

  // Calculate KDA ratio for display
  const kdaRatio = (() => {
    if (kda && typeof kda === "object") {
      const { kills = 0, deaths = 0, assists = 0 } = kda;
      if (deaths === 0) return kills + assists; // Perfect KDA
      return ((kills + assists) / deaths).toFixed(2);
    }
    return "N/A";
  })();

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg font-semibold text-foreground flex items-center gap-2">
          <User className="w-5 h-5 text-primary" />
          Overview & Performance
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Hero & Role */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Hero</p>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="bg-primary/10 text-primary font-medium">
                {hero || "Unknown"}
              </Badge>
            </div>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Role</p>
            <div className="flex items-center gap-2">
              <Target className="w-4 h-4 text-muted-foreground" />
              <span className="font-medium text-foreground">{role || "Unknown"}</span>
            </div>
          </div>
        </div>

        {/* KDA Display */}
        <div className="space-y-2">
          <p className="text-sm text-muted-foreground">KDA Performance</p>
          <div className="flex items-center justify-between bg-muted/50 rounded-lg p-3">
            <div className="text-center">
              <p className="text-2xl font-bold text-foreground">{kdaDisplay}</p>
              <p className="text-xs text-muted-foreground">Kill/Death/Assist</p>
            </div>
            <div className="text-center">
              <p className="text-xl font-semibold text-primary">{kdaRatio}</p>
              <p className="text-xs text-muted-foreground">KDA Ratio</p>
            </div>
          </div>
        </div>

        {/* MVP Score & Duration */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">MVP Score</p>
            <div className="flex items-center gap-2">
              <Trophy className="w-4 h-4 text-yellow-500" />
              <span className="font-bold text-lg text-foreground">
                {mvpScore !== null && mvpScore !== undefined ? mvpScore : "N/A"}
              </span>
            </div>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Match Duration</p>
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-muted-foreground" />
              <span className="font-medium text-foreground">{duration || "N/A"}</span>
            </div>
          </div>
        </div>

        {/* Confidence Score */}
        {confidence !== null && confidence !== undefined && (
          <div className="pt-2 border-t border-border">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Analysis Confidence</span>
              <Badge
                variant="outline"
                className={confidence >= 0.8
                  ? "bg-green-50 text-green-700 border-green-200"
                  : confidence >= 0.6
                    ? "bg-yellow-50 text-yellow-700 border-yellow-200"
                    : "bg-red-50 text-red-700 border-red-200"
                }
              >
                {Math.round(confidence * 100)}%
              </Badge>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}