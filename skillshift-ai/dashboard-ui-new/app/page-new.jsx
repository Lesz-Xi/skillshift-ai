"use client";

import { useState } from "react";
import {
  ChevronRight,
  Monitor,
  Settings,
  Target,
  Users,
  Bell,
  RefreshCw,
  Camera,
  Brain,
  Video,
  Menu,
  X,
  Trophy,
  Heart,
  BarChart3,
  History,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import ClientOnly from "@/components/ClientOnly";
import { CommandPalette } from "@/components/ui/command-palette";
import { toast } from "sonner";
import { ModernDashboardLayout } from "@/components/ui/modern-dashboard-layout";
import PlayerHubPage from "./player-hub/page";
import PlayerNetworkPage from "./player-network/page";
import ScreenshotAnalysisPage from "./screenshot-analysis/page";
import AnalysisOpsPage from "./analysis-ops/page";
import PlayerInsightsPage from "./player-insights/page";
import AiCoachStatusPage from "./ai-coach-status/page";
import VideoAnalysisPage from "./video-analysis/page";
import AnalysisHistoryPage from "./analysis-history/page";

export default function TacticalDashboard() {
  const [activeSection, setActiveSection] = useState("overview");

  const navigationItems = [
    { id: "overview", icon: BarChart3, label: "Overview" },
    { id: "heroes", icon: Trophy, label: "Heroes" },
    { id: "coaching", icon: Target, label: "Coaching" },
    { id: "mindset", icon: Heart, label: "Mindset" },
    { id: "history", icon: History, label: "Analysis History" },
    { id: "screenshot-analysis", icon: Camera, label: "Screenshot Analysis" },
    { id: "video-analysis", icon: Video, label: "Video Analysis" },
    { id: "admin", icon: Settings, label: "System Status" },
  ];

  const renderActiveSection = () => {
    switch (activeSection) {
      case "overview":
        return <PlayerHubPage />;
      case "heroes":
        return <PlayerNetworkPage />;
      case "coaching":
        return <AnalysisOpsPage />;
      case "mindset":
        return <PlayerInsightsPage />;
      case "history":
        return <AnalysisHistoryPage />;
      case "screenshot-analysis":
        return <ScreenshotAnalysisPage />;
      case "video-analysis":
        return <VideoAnalysisPage />;
      case "admin":
        return <AiCoachStatusPage />;
      default:
        return <PlayerHubPage />;
    }
  };

  return (
    <ModernDashboardLayout
      activeSection={activeSection}
      onSectionChange={setActiveSection}
      navigationItems={navigationItems}
    >
      {renderActiveSection()}
    </ModernDashboardLayout>
  );
}
