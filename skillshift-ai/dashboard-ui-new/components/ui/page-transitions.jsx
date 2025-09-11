"use client";

import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

const pageVariants = {
  initial: {
    opacity: 0,
    y: 20,
    scale: 0.98,
  },
  in: {
    opacity: 1,
    y: 0,
    scale: 1,
  },
  out: {
    opacity: 0,
    y: -20,
    scale: 1.02,
  },
};

const pageTransition = {
  type: "tween",
  ease: "anticipate",
  duration: 0.4,
};

export function PageTransition({ children, className, pageKey }) {
  return (
    <motion.div
      key={pageKey}
      initial="initial"
      animate="in"
      exit="out"
      variants={pageVariants}
      transition={pageTransition}
      className={cn("w-full", className)}
    >
      {children}
    </motion.div>
  );
}

export function StaggeredContainer({ children, className, delay = 0.1 }) {
  return (
    <motion.div
      className={cn("space-y-6", className)}
      initial="initial"
      animate="in"
      variants={{
        initial: {},
        in: {
          transition: {
            staggerChildren: delay,
          },
        },
      }}
    >
      {children}
    </motion.div>
  );
}

export function FadeInUp({ children, className, delay = 0 }) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.5,
        delay,
        ease: "easeOut",
      }}
    >
      {children}
    </motion.div>
  );
}

export function SlideInLeft({ children, className, delay = 0 }) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{
        duration: 0.4,
        delay,
        ease: "easeOut",
      }}
    >
      {children}
    </motion.div>
  );
}

export function ScaleIn({ children, className, delay = 0 }) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{
        duration: 0.3,
        delay,
        ease: "backOut",
      }}
    >
      {children}
    </motion.div>
  );
}
