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
      className="flex h-14 items-center gap-3 border-b px-4"
      role="banner"
    >
      <SidebarTrigger aria-label="Toggle sidebar" className="-ml-1" />
      <Separator orientation="vertical" className="h-5" />

      <div className="flex-1">
        <h1 className="text-sm font-semibold">{title}</h1>
      </div>

      <Badge variant="outline" className="text-[10px] font-mono font-normal hidden sm:inline-flex">
        v0.1.0
      </Badge>

      <FontSizeToggle />
      <ThemeToggle />
    </header>
  );
}
