"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  BarChart3,
  Trophy,
  Target,
  Heart,
  History,
  Camera,
  Video,
  Settings,
  Menu,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigationGroups = [
  {
    label: "Analytics",
    items: [
      { id: "overview", icon: BarChart3, label: "Overview", badge: "Live" },
      { id: "heroes", icon: Trophy, label: "Heroes", badge: "47" },
      { id: "history", icon: History, label: "Analysis History" },
    ],
  },
  {
    label: "Coaching",
    items: [
      { id: "coaching", icon: Target, label: "Pipeline", badge: "3" },
      { id: "mindset", icon: Heart, label: "Mindset", badge: "New" },
    ],
  },
  {
    label: "Tools",
    items: [
      { id: "screenshot-analysis", icon: Camera, label: "Screenshot" },
      { id: "video-analysis", icon: Video, label: "Video" },
      { id: "admin", icon: Settings, label: "System Status" },
    ],
  },
];

export function MobileNav({ activeSection, onSectionChange }) {
  const [isOpen, setIsOpen] = useState(false);

  const handleNavigation = (sectionId) => {
    onSectionChange(sectionId);
    setIsOpen(false);
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
    <div className="md:hidden">
      <Sheet open={isOpen} onOpenChange={setIsOpen}>
        <SheetTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="text-muted-foreground hover:text-foreground hover:bg-accent"
          >
            <Menu className="w-5 h-5" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="w-80 p-0">
          <SheetHeader className="border-b border-border p-6">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-primary-foreground" />
              </div>
              <div>
                <SheetTitle className="h4 font-display text-left">
                  SkillShift AI
                </SheetTitle>
                <SheetDescription className="text-xs mono text-left">
                  v2.1.7
                </SheetDescription>
              </div>
            </div>
          </SheetHeader>

          <div className="flex-1 overflow-auto p-4">
            {navigationGroups.map((group, groupIndex) => (
              <motion.div
                key={group.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: groupIndex * 0.1 }}
                className="mb-6"
              >
                <h3 className="table-header mb-3 px-2">{group.label}</h3>
                <div className="space-y-1">
                  {group.items.map((item, itemIndex) => {
                    const Icon = item.icon;
                    const isActive = activeSection === item.id;

                    return (
                      <motion.button
                        key={item.id}
                        onClick={() => handleNavigation(item.id)}
                        className={cn(
                          "w-full flex items-center gap-3 p-3 rounded-lg transition-all duration-200 text-left",
                          isActive
                            ? "bg-primary text-primary-foreground shadow-sm"
                            : "text-muted-foreground hover:text-foreground hover:bg-accent"
                        )}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{
                          delay: groupIndex * 0.1 + itemIndex * 0.05,
                        }}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                      >
                        <Icon className="w-5 h-5 flex-shrink-0" />
                        <span className="flex-1 text-sm font-medium">
                          {item.label}
                        </span>
                        {item.badge && (
                          <Badge
                            variant="outline"
                            className={`text-xs ${getBadgeVariant(item.badge)}`}
                          >
                            {item.badge}
                          </Badge>
                        )}
                      </motion.button>
                    );
                  })}
                </div>
              </motion.div>
            ))}
          </div>

          {/* Mobile Footer */}
          <div className="border-t border-border p-4">
            <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <div className="flex-1">
                <div className="text-sm font-medium text-foreground">
                  All Systems Online
                </div>
                <div className="text-xs text-muted-foreground">
                  89 analyses running
                </div>
              </div>
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
}
