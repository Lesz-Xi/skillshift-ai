import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Brain,
  Trophy,
  Sword,
  DollarSign,
  Users,
  Target,
  Zap,
  Shield,
  TrendingUp,
  AlertTriangle,
  ChevronDown,
  ChevronUp
} from "lucide-react";
import { useState } from "react";

export default function InsightsList({ insights = [], confidence }) {
  const [isExpanded, setIsExpanded] = useState(true);

  // Icon mapping for different insight categories
  const getInsightIcon = (category) => {
    const iconMap = {
      "MVP Performance": Trophy,
      "Combat Excellence": Sword,
      "Economic Efficiency": DollarSign,
      "Team Performance": Users,
      "Positioning": Target,
      "Advanced Combos": Zap,
      "Survivability": Shield,
      "Improvement": TrendingUp,
      "Warning": AlertTriangle,
      "Damage Mastery": Sword,
      "Strategic": Brain,
    };

    const IconComponent = iconMap[category] || Brain;
    return IconComponent;
  };

  // Color mapping for different insight categories
  const getCategoryColor = (category) => {
    const colorMap = {
      "MVP Performance": "text-yellow-500",
      "Combat Excellence": "text-red-500",
      "Economic Efficiency": "text-green-500",
      "Team Performance": "text-purple-500",
      "Positioning": "text-blue-500",
      "Advanced Combos": "text-indigo-500",
      "Survivability": "text-emerald-500",
      "Improvement": "text-orange-500",
      "Warning": "text-amber-500",
      "Damage Mastery": "text-red-600",
      "Strategic": "text-slate-500",
    };

    return colorMap[category] || "text-slate-500";
  };

  // Parse insights from coaching feedback array
  const processInsights = () => {
    if (!insights || insights.length === 0) {
      // Generate fallback insights based on common coaching patterns
      return [
        {
          category: "Strategic",
          message: "Continue practicing to improve your gameplay performance",
          priority: "medium"
        },
        {
          category: "Team Performance",
          message: "Focus on teamwork and coordination for better results",
          priority: "medium"
        },
      ];
    }

    // Convert simple feedback strings to structured insights
    return insights.map((insight, index) => {
      let category = "Strategic";
      let priority = "medium";
      let message = insight;

      if (typeof insight === "string") {
        // Categorize based on content keywords
        if (insight.toLowerCase().includes("mvp") || insight.toLowerCase().includes("performance")) {
          category = "MVP Performance";
          priority = "high";
        } else if (insight.toLowerCase().includes("kda") || insight.toLowerCase().includes("combat")) {
          category = "Combat Excellence";
          priority = "high";
        } else if (insight.toLowerCase().includes("gpm") || insight.toLowerCase().includes("gold")) {
          category = "Economic Efficiency";
          priority = "medium";
        } else if (insight.toLowerCase().includes("team") || insight.toLowerCase().includes("participation")) {
          category = "Team Performance";
          priority = "high";
        } else if (insight.toLowerCase().includes("combo") || insight.toLowerCase().includes("skill")) {
          category = "Advanced Combos";
          priority = "high";
        } else if (insight.toLowerCase().includes("damage")) {
          category = "Damage Mastery";
          priority = "high";
        } else if (insight.toLowerCase().includes("position")) {
          category = "Positioning";
          priority = "high";
        }
      }

      return {
        category,
        message,
        priority,
        id: index
      };
    });
  };

  const processedInsights = processInsights();

  // Sort insights by priority
  const sortedInsights = processedInsights.sort((a, b) => {
    const priorityOrder = { high: 3, medium: 2, low: 1 };
    return priorityOrder[b.priority] - priorityOrder[a.priority];
  });

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold text-foreground flex items-center gap-2">
            <Brain className="w-5 h-5 text-primary" />
            AI Coaching Insights
            <Badge variant="outline" className="ml-2 text-xs">
              {sortedInsights.length} insights
            </Badge>
          </CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="h-8 w-8 p-0"
          >
            {isExpanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </Button>
        </div>
        {confidence && (
          <p className="text-sm text-muted-foreground">
            Analysis confidence: {Math.round(confidence * 100)}%
          </p>
        )}
      </CardHeader>

      {isExpanded && (
        <CardContent className="space-y-3">
          {sortedInsights.length > 0 ? (
            sortedInsights.map((insight) => {
              const IconComponent = getInsightIcon(insight.category);
              const iconColor = getCategoryColor(insight.category);

              return (
                <div
                  key={insight.id}
                  className="flex items-start gap-3 p-3 bg-muted/30 rounded-lg border border-border/50 hover:bg-muted/50 transition-colors"
                >
                  <div className={`mt-0.5 ${iconColor}`}>
                    <IconComponent className="w-5 h-5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge
                        variant="outline"
                        className={`text-xs font-medium ${
                          insight.priority === "high"
                            ? "bg-red-50 text-red-700 border-red-200"
                            : insight.priority === "medium"
                            ? "bg-yellow-50 text-yellow-700 border-yellow-200"
                            : "bg-blue-50 text-blue-700 border-blue-200"
                        }`}
                      >
                        {insight.category}
                      </Badge>
                      {insight.priority === "high" && (
                        <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                      )}
                    </div>
                    <p className="text-sm text-foreground leading-relaxed">
                      {insight.message}
                    </p>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="text-center py-6">
              <Brain className="w-8 h-8 text-muted-foreground mx-auto mb-3" />
              <p className="text-sm text-muted-foreground mb-2">
                No specific coaching insights available
              </p>
              <p className="text-xs text-muted-foreground">
                Upload more detailed screenshots for personalized feedback
              </p>
            </div>
          )}

          {/* Insights footer */}
          <div className="pt-3 border-t border-border">
            <p className="text-xs text-muted-foreground text-center">
              💡 Insights are generated based on your performance data and hero-specific patterns
            </p>
          </div>
        </CardContent>
      )}
    </Card>
  );
}