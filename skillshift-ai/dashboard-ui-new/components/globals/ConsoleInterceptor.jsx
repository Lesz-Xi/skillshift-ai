"use client";

import { useEffect } from "react";

/**
 * ConsoleInterceptor
 * Filters noisy AbortError logs that occur when fetch/requests are intentionally timed out or aborted.
 * This keeps the dev overlay clean without hiding real errors.
 */
export default function ConsoleInterceptor() {
  useEffect(() => {
    const originalError = console.error;
    const originalWarn = console.warn;

    const isAbortLike = (val) => {
      try {
        if (!val) return false;
        if (val?.name === "AbortError") return true;
        if (val?.type === "aborted") return true;
        const msg = String(val?.message || val || "").toLowerCase();
        return (
          msg.includes("aborterror") ||
          msg.includes("operation was aborted") ||
          msg.includes("fetch is aborted") ||
          msg.includes("the request was aborted") ||
          msg.includes("was aborted")
        );
      } catch {
        return false;
      }
    };

    const shouldFilter = (args) => {
      return Array.from(args).some(isAbortLike);
    };

    console.error = function (...args) {
      if (shouldFilter(args)) return; // drop AbortError noise
      return originalError.apply(this, args);
    };

    console.warn = function (...args) {
      if (shouldFilter(args)) return;
      return originalWarn.apply(this, args);
    };

    // Prevent unhandledrejection overlay for AbortError from fetch timeouts
    const onUnhandledRejection = (event) => {
      const r = event?.reason;
      if (isAbortLike(r)) {
        event.preventDefault();
      }
    };
    window.addEventListener("unhandledrejection", onUnhandledRejection);

    return () => {
      console.error = originalError;
      console.warn = originalWarn;
      window.removeEventListener("unhandledrejection", onUnhandledRejection);
    };
  }, []);

  return null;
}

