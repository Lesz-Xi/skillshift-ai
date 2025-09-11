"use client";

import { motion } from "framer-motion";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

export function AnimatedProgress({
  value,
  max = 100,
  className,
  showValue = false,
  animationDelay = 0,
  color = "primary",
  size = "default",
}) {
  const percentage = Math.min((value / max) * 100, 100);

  const sizeClasses = {
    sm: "h-1",
    default: "h-2",
    lg: "h-3",
  };

  const colorClasses = {
    primary: "bg-primary",
    green: "bg-green-500",
    blue: "bg-blue-500",
    yellow: "bg-yellow-500",
    red: "bg-red-500",
    purple: "bg-purple-500",
  };

  return (
    <div className={cn("space-y-1", className)}>
      <div
        className={cn(
          "relative overflow-hidden rounded-full bg-muted",
          sizeClasses[size]
        )}
      >
        <motion.div
          className={cn("h-full rounded-full", colorClasses[color])}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{
            duration: 1.2,
            delay: animationDelay,
            ease: "easeOut",
          }}
        />
      </div>
      {showValue && (
        <motion.div
          className="flex justify-between text-xs text-muted-foreground"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: animationDelay + 0.5 }}
        >
          <span>Progress</span>
          <span className="num font-medium">{Math.round(percentage)}%</span>
        </motion.div>
      )}
    </div>
  );
}

export function SkillProgressBar({
  label,
  value,
  max = 100,
  color = "primary",
  delay = 0,
}) {
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium text-foreground num">{value}%</span>
      </div>
      <AnimatedProgress
        value={value}
        max={max}
        color={color}
        animationDelay={delay}
        size="default"
      />
    </div>
  );
}

export function MultiProgressIndicator({
  skills = [],
  className,
  staggerDelay = 0.2,
}) {
  return (
    <div className={cn("space-y-4", className)}>
      {skills.map((skill, index) => (
        <SkillProgressBar
          key={skill.label}
          label={skill.label}
          value={skill.value}
          color={skill.color || "primary"}
          delay={index * staggerDelay}
        />
      ))}
    </div>
  );
}
