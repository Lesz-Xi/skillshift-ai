"use client";

import { useState, useEffect } from "react";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import {
  BarChart3,
  Trophy,
  Target,
  Heart,
  History,
  Camera,
  Video,
  Settings,
  Search,
  Upload,
  Eye,
  Download,
  Filter,
  RefreshCw,
  Bell,
  Users,
  Brain,
} from "lucide-react";

export function CommandPalette({ onNavigate }) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const down = (e) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };

    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  const handleSelect = (value) => {
    setOpen(false);
    if (onNavigate) {
      onNavigate(value);
    }
  };

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="Type a command or search..." />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>

        <CommandGroup heading="Navigation">
          <CommandItem onSelect={() => handleSelect("overview")}>
            <BarChart3 className="mr-2 h-4 w-4" />
            <span>Overview</span>
          </CommandItem>
          <CommandItem onSelect={() => handleSelect("heroes")}>
            <Trophy className="mr-2 h-4 w-4" />
            <span>Heroes Mastery</span>
          </CommandItem>
          <CommandItem onSelect={() => handleSelect("coaching")}>
            <Target className="mr-2 h-4 w-4" />
            <span>Coaching Pipeline</span>
          </CommandItem>
          <CommandItem onSelect={() => handleSelect("mindset")}>
            <Heart className="mr-2 h-4 w-4" />
            <span>Mindset</span>
          </CommandItem>
          <CommandItem onSelect={() => handleSelect("history")}>
            <History className="mr-2 h-4 w-4" />
            <span>Analysis History</span>
          </CommandItem>
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Analysis Tools">
          <CommandItem onSelect={() => handleSelect("screenshot-analysis")}>
            <Camera className="mr-2 h-4 w-4" />
            <span>Screenshot Analysis</span>
          </CommandItem>
          <CommandItem onSelect={() => handleSelect("video-analysis")}>
            <Video className="mr-2 h-4 w-4" />
            <span>Video Analysis</span>
          </CommandItem>
          <CommandItem onSelect={() => handleSelect("upload")}>
            <Upload className="mr-2 h-4 w-4" />
            <span>Upload New Analysis</span>
          </CommandItem>
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Quick Actions">
          <CommandItem onSelect={() => handleSelect("search")}>
            <Search className="mr-2 h-4 w-4" />
            <span>Search Analyses</span>
          </CommandItem>
          <CommandItem onSelect={() => handleSelect("export")}>
            <Download className="mr-2 h-4 w-4" />
            <span>Export Data</span>
          </CommandItem>
          <CommandItem onSelect={() => handleSelect("filter")}>
            <Filter className="mr-2 h-4 w-4" />
            <span>Advanced Filters</span>
          </CommandItem>
          <CommandItem onSelect={() => handleSelect("refresh")}>
            <RefreshCw className="mr-2 h-4 w-4" />
            <span>Refresh Dashboard</span>
          </CommandItem>
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="System">
          <CommandItem onSelect={() => handleSelect("admin")}>
            <Settings className="mr-2 h-4 w-4" />
            <span>System Status</span>
          </CommandItem>
          <CommandItem onSelect={() => handleSelect("notifications")}>
            <Bell className="mr-2 h-4 w-4" />
            <span>Notifications</span>
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
