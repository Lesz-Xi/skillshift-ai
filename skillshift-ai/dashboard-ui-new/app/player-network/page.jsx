"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { HeroCard3D } from "@/components/ui/card-3d";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { toast } from "sonner";
import { DataTable } from "@/components/ui/data-table";
import { heroColumns } from "@/components/ui/hero-columns";
import { FadeInUp, StaggeredContainer } from "@/components/ui/page-transitions";
import { InteractiveCard } from "@/components/ui/interactive-card";
import {
  Users,
  Search,
  Filter,
  UserPlus,
  Shield,
  AlertTriangle,
  CheckCircle,
  Clock,
  MoreHorizontal,
  Eye,
  Settings,
  Trophy,
} from "lucide-react";

export default function HeroMasteryPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedFilter, setSelectedFilter] = useState("all");

  const heroes = [
    {
      id: "H-001",
      name: "Ling",
      role: "Assassin",
      masteryScore: 87,
      matches: 47,
      winRate: 68,
      metaTier: "S",
      lastPlayed: "2 hours ago",
      performance: "high",
    },
    {
      id: "H-002",
      name: "Chang'e",
      role: "Mage",
      masteryScore: 72,
      matches: 32,
      winRate: 59,
      metaTier: "A",
      lastPlayed: "1 day ago",
      performance: "medium",
    },
    {
      id: "H-003",
      name: "Chou",
      role: "Fighter",
      masteryScore: 91,
      matches: 63,
      winRate: 74,
      metaTier: "S",
      lastPlayed: "5 hours ago",
      performance: "high",
    },
    {
      id: "H-004",
      name: "Granger",
      role: "Marksman",
      masteryScore: 45,
      matches: 28,
      winRate: 43,
      metaTier: "B",
      lastPlayed: "3 days ago",
      performance: "critical",
    },
    {
      id: "H-005",
      name: "Kagura",
      role: "Mage",
      masteryScore: 66,
      matches: 41,
      winRate: 61,
      metaTier: "A",
      lastPlayed: "1 day ago",
      performance: "medium",
    },
    {
      id: "H-006",
      name: "Tigreal",
      role: "Tank",
      masteryScore: 38,
      matches: 12,
      winRate: 42,
      metaTier: "C",
      lastPlayed: "1 week ago",
      performance: "low",
    },
    {
      id: "H-007",
      name: "Gusion",
      role: "Assassin",
      masteryScore: 89,
      matches: 55,
      winRate: 76,
      metaTier: "S",
      lastPlayed: "4 hours ago",
      performance: "high",
    },
    {
      id: "P-008",
      username: "LIGHT_BEARER",
      status: "pending",
      gameMode: "Classic",
      role: "Support",
      rank: "Legend III",
      matches: 38,
      performance: "medium",
    },
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case "analyzed":
        return "bg-muted text-muted-foreground";
      case "pending":
        return "bg-secondary text-secondary-foreground";
      case "training":
        return "bg-accent text-accent-foreground";
      case "flagged":
        return "bg-muted text-muted-foreground";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  const getPerformanceColor = (performance) => {
    switch (performance) {
      case "high":
        return "bg-primary text-primary-foreground";
      case "medium":
        return "bg-muted text-muted-foreground";
      case "low":
        return "bg-secondary text-secondary-foreground";
      case "critical":
        return "bg-muted text-muted-foreground";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  // Filter heroes based on search term and selected filter
  const filteredHeroes = heroes.filter((hero) => {
    const matchesSearch =
      (hero.name || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (hero.role || "").toLowerCase().includes(searchTerm.toLowerCase());

    const matchesFilter =
      selectedFilter === "all" ||
      (hero.role || "").toLowerCase() === selectedFilter.toLowerCase() ||
      (selectedFilter === "high-mastery" && (hero.masteryScore || 0) >= 80);

    return matchesSearch && matchesFilter;
  });

  const getMetaTierColor = (tier) => {
    switch (tier) {
      case "S":
        return "bg-red-100 text-red-800 border-red-200";
      case "A":
        return "bg-orange-100 text-orange-800 border-orange-200";
      case "B":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "C":
        return "bg-gray-100 text-gray-800 border-gray-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "analyzed":
        return <CheckCircle className="w-4 h-4" />;
      case "pending":
        return <Clock className="w-4 h-4" />;
      case "training":
        return <Users className="w-4 h-4" />;
      case "flagged":
        return <AlertTriangle className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  return (
    <TooltipProvider>
      <StaggeredContainer className="p-6">
        {/* Header */}
        <FadeInUp>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-foreground">
                Hero Mastery
              </h1>
              <p className="text-muted-foreground">
                Track hero performance, mastery levels, and MLBB meta compliance
              </p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline">
                <UserPlus className="w-4 h-4 mr-2" />
                Analyze Hero
              </Button>
              <Button variant="outline">
                <Filter className="w-4 h-4 mr-2" />
                Filter by Role
              </Button>
            </div>
          </div>
        </FadeInUp>

        {/* Search and Stats */}
        <FadeInUp delay={0.1}>
          <div className="flex flex-col lg:flex-row gap-6">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                <Input
                  placeholder="Search heroes..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4 lg:w-auto">
              <Card className="bg-card border-border">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">
                        Heroes Mastered
                      </p>
                      <p className="text-2xl font-bold text-foreground">23</p>
                    </div>
                    <div className="p-2 bg-muted rounded-lg">
                      <Shield className="w-5 h-5 text-muted-foreground" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-card border-border">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">
                        Meta Tier S/A
                      </p>
                      <p className="text-2xl font-bold text-foreground">12</p>
                    </div>
                    <div className="p-2 bg-muted rounded-lg">
                      <AlertTriangle className="w-5 h-5 text-muted-foreground" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-card border-border">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">
                        Pool Depth
                      </p>
                      <p className="text-2xl font-bold text-foreground">8</p>
                    </div>
                    <div className="p-2 bg-muted rounded-lg">
                      <Users className="w-5 h-5 text-muted-foreground" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </FadeInUp>

        {/* Top Heroes Showcase */}
        <FadeInUp delay={0.2}>
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-foreground">
                <Trophy className="w-5 h-5" />
                Top Mastery Heroes
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {heroes.slice(0, 4).map((hero) => (
                  <HeroCard3D
                    key={hero.id}
                    hero={hero}
                    onClick={() =>
                      toast.info(`Viewing ${hero.name} detailed analysis`)
                    }
                  />
                ))}
              </div>
            </CardContent>
          </Card>
        </FadeInUp>

        {/* Hero Mastery Table */}
        <FadeInUp delay={0.3}>
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-foreground">
                Hero Mastery Analysis
              </CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={heroColumns}
                data={filteredHeroes}
                searchKey="name"
                searchPlaceholder="Search heroes by name..."
                pageSize={10}
              />
            </CardContent>
          </Card>
        </FadeInUp>
      </StaggeredContainer>
    </TooltipProvider>
  );
}
