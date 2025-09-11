"use client";

import { useEffect, useRef } from "react";
import { motion, useSpring, useTransform } from "framer-motion";
import { cn } from "@/lib/utils";

export function NumberTicker({
  value,
  direction = "up",
  delay = 0,
  className,
  decimalPlaces = 0,
}) {
  const ref = useRef(null);
  const motionValue = useSpring(0, { damping: 60, stiffness: 100 });
  const rounded = useTransform(motionValue, (latest) =>
    Intl.NumberFormat("en-US", {
      minimumFractionDigits: decimalPlaces,
      maximumFractionDigits: decimalPlaces,
    }).format(Number(latest.toFixed(decimalPlaces)))
  );

  useEffect(() => {
    const timer = setTimeout(() => {
      motionValue.set(value);
    }, delay);

    return () => clearTimeout(timer);
  }, [motionValue, delay, value]);

  return (
    <motion.span
      ref={ref}
      className={cn("inline-block tabular-nums", className)}
      initial={{ opacity: 0, y: direction === "down" ? -10 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: delay / 1000 }}
    >
      {rounded}
    </motion.span>
  );
}

export function AnimatedCounter({
  value,
  suffix = "",
  prefix = "",
  className,
  delay = 0,
}) {
  return (
    <div className={cn("flex items-baseline", className)}>
      {prefix && <span className="mr-1">{prefix}</span>}
      <NumberTicker value={value} delay={delay} className="font-bold" />
      {suffix && <span className="ml-1">{suffix}</span>}
    </div>
  );
}
