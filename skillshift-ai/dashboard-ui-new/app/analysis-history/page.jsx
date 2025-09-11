"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { KPIGridSkeleton } from "@/components/ui/kpi-card-skeleton";
import { EnhancedSearch } from "@/components/ui/enhanced-search";
import { VirtualAnalysisHistoryList } from "@/components/ui/virtual-list";
import { FadeInUp, StaggeredContainer } from "@/components/ui/page-transitions";
import {
  History,
  Search,
  Filter,
  Download,
  Eye,
  Calendar,
  Clock,
  Trophy,
  Target,
  TrendingUp,
  FileText,
  Play,
  Camera,
  Video,
  Star,
  AlertCircle,
  CheckCircle,
  MoreHorizontal,
} from "lucide-react";

export default function AnalysisHistoryPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedFilter, setSelectedFilter] = useState("all");
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);
  const [advancedFilters, setAdvancedFilters] = useState({});
  const [analysisHistory, setAnalysisHistory] = useState([]);
  const [summary, setSummary] = useState({
    total_analyses: 0,
    avg_score: 0,
    recent_count: 0,
    improvement_rate: 0,
  });
  const [loading, setLoading] = useState(true);

  // Fetch analysis history on component mount
  useEffect(() => {
    const fetchAnalysisHistory = async () => {
      try {
        setLoading(true);
        const response = await fetch("/api/analysis-history");
        const data = await response.json();

        if (data.success) {
          // Map API response to match expected format
          const mappedAnalyses = (data.data.analyses || []).map((analysis) => ({
            id: analysis.id,
            sessionId: analysis.session_id || analysis.sessionId,
            type: analysis.analysis_type || analysis.type,
            title: analysis.title,
            timestamp: analysis.timestamp,
            hero: analysis.hero,
            role: analysis.role,
            confidence: analysis.confidence,
            status: analysis.status,
            badges: analysis.match_data?.badges || analysis.badges || [],
            kda: analysis.match_data?.kda || analysis.kda,
            matchResult: analysis.match_data?.result || analysis.matchResult,
            coachingInsights:
              analysis.coaching_insights || analysis.coachingInsights || [],
            feedback: analysis.feedback || {},
          }));

          setAnalysisHistory(mappedAnalyses);
          setSummary(data.data.summary || {});
        } else {
          console.error("Failed to fetch analysis history:", data.error);
          // Fallback to mock data
          setAnalysisHistory(mockAnalysisHistory);
        }
      } catch (error) {
        console.error("Error fetching analysis history:", error);
        // Fallback to mock data
        setAnalysisHistory(mockAnalysisHistory);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysisHistory();
  }, []);

  // Mock data fallback
  const mockAnalysisHistory = [
    {
      id: "AH-001",
      sessionId: "session_12345",
      type: "screenshot",
      title: "MVP Performance Analysis",
      timestamp: "2025-01-17 14:30:00",
      hero: "Ling",
      role: "Assassin",
      confidence: 94,
      status: "completed",
      badges: ["MVP", "SAVAGE"],
      kda: "12/2/8",
      matchResult: "Victory",
      coachingInsights: [
        "Excellent positioning during team fights",
        "Consider improving early game farm efficiency",
        "Outstanding objective control timing",
      ],
      feedback: {
        strengths: ["Team fight positioning", "Objective timing"],
        improvements: ["Early game farming", "Map awareness"],
        score: 87,
      },
    },
    {
      id: "AH-002",
      sessionId: "session_12344",
      type: "video",
      title: "Team Fight Analysis",
      timestamp: "2025-01-17 12:15:00",
      hero: "Chang'e",
      role: "Mage",
      confidence: 88,
      status: "completed",
      badges: ["LEGENDARY"],
      kda: "8/3/15",
      matchResult: "Victory",
      coachingInsights: [
        "Good spell rotation timing",
        "Needs better positioning vs assassins",
        "Excellent team coordination",
      ],
      feedback: {
        strengths: ["Spell rotation", "Team coordination"],
        improvements: ["Positioning", "Vision control"],
        score: 79,
      },
    },
    {
      id: "AH-003",
      sessionId: "session_12343",
      type: "screenshot",
      title: "Laning Phase Analysis",
      timestamp: "2025-01-16 20:45:00",
      hero: "Granger",
      role: "Marksman",
      confidence: 76,
      status: "completed",
      badges: [],
      kda: "6/5/12",
      matchResult: "Defeat",
      coachingInsights: [
        "Improve last-hitting consistency",
        "Better warding placement needed",
        "Good item build choices",
      ],
      feedback: {
        strengths: ["Item builds", "Late game scaling"],
        improvements: ["Last-hitting", "Warding", "Lane pressure"],
        score: 64,
      },
    },
    {
      id: "AH-004",
      sessionId: "session_12342",
      type: "video",
      title: "Objective Control Study",
      timestamp: "2025-01-16 18:20:00",
      hero: "Tigreal",
      role: "Tank",
      confidence: 91,
      status: "completed",
      badges: ["PROTECTOR"],
      kda: "2/6/18",
      matchResult: "Victory",
      coachingInsights: [
        "Excellent initiation timing",
        "Strong vision control around objectives",
        "Consider more aggressive early roaming",
      ],
      feedback: {
        strengths: ["Initiation", "Vision control", "Team coordination"],
        improvements: ["Early aggression", "Lane presence"],
        score: 82,
      },
    },
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-800 border-green-200";
      case "processing":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "failed":
        return "bg-red-100 text-red-800 border-red-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getTypeIcon = (type) => {
    return type === "screenshot" ? (
      <Camera className="w-4 h-4" />
    ) : (
      <Video className="w-4 h-4" />
    );
  };

  const getScoreColor = (score) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  const filteredHistory = analysisHistory.filter((analysis) => {
    const matchesSearch =
      analysis.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      analysis.hero.toLowerCase().includes(searchTerm.toLowerCase()) ||
      analysis.role.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesFilter =
      selectedFilter === "all" ||
      analysis.type === selectedFilter ||
      (selectedFilter === "recent" &&
        new Date(analysis.timestamp) >
          new Date(Date.now() - 7 * 24 * 60 * 60 * 1000));

    // Advanced filters
    const matchesAdvancedFilters = Object.entries(advancedFilters).every(
      ([filterId, values]) => {
        if (!values || values.length === 0) return true;

        switch (filterId) {
          case "type":
            return values.includes(analysis.type);
          case "hero":
            return values.includes(analysis.hero.toLowerCase());
          case "result":
            return values.includes(analysis.matchResult?.toLowerCase());
          case "score":
            const score = analysis.feedback?.score || 0;
            return values.some((value) => {
              if (value === "excellent") return score >= 80;
              if (value === "good") return score >= 60 && score < 80;
              if (value === "needs-work") return score < 60;
              return false;
            });
          default:
            return true;
        }
      }
    );

    return matchesSearch && matchesFilter && matchesAdvancedFilters;
  });

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        {/* Header Skeleton */}
        <div className="flex items-center justify-between">
          <div>
            <Skeleton className="h-8 w-48 mb-2" />
            <Skeleton className="h-4 w-96" />
          </div>
          <div className="flex gap-2">
            <Skeleton className="h-10 w-32" />
            <Skeleton className="h-10 w-28" />
          </div>
        </div>

        {/* Search and KPI Skeletons */}
        <div className="flex flex-col lg:flex-row gap-6">
          <Skeleton className="h-10 flex-1" />
          <KPIGridSkeleton count={4} />
        </div>

        {/* Filter Tabs Skeleton */}
        <div className="flex gap-2">
          {Array.from({ length: 4 }).map((_, index) => (
            <Skeleton key={index} className="h-8 w-20" />
          ))}
        </div>

        {/* Analysis List Skeleton */}
        <Card className="bg-card border-border">
          <CardHeader>
            <Skeleton className="h-6 w-64" />
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Array.from({ length: 3 }).map((_, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-4 bg-muted/50 rounded-lg"
                >
                  <div className="flex items-center gap-4">
                    <Skeleton className="w-12 h-12 rounded-lg" />
                    <div className="space-y-2">
                      <Skeleton className="h-5 w-48" />
                      <Skeleton className="h-4 w-32" />
                      <Skeleton className="h-3 w-24" />
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right space-y-1">
                      <Skeleton className="h-4 w-16" />
                      <Skeleton className="h-3 w-20" />
                    </div>
                    <div className="flex gap-1">
                      <Skeleton className="w-8 h-8 rounded" />
                      <Skeleton className="w-8 h-8 rounded" />
                      <Skeleton className="w-8 h-8 rounded" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <StaggeredContainer className="p-6">
      {/* Header */}
      <FadeInUp>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="h2 font-display">Analysis History</h1>
            <p className="text-muted-foreground">
              Review your past coaching analyses and track improvement over time
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline">
              <Download className="w-4 h-4 mr-2" />
              Export History
            </Button>
            <Button variant="outline">
              <Filter className="w-4 h-4 mr-2" />
              Advanced Filter
            </Button>
          </div>
        </div>
      </FadeInUp>

      {/* Enhanced Search and Stats */}
      <FadeInUp delay={0.1}>
        <div className="flex flex-col lg:flex-row gap-6">
          <div className="flex-1">
            <EnhancedSearch
              searchTerm={searchTerm}
              onSearchChange={setSearchTerm}
              filters={advancedFilters}
              onFiltersChange={setAdvancedFilters}
              placeholder="Search analyses by hero, type, or keywords..."
              filterOptions={[
                {
                  id: "type",
                  label: "Analysis Type",
                  options: [
                    { value: "screenshot", label: "Screenshot", count: 28 },
                    { value: "video", label: "Video", count: 19 },
                  ],
                },
                {
                  id: "hero",
                  label: "Heroes",
                  options: [
                    { value: "ling", label: "Ling", count: 8 },
                    { value: "change", label: "Chang'e", count: 6 },
                    { value: "granger", label: "Granger", count: 5 },
                    { value: "tigreal", label: "Tigreal", count: 4 },
                    { value: "hayabusa", label: "Hayabusa", count: 3 },
                  ],
                },
                {
                  id: "result",
                  label: "Match Result",
                  options: [
                    { value: "victory", label: "Victory", count: 31 },
                    { value: "defeat", label: "Defeat", count: 16 },
                  ],
                },
                {
                  id: "score",
                  label: "Performance Score",
                  options: [
                    { value: "excellent", label: "Excellent (80+)", count: 12 },
                    { value: "good", label: "Good (60-79)", count: 23 },
                    {
                      value: "needs-work",
                      label: "Needs Work (<60)",
                      count: 12,
                    },
                  ],
                },
              ]}
            />
          </div>

          <div className="grid grid-cols-4 gap-4 lg:w-auto">
            <Card className="bg-card border-border">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="kpi-label">Total Analyses</p>
                    <p className="kpi-value num">{summary.total_analyses}</p>
                  </div>
                  <div className="p-2 bg-muted rounded-lg">
                    <History className="w-5 h-5 text-muted-foreground" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-card border-border">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="kpi-label">Avg Score</p>
                    <p className="kpi-value num">{summary.avg_score}</p>
                  </div>
                  <div className="p-2 bg-muted rounded-lg">
                    <Star className="w-5 h-5 text-muted-foreground" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-card border-border">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="kpi-label">This Week</p>
                    <p className="kpi-value num">{summary.recent_count}</p>
                  </div>
                  <div className="p-2 bg-muted rounded-lg">
                    <Calendar className="w-5 h-5 text-muted-foreground" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-card border-border">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="kpi-label">Improvement</p>
                    <p
                      className={`kpi-value num ${
                        summary.improvement_rate >= 0
                          ? "text-green-600"
                          : "text-red-600"
                      }`}
                    >
                      {summary.improvement_rate >= 0 ? "+" : ""}
                      {summary.improvement_rate}%
                    </p>
                  </div>
                  <div className="p-2 bg-muted rounded-lg">
                    <TrendingUp className="w-5 h-5 text-muted-foreground" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </FadeInUp>

      {/* Filter Tabs */}
      <FadeInUp delay={0.2}>
        <div className="flex gap-2">
          {["all", "screenshot", "video", "recent"].map((filter) => (
            <Button
              key={filter}
              variant={selectedFilter === filter ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedFilter(filter)}
            >
              {filter.charAt(0).toUpperCase() + filter.slice(1)}
            </Button>
          ))}
        </div>
      </FadeInUp>

      {/* Analysis History List */}
      <FadeInUp delay={0.3}>
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="h3 font-display">
              Coaching Analysis History ({filteredHistory.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {filteredHistory.length > 0 ? (
              <VirtualAnalysisHistoryList
                analyses={filteredHistory}
                onSelectAnalysis={setSelectedAnalysis}
              />
            ) : (
              <div className="text-center py-12">
                <History className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium text-foreground mb-2">
                  No analyses found
                </h3>
                <p className="text-muted-foreground mb-4">
                  Try adjusting your search terms or filters
                </p>
                <Button
                  onClick={() => {
                    setSearchTerm("");
                    setAdvancedFilters({});
                    setSelectedFilter("all");
                  }}
                >
                  Clear All Filters
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </FadeInUp>

      {/* Analysis Detail Modal/Panel */}
      <FadeInUp delay={0.4}>
        {selectedAnalysis && (
          <Card className="bg-card border-border">
            <CardHeader className="pb-4">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg font-semibold text-foreground">
                  Analysis Details: {selectedAnalysis.title}
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedAnalysis(null)}
                >
                  Close
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Match Info */}
                <div className="space-y-4">
                  <h4 className="font-medium text-foreground">
                    Match Information
                  </h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Hero:</span>
                      <span className="text-foreground">
                        {selectedAnalysis.hero} ({selectedAnalysis.role})
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">KDA:</span>
                      <span className="text-foreground">
                        {selectedAnalysis.kda}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Result:</span>
                      <span
                        className={
                          selectedAnalysis.matchResult === "Victory"
                            ? "text-green-600"
                            : "text-red-600"
                        }
                      >
                        {selectedAnalysis.matchResult}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Confidence:</span>
                      <span className="text-foreground">
                        {selectedAnalysis.confidence}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Coaching Feedback */}
                <div className="space-y-4">
                  <h4 className="font-medium text-foreground">
                    Coaching Insights
                  </h4>
                  <div className="space-y-2">
                    {(selectedAnalysis.coachingInsights || []).map(
                      (insight, index) => (
                        <div key={index} className="flex items-start gap-2">
                          <Target className="w-4 h-4 text-muted-foreground mt-0.5" />
                          <span className="text-sm text-foreground">
                            {insight}
                          </span>
                        </div>
                      )
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-4 mt-4">
                    <div>
                      <h5 className="font-medium text-green-600 mb-2">
                        Strengths
                      </h5>
                      <ul className="space-y-1">
                        {(selectedAnalysis.feedback?.strengths || []).map(
                          (strength, index) => (
                            <li
                              key={index}
                              className="text-sm text-muted-foreground flex items-center gap-1"
                            >
                              <CheckCircle className="w-3 h-3 text-green-500" />
                              {strength}
                            </li>
                          )
                        )}
                      </ul>
                    </div>
                    <div>
                      <h5 className="font-medium text-orange-600 mb-2">
                        Areas to Improve
                      </h5>
                      <ul className="space-y-1">
                        {(selectedAnalysis.feedback?.improvements || []).map(
                          (improvement, index) => (
                            <li
                              key={index}
                              className="text-sm text-muted-foreground flex items-center gap-1"
                            >
                              <AlertCircle className="w-3 h-3 text-orange-500" />
                              {improvement}
                            </li>
                          )
                        )}
                      </ul>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex gap-2 mt-6">
                <Button>
                  <FileText className="w-4 h-4 mr-2" />
                  View Full Report
                </Button>
                <Button variant="outline">
                  <Download className="w-4 h-4 mr-2" />
                  Export Analysis
                </Button>
                {selectedAnalysis.type === "video" && (
                  <Button variant="outline">
                    <Play className="w-4 h-4 mr-2" />
                    Watch Replay
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        )}
      </FadeInUp>
    </StaggeredContainer>
  );
}
