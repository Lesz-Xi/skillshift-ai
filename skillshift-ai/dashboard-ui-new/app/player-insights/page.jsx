"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Search,
  FileText,
  Eye,
  Download,
  Filter,
  Globe,
  Shield,
  AlertTriangle,
  Trophy,
  TrendingUp,
  TrendingDown,
} from "lucide-react";

export default function PlayerInsightsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedReport, setSelectedReport] = useState(null);

  const reports = [
    {
      id: "PI-2025-001",
      title: "SHADOW_STRIKER PERFORMANCE ANALYSIS",
      classification: "DETAILED",
      analysisType: "Performance Review",
      player: "SHADOW_STRIKER",
      date: "2025-01-17",
      status: "completed",
      threat: "high",
      summary:
        "Comprehensive analysis showing consistent MVP performance with strong KDA ratios across ranked matches",
      tags: ["MVP STREAK", "HIGH KDA", "RANKED DOMINATION", "ASSASSIN MASTERY"],
      rank: "Mythic III",
      role: "Assassin",
      matches: 47,
    },
    {
      id: "PI-2025-002",
      title: "FROST_MAGE SYNERGY BREAKDOWN",
      classification: "CRITICAL",
      analysisType: "Team Sync Analysis",
      player: "FROST_MAGE",
      date: "2025-01-17",
      status: "flagged",
      threat: "critical",
      summary:
        "Analysis reveals concerning team coordination issues and positioning problems in recent matches",
      tags: [
        "POOR SYNERGY",
        "POSITIONING ISSUES",
        "TEAM COORDINATION",
        "NEEDS COACHING",
      ],
      rank: "Legend I",
      role: "Mage",
      matches: 32,
    },
    {
      id: "PI-2025-003",
      title: "BLADE_MASTER MEDAL ACHIEVEMENT",
      classification: "STANDARD",
      analysisType: "Achievement Analysis",
      player: "BLADE_MASTER",
      date: "2025-01-17",
      status: "completed",
      threat: "low",
      summary:
        "Recent medal achievements indicate improved gameplay mechanics and strategic decision-making",
      tags: [
        "MEDAL EARNED",
        "IMPROVEMENT TREND",
        "GOOD MECHANICS",
        "STRATEGIC PLAY",
      ],
      rank: "Mythic V",
      role: "Fighter",
      matches: 63,
    },
    {
      id: "PI-2025-004",
      title: "MYSTIC_ARCHER BEHAVIORAL PATTERNS",
      classification: "DETAILED",
      analysisType: "Behavior Analysis",
      player: "MYSTIC_ARCHER",
      date: "2025-01-17",
      status: "active",
      threat: "medium",
      summary:
        "Behavioral analysis shows inconsistent engagement patterns and potential tilt indicators",
      tags: [
        "BEHAVIORAL ISSUES",
        "INCONSISTENT PLAY",
        "TILT INDICATORS",
        "NEEDS MENTAL COACHING",
      ],
      rank: "Epic I",
      role: "Marksman",
      matches: 28,
    },
    {
      id: "PI-2025-005",
      title: "IRON_GUARDIAN TRAINING PROGRESS",
      classification: "STANDARD",
      analysisType: "Training Assessment",
      player: "IRON_GUARDIAN",
      date: "2025-01-17",
      status: "completed",
      threat: "low",
      summary:
        "Training module completion shows steady improvement in tank positioning and team protection",
      tags: [
        "TRAINING PROGRESS",
        "TANK POSITIONING",
        "TEAM PROTECTION",
        "STEADY IMPROVEMENT",
      ],
      rank: "Master IV",
      role: "Tank",
      matches: 12,
    },
  ];

  const getClassificationColor = (classification) => {
    switch (classification) {
      case "CRITICAL":
        return "bg-muted text-muted-foreground";
      case "DETAILED":
        return "bg-secondary text-secondary-foreground";
      case "STANDARD":
        return "bg-muted text-muted-foreground";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  const getThreatColor = (threat) => {
    switch (threat) {
      case "critical":
        return "bg-muted text-muted-foreground";
      case "high":
        return "bg-primary text-primary-foreground";
      case "medium":
        return "bg-secondary text-secondary-foreground";
      case "low":
        return "bg-muted text-muted-foreground";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "completed":
        return "bg-primary text-primary-foreground";
      case "flagged":
        return "bg-muted text-muted-foreground";
      case "active":
        return "bg-secondary text-secondary-foreground";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  const getTagColor = (tag) => {
    if (
      tag.includes("MVP") ||
      tag.includes("HIGH") ||
      tag.includes("MASTERY") ||
      tag.includes("IMPROVEMENT")
    ) {
      return "bg-primary text-primary-foreground";
    }
    if (
      tag.includes("POOR") ||
      tag.includes("ISSUES") ||
      tag.includes("NEEDS") ||
      tag.includes("BEHAVIORAL")
    ) {
      return "bg-muted text-muted-foreground";
    }
    if (
      tag.includes("TRAINING") ||
      tag.includes("PROGRESS") ||
      tag.includes("STEADY")
    ) {
      return "bg-secondary text-secondary-foreground";
    }
    return "bg-muted text-muted-foreground";
  };

  const filteredReports = reports.filter(
    (report) =>
      report.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      report.player.toLowerCase().includes(searchTerm.toLowerCase()) ||
      report.tags.some((tag) =>
        tag.toLowerCase().includes(searchTerm.toLowerCase())
      )
  );

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground tracking-wider">
            PLAYER INSIGHTS
          </h1>
          <p className="text-sm text-muted-foreground">
            Generated reports and analysis insights
          </p>
        </div>
        <div className="flex gap-2">
          <Button>Generate Report</Button>
          <Button variant="outline">
            <Filter className="w-4 h-4 mr-2" />
            Filter
          </Button>
        </div>
      </div>

      {/* Stats and Search */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <Card className="lg:col-span-2 bg-card border-border">
          <CardContent className="p-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search insights reports..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground tracking-wider">
                  TOTAL REPORTS
                </p>
                <p className="text-2xl font-bold text-foreground font-mono">
                  2,847
                </p>
              </div>
              <FileText className="w-8 h-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground tracking-wider">
                  FLAGGED PLAYERS
                </p>
                <p className="text-2xl font-bold text-foreground font-mono">
                  23
                </p>
              </div>
              <AlertTriangle className="w-8 h-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground tracking-wider">
                  HIGH PERFORMERS
                </p>
                <p className="text-2xl font-bold text-foreground font-mono">
                  156
                </p>
              </div>
              <Trophy className="w-8 h-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Player Insights Reports */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-muted-foreground tracking-wider">
            PLAYER INSIGHTS REPORTS
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredReports.map((report) => (
              <div
                key={report.id}
                className="border border-border rounded p-4 hover:border-primary/50 transition-colors cursor-pointer"
                onClick={() => setSelectedReport(report)}
              >
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                  <div className="flex-1 space-y-2">
                    <div className="flex items-start gap-3">
                      <FileText className="w-5 h-5 text-muted-foreground mt-0.5" />
                      <div className="flex-1">
                        <h3 className="text-sm font-bold text-foreground tracking-wider">
                          {report.title}
                        </h3>
                        <div className="flex items-center gap-2 mt-1">
                          <p className="text-xs text-muted-foreground font-mono">
                            {report.id}
                          </p>
                          <span className="text-xs text-muted-foreground">
                            •
                          </span>
                          <p className="text-xs text-muted-foreground">
                            Player: {report.player}
                          </p>
                          <span className="text-xs text-muted-foreground">
                            •
                          </span>
                          <p className="text-xs text-muted-foreground">
                            {report.role} - {report.rank}
                          </p>
                        </div>
                      </div>
                    </div>

                    <p className="text-sm text-foreground ml-8">
                      {report.summary}
                    </p>

                    <div className="flex flex-wrap gap-2 ml-8">
                      {report.tags.map((tag) => (
                        <Badge
                          key={tag}
                          className={`text-xs ${getTagColor(tag)}`}
                        >
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  <div className="flex flex-col sm:items-end gap-2">
                    <div className="flex flex-wrap gap-2">
                      <Badge
                        className={getClassificationColor(
                          report.classification
                        )}
                      >
                        {report.classification}
                      </Badge>
                      <Badge className={getThreatColor(report.threat)}>
                        {report.threat === "high"
                          ? "HIGH IMPACT"
                          : report.threat.toUpperCase()}
                      </Badge>
                      <Badge className={getStatusColor(report.status)}>
                        {report.status.toUpperCase()}
                      </Badge>
                    </div>

                    <div className="text-xs text-muted-foreground space-y-1">
                      <div className="flex items-center gap-2">
                        <Eye className="w-3 h-3" />
                        <span>{report.analysisType}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Trophy className="w-3 h-3" />
                        <span>{report.matches} matches analyzed</span>
                      </div>
                      <div className="font-mono">{report.date}</div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Report Detail Modal */}
      {selectedReport && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <Card className="bg-card border-border w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-xl font-bold text-foreground tracking-wider">
                  {selectedReport.title}
                </CardTitle>
                <p className="text-sm text-muted-foreground font-mono">
                  {selectedReport.id}
                </p>
              </div>
              <Button
                variant="ghost"
                onClick={() => setSelectedReport(null)}
                className="text-muted-foreground hover:text-foreground"
              >
                ✕
              </Button>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-medium text-muted-foreground tracking-wider mb-2">
                      CLASSIFICATION
                    </h3>
                    <div className="flex gap-2">
                      <Badge
                        className={getClassificationColor(
                          selectedReport.classification
                        )}
                      >
                        {selectedReport.classification}
                      </Badge>
                      <Badge className={getThreatColor(selectedReport.threat)}>
                        IMPACT: {selectedReport.threat.toUpperCase()}
                      </Badge>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm font-medium text-muted-foreground tracking-wider mb-2">
                      PLAYER DETAILS
                    </h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Player:</span>
                        <span className="text-foreground font-mono">
                          {selectedReport.player}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Role:</span>
                        <span className="text-foreground">
                          {selectedReport.role}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Rank:</span>
                        <span className="text-foreground font-mono">
                          {selectedReport.rank}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Matches:</span>
                        <span className="text-foreground font-mono">
                          {selectedReport.matches}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">
                          Report Date:
                        </span>
                        <span className="text-foreground font-mono">
                          {selectedReport.date}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Status:</span>
                        <Badge
                          className={getStatusColor(selectedReport.status)}
                        >
                          {selectedReport.status.toUpperCase()}
                        </Badge>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-medium text-muted-foreground tracking-wider mb-2">
                      ANALYSIS TYPE
                    </h3>
                    <div className="flex items-center gap-2">
                      <Eye className="w-4 h-4 text-muted-foreground" />
                      <span className="text-foreground">
                        {selectedReport.analysisType}
                      </span>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm font-medium text-muted-foreground tracking-wider mb-2">
                      IMPACT ASSESSMENT
                    </h3>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">
                          Impact Level
                        </span>
                        <Badge
                          className={getThreatColor(selectedReport.threat)}
                        >
                          {selectedReport.threat.toUpperCase()}
                        </Badge>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm font-medium text-muted-foreground tracking-wider mb-2">
                      INSIGHT TAGS
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedReport.tags.map((tag) => (
                        <Badge
                          key={tag}
                          className={`text-xs ${getTagColor(tag)}`}
                        >
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-sm font-medium text-muted-foreground tracking-wider mb-2">
                  ANALYSIS SUMMARY
                </h3>
                <p className="text-sm text-foreground leading-relaxed">
                  {selectedReport.summary}
                </p>
              </div>

              <div className="flex gap-2 pt-4 border-t border-border">
                <Button>
                  <Eye className="w-4 h-4 mr-2" />
                  View Full Report
                </Button>
                <Button variant="outline">
                  <Download className="w-4 h-4 mr-2" />
                  Export
                </Button>
                <Button variant="outline">Send to Player</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
