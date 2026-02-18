"use client";

import { SidebarTrigger } from "@/components/ui/sidebar";
import { ThemeToggle } from "@/components/theme-toggle";
import { FontSizeToggle } from "@/components/font-size-toggle";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { usePathname } from "next/navigation";

const PAGE_TITLES: Record<string, string> = {
  "/": "Process Transcript",
  "/dashboard": "Dashboard",
  "/meetings": "Meeting History",
  "/intelligence": "Intelligence",
  "/search": "Semantic Search",
};

export function AppHeader() {
  const pathname = usePathname();
  const title = PAGE_TITLES[pathname] ?? "Meeting Intelligence";

  return (
    <header
      className="sticky top-0 z-50 flex h-14 shrink-0 items-center gap-2 border-b bg-background/95 backdrop-blur-sm supports-backdrop-filter:bg-background/60 px-3 sm:gap-3 sm:px-4"
      role="banner"
    >
      <SidebarTrigger aria-label="Toggle sidebar" className="-ml-1" />
      <Separator orientation="vertical" className="h-5 hidden sm:block" />

      <div className="flex-1 min-w-0">
        <h1 className="text-xs sm:text-sm font-semibold truncate">{title}</h1>
      </div>

      <Badge variant="outline" className="text-[10px] font-mono font-normal hidden md:inline-flex">
        v0.1.0
      </Badge>

      <FontSizeToggle />
      <ThemeToggle />
    </header>
  );
}
