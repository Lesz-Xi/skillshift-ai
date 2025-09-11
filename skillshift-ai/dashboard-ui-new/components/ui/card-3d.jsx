"use client";

import { motion } from "framer-motion";
import { useState } from "react";
import { cn } from "@/lib/utils";

export function Card3D({ children, className, containerClassName, ...props }) {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isHovering, setIsHovering] = useState(false);

  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - rect.left - rect.width / 2) / rect.width;
    const y = (e.clientY - rect.top - rect.height / 2) / rect.height;
    setMousePosition({ x, y });
  };

  return (
    <motion.div
      className={cn("relative", containerClassName)}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
      style={{
        transformStyle: "preserve-3d",
      }}
      animate={{
        rotateX: isHovering ? mousePosition.y * 10 : 0,
        rotateY: isHovering ? mousePosition.x * 10 : 0,
      }}
      transition={{
        type: "spring",
        stiffness: 350,
        damping: 20,
      }}
    >
      <motion.div
        className={cn(
          "relative rounded-lg bg-card border border-border shadow-lg overflow-hidden",
          "before:absolute before:inset-0 before:bg-gradient-to-r before:from-transparent before:via-white/10 before:to-transparent before:translate-x-[-100%] before:transition-transform before:duration-700",
          isHovering && "before:translate-x-[100%]",
          className
        )}
        style={{
          transformStyle: "preserve-3d",
          transform: "translateZ(20px)",
        }}
        {...props}
      >
        {children}

        {/* Glow effect */}
        <motion.div
          className="absolute inset-0 rounded-lg bg-gradient-to-r from-blue-500/0 via-purple-500/20 to-pink-500/0 opacity-0"
          animate={{
            opacity: isHovering ? 0.6 : 0,
          }}
          transition={{
            duration: 0.3,
          }}
          style={{
            transform: "translateZ(-10px)",
          }}
        />
      </motion.div>
    </motion.div>
  );
}

export function HeroCard3D({ hero, className, onClick }) {
  return (
    <Card3D className={cn("cursor-pointer", className)} onClick={onClick}>
      <div className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-foreground">{hero.name}</h3>
            <p className="text-sm text-muted-foreground">{hero.role}</p>
          </div>
          <div className="text-right">
            <p className="text-lg font-bold text-foreground num">
              {hero.masteryScore}
            </p>
            <p className="text-xs text-muted-foreground">Mastery</p>
          </div>
        </div>

        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Win Rate:</span>
          <span className="font-medium text-foreground num">
            {hero.winRate}%
          </span>
        </div>

        <div className="flex items-center justify-between">
          <span
            className={`text-xs px-2 py-1 rounded ${
              hero.metaTier === "S"
                ? "bg-red-100 text-red-800"
                : hero.metaTier === "A"
                ? "bg-orange-100 text-orange-800"
                : hero.metaTier === "B"
                ? "bg-yellow-100 text-yellow-800"
                : "bg-gray-100 text-gray-800"
            }`}
          >
            Tier {hero.metaTier}
          </span>
          <span className="text-xs text-muted-foreground">
            {hero.matches} matches
          </span>
        </div>
      </div>
    </Card3D>
  );
}
