import "./globals.css";

export const metadata = {
  title: "SkillShift AI - Dashboard",
  description: "Advanced AI-powered coaching and performance analysis platform",
  generator: "v0.dev",
};

import { Toaster } from "@/components/ui/sonner";
import ConsoleInterceptor from "@/components/globals/ConsoleInterceptor";

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-background text-foreground antialiased">
        <ConsoleInterceptor />
        {children}
        <Toaster />
      </body>
    </html>
  );
}
