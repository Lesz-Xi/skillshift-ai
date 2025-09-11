"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { CustomSidebar } from "@/components/ui/custom-sidebar";
import { NavBreadcrumb } from "@/components/ui/nav-breadcrumb";
import { CommandPalette } from "@/components/ui/command-palette";
import { SidebarProvider } from "@/components/ui/sidebar";
import { toast } from "sonner";
import { Bell, RefreshCw, Menu, X } from "lucide-react";
import ClientOnly from "@/components/ClientOnly";
import { MobileNav } from "@/components/ui/mobile-nav";
import { PageTransition } from "@/components/ui/page-transitions";
import { FloatingActionButton } from "@/components/ui/floating-action-button";

export function ModernDashboardLayout({
  children,
  activeSection,
  onSectionChange,
  navigationItems,
}) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const getSectionTitle = (section) => {
    const item = navigationItems.find((item) => item.id === section);
    return item ? item.label : "Dashboard";
  };

  const handleCommandNavigate = (command) => {
    // Handle navigation commands
    if (navigationItems.find((item) => item.id === command)) {
      onSectionChange(command);
      toast.success(`Navigated to ${getSectionTitle(command)}`);
    } else {
      // Handle action commands
      switch (command) {
        case "upload":
          onSectionChange("screenshot-analysis");
          toast.info("Ready to upload new analysis");
          break;
        case "search":
          toast.info("Search functionality activated");
          break;
        case "export":
          toast.success("Export started - check downloads");
          break;
        case "refresh":
          window.location.reload();
          break;
        case "notifications":
          toast.info("Notifications center opened");
          break;
        default:
          toast.info(`Command: ${command}`);
      }
    }
  };

  return (
    <SidebarProvider>
      <div className="flex h-screen w-full bg-background">
        {/* Custom Sidebar */}
        {sidebarOpen && (
          <CustomSidebar
            activeSection={activeSection}
            onSectionChange={onSectionChange}
          />
        )}

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header with Breadcrumb */}
          <header className="bg-background border-b border-border p-4 md:p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="hidden md:block">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSidebarOpen(!sidebarOpen)}
                    className="h-8 w-8 p-0"
                  >
                    {sidebarOpen ? (
                      <X className="h-4 w-4" />
                    ) : (
                      <Menu className="h-4 w-4" />
                    )}
                  </Button>
                </div>
                <div className="md:hidden">
                  <MobileNav
                    activeSection={activeSection}
                    onSectionChange={onSectionChange}
                  />
                </div>
                <NavBreadcrumb
                  activeSection={activeSection}
                  onNavigate={onSectionChange}
                />
              </div>

              <div className="flex items-center gap-4">
                <div className="hidden md:flex items-center gap-1 text-xs text-muted-foreground">
                  <span>Press</span>
                  <kbd className="mono-small px-1.5 py-0.5 bg-muted border border-border rounded">
                    ⌘K
                  </kbd>
                  <span>for quick navigation</span>
                </div>

                <div className="text-xs text-muted-foreground hidden sm:block">
                  <ClientOnly fallback="Last update: --/--/---- --:-- UTC">
                    Last update: 17/01/2025 14:30 UTC
                  </ClientOnly>
                </div>

                <Button
                  variant="ghost"
                  size="icon"
                  className="text-muted-foreground hover:text-foreground hover:bg-accent"
                  onClick={() => toast.info("Notifications opened")}
                >
                  <Bell className="w-4 h-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="text-muted-foreground hover:text-foreground hover:bg-accent"
                  onClick={() => window.location.reload()}
                >
                  <RefreshCw className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </header>

          {/* Dashboard Content */}
          <main className="flex-1 overflow-auto bg-background">
            <PageTransition pageKey={activeSection}>{children}</PageTransition>
          </main>
        </div>

        {/* Command Palette */}
        <CommandPalette onNavigate={handleCommandNavigate} />

        {/* Floating Action Button */}
        <FloatingActionButton
          activeSection={activeSection}
          onNavigate={onSectionChange}
        />
      </div>
    </SidebarProvider>
  );
}
