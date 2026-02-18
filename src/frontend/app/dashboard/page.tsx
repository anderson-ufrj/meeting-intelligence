"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { healthCheck, listMeetings } from "@/lib/api";
import {
  FileText,
  Search,
  Database,
  Brain,
  Shield,
  Activity,
  ArrowRight,
  Server,
} from "lucide-react";

type HealthData = {
  status: string;
  redis: string;
  version: string;
};

type MeetingSummary = {
  meeting_id: string;
  title: string;
  tier: string;
  processed_at: string;
};

export default function DashboardPage() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [meetings, setMeetings] = useState<MeetingSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [h, m] = await Promise.all([
          healthCheck().catch(() => null),
          listMeetings().catch(() => ({ meetings: [] })),
        ]);
        setHealth(h);
        setMeetings(m.meetings ?? []);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const isHealthy = health?.status === "healthy";
  const redisOk = health?.redis === "connected";
  const totalMeetings = meetings.length;
  const recentMeetings = meetings.slice(-5).reverse();

  if (loading) {
    return (
      <div className="max-w-6xl space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Meetings</p>
                <p className="text-3xl font-bold mt-1">{totalMeetings}</p>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
                <FileText className="h-6 w-6 text-primary" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">API Status</p>
                <div className="flex items-center gap-2 mt-1">
                  <div className={`h-2.5 w-2.5 rounded-full ${isHealthy ? "bg-emerald-500" : "bg-red-500"}`} />
                  <p className="text-lg font-semibold">{isHealthy ? "Healthy" : "Down"}</p>
                </div>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/10">
                <Activity className="h-6 w-6 text-emerald-500" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Redis</p>
                <div className="flex items-center gap-2 mt-1">
                  <div className={`h-2.5 w-2.5 rounded-full ${redisOk ? "bg-emerald-500" : "bg-red-500"}`} />
                  <p className="text-lg font-semibold">{redisOk ? "Connected" : "Offline"}</p>
                </div>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-orange-500/10">
                <Database className="h-6 w-6 text-orange-500" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Version</p>
                <p className="text-lg font-semibold font-mono mt-1">{health?.version ?? "—"}</p>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-violet-500/10">
                <Server className="h-6 w-6 text-violet-500" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Meetings */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-base">Recent Meetings</CardTitle>
            <Link href="/meetings">
              <Button variant="ghost" size="sm" className="text-xs gap-1">
                View all <ArrowRight className="h-3 w-3" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {recentMeetings.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground text-sm">
                No meetings processed yet.
              </div>
            ) : (
              <div className="space-y-3">
                {recentMeetings.map((m) => (
                  <div key={m.meeting_id} className="flex items-center justify-between gap-3 py-2 border-b last:border-0">
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium truncate">{m.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(m.processed_at).toLocaleString()}
                      </p>
                    </div>
                    <Badge variant={m.tier === "sensitive" ? "destructive" : "secondary"} className="shrink-0">
                      {m.tier}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Pipeline Architecture */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Pipeline Architecture</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { icon: FileText, label: "Transcript Input", desc: "Microsoft Teams VTT/text format", color: "text-blue-500 bg-blue-500/10" },
                { icon: Brain, label: "Claude Extraction", desc: "Structured insights via Instructor + Anthropic", color: "text-violet-500 bg-violet-500/10" },
                { icon: Activity, label: "Sentiment Analysis", desc: "BERT-based per-speaker sentiment scoring", color: "text-amber-500 bg-amber-500/10" },
                { icon: Shield, label: "PII Redaction", desc: "Presidio-powered sensitive data anonymization", color: "text-red-500 bg-red-500/10" },
                { icon: Search, label: "Semantic Indexing", desc: "Sentence-transformers → Redis vector store", color: "text-emerald-500 bg-emerald-500/10" },
                { icon: Database, label: "Storage & Search", desc: "Cosine similarity search across meetings", color: "text-orange-500 bg-orange-500/10" },
              ].map((step, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className={`flex h-9 w-9 items-center justify-center rounded-lg shrink-0 ${step.color}`}>
                    <step.icon className="h-4 w-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium">{step.label}</p>
                    <p className="text-xs text-muted-foreground">{step.desc}</p>
                  </div>
                  {i < 5 && (
                    <ArrowRight className="h-3 w-3 text-muted-foreground/40 shrink-0" />
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Link href="/">
          <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
            <CardContent className="pt-6 flex items-center gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 shrink-0">
                <FileText className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="font-medium text-sm">Process Transcript</p>
                <p className="text-xs text-muted-foreground">Upload and extract insights</p>
              </div>
            </CardContent>
          </Card>
        </Link>

        <Link href="/meetings">
          <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
            <CardContent className="pt-6 flex items-center gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 shrink-0">
                <Database className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="font-medium text-sm">Browse Meetings</p>
                <p className="text-xs text-muted-foreground">View all processed meetings</p>
              </div>
            </CardContent>
          </Card>
        </Link>

        <Link href="/search">
          <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
            <CardContent className="pt-6 flex items-center gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 shrink-0">
                <Search className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="font-medium text-sm">Semantic Search</p>
                <p className="text-xs text-muted-foreground">Find meetings by meaning</p>
              </div>
            </CardContent>
          </Card>
        </Link>
      </div>
    </div>
  );
}
