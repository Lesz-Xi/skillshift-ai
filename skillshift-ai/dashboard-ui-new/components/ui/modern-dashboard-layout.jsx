"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { CustomSidebar } from "@/components/ui/custom-sidebar";
import { NavBreadcrumb } from "@/components/ui/nav-breadcrumb";
import { CommandPalette } from "@/components/ui/command-palette";
import { SidebarProvider } from "@/components/ui/sidebar";
import { toast } from "sonner";
import { Bell, RefreshCw, Menu, X, ChevronRight, Sparkles } from "lucide-react";
import ClientOnly from "@/components/ClientOnly";
import { MobileNav } from "@/components/ui/mobile-nav";
import { PageTransition } from "@/components/ui/page-transitions";
import { FloatingActionButton } from "@/components/ui/floating-action-button";
import ActiveUsersIndicator from "./active-users-indicator";
import UserAvatarMenu from "./user-avatar-menu";
import { cn } from "@/lib/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

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
            onClose={() => setSidebarOpen(false)}
          />
        )}

        {/* Collapsed Sidebar with Icons - When Closed */}
        {!sidebarOpen && (
          <div className="w-16 bg-card border-r border-border h-full flex flex-col">
            {/* Header */}
            <div className="p-3 border-b border-border">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center mx-auto">
                <Sparkles className="w-5 h-5 text-primary-foreground" />
              </div>
            </div>

            {/* Navigation Icons */}
            <div
              className="flex-1 overflow-y-auto p-2 space-y-1 [&::-webkit-scrollbar]:w-0 [&::-webkit-scrollbar]:h-0"
              style={{ scrollbarWidth: "none", scrollbarGutter: "auto" }}
            >
              <TooltipProvider>
                {navigationItems.map((item) => (
                  <Tooltip key={item.id}>
                    <TooltipTrigger asChild>
                      <button
                        onClick={() => {
                          onSectionChange(item.id);
                          setSidebarOpen(true);
                        }}
                        className={cn(
                          "w-10 h-10 flex items-center justify-center rounded-md transition-colors",
                          activeSection === item.id
                            ? "bg-accent/60 text-accent-foreground"
                            : "text-muted-foreground hover:text-foreground hover:bg-accent/30"
                        )}
                      >
                        <item.icon className="w-5 h-5" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="right" className="ml-2">
                      <p>{item.label}</p>
                    </TooltipContent>
                  </Tooltip>
                ))}
              </TooltipProvider>
            </div>

            {/* Footer with Avatar and Close Button */}
            <div className="p-3 border-t border-border">
              <div className="flex flex-col items-center gap-3">
                <UserAvatarMenu />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSidebarOpen(true)}
                  className="h-8 w-8 p-0 text-muted-foreground hover:text-foreground"
                >
                  <ChevronRight className="w-4 h-4" />
                  <ChevronRight className="w-4 h-4 -ml-4" />
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Main Content Area */}
        <div
          className="flex-1 flex flex-col overflow-hidden [&::-webkit-scrollbar]:w-0 [&::-webkit-scrollbar]:h-0"
          style={{
            scrollbarWidth: "none",
            scrollbarGutter: "auto",
          }}
        >
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
                <div className="hidden sm:block">
                  <ActiveUsersIndicator />
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
          <main
            className="flex-1 overflow-auto bg-background [&::-webkit-scrollbar]:w-0 [&::-webkit-scrollbar]:h-0"
            style={{
              scrollbarWidth: "none",
              scrollbarGutter: "auto",
            }}
          >
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
