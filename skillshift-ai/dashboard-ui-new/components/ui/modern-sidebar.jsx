"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  BarChart3,
  Trophy,
  Target,
  Heart,
  History,
  Camera,
  Video,
  Settings,
  ChevronDown,
  Sparkles,
  TrendingUp,
  Users,
  Brain,
  Shield,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigationGroups = [
  {
    label: "Analytics",
    items: [
      {
        id: "overview",
        icon: BarChart3,
        label: "Overview",
        description: "Match analytics and KPIs",
        badge: "Live",
      },
      {
        id: "heroes",
        icon: Trophy,
        label: "Heroes",
        description: "Mastery and performance",
        badge: "47",
      },
      {
        id: "history",
        icon: History,
        label: "Analysis History",
        description: "Past coaching sessions",
        badge: null,
      },
    ],
  },
  {
    label: "Coaching",
    items: [
      {
        id: "coaching",
        icon: Target,
        label: "Pipeline",
        description: "Active coaching requests",
        badge: "3",
      },
      {
        id: "mindset",
        icon: Heart,
        label: "Mindset",
        description: "Mental performance tracking",
        badge: "New",
      },
    ],
  },
  {
    label: "Analysis Tools",
    items: [
      {
        id: "screenshot-analysis",
        icon: Camera,
        label: "Screenshot",
        description: "Upload and analyze screenshots",
        subItems: [
          { id: "screenshot-upload", label: "Upload New", icon: Camera },
          { id: "screenshot-batch", label: "Batch Analysis", icon: Users },
        ],
      },
      {
        id: "video-analysis",
        icon: Video,
        label: "Video",
        description: "Match replay analysis",
        subItems: [
          { id: "video-upload", label: "Upload Replay", icon: Video },
          { id: "video-library", label: "Match Library", icon: History },
        ],
      },
    ],
  },
];

export function ModernSidebar({ activeSection, onSectionChange, className }) {
  const [expandedGroups, setExpandedGroups] = useState([
    "Analytics",
    "Coaching",
  ]);

  const toggleGroup = (groupLabel) => {
    setExpandedGroups((prev) =>
      prev.includes(groupLabel)
        ? prev.filter((g) => g !== groupLabel)
        : [...prev, groupLabel]
    );
  };

  const getBadgeVariant = (badge) => {
    switch (badge) {
      case "Live":
        return "bg-green-100 text-green-800 border-green-200";
      case "New":
        return "bg-blue-100 text-blue-800 border-blue-200";
      default:
        return "bg-muted text-muted-foreground border-border";
    }
  };

  return (
    <Sidebar className={cn("border-r border-border", className)}>
      <SidebarHeader className="border-b border-border p-6">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-primary-foreground" />
          </div>
          <div>
            <h1 className="h4 font-display">SkillShift AI</h1>
            <p className="text-xs text-muted-foreground mono">v2.1.7</p>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        {navigationGroups.map((group) => (
          <SidebarGroup key={group.label}>
            <Collapsible
              open={expandedGroups.includes(group.label)}
              onOpenChange={() => toggleGroup(group.label)}
            >
              <CollapsibleTrigger asChild>
                <SidebarGroupLabel className="flex items-center justify-between cursor-pointer hover:text-foreground transition-colors px-4 py-2">
                  <span className="table-header">{group.label}</span>
                  <ChevronDown
                    className={cn(
                      "w-4 h-4 transition-transform",
                      expandedGroups.includes(group.label) ? "rotate-180" : ""
                    )}
                  />
                </SidebarGroupLabel>
              </CollapsibleTrigger>

              <CollapsibleContent>
                <SidebarGroupContent className="pl-6 ml-2">
                  <SidebarMenu className="space-y-1">
                    {group.items.map((item) => (
                      <SidebarMenuItem key={item.id}>
                        {item.subItems ? (
                          <Collapsible>
                            <CollapsibleTrigger asChild>
                              <SidebarMenuButton
                                className={cn(
                                  "w-full justify-between py-3",
                                  activeSection === item.id &&
                                    "bg-accent text-accent-foreground"
                                )}
                              >
                                <div className="flex items-center gap-3">
                                  <item.icon className="w-4 h-4" />
                                  <div className="flex-1 text-left">
                                    <div className="font-medium">
                                      {item.label}
                                    </div>
                                    <div className="text-xs text-muted-foreground">
                                      {item.description}
                                    </div>
                                  </div>
                                </div>
                                <ChevronDown className="w-4 h-4" />
                              </SidebarMenuButton>
                            </CollapsibleTrigger>
                            <CollapsibleContent>
                              <SidebarMenuSub>
                                {item.subItems.map((subItem) => (
                                  <SidebarMenuSubItem key={subItem.id}>
                                    <SidebarMenuSubButton
                                      onClick={() => onSectionChange(item.id)}
                                      className={cn(
                                        "py-2 pl-4",
                                        activeSection === item.id &&
                                          "bg-accent text-accent-foreground"
                                      )}
                                    >
                                      <subItem.icon className="w-4 h-4" />
                                      <span>{subItem.label}</span>
                                    </SidebarMenuSubButton>
                                  </SidebarMenuSubItem>
                                ))}
                              </SidebarMenuSub>
                            </CollapsibleContent>
                          </Collapsible>
                        ) : (
                          <SidebarMenuButton
                            onClick={() => onSectionChange(item.id)}
                            className={cn(
                              "w-full justify-start py-3",
                              activeSection === item.id &&
                                "bg-accent text-accent-foreground"
                            )}
                          >
                            <div className="flex items-center gap-3 flex-1">
                              <item.icon className="w-4 h-4" />
                              <div className="flex-1">
                                <div className="font-medium">{item.label}</div>
                                <div className="text-xs text-muted-foreground">
                                  {item.description}
                                </div>
                              </div>
                              {item.badge && (
                                <Badge
                                  variant="outline"
                                  className={`text-xs ${getBadgeVariant(
                                    item.badge
                                  )}`}
                                >
                                  {item.badge}
                                </Badge>
                              )}
                            </div>
                          </SidebarMenuButton>
                        )}
                      </SidebarMenuItem>
                    ))}
                  </SidebarMenu>
                </SidebarGroupContent>
              </CollapsibleContent>
            </Collapsible>
          </SidebarGroup>
        ))}
      </SidebarContent>

      <SidebarFooter className="border-t border-border p-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-muted rounded-full flex items-center justify-center">
            <Shield className="w-4 h-4 text-muted-foreground" />
          </div>
          <div className="flex-1">
            <div className="text-sm font-medium text-foreground">
              System Status
            </div>
            <div className="text-xs text-muted-foreground">
              All systems operational
            </div>
          </div>
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
