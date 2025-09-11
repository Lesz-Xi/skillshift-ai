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
  Sparkles,
  Shield,
  Users,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigationGroups = [
  {
    label: "ANALYTICS",
    items: [
      {
        id: "overview",
        icon: BarChart3,
        label: "Overview",
        description: "Match analytics and KPIs",
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
        label: "Pipeline",
        description: "Active coaching requests",
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

export function CustomSidebar({ activeSection, onSectionChange, className }) {
  const [expandedGroups, setExpandedGroups] = useState([
    "ANALYTICS",
    "COACHING",
    "ANALYSIS TOOLS",
  ]);
  const [expandedItems, setExpandedItems] = useState([
    "screenshot-analysis",
    "video-analysis",
  ]);

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
    >
      {/* Header */}
      <div className="border-b border-border p-4">
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
      <div className="flex-1 overflow-y-auto p-3">
        {navigationGroups.map((group) => (
          <div key={group.label} className="mb-4">
            {/* Group Header */}
            <button
              onClick={() => toggleGroup(group.label)}
              className="flex items-center justify-between w-full px-2 py-2 text-left hover:text-foreground transition-colors"
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
                          onClick={() => {
                            if (item.subItems) {
                              toggleItem(item.id);
                            } else {
                              onSectionChange(item.id);
                            }
                          }}
                          className={cn(
                            "flex items-center justify-between w-full px-3 py-2 rounded-md text-left transition-all duration-200 min-h-[2.5rem]",
                            activeSection === item.id
                              ? "bg-accent/60 text-accent-foreground border-l-2 border-primary"
                              : "text-muted-foreground hover:text-foreground hover:bg-accent/30"
                          )}
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
                            {item.subItems && (
                              <ChevronDown
                                className={cn(
                                  "w-4 h-4 transition-transform",
                                  expandedItems.includes(item.id)
                                    ? "rotate-180"
                                    : ""
                                )}
                              />
                            )}
                          </div>
                        </button>

                        {/* Sub Items */}
                        {item.subItems && (
                          <AnimatePresence>
                            {expandedItems.includes(item.id) && (
                              <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: "auto" }}
                                exit={{ opacity: 0, height: 0 }}
                                transition={{ duration: 0.2 }}
                                className="overflow-hidden ml-4 mt-0.5"
                              >
                                <div className="space-y-1">
                                  {item.subItems.map((subItem) => (
                                    <button
                                      key={subItem.id}
                                      onClick={() => onSectionChange(item.id)}
                                      className={cn(
                                        "flex items-center gap-2 w-full px-2 py-1.5 rounded-sm text-left transition-all duration-200 text-sm",
                                        activeSection === item.id
                                          ? "bg-accent/40 text-accent-foreground border-l border-primary"
                                          : "text-muted-foreground hover:text-foreground hover:bg-accent/20"
                                      )}
                                    >
                                      <subItem.icon className="w-3 h-3 flex-shrink-0" />
                                      <span className="truncate">
                                        {subItem.label}
                                      </span>
                                    </button>
                                  ))}
                                </div>
                              </motion.div>
                            )}
                          </AnimatePresence>
                        )}
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="border-t border-border p-3">
        <div className="flex items-center gap-2 p-2 bg-muted rounded-md">
          <div className="w-6 h-6 bg-muted rounded-full flex items-center justify-center">
            <Shield className="w-3 h-3 text-muted-foreground" />
          </div>
          <div className="flex-1">
            <div className="text-xs font-medium text-foreground">
              System Status
            </div>
            <div className="text-xs text-muted-foreground">All operational</div>
          </div>
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
        </div>
      </div>
    </div>
  );
}
