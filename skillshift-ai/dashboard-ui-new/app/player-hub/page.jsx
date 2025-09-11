"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { KPIGridSkeleton } from "@/components/ui/kpi-card-skeleton";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { MiniTrendChart } from "@/components/ui/mini-chart";
import { NumberTicker } from "@/components/ui/number-ticker";
import { MultiProgressIndicator } from "@/components/ui/animated-progress";
import { InteractiveCard, GlowCard } from "@/components/ui/interactive-card";
import { FadeInUp, StaggeredContainer } from "@/components/ui/page-transitions";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Users,
  TrendingUp,
  Activity,
  Clock,
  MoreHorizontal,
  Eye,
  Play,
  Loader,
  CheckCircle,
  Percent,
  ArrowUp,
  ArrowDown,
} from "lucide-react";

export default function PlayerHubPage() {
  const [loading, setLoading] = useState(true);

  // Simulate loading for demo
  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 1500);
    return () => clearTimeout(timer);
  }, []);

  const players = [
    {
      id: "S",
      name: "SHADOW_STRIKER",
      status: "analyzed",
      role: "Assassin",
      kda: "5/2/8",
      score: 87,
      badges: ["MVP"],
      lastActive: "2 hours ago",
    },
    {
      id: "F",
      name: "FROST_MAGE",
      status: "pending",
      role: "Mage",
      kda: "8/1/12",
      score: 92,
      badges: ["LEGENDARY"],
      lastActive: "5 minutes ago",
    },
    {
      id: "L",
      name: "LIGHTNING_BOLT",
      status: "training",
      role: "Fighter",
      kda: "3/4/6",
      score: 78,
      badges: [],
      lastActive: "1 hour ago",
    },
    {
      id: "C",
      name: "CYBER_NINJA",
      status: "analyzed",
      role: "Assassin",
      kda: "12/0/5",
      score: 95,
      badges: ["MVP", "SAVAGE"],
      lastActive: "30 minutes ago",
    },
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case "analyzed":
        return "bg-muted text-muted-foreground border-border";
      case "pending":
        return "bg-secondary text-secondary-foreground border-border";
      case "training":
        return "bg-accent text-accent-foreground border-border";
      default:
        return "bg-muted text-muted-foreground border-border";
    }
  };

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        {/* KPI Skeletons */}
        <KPIGridSkeleton count={4} />

        {/* Recent Players Skeleton */}
        <Card className="bg-card border-border">
          <CardHeader>
            <Skeleton className="h-6 w-48" />
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Array.from({ length: 4 }).map((_, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-muted/30 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <Skeleton className="w-10 h-10 rounded-full" />
                    <div className="space-y-1">
                      <Skeleton className="h-4 w-32" />
                      <Skeleton className="h-3 w-24" />
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Skeleton className="h-6 w-16" />
                    <Skeleton className="h-6 w-12" />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Performance Overview Skeleton */}
        <Card className="bg-card border-border">
          <CardHeader>
            <Skeleton className="h-6 w-40" />
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="space-y-2">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-2 w-full" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-4 w-28" />
                <Skeleton className="h-2 w-full" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-2 w-full" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <StaggeredContainer className="p-6">
        {/* Match Analytics KPIs */}
        <FadeInUp>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Tooltip>
              <TooltipTrigger asChild>
                <Card className="bg-card border-border hover:bg-muted/50 transition-colors cursor-help">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="kpi-label">Processing</p>
                        <p className="kpi-value num">
                          <NumberTicker value={89} delay={200} />
                        </p>
                        <div className="flex items-center gap-1 mt-1">
                          <ArrowUp className="w-3 h-3 text-green-500" />
                          <p className="text-xs text-green-500">
                            +12% vs last week
                          </p>
                        </div>
                      </div>
                      <div className="p-3 bg-muted rounded-lg flex flex-col items-center gap-1">
                        <Loader className="w-5 h-5 text-muted-foreground animate-spin" />
                        <MiniTrendChart color="#10b981" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TooltipTrigger>
              <TooltipContent>
                <p>
                  Number of analyses currently being processed by our AI models
                </p>
              </TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Card className="bg-card border-border hover:bg-muted/50 transition-colors cursor-help">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="kpi-label">Waiting</p>
                        <p className="kpi-value num">
                          <NumberTicker value={23} delay={400} />
                        </p>
                        <div className="flex items-center gap-1 mt-1">
                          <ArrowDown className="w-3 h-3 text-red-500" />
                          <p className="text-xs text-red-500">
                            -3% vs last week
                          </p>
                        </div>
                      </div>
                      <div className="p-3 bg-muted rounded-lg flex flex-col items-center gap-1">
                        <Clock className="w-5 h-5 text-muted-foreground" />
                        <MiniTrendChart color="#ef4444" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TooltipTrigger>
              <TooltipContent>
                <p>Coaching requests queued and waiting for analysis</p>
              </TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Card className="bg-card border-border hover:bg-muted/50 transition-colors cursor-help">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="kpi-label">Completed (24h)</p>
                        <p className="kpi-value num">
                          <NumberTicker value={156} delay={600} />
                        </p>
                        <div className="flex items-center gap-1 mt-1">
                          <ArrowUp className="w-3 h-3 text-green-500" />
                          <p className="text-xs text-green-500">
                            +8% vs yesterday
                          </p>
                        </div>
                      </div>
                      <div className="p-3 bg-muted rounded-lg flex flex-col items-center gap-1">
                        <CheckCircle className="w-5 h-5 text-muted-foreground" />
                        <MiniTrendChart color="#3b82f6" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TooltipTrigger>
              <TooltipContent>
                <p>Coaching analyses completed in the last 24 hours</p>
              </TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Card className="bg-card border-border hover:bg-muted/50 transition-colors cursor-help">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="kpi-label">Success Rate</p>
                        <p className="kpi-value num">
                          <NumberTicker value={96} delay={800} />%
                        </p>
                        <div className="flex items-center gap-1 mt-1">
                          <ArrowUp className="w-3 h-3 text-green-500" />
                          <p className="text-xs text-green-500">
                            +2.1% improvement
                          </p>
                        </div>
                      </div>
                      <div className="p-3 bg-muted rounded-lg flex flex-col items-center gap-1">
                        <Percent className="w-5 h-5 text-muted-foreground" />
                        <MiniTrendChart color="#8b5cf6" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TooltipTrigger>
              <TooltipContent>
                <p>Percentage of coaching analyses completed successfully</p>
              </TooltipContent>
            </Tooltip>
          </div>
        </FadeInUp>

        {/* Main Dashboard Grid */}
        <FadeInUp delay={0.2}>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Recent Players */}
            <Card className="lg:col-span-2 bg-card border-border">
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg font-semibold text-foreground">
                    Recent Players
                  </CardTitle>
                  <Button variant="outline" size="sm">
                    View All
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {players.map((player) => (
                    <div
                      key={player.id}
                      className="flex items-center justify-between p-4 bg-muted/50 rounded-lg border border-border hover:bg-muted/80 transition-colors"
                    >
                      <div className="flex items-center gap-4">
                        <Avatar className="w-10 h-10">
                          <AvatarImage
                            src={`/avatars/${player.name.toLowerCase()}.png`}
                            alt={player.name}
                          />
                          <AvatarFallback className="bg-muted text-muted-foreground font-medium">
                            {player.id}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <p className="font-medium text-foreground">
                              {player.name}
                            </p>
                            <Badge
                              variant="outline"
                              className={getStatusColor(player.status)}
                            >
                              {player.status}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-2 mb-1">
                            <p className="text-sm text-muted-foreground">
                              {player.role} • KDA {player.kda}
                            </p>
                          </div>
                          <div className="flex items-center gap-1">
                            {player.badges.map((badge) => (
                              <Badge
                                key={badge}
                                variant="secondary"
                                className="text-xs px-1.5 py-0.5 bg-yellow-100 text-yellow-800 border-yellow-200"
                              >
                                {badge}
                              </Badge>
                            ))}
                            <span className="text-xs text-muted-foreground ml-2">
                              {player.lastActive}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="text-sm font-medium text-foreground">
                            {player.score}%
                          </p>
                          <Progress value={player.score} className="w-16 h-2" />
                        </div>
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="w-8 h-8"
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="w-8 h-8"
                          >
                            <Play className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="w-8 h-8"
                          >
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card className="bg-card border-border">
              <CardHeader className="pb-4">
                <CardTitle className="text-lg font-semibold text-foreground">
                  Quick Actions
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <Button className="w-full justify-start" variant="outline">
                    <Users className="w-4 h-4 mr-2" />
                    Add New Player
                  </Button>
                  <Button className="w-full justify-start" variant="outline">
                    <Activity className="w-4 h-4 mr-2" />
                    Start Analysis
                  </Button>
                  <Button className="w-full justify-start" variant="outline">
                    <TrendingUp className="w-4 h-4 mr-2" />
                    View Reports
                  </Button>
                  <Button className="w-full justify-start" variant="outline">
                    <Clock className="w-4 h-4 mr-2" />
                    Schedule Training
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Performance Overview */}
            <Card className="bg-card border-border">
              <CardHeader className="pb-4">
                <CardTitle className="text-lg font-semibold text-foreground">
                  Performance Overview
                </CardTitle>
              </CardHeader>
              <CardContent>
                <MultiProgressIndicator
                  skills={[
                    { label: "Skill Development", value: 85, color: "green" },
                    { label: "Team Coordination", value: 92, color: "blue" },
                    { label: "Strategic Thinking", value: 78, color: "purple" },
                  ]}
                  staggerDelay={0.3}
                />
              </CardContent>
            </Card>
          </div>
        </FadeInUp>
      </StaggeredContainer>
    </TooltipProvider>
  );
}
