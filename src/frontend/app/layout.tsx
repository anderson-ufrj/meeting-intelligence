import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

import { ThemeProvider } from "@/components/theme-provider";
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { AppHeader } from "@/components/app-header";
import { TooltipProvider } from "@/components/ui/tooltip";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Meeting Intelligence | StormGeo",
  description:
    "Two-tier meeting intelligence pipeline — structured extraction, sentiment analysis, and semantic search from Microsoft Teams transcripts.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} ${jetbrainsMono.variable} antialiased`}>
        <ThemeProvider>
          <TooltipProvider>
            <SidebarProvider>
              <AppSidebar />
              <SidebarInset>
                <AppHeader />
                <main className="flex-1 p-3 sm:p-6" role="main">
                  {children}
                </main>
                <footer className="border-t px-3 sm:px-6 py-3 flex flex-col sm:flex-row items-center justify-between gap-1 text-xs text-muted-foreground" role="contentinfo">
                  <span>Architecture demonstration — Anderson Henrique da Silva</span>
                  <span className="font-mono text-[10px] sm:text-xs">FastAPI + Claude + Redis + Next.js</span>
                </footer>
              </SidebarInset>
            </SidebarProvider>
          </TooltipProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
