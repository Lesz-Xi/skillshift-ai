"use client";

import {
  Breadcrumb,
  BreadcrumbEllipsis,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Home,
  BarChart3,
  Trophy,
  Target,
  Heart,
  History,
  Camera,
  Video,
  Settings,
} from "lucide-react";

const sectionIcons = {
  overview: BarChart3,
  heroes: Trophy,
  coaching: Target,
  mindset: Heart,
  history: History,
  "screenshot-analysis": Camera,
  "video-analysis": Video,
  admin: Settings,
};

const sectionLabels = {
  overview: "Overview",
  heroes: "Heroes",
  coaching: "Coaching",
  mindset: "Mindset",
  history: "Analysis History",
  "screenshot-analysis": "Screenshot Analysis",
  "video-analysis": "Video Analysis",
  admin: "System Status",
};

export function NavBreadcrumb({
  activeSection,
  onNavigate,
  showIcons = true,
  className,
}) {
  const Icon = sectionIcons[activeSection] || Home;
  const sectionLabel = sectionLabels[activeSection] || "Dashboard";

  const allSections = Object.keys(sectionLabels);
  const recentSections = ["overview", "heroes", "coaching", "history"];

  return (
    <Breadcrumb className={className}>
      <BreadcrumbList>
        <BreadcrumbItem>
          <BreadcrumbLink
            onClick={() => onNavigate("overview")}
            className="flex items-center gap-1 cursor-pointer hover:text-foreground transition-colors"
          >
            <Home className="w-3 h-3" />
            Dashboard
          </BreadcrumbLink>
        </BreadcrumbItem>

        {activeSection !== "overview" && (
          <>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <DropdownMenu>
                <DropdownMenuTrigger className="flex items-center gap-1">
                  <BreadcrumbEllipsis className="h-4 w-4" />
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start">
                  <div className="px-2 py-1">
                    <div className="text-xs font-medium text-muted-foreground mb-1">
                      Recent Sections
                    </div>
                    {recentSections
                      .filter((section) => section !== activeSection)
                      .slice(0, 3)
                      .map((section) => {
                        const SectionIcon = sectionIcons[section];
                        return (
                          <DropdownMenuItem
                            key={section}
                            onClick={() => onNavigate(section)}
                            className="flex items-center gap-2"
                          >
                            <SectionIcon className="w-4 h-4" />
                            {sectionLabels[section]}
                          </DropdownMenuItem>
                        );
                      })}
                  </div>
                  <div className="border-t px-2 py-1 mt-1">
                    <div className="text-xs font-medium text-muted-foreground mb-1">
                      All Sections
                    </div>
                    {allSections
                      .filter(
                        (section) =>
                          !recentSections.includes(section) &&
                          section !== activeSection
                      )
                      .map((section) => {
                        const SectionIcon = sectionIcons[section];
                        return (
                          <DropdownMenuItem
                            key={section}
                            onClick={() => onNavigate(section)}
                            className="flex items-center gap-2"
                          >
                            <SectionIcon className="w-4 h-4" />
                            {sectionLabels[section]}
                          </DropdownMenuItem>
                        );
                      })}
                  </div>
                </DropdownMenuContent>
              </DropdownMenu>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbPage className="flex items-center gap-1">
                {showIcons && <Icon className="w-3 h-3" />}
                {sectionLabel}
              </BreadcrumbPage>
            </BreadcrumbItem>
          </>
        )}
      </BreadcrumbList>
    </Breadcrumb>
  );
}
