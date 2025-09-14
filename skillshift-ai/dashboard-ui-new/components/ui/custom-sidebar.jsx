"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
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
  ChevronLeft,
  Sparkles,
  Shield,
  Users,
} from "lucide-react";
import { cn } from "@/lib/utils";
import ActiveUsersIndicator from "./active-users-indicator";
import UserAvatarMenu from "./user-avatar-menu";

const navigationGroups = [
  {
    label: "ANALYTICS",
    items: [
      {
        id: "overview",
        icon: BarChart3,
        label: "Profile",
        description: "Your stats and performance overview",
      },
      {
        id: "heroes",
        icon: Trophy,
        label: "Heroes",
        description: "Mastery and performance",
      },
      {
        id: "history",
        icon: History,
        label: "Analysis History",
        description: "Past coaching sessions",
      },
    ],
  },
  {
    label: "COACHING",
    items: [
      {
        id: "coaching",
        icon: Target,
        label: "Coaching Sessions",
        description: "Active coaching and training",
      },
      {
        id: "mindset",
        icon: Heart,
        label: "Mindset",
        description: "Mental performance tracking",
      },
    ],
  },
  {
    label: "ANALYSIS TOOLS",
    items: [
      {
        id: "screenshot-analysis",
        icon: Camera,
        label: "Screenshot",
        description: "Upload and analyze screenshots",
      },
      {
        id: "video-analysis",
        icon: Video,
        label: "Video",
        description: "Match replay analysis",
      },
    ],
  },
  {
    label: "SUPPORT",
    items: [
      {
        id: "admin",
        icon: Settings,
        label: "Settings",
        description: "Account settings and preferences",
      },
    ],
  },
];

export function CustomSidebar({
  activeSection,
  onSectionChange,
  onClose,
  className,
}) {
  const [expandedGroups, setExpandedGroups] = useState([
    "ANALYTICS",
    "COACHING",
    "ANALYSIS TOOLS",
    "SUPPORT",
  ]);
  const [expandedItems, setExpandedItems] = useState([]);

  const toggleGroup = (groupLabel) => {
    setExpandedGroups((prev) =>
      prev.includes(groupLabel)
        ? prev.filter((g) => g !== groupLabel)
        : [...prev, groupLabel]
    );
  };

  const toggleItem = (itemId) => {
    setExpandedItems((prev) =>
      prev.includes(itemId)
        ? prev.filter((id) => id !== itemId)
        : [...prev, itemId]
    );
  };

  return (
    <div
      className={cn(
        "w-72 bg-card border-r border-border h-full flex flex-col",
        className
      )}
      style={{
        scrollbarWidth: "none",
        scrollbarGutter: "auto",
      }}
    >
      {/* Header */}
      <div className="p-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-primary-foreground" />
          </div>
          <div>
            <h1 className="h4 font-display">SkillShift AI</h1>
            <p className="text-xs text-muted-foreground mono">v2.1.7</p>
          </div>
        </div>
      </div>

      {/* Navigation Content */}
      <div
        className="flex-1 overflow-y-auto p-3 [&::-webkit-scrollbar]:w-0 [&::-webkit-scrollbar]:h-0"
        style={{
          scrollbarWidth: "none",
          scrollbarGutter: "auto",
        }}
      >
        {navigationGroups.map((group) => (
          <div key={group.label} className="mb-2">
            {/* Group Header */}
            <button
              onClick={() => toggleGroup(group.label)}
              className="flex items-center justify-between w-full px-2 py-2 text-left hover:text-foreground transition-colors border-0"
            >
              <span className="table-header text-muted-foreground">
                {group.label}
              </span>
              <ChevronDown
                className={cn(
                  "w-4 h-4 transition-transform text-muted-foreground",
                  expandedGroups.includes(group.label) ? "rotate-180" : ""
                )}
              />
            </button>

            {/* Group Items */}
            <AnimatePresence>
              {expandedGroups.includes(group.label) && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden"
                >
                  <div className="ml-4 mt-1 space-y-0.5">
                    {group.items.map((item) => (
                      <div key={item.id}>
                        {/* Main Item */}
                        <button
                          onClick={() => onSectionChange(item.id)}
                          className={cn(
                            "flex items-center justify-between w-full px-3 py-2 rounded-md text-left min-h-[2.5rem] focus:outline-none focus:ring-0 border-r-0 border-t-0 border-b-0 outline-none ring-0 shadow-none",
                            activeSection === item.id
                              ? "bg-accent/60 text-accent-foreground border-l border-muted-foreground"
                              : "text-muted-foreground"
                          )}
                          style={{
                            borderRight: "none !important",
                            outline: "none !important",
                            boxShadow: "none !important",
                            borderTop: "none !important",
                            borderBottom: "none !important",
                            border: "none !important",
                            borderWidth: "0 !important",
                          }}
                        >
                          <div className="flex items-center gap-3 flex-1">
                            <item.icon className="w-4 h-4 flex-shrink-0" />
                            <div className="flex-1 min-w-0">
                              <div className="text-sm font-medium truncate">
                                {item.label}
                              </div>
                              <div className="text-xs text-muted-foreground leading-tight">
                                {item.description}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-1 flex-shrink-0">
                            {/* No sub-items, so no chevron needed */}
                          </div>
                        </button>

                        {/* No sub-items */}
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ))}
      </div>

      {/* Footer - User Avatar and Controls */}
      <div className="border-t border-border p-3">
        <div className="flex items-center justify-between">
          <UserAvatarMenu />
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="h-8 w-8 p-0 text-muted-foreground hover:text-foreground"
          >
            <ChevronLeft className="w-4 h-4" />
            <ChevronLeft className="w-4 h-4 -ml-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
