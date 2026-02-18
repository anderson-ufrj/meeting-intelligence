"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { useTheme } from "next-themes";
import {
  FileText,
  Search,
  LayoutDashboard,
  Brain,
  Activity,
  Gauge,
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";

const NAV_ITEMS = [
  { title: "Dashboard", href: "/dashboard", icon: Gauge },
  { title: "Process", href: "/", icon: FileText },
  { title: "Meetings", href: "/meetings", icon: LayoutDashboard },
  { title: "Intelligence", href: "/intelligence", icon: Brain },
  { title: "Search", href: "/search", icon: Search },
];

export function AppSidebar() {
  const pathname = usePathname();
  const { resolvedTheme } = useTheme();
  const { isMobile, setOpenMobile } = useSidebar();

  return (
    <Sidebar collapsible="icon" aria-label="Main navigation">
      <SidebarHeader className="p-4 pb-6">
        <Link href="/dashboard" className="flex items-center gap-3 group-data-[collapsible=icon]:justify-center">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 shrink-0">
            <Brain className="h-4.5 w-4.5 text-primary" />
          </div>
          <div className="group-data-[collapsible=icon]:hidden">
            <Image
              src="/logo.svg"
              alt="StormGeo"
              width={120}
              height={30}
              className={resolvedTheme === "dark" ? "brightness-0 invert" : ""}
            />
            <div className="text-[10px] text-muted-foreground leading-tight mt-1">
              Meeting Intelligence
            </div>
          </div>
        </Link>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel className="text-[10px] uppercase tracking-wider">
            Pipeline
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {NAV_ITEMS.map((item) => (
                <SidebarMenuItem key={item.href}>
                  <SidebarMenuButton
                    asChild
                    isActive={pathname === item.href}
                    tooltip={item.title}
                  >
                    <Link
                      href={item.href}
                      onClick={() => isMobile && setOpenMobile(false)}
                    >
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel className="text-[10px] uppercase tracking-wider">
            Stack
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <div className="px-3 py-2 space-y-2.5 group-data-[collapsible=icon]:hidden">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <div className="h-2 w-2 rounded-full bg-emerald-500 shrink-0" />
                Claude Sonnet 4
              </div>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <div className="h-2 w-2 rounded-full bg-emerald-500 shrink-0" />
                Sentence Transformers
              </div>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <div className="h-2 w-2 rounded-full bg-emerald-500 shrink-0" />
                Redis Vector Store
              </div>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <div className="h-2 w-2 rounded-full bg-emerald-500 shrink-0" />
                Presidio PII Redaction
              </div>
            </div>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="p-4">
        <div className="group-data-[collapsible=icon]:hidden space-y-2">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wider">
            Built as PoC for
          </span>
          <Image
            src="/logo.svg"
            alt="StormGeo"
            width={140}
            height={34}
            className={resolvedTheme === "dark" ? "opacity-70 brightness-0 invert" : "opacity-70"}
          />
        </div>
        <div className="hidden group-data-[collapsible=icon]:flex justify-center">
          <Activity className="h-3.5 w-3.5 text-muted-foreground" />
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
