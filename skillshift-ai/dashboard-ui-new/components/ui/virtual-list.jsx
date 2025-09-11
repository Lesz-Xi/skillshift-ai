"use client";

import { useVirtualizer } from "@tanstack/react-virtual";
import { useRef, useMemo } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Camera, Video, Eye, Download } from "lucide-react";

export function VirtualList({
  items,
  renderItem,
  estimateSize = 80,
  className,
  containerHeight = 400,
  gap = 0,
}) {
  const parentRef = useRef();

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => estimateSize,
    gap,
  });

  const virtualItems = virtualizer.getVirtualItems();

  return (
    <div
      ref={parentRef}
      className={cn("overflow-auto border border-border rounded-md", className)}
      style={{
        height: `${containerHeight}px`,
      }}
    >
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: "100%",
          position: "relative",
        }}
      >
        {virtualItems.map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: `${virtualItem.size}px`,
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            {renderItem(items[virtualItem.index], virtualItem.index)}
          </div>
        ))}
      </div>
    </div>
  );
}

export function VirtualAnalysisHistoryList({ analyses, onSelectAnalysis }) {
  const renderAnalysisItem = (analysis, index) => (
    <div
      className="flex items-center justify-between p-4 bg-muted/30 hover:bg-muted/50 transition-colors cursor-pointer border-b border-border last:border-b-0"
      onClick={() => onSelectAnalysis(analysis)}
    >
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 bg-muted rounded-lg flex items-center justify-center">
          {analysis.type === "screenshot" ? (
            <Camera className="w-5 h-5 text-muted-foreground" />
          ) : (
            <Video className="w-5 h-5 text-muted-foreground" />
          )}
        </div>
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-medium text-foreground">{analysis.title}</h3>
            <Badge
              variant="outline"
              className={`text-xs ${
                analysis.status === "completed"
                  ? "bg-green-100 text-green-800 border-green-200"
                  : analysis.status === "processing"
                  ? "bg-blue-100 text-blue-800 border-blue-200"
                  : "bg-red-100 text-red-800 border-red-200"
              }`}
            >
              {analysis.status}
            </Badge>
          </div>
          <div className="flex items-center gap-3 text-sm text-muted-foreground mb-2">
            <span>
              {analysis.hero} • {analysis.role}
            </span>
            <span className="num">KDA {analysis.kda}</span>
            <span
              className={
                analysis.matchResult === "Victory"
                  ? "text-green-600"
                  : "text-red-600"
              }
            >
              {analysis.matchResult}
            </span>
          </div>
          <div className="flex items-center gap-1">
            {(analysis.badges || []).map((badge) => (
              <Badge
                key={badge}
                variant="secondary"
                className="text-xs px-1.5 py-0.5 bg-yellow-100 text-yellow-800 border-yellow-200"
              >
                {badge}
              </Badge>
            ))}
            <span className="text-xs text-muted-foreground ml-2 mono-small">
              {new Date(analysis.timestamp).toLocaleDateString()} •{" "}
              {new Date(analysis.timestamp).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>
          </div>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <div className="text-right">
          <p
            className={`text-sm font-medium num ${
              (analysis.feedback?.score || 0) >= 80
                ? "text-green-600"
                : (analysis.feedback?.score || 0) >= 60
                ? "text-yellow-600"
                : "text-red-600"
            }`}
          >
            {analysis.feedback?.score || 0}%
          </p>
          <p className="text-xs text-muted-foreground num">
            {analysis.confidence}% confidence
          </p>
        </div>
        <div className="flex gap-1">
          <Button variant="ghost" size="icon" className="w-8 h-8">
            <Eye className="w-4 h-4" />
          </Button>
          <Button variant="ghost" size="icon" className="w-8 h-8">
            <Download className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );

  return (
    <VirtualList
      items={analyses}
      renderItem={renderAnalysisItem}
      estimateSize={120}
      containerHeight={600}
      gap={0}
    />
  );
}
