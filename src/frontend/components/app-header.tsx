"use client";

import { SidebarTrigger } from "@/components/ui/sidebar";
import { ThemeToggle } from "@/components/theme-toggle";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";

export function AppHeader() {
  return (
    <header
      className="flex h-12 items-center gap-3 border-b px-4"
      role="banner"
    >
      <SidebarTrigger aria-label="Toggle sidebar" className="-ml-1" />
      <Separator orientation="vertical" className="h-4" />

      <div className="flex-1">
        <span className="text-sm font-medium sr-only sm:not-sr-only">
          Meeting Intelligence
        </span>
      </div>

      <Badge variant="outline" className="text-xs font-normal hidden sm:inline-flex">
        v0.1.0
      </Badge>

      <ThemeToggle />
    </header>
  );
}
