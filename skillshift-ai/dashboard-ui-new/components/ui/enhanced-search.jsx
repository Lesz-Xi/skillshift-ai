"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Search,
  Filter,
  X,
  ChevronDown,
  SlidersHorizontal,
} from "lucide-react";
import { cn } from "@/lib/utils";

export function EnhancedSearch({
  searchTerm,
  onSearchChange,
  filters = [],
  onFiltersChange,
  placeholder = "Search...",
  filterOptions = [],
  className,
}) {
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  const handleFilterToggle = (filterId, value) => {
    const newFilters = { ...filters };
    if (newFilters[filterId]) {
      if (newFilters[filterId].includes(value)) {
        newFilters[filterId] = newFilters[filterId].filter((v) => v !== value);
      } else {
        newFilters[filterId] = [...newFilters[filterId], value];
      }
    } else {
      newFilters[filterId] = [value];
    }

    if (newFilters[filterId].length === 0) {
      delete newFilters[filterId];
    }

    onFiltersChange(newFilters);
  };

  const clearFilters = () => {
    onFiltersChange({});
  };

  const getActiveFilterCount = () => {
    return Object.values(filters).flat().length;
  };

  return (
    <div className={cn("flex items-center gap-2", className)}>
      {/* Search Input */}
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
        <Input
          placeholder={placeholder}
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Advanced Filters */}
      <Popover open={isFilterOpen} onOpenChange={setIsFilterOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" size="sm" className="relative">
            <SlidersHorizontal className="w-4 h-4 mr-2" />
            Filters
            {getActiveFilterCount() > 0 && (
              <Badge
                variant="secondary"
                className="ml-2 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs"
              >
                {getActiveFilterCount()}
              </Badge>
            )}
            <ChevronDown className="w-4 h-4 ml-1" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-80 p-0" align="end">
          <Command>
            <CommandInput placeholder="Search filters..." />
            <CommandList>
              <CommandEmpty>No filters found.</CommandEmpty>

              {filterOptions.map((filterGroup) => (
                <CommandGroup key={filterGroup.id} heading={filterGroup.label}>
                  {filterGroup.options.map((option) => (
                    <CommandItem
                      key={option.value}
                      className="flex items-center space-x-2"
                    >
                      <Checkbox
                        id={`${filterGroup.id}-${option.value}`}
                        checked={
                          filters[filterGroup.id]?.includes(option.value) ||
                          false
                        }
                        onCheckedChange={(checked) => {
                          handleFilterToggle(filterGroup.id, option.value);
                        }}
                      />
                      <label
                        htmlFor={`${filterGroup.id}-${option.value}`}
                        className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer flex-1"
                      >
                        {option.label}
                      </label>
                      {option.count && (
                        <span className="text-xs text-muted-foreground">
                          ({option.count})
                        </span>
                      )}
                    </CommandItem>
                  ))}
                </CommandGroup>
              ))}
            </CommandList>

            {getActiveFilterCount() > 0 && (
              <div className="border-t p-3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearFilters}
                  className="w-full"
                >
                  <X className="w-4 h-4 mr-2" />
                  Clear All Filters
                </Button>
              </div>
            )}
          </Command>
        </PopoverContent>
      </Popover>

      {/* Active Filters Display */}
      {getActiveFilterCount() > 0 && (
        <div className="flex items-center gap-1 flex-wrap">
          {Object.entries(filters).map(([filterId, values]) =>
            values.map((value) => (
              <Badge
                key={`${filterId}-${value}`}
                variant="secondary"
                className="text-xs"
              >
                {value}
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-auto p-0 ml-1 hover:bg-transparent"
                  onClick={() => handleFilterToggle(filterId, value)}
                >
                  <X className="w-3 h-3" />
                </Button>
              </Badge>
            ))
          )}
        </div>
      )}
    </div>
  );
}
