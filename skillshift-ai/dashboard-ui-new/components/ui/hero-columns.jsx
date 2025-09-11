"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MoreHorizontal, Eye, TrendingUp, Target } from "lucide-react";
import { toast } from "sonner";

const getMetaTierColor = (tier) => {
  switch (tier) {
    case "S":
      return "bg-red-100 text-red-800 border-red-200";
    case "A":
      return "bg-orange-100 text-orange-800 border-orange-200";
    case "B":
      return "bg-yellow-100 text-yellow-800 border-yellow-200";
    case "C":
      return "bg-gray-100 text-gray-800 border-gray-200";
    default:
      return "bg-gray-100 text-gray-800 border-gray-200";
  }
};

const getRoleColor = (role) => {
  switch (role) {
    case "Assassin":
      return "bg-purple-100 text-purple-800 border-purple-200";
    case "Mage":
      return "bg-blue-100 text-blue-800 border-blue-200";
    case "Marksman":
      return "bg-green-100 text-green-800 border-green-200";
    case "Tank":
      return "bg-gray-100 text-gray-800 border-gray-200";
    case "Support":
      return "bg-pink-100 text-pink-800 border-pink-200";
    case "Fighter":
      return "bg-orange-100 text-orange-800 border-orange-200";
    default:
      return "bg-gray-100 text-gray-800 border-gray-200";
  }
};

export const heroColumns = [
  {
    accessorKey: "name",
    header: "Hero",
    cell: ({ row }) => {
      const hero = row.original;
      return (
        <div className="flex items-center gap-3">
          <Avatar className="w-8 h-8">
            <AvatarImage
              src={`/heroes/${(hero.name || "").toLowerCase()}.png`}
              alt={hero.name || "Unknown"}
            />
            <AvatarFallback className="text-xs font-medium">
              {(hero.name || "UN").slice(0, 2).toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <div>
            <div className="font-medium text-foreground">
              {hero.name || "Unknown"}
            </div>
            <div className="text-sm text-muted-foreground">
              {hero.id || "N/A"}
            </div>
          </div>
        </div>
      );
    },
  },
  {
    accessorKey: "role",
    header: "Role",
    cell: ({ row }) => {
      const role = row.getValue("role") || "Unknown";
      return (
        <Badge variant="outline" className={getRoleColor(role)}>
          {role}
        </Badge>
      );
    },
  },
  {
    accessorKey: "masteryScore",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="h-auto p-0 font-semibold hover:bg-transparent"
        >
          Mastery Score
          {column.getIsSorted() === "desc" ? (
            <TrendingUp className="ml-2 h-4 w-4" />
          ) : column.getIsSorted() === "asc" ? (
            <TrendingUp className="ml-2 h-4 w-4 rotate-180" />
          ) : (
            <TrendingUp className="ml-2 h-4 w-4 opacity-50" />
          )}
        </Button>
      );
    },
    cell: ({ row }) => {
      const score = row.getValue("masteryScore") || 0;
      return (
        <div className="flex items-center gap-2">
          <div className="font-bold num text-foreground">{score}</div>
          <div
            className={`w-2 h-2 rounded-full ${
              score >= 90
                ? "bg-green-500"
                : score >= 70
                ? "bg-yellow-500"
                : "bg-red-500"
            }`}
          />
        </div>
      );
    },
  },
  {
    accessorKey: "winRate",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="h-auto p-0 font-semibold hover:bg-transparent"
        >
          Win Rate
          {column.getIsSorted() === "desc" ? (
            <TrendingUp className="ml-2 h-4 w-4" />
          ) : column.getIsSorted() === "asc" ? (
            <TrendingUp className="ml-2 h-4 w-4 rotate-180" />
          ) : (
            <TrendingUp className="ml-2 h-4 w-4 opacity-50" />
          )}
        </Button>
      );
    },
    cell: ({ row }) => {
      const winRate = row.getValue("winRate") || 0;
      return (
        <div
          className={`font-medium num ${
            winRate >= 70
              ? "text-green-600"
              : winRate >= 50
              ? "text-yellow-600"
              : "text-red-600"
          }`}
        >
          {winRate}%
        </div>
      );
    },
  },
  {
    accessorKey: "metaTier",
    header: "Meta Tier",
    cell: ({ row }) => {
      const metaTier = row.getValue("metaTier") || "C";
      return (
        <Badge variant="outline" className={getMetaTierColor(metaTier)}>
          {metaTier}
        </Badge>
      );
    },
  },
  {
    accessorKey: "matches",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="h-auto p-0 font-semibold hover:bg-transparent"
        >
          Matches
          {column.getIsSorted() === "desc" ? (
            <TrendingUp className="ml-2 h-4 w-4" />
          ) : column.getIsSorted() === "asc" ? (
            <TrendingUp className="ml-2 h-4 w-4 rotate-180" />
          ) : (
            <TrendingUp className="ml-2 h-4 w-4 opacity-50" />
          )}
        </Button>
      );
    },
    cell: ({ row }) => {
      return (
        <div className="num text-muted-foreground">
          {row.getValue("matches") || 0}
        </div>
      );
    },
  },
  {
    accessorKey: "lastPlayed",
    header: "Last Played",
    cell: ({ row }) => {
      return (
        <div className="mono-small text-muted-foreground">
          {row.getValue("lastPlayed") || "Never"}
        </div>
      );
    },
  },
  {
    id: "actions",
    enableHiding: false,
    cell: ({ row }) => {
      const hero = row.original || {};

      return (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <span className="sr-only">Open menu</span>
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Actions</DropdownMenuLabel>
            <DropdownMenuItem
              onClick={() =>
                toast.info(
                  `Viewing ${hero.name || "Unknown"} detailed analysis`
                )
              }
            >
              <Eye className="mr-2 h-4 w-4" />
              View Details
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() =>
                toast.info(
                  `Starting coaching session for ${hero.name || "Unknown"}`
                )
              }
            >
              <Target className="mr-2 h-4 w-4" />
              Request Coaching
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={() =>
                toast.success(`${hero.name || "Hero"} copied to clipboard`)
              }
            >
              Copy Hero ID
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );
    },
  },
];
