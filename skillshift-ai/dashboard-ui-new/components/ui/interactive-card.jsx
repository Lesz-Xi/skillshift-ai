"use client";

import { motion } from "framer-motion";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function InteractiveCard({
  children,
  className,
  onClick,
  hoverScale = 1.02,
  tapScale = 0.98,
  ...props
}) {
  return (
    <motion.div
      whileHover={{
        scale: hoverScale,
        y: -4,
      }}
      whileTap={{ scale: tapScale }}
      transition={{
        type: "spring",
        stiffness: 300,
        damping: 20,
      }}
      className="cursor-pointer"
      onClick={onClick}
    >
      <Card
        className={cn(
          "transition-shadow duration-200 hover:shadow-lg border-border",
          className
        )}
        {...props}
      >
        {children}
      </Card>
    </motion.div>
  );
}

export function PulseCard({ children, className, ...props }) {
  return (
    <motion.div
      animate={{
        scale: [1, 1.01, 1],
      }}
      transition={{
        duration: 2,
        repeat: Infinity,
        ease: "easeInOut",
      }}
    >
      <Card className={cn("border-border", className)} {...props}>
        {children}
      </Card>
    </motion.div>
  );
}

export function GlowCard({
  children,
  className,
  glowColor = "blue",
  intensity = "medium",
  ...props
}) {
  const glowIntensity = {
    low: "drop-shadow-sm",
    medium: "drop-shadow-md",
    high: "drop-shadow-lg",
  };

  const glowColors = {
    blue: "shadow-blue-500/25",
    green: "shadow-green-500/25",
    purple: "shadow-purple-500/25",
    red: "shadow-red-500/25",
    yellow: "shadow-yellow-500/25",
  };

  return (
    <motion.div
      whileHover={{
        filter: "brightness(1.05)",
      }}
      transition={{ duration: 0.2 }}
    >
      <Card
        className={cn(
          "border-border transition-all duration-300",
          "hover:shadow-lg",
          glowColors[glowColor],
          glowIntensity[intensity],
          className
        )}
        {...props}
      >
        {children}
      </Card>
    </motion.div>
  );
}
