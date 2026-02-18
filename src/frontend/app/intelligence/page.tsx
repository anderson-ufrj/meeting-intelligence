"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { getStats } from "@/lib/api";
import {
  Brain,
  ListChecks,
  ClipboardList,
  HelpCircle,
  Users,
  Tag,
  AlertTriangle,
  SmilePlus,
  Meh,
  Frown,
  Shield,
  TrendingUp,
} from "lucide-react";

type Stats = {
  total_meetings: number;
  total_decisions: number;
  total_actions: number;
  total_questions: number;
  total_speakers: number;
  tier_breakdown: Record<string, number>;
  sentiment_distribution: Record<string, number>;
  top_topics: [string, number][];
  priority_breakdown: Record<string, number>;
  speaker_sentiments: Record<string, Record<string, number>>;
};

const SENTIMENT_ICONS: Record<string, typeof SmilePlus> = {
  positive: SmilePlus,
  neutral: Meh,
  negative: Frown,
};

const SENTIMENT_COLORS: Record<string, string> = {
  positive: "text-emerald-500",
  neutral: "text-amber-500",
  negative: "text-red-500",
};

const SENTIMENT_BAR_COLORS: Record<string, string> = {
  positive: "bg-emerald-500",
  neutral: "bg-amber-500",
  negative: "bg-red-500",
};

const PRIORITY_COLORS: Record<string, string> = {
  high: "bg-red-500",
  medium: "bg-amber-500",
  low: "bg-emerald-500",
};

