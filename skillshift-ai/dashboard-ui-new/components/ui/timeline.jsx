"use client";

import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  CheckCircle,
  Clock,
  Play,
  XCircle,
  AlertTriangle,
  Eye,
  MoreHorizontal,
} from "lucide-react";
import { cn } from "@/lib/utils";

const getStatusIcon = (status) => {
  switch (status) {
    case "completed":
      return <CheckCircle className="w-4 h-4 text-green-500" />;
    case "analyzing":
      return <Play className="w-4 h-4 text-blue-500" />;
    case "queued":
      return <Clock className="w-4 h-4 text-yellow-500" />;
    case "failed":
      return <XCircle className="w-4 h-4 text-red-500" />;
    default:
      return <Clock className="w-4 h-4 text-gray-500" />;
  }
};

const getStatusColor = (status) => {
  switch (status) {
    case "completed":
      return "border-green-500 bg-green-50";
    case "analyzing":
      return "border-blue-500 bg-blue-50";
    case "queued":
      return "border-yellow-500 bg-yellow-50";
    case "failed":
      return "border-red-500 bg-red-50";
    default:
      return "border-gray-500 bg-gray-50";
  }
};

export function TimelineItem({
  item,
  index,
  isLast = false,
  onClick,
  className,
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className={cn("relative", className)}
    >
      {/* Timeline Line */}
      {!isLast && (
        <div className="absolute left-6 top-12 w-0.5 h-full bg-border" />
      )}

      {/* Timeline Node */}
      <div className="flex items-start gap-4">
        <motion.div
          className={cn(
            "w-12 h-12 rounded-full border-2 flex items-center justify-center",
            getStatusColor(item.status)
          )}
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: index * 0.1 + 0.2 }}
          whileHover={{ scale: 1.1 }}
        >
          {getStatusIcon(item.status)}
        </motion.div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <motion.div
            className="bg-card border border-border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => onClick?.(item)}
            whileHover={{ y: -2 }}
            transition={{ type: "spring", stiffness: 300, damping: 20 }}
          >
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-medium text-foreground">{item.title}</h3>
              <Badge
                variant="outline"
                className={cn(
                  "text-xs",
                  item.status === "completed" &&
                    "bg-green-100 text-green-800 border-green-200",
                  item.status === "analyzing" &&
                    "bg-blue-100 text-blue-800 border-blue-200",
                  item.status === "queued" &&
                    "bg-yellow-100 text-yellow-800 border-yellow-200",
                  item.status === "failed" &&
                    "bg-red-100 text-red-800 border-red-200"
                )}
              >
                {item.status}
              </Badge>
            </div>

            <p className="text-sm text-muted-foreground mb-3">
              {item.description}
            </p>

            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <div className="flex items-center gap-4">
                <span>
                  {item.hero} • {item.role}
                </span>
                <span className="mono-small">{item.submittedAt}</span>
              </div>

              <div className="flex items-center gap-2">
                {item.progress !== undefined && (
                  <div className="flex items-center gap-1">
                    <div className="w-16 h-1 bg-muted rounded-full overflow-hidden">
                      <motion.div
                        className="h-full bg-primary"
                        initial={{ width: 0 }}
                        animate={{ width: `${item.progress}%` }}
                        transition={{ duration: 1, delay: index * 0.1 + 0.5 }}
                      />
                    </div>
                    <span className="num">{item.progress}%</span>
                  </div>
                )}

                <Button variant="ghost" size="icon" className="w-6 h-6">
                  <Eye className="w-3 h-3" />
                </Button>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
}

export function Timeline({ items, onItemClick, className }) {
  return (
    <div className={cn("space-y-6", className)}>
      {items.map((item, index) => (
        <TimelineItem
          key={item.id}
          item={item}
          index={index}
          isLast={index === items.length - 1}
          onClick={onItemClick}
        />
      ))}
    </div>
  );
}

export function CoachingTimeline({ requests, onRequestClick }) {
  // Sort requests by status priority and submission time
  const sortedRequests = [...requests].sort((a, b) => {
    const statusPriority = {
      analyzing: 0,
      queued: 1,
      completed: 2,
      failed: 3,
    };

    const aPriority = statusPriority[a.status] ?? 999;
    const bPriority = statusPriority[b.status] ?? 999;

    if (aPriority !== bPriority) {
      return aPriority - bPriority;
    }

    return new Date(b.submittedAt) - new Date(a.submittedAt);
  });

  return (
    <Timeline
      items={sortedRequests}
      onItemClick={onRequestClick}
      className="max-h-[600px] overflow-y-auto pr-2"
    />
  );
}
