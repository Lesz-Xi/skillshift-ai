"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Plus, Upload, Camera, Video, Target } from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

export function FloatingActionButton({ activeSection, onNavigate, className }) {
  const getActionsBySection = (section) => {
    switch (section) {
      case "overview":
        return [
          {
            icon: Upload,
            label: "Upload Analysis",
            action: () => onNavigate("screenshot-analysis"),
            color: "bg-blue-500 hover:bg-blue-600",
          },
          {
            icon: Target,
            label: "Request Coaching",
            action: () => onNavigate("coaching"),
            color: "bg-green-500 hover:bg-green-600",
          },
        ];
      case "heroes":
        return [
          {
            icon: Camera,
            label: "Analyze Screenshot",
            action: () => onNavigate("screenshot-analysis"),
            color: "bg-purple-500 hover:bg-purple-600",
          },
          {
            icon: Video,
            label: "Analyze Video",
            action: () => onNavigate("video-analysis"),
            color: "bg-orange-500 hover:bg-orange-600",
          },
        ];
      case "history":
        return [
          {
            icon: Upload,
            label: "New Analysis",
            action: () => onNavigate("screenshot-analysis"),
            color: "bg-indigo-500 hover:bg-indigo-600",
          },
        ];
      default:
        return [
          {
            icon: Plus,
            label: "Quick Action",
            action: () => toast.info("Quick action menu"),
            color: "bg-primary hover:bg-primary/90",
          },
        ];
    }
  };

  const actions = getActionsBySection(activeSection);

  if (actions.length === 0) return null;

  return (
    <TooltipProvider>
      <div className={cn("fixed bottom-6 right-6 z-50", className)}>
        <div className="flex flex-col gap-3">
          {actions.map((action, index) => (
            <Tooltip key={index}>
              <TooltipTrigger asChild>
                <motion.div
                  initial={{ opacity: 0, scale: 0, y: 20 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  transition={{
                    delay: index * 0.1,
                    type: "spring",
                    stiffness: 260,
                    damping: 20,
                  }}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                >
                  <Button
                    size="icon"
                    onClick={action.action}
                    className={cn(
                      "w-12 h-12 rounded-full shadow-lg border-0",
                      action.color
                    )}
                  >
                    <action.icon className="w-5 h-5 text-white" />
                  </Button>
                </motion.div>
              </TooltipTrigger>
              <TooltipContent side="left">
                <p>{action.label}</p>
              </TooltipContent>
            </Tooltip>
          ))}
        </div>
      </div>
    </TooltipProvider>
  );
}
