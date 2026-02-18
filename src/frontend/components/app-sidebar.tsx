"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import {
  FileText,
  Search,
  LayoutDashboard,
  Brain,
  Activity,
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
} from "@/components/ui/sidebar";

const NAV_ITEMS = [
  { title: "Process", href: "/", icon: FileText, description: "Extract insights" },
  { title: "Meetings", href: "/meetings", icon: LayoutDashboard, description: "Browse results" },
  { title: "Search", href: "/search", icon: Search, description: "Semantic search" },
];

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <Sidebar collapsible="icon" aria-label="Main navigation">
      <SidebarHeader className="p-4 pb-6">
        <Link href="/" className="flex items-center gap-3 group-data-[collapsible=icon]:justify-center">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sidebar-primary/10 shrink-0">
            <Brain className="h-4.5 w-4.5 text-sidebar-primary" />
          </div>
          <div className="group-data-[collapsible=icon]:hidden">
            <div className="font-semibold text-sm leading-tight text-sidebar-foreground">
              Meeting Intelligence
            </div>
            <div className="text-[10px] text-sidebar-foreground/50 leading-tight mt-0.5">
              AI-Powered Pipeline
            </div>
          </div>
        </Link>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel className="text-sidebar-foreground/40 text-[10px] uppercase tracking-wider">
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
                    <Link href={item.href}>
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
          <SidebarGroupLabel className="text-sidebar-foreground/40 text-[10px] uppercase tracking-wider">
            Stack
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <div className="px-3 py-2 space-y-2 group-data-[collapsible=icon]:hidden">
              <div className="flex items-center gap-2 text-[11px] text-sidebar-foreground/60">
                <div className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                Claude Sonnet 4
              </div>
              <div className="flex items-center gap-2 text-[11px] text-sidebar-foreground/60">
                <div className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                Sentence Transformers
              </div>
              <div className="flex items-center gap-2 text-[11px] text-sidebar-foreground/60">
                <div className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                Redis Vector Store
              </div>
              <div className="flex items-center gap-2 text-[11px] text-sidebar-foreground/60">
                <div className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                Presidio PII Redaction
              </div>
            </div>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="p-4">
        <div className="group-data-[collapsible=icon]:hidden space-y-3">
          <div className="flex items-center gap-2">
            <Activity className="h-3 w-3 text-emerald-400 shrink-0" />
            <span className="text-[10px] text-sidebar-foreground/50 uppercase tracking-wider">Powered by</span>
          </div>
          <Image
            src="/logo.svg"
            alt="StormGeo"
            width={100}
            height={24}
            className="opacity-60 brightness-0 invert"
          />
        </div>
        <div className="hidden group-data-[collapsible=icon]:flex justify-center">
          <Activity className="h-3.5 w-3.5 text-emerald-400" />
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
