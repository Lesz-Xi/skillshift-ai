"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import { CoachingTimeline } from "@/components/ui/timeline";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { FadeInUp, StaggeredContainer } from "@/components/ui/page-transitions";
import { InteractiveCard } from "@/components/ui/interactive-card";
import {
  Target,
  MapPin,
  Clock,
  Users,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Camera,
  Video,
  Brain,
  Eye,
  Play,
  Pause,
  MoreHorizontal,
} from "lucide-react";

export default function CoachingJobsPage() {
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);
  const [activeView, setActiveView] = useState("grid");

  // Player-focused coaching requests and analyses
  const coachingRequests = [
    {
      id: "CR-001",
      title: "Ling Jungle Optimization",
      type: "Screenshot Analysis",
      hero: "Ling",
      role: "Assassin",
      status: "analyzing",
      progress: 85,
      submittedAt: "2025-01-17 14:25",
      estimatedCompletion: "2025-01-17 14:32",
      description:
        "Analyzing your MVP performance to improve jungle efficiency and team fight positioning",
      focusAreas: [
        "Jungle Route Optimization",
        "Gank Timing Analysis",
        "Team Fight Positioning",
        "Objective Control",
      ],
      sourceFile: "mvp_screenshot_001.png",
      coachingGoal: "Improve from Epic to Legend rank",
    },
    {
      id: "CR-002",
      title: "Chang'e Positioning Improvement",
      type: "Video Analysis",
      hero: "Chang'e",
      role: "Mage",
      status: "queued",
      progress: 0,
      submittedAt: "2025-01-17 14:35",
      estimatedCompletion: "2025-01-17 14:45",
      description:
        "Analyzing your team fight positioning and spell rotation timing for better survivability",
      focusAreas: [
        "Safe Positioning vs Assassins",
        "Spell Rotation Timing",
        "Escape Route Planning",
        "Vision Control",
      ],
      sourceFile: "teamfight_video_002.mp4",
      coachingGoal: "Reduce deaths and increase team fight impact",
    },
    {
      id: "CR-003",
      title: "Granger ADC Improvement",
      type: "Screenshot Analysis",
      hero: "Granger",
      role: "Marksman",
      status: "completed",
      progress: 100,
      submittedAt: "2025-01-17 14:15",
      estimatedCompletion: "2025-01-17 14:22",
      description:
        "Analysis completed! Focus on improving your laning phase and team fight positioning",
      focusAreas: [
        "Last-hitting Consistency",
        "Position in Team Fights",
        "Target Prioritization",
        "Escape Timing",
      ],
      sourceFile: "granger_teamfight_003.png",
      coachingGoal: "Improve ADC performance and reduce deaths",
      resultSummary:
        "Good item builds, needs work on positioning and target selection",
    },
    {
      id: "CR-004",
      title: "Tigreal Tank Mastery",
      type: "Video Analysis",
      hero: "Tigreal",
      role: "Tank",
      status: "analyzing",
      progress: 62,
      submittedAt: "2025-01-17 14:20",
      estimatedCompletion: "2025-01-17 14:38",
      description:
        "Analyzing your initiation timing and team coordination for better tank performance",
      focusAreas: [
        "Initiation Timing",
        "Vision Control",
        "Peeling for ADC",
        "Objective Securing",
      ],
      sourceFile: "tigreal_objectives_004.mp4",
      coachingGoal: "Master tank role for better team coordination",
    },
    {
      id: "CR-005",
      title: "Hayabusa Combo Optimization",
      type: "Video Analysis",
      hero: "Hayabusa",
      role: "Assassin",
      status: "failed",
      progress: 45,
      submittedAt: "2025-01-17 14:10",
      estimatedCompletion: "2025-01-17 14:25",
      description:
        "Analysis failed due to video quality issues. Please resubmit with clearer footage",
      focusAreas: [
        "Shadow Combo Execution",
        "Target Selection",
        "Escape Routes",
        "Ultimate Timing",
      ],
      sourceFile: "hayabusa_combo_005.mp4",
      coachingGoal: "Perfect assassination combos and improve KDA",
      errorMessage: "Video quality too low for accurate analysis",
    },
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case "analyzing":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "completed":
        return "bg-green-100 text-green-800 border-green-200";
      case "queued":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "failed":
        return "bg-red-100 text-red-800 border-red-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case "high":
        return "bg-primary text-primary-foreground";
      case "medium":
        return "bg-muted text-muted-foreground";
      case "low":
        return "bg-secondary text-secondary-foreground";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "analyzing":
        return <Play className="w-4 h-4" />;
      case "completed":
        return <CheckCircle className="w-4 h-4" />;
      case "queued":
        return <Clock className="w-4 h-4" />;
      case "failed":
        return <XCircle className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  return (
    <StaggeredContainer className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="h2 font-display">Your Coaching Pipeline</h1>
          <p className="text-muted-foreground">
            Track your submitted analyses and coaching progress
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() =>
              toast.success(
                "New analysis request submitted! Check your coaching pipeline for progress."
              )
            }
          >
            <Target className="w-4 h-4 mr-2" />
            Request New Analysis
          </Button>
          <Button
            variant="outline"
            onClick={() =>
              toast.info(
                "💡 Pro tip: Upload clear screenshots for better analysis accuracy!"
              )
            }
          >
            <Brain className="w-4 h-4 mr-2" />
            Coaching Tips
          </Button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="bg-card border-border">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="kpi-label">Being Analyzed</p>
                <p className="kpi-value num">2</p>
              </div>
              <div className="p-3 bg-muted rounded-lg">
                <Target className="w-6 h-6 text-muted-foreground" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="kpi-label">Coaching Ready</p>
                <p className="kpi-value num">1</p>
              </div>
              <div className="p-3 bg-muted rounded-lg">
                <CheckCircle className="w-6 h-6 text-muted-foreground" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="kpi-label">In Queue</p>
                <p className="kpi-value num">1</p>
              </div>
              <div className="p-3 bg-muted rounded-lg">
                <Clock className="w-6 h-6 text-muted-foreground" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="kpi-label">Need Resubmit</p>
                <p className="kpi-value num">1</p>
              </div>
              <div className="p-3 bg-muted rounded-lg">
                <AlertTriangle className="w-6 h-6 text-muted-foreground" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* View Tabs */}
      <Tabs value={activeView} onValueChange={setActiveView}>
        <TabsList className="grid w-full grid-cols-2 max-w-md">
          <TabsTrigger value="grid">Grid View</TabsTrigger>
          <TabsTrigger value="timeline">Timeline View</TabsTrigger>
        </TabsList>

        <TabsContent value="grid" className="mt-6">
          {/* Operations Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {coachingRequests.map((request) => (
              <Card
                key={request.id}
                className="bg-card border-border hover:bg-muted/50 transition-colors"
              >
                <CardHeader className="pb-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-muted rounded-lg">
                        {request.type === "Screenshot Analysis" ? (
                          <Camera className="w-5 h-5 text-muted-foreground" />
                        ) : (
                          <Video className="w-5 h-5 text-muted-foreground" />
                        )}
                      </div>
                      <div>
                        <CardTitle className="text-lg font-semibold text-foreground">
                          {request.title}
                        </CardTitle>
                        <p className="text-sm text-muted-foreground">
                          {request.hero} • {request.role}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant="outline"
                        className={getStatusColor(request.status)}
                      >
                        {getStatusIcon(request.status)}
                        <span className="ml-1">{request.status}</span>
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <p className="text-sm text-muted-foreground">
                      {request.description}
                    </p>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Hero:</span>
                        <span className="ml-2 font-medium text-foreground">
                          {request.hero}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Goal:</span>
                        <span className="ml-2 font-medium text-foreground">
                          {request.coachingGoal}
                        </span>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Progress</span>
                        <span className="font-medium text-foreground">
                          {request.progress}%
                        </span>
                      </div>
                      <Progress value={request.progress} className="h-2" />
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-xs text-muted-foreground">
                      <div>
                        <span>Submitted:</span>
                        <div className="mono-small">{request.submittedAt}</div>
                      </div>
                      <div>
                        <span>ETA:</span>
                        <div className="mono-small">
                          {request.estimatedCompletion}
                        </div>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <div className="text-sm font-medium text-foreground">
                        Focus Areas:
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {request.focusAreas.map((area, index) => (
                          <Badge
                            key={index}
                            variant="secondary"
                            className="text-xs"
                          >
                            {area}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-2">
                      <div className="text-xs text-muted-foreground">
                        Source: {request.sourceFile}
                      </div>
                      <div className="flex gap-1">
                        <Button variant="ghost" size="icon" className="w-8 h-8">
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="icon" className="w-8 h-8">
                          <MoreHorizontal className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="timeline" className="mt-6">
          {/* Timeline View */}
          <CoachingTimeline
            requests={coachingRequests}
            onRequestClick={setSelectedAnalysis}
          />
        </TabsContent>
      </Tabs>
    </StaggeredContainer>
  );
}
