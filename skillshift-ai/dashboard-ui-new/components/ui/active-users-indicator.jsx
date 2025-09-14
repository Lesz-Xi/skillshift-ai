"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Users } from "lucide-react";

const ActiveUsersIndicator = () => {
  const [activeUsers, setActiveUsers] = useState(0);
  const [isBlinking, setIsBlinking] = useState(true);

  // Simulate active users count
  useEffect(() => {
    const updateActiveUsers = () => {
      // Generate random number between 12-47 for realistic variation
      const newCount = Math.floor(Math.random() * 36) + 12;
      setActiveUsers(newCount);
    };

    // Update immediately
    updateActiveUsers();

    // Update every 3-7 seconds for realistic variation
    const interval = setInterval(() => {
      updateActiveUsers();
    }, Math.random() * 4000 + 3000);

    return () => clearInterval(interval);
  }, []);

  // Blinking animation control
  useEffect(() => {
    const blinkInterval = setInterval(() => {
      setIsBlinking((prev) => !prev);
    }, 1000);

    return () => clearInterval(blinkInterval);
  }, []);

  return (
    <div className="flex items-center gap-1.5 px-2 py-1 bg-muted rounded-md">
      <div className="w-4 h-4 bg-muted rounded-full flex items-center justify-center">
        <Users className="w-2.5 h-2.5 text-muted-foreground" />
      </div>
      <div className="flex items-center gap-1">
        <div className="text-xs text-foreground">{activeUsers}</div>
        <motion.div
          className="w-1.5 h-1.5 bg-green-500 rounded-full"
          animate={{
            opacity: isBlinking ? [1, 0.3, 1] : 1,
            scale: isBlinking ? [1, 1.2, 1] : 1,
          }}
          transition={{
            duration: 1,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      </div>
    </div>
  );
};

export default ActiveUsersIndicator;