export default function IntelligencePage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const data = await getStats();
        setStats(data);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to load stats");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="max-w-6xl space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-72" />
          <Skeleton className="h-72" />
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="max-w-6xl">
        <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 px-4 py-3 rounded-lg" role="alert">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          {error || "No data available"}
        </div>
      </div>
    );
  }

  const totalSentiments = Object.values(stats.sentiment_distribution).reduce((a, b) => a + b, 0);
  const totalPriorities = Object.values(stats.priority_breakdown).reduce((a, b) => a + b, 0);

  return (
    <div className="max-w-6xl space-y-6">
      {/* KPI Row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        {[
          { label: "Meetings", value: stats.total_meetings, icon: Brain, color: "text-primary bg-primary/10" },
          { label: "Decisions", value: stats.total_decisions, icon: ListChecks, color: "text-violet-500 bg-violet-500/10" },
          { label: "Action Items", value: stats.total_actions, icon: ClipboardList, color: "text-blue-500 bg-blue-500/10" },
          { label: "Open Questions", value: stats.total_questions, icon: HelpCircle, color: "text-amber-500 bg-amber-500/10" },
          { label: "Speakers", value: stats.total_speakers, icon: Users, color: "text-emerald-500 bg-emerald-500/10" },
        ].map((kpi) => (
          <Card key={kpi.label}>
            <CardContent className="pt-5 pb-4">
              <div className="flex items-center gap-3">
                <div className={`flex h-10 w-10 items-center justify-center rounded-lg shrink-0 ${kpi.color}`}>
                  <kpi.icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{kpi.value}</p>
                  <p className="text-xs text-muted-foreground">{kpi.label}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sentiment Distribution */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <TrendingUp className="h-4 w-4" /> Sentiment Overview
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            {/* Big sentiment bar */}
            <div className="flex h-6 rounded-full overflow-hidden">
              {(["positive", "neutral", "negative"] as const).map((s) => {
                const count = stats.sentiment_distribution[s] || 0;
                const pct = totalSentiments > 0 ? (count / totalSentiments) * 100 : 0;
                if (pct === 0) return null;
                return (
                  <div
                    key={s}
                    className={`${SENTIMENT_BAR_COLORS[s]} transition-all relative group`}
                    style={{ width: `${pct}%` }}
                    title={`${s}: ${count} (${pct.toFixed(0)}%)`}
                  />
                );
              })}
            </div>

            {/* Legend */}
            <div className="grid grid-cols-3 gap-4">
              {(["positive", "neutral", "negative"] as const).map((s) => {
                const Icon = SENTIMENT_ICONS[s];
                const count = stats.sentiment_distribution[s] || 0;
                const pct = totalSentiments > 0 ? (count / totalSentiments) * 100 : 0;
                return (
                  <div key={s} className="text-center space-y-1">
                    <Icon className={`h-6 w-6 mx-auto ${SENTIMENT_COLORS[s]}`} />
                    <p className="text-xl font-bold">{pct.toFixed(0)}%</p>
                    <p className="text-xs text-muted-foreground capitalize">{s} ({count})</p>
                  </div>
                );
              })}
            </div>

            {/* Per-speaker breakdown */}
            <div className="space-y-2 pt-2 border-t">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">By Speaker</p>
              {Object.entries(stats.speaker_sentiments).slice(0, 8).map(([speaker, counts]) => {
                const total = Object.values(counts).reduce((a, b) => a + b, 0);
                return (
                  <div key={speaker} className="space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium truncate">{speaker}</span>
                      <span className="text-[10px] text-muted-foreground">{total} sample{total !== 1 ? "s" : ""}</span>
                    </div>
                    <div className="flex h-2 rounded-full overflow-hidden bg-muted">
                      {(["positive", "neutral", "negative"] as const).map((s) => {
                        const pct = total > 0 ? ((counts[s] || 0) / total) * 100 : 0;
                        if (pct === 0) return null;
                        return (
                          <div
                            key={s}
                            className={`${SENTIMENT_BAR_COLORS[s]}`}
                            style={{ width: `${pct}%` }}
                          />
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Topics Word Cloud style */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Tag className="h-4 w-4" /> Top Topics Across Meetings
            </CardTitle>
          </CardHeader>
          <CardContent>
            {stats.top_topics.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">No topics yet.</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {stats.top_topics.map(([topic, count], i) => {
                  const maxCount = stats.top_topics[0][1];
                  const ratio = count / maxCount;
                  const sizeClass = ratio > 0.7
                    ? "text-base px-4 py-2"
                    : ratio > 0.4
                    ? "text-sm px-3 py-1.5"
                    : "text-xs px-2.5 py-1";
                  const variant = i < 3 ? "default" : i < 8 ? "secondary" : "outline";
                  return (
                    <Badge
                      key={topic}
                      variant={variant as "default" | "secondary" | "outline"}
                      className={`${sizeClass} font-medium`}
                    >
                      {topic}
                      <span className="ml-1.5 opacity-60">{count}</span>
                    </Badge>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Action Priority Breakdown */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <ClipboardList className="h-4 w-4" /> Action Items by Priority
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {(["high", "medium", "low"] as const).map((p) => {
              const count = stats.priority_breakdown[p] || 0;
              const pct = totalPriorities > 0 ? (count / totalPriorities) * 100 : 0;
              return (
                <div key={p} className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium capitalize">{p} Priority</span>
                    <span className="text-sm text-muted-foreground">{count} ({pct.toFixed(0)}%)</span>
                  </div>
                  <div className="h-3 rounded-full bg-muted overflow-hidden">
                    <div
                      className={`h-full rounded-full ${PRIORITY_COLORS[p]} transition-all`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>

        {/* Tier Breakdown */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Shield className="h-4 w-4" /> Data Classification
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-xl border-2 border-primary/20 p-5 text-center space-y-2">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 mx-auto">
                  <Brain className="h-6 w-6 text-primary" />
                </div>
                <p className="text-3xl font-bold">{stats.tier_breakdown.ordinary || 0}</p>
                <p className="text-xs text-muted-foreground">Ordinary Tier</p>
              </div>
              <div className="rounded-xl border-2 border-destructive/20 p-5 text-center space-y-2">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10 mx-auto">
                  <Shield className="h-6 w-6 text-destructive" />
                </div>
                <p className="text-3xl font-bold">{stats.tier_breakdown.sensitive || 0}</p>
                <p className="text-xs text-muted-foreground">Sensitive Tier</p>
              </div>
            </div>
            <p className="text-xs text-muted-foreground mt-4 text-center">
              Sensitive meetings undergo PII redaction via Presidio before storage.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
