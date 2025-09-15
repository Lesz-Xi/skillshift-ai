import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Swords, Shield, Building, Users } from "lucide-react";

export default function AdvancedStatsCard({ data }) {
  const {
    heroDamage,
    damageTaken,
    turretDamage,
    teamfightParticipation,
    gpm
  } = data;

  // Format damage numbers
  const formatDamage = (value) => {
    if (value === null || value === undefined) return "N/A";
    if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}k`;
    }
    return value.toString();
  };

  // Format GPM
  const formatGPM = (value) => {
    if (value === null || value === undefined) return "N/A";
    return value.toString();
  };

  // Get performance badge color based on values
  const getPerformanceBadge = (value, thresholds) => {
    if (value === null || value === undefined) return "secondary";
    if (value >= thresholds.excellent) return "default"; // Green
    if (value >= thresholds.good) return "outline"; // Yellow
    return "destructive"; // Red
  };

  // Performance thresholds (these can be made configurable later)
  const thresholds = {
    heroDamage: { excellent: 100000, good: 60000 },
    gpm: { excellent: 500, good: 400 },
    teamfight: { excellent: 80, good: 60 },
  };

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg font-semibold text-foreground flex items-center gap-2">
          <Swords className="w-5 h-5 text-primary" />
          Advanced Statistics
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Damage Statistics */}
        <div className="grid grid-cols-1 gap-3">
          {/* Hero Damage */}
          <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
            <div className="flex items-center gap-3">
              <Swords className="w-5 h-5 text-red-500" />
              <div>
                <p className="font-medium text-foreground">Hero Damage</p>
                <p className="text-sm text-muted-foreground">Damage dealt to enemies</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xl font-bold text-foreground">
                {formatDamage(heroDamage)}
              </p>
              <Badge
                variant={getPerformanceBadge(heroDamage, thresholds.heroDamage)}
                className="text-xs"
              >
                {heroDamage >= thresholds.heroDamage.excellent ? "Excellent" :
                 heroDamage >= thresholds.heroDamage.good ? "Good" :
                 heroDamage !== null ? "Fair" : "N/A"}
              </Badge>
            </div>
          </div>

          {/* Damage Taken */}
          <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
            <div className="flex items-center gap-3">
              <Shield className="w-5 h-5 text-blue-500" />
              <div>
                <p className="font-medium text-foreground">Damage Taken</p>
                <p className="text-sm text-muted-foreground">Damage received from enemies</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xl font-bold text-foreground">
                {formatDamage(damageTaken)}
              </p>
              <p className="text-xs text-muted-foreground">Survivability</p>
            </div>
          </div>

          {/* Turret Damage */}
          <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
            <div className="flex items-center gap-3">
              <Building className="w-5 h-5 text-orange-500" />
              <div>
                <p className="font-medium text-foreground">Turret Damage</p>
                <p className="text-sm text-muted-foreground">Objective damage dealt</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xl font-bold text-foreground">
                {formatDamage(turretDamage)}
              </p>
              <p className="text-xs text-muted-foreground">Push potential</p>
            </div>
          </div>
        </div>

        {/* Team Performance */}
        <div className="pt-2 border-t border-border">
          <div className="grid grid-cols-2 gap-4">
            {/* Teamfight Participation */}
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-purple-500" />
                <p className="text-sm text-muted-foreground">Teamfight %</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-foreground">
                  {teamfightParticipation !== null ? `${teamfightParticipation}%` : "N/A"}
                </p>
                <Badge
                  variant={getPerformanceBadge(teamfightParticipation, thresholds.teamfight)}
                  className="text-xs mt-1"
                >
                  {teamfightParticipation >= thresholds.teamfight.excellent ? "Excellent" :
                   teamfightParticipation >= thresholds.teamfight.good ? "Good" :
                   teamfightParticipation !== null ? "Fair" : "N/A"}
                </Badge>
              </div>
            </div>

            {/* GPM */}
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-yellow-500 rounded-full flex items-center justify-center">
                  <span className="text-xs font-bold text-black">G</span>
                </div>
                <p className="text-sm text-muted-foreground">Gold/Min</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-foreground">
                  {formatGPM(gpm)}
                </p>
                <Badge
                  variant={getPerformanceBadge(gpm, thresholds.gpm)}
                  className="text-xs mt-1"
                >
                  {gpm >= thresholds.gpm.excellent ? "Excellent" :
                   gpm >= thresholds.gpm.good ? "Good" :
                   gpm !== null ? "Fair" : "N/A"}
                </Badge>
              </div>
            </div>
          </div>
        </div>

        {/* Performance Summary */}
        <div className="pt-3 border-t border-border">
          <p className="text-xs text-muted-foreground text-center">
            Advanced statistics help identify strengths and improvement areas
          </p>
        </div>
      </CardContent>
    </Card>
  );
}