"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { processTranscript } from "@/lib/api";
import {
  FileText,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  Users,
  ListChecks,
  MessageSquare,
  ClipboardList,
} from "lucide-react";

const EXAMPLE_TRANSCRIPT = `--- Microsoft Teams Meeting Transcript ---
Meeting: Weekly Standup — Shipping Route Optimization
Date: 2025-01-15
Participants: Lars Erik Jordet, Maria Chen, Johan Berg, Aisha Patel

[00:00:12] Lars Erik Jordet: Good morning everyone. Let's start with the sprint update. Johan, how's the route optimization model looking?

[00:00:25] Johan Berg: The new weather integration is working well. We reduced fuel estimation error from 8.2% to 3.1% by incorporating the 72-hour wave height forecast.

[00:00:58] Lars Erik Jordet: That's a significant improvement. Are we ready to push this to staging?

[00:01:05] Johan Berg: Yes, but we need Maria's review on the API changes first.

[00:01:18] Maria Chen: I'll review it this afternoon. The authentication part should be straightforward.

[00:01:35] Aisha Patel: Quick question — when do we update the documentation?

[00:01:48] Lars Erik Jordet: Good catch. Let's make that part of the Definition of Done.

[00:02:12] Maria Chen: I noticed we don't have monitoring alerts for the forecast API.

[00:02:28] Lars Erik Jordet: That's a problem. Can you create an alert for API failures?

[00:02:35] Maria Chen: Will do. I'll set it up in Datadog with a P2 priority.

[00:02:52] Lars Erik Jordet: Targeting end of next week for production, pending QA sign-off.

[00:03:38] Lars Erik Jordet: Meeting adjourned. Thanks everyone!

--- End of Transcript ---`;

type ProcessResult = {
  meeting_id: string;
  tier: string;
  insights: {
    meeting_title: string;
    summary: string;
    decisions: { topic: string; decision: string; deciders: string[]; confidence: number }[];
    action_items: { task: string; owner: string; deadline?: string; priority?: string }[];
    key_topics: { name: string; importance: string }[];
    open_questions: { question: string; context: string }[];
  };
  sentiments: {
    speaker: string;
    overall_sentiment: string;
    confidence: number;
    key_phrases: string[];
  }[];
  audit_log: Record<string, unknown>[];
};

export default function ProcessPage() {
  const [title, setTitle] = useState("Weekly Standup — Shipping Route Optimization");
  const [tier, setTier] = useState("ordinary");
  const [transcript, setTranscript] = useState("");
  const [result, setResult] = useState<ProcessResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleProcess() {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await processTranscript({ title, tier, transcript });
      setResult(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Processing failed");
    } finally {
      setLoading(false);
    }
  }

  function loadExample() {
    setTranscript(EXAMPLE_TRANSCRIPT);
    setTitle("Weekly Standup — Shipping Route Optimization");
    setTier("ordinary");
  }

  return (
    <div className="max-w-5xl space-y-6">
      {/* Input */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
              <FileText className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle>Process Transcript</CardTitle>
              <CardDescription>
                Paste a Microsoft Teams transcript to extract decisions, action items, and sentiment.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-3">
            <Input
              placeholder="Meeting title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              aria-label="Meeting title"
              className="flex-1"
            />
            <select
              value={tier}
              onChange={(e) => setTier(e.target.value)}
              aria-label="Privacy tier"
              className="h-9 rounded-md border border-input bg-transparent px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="ordinary">Ordinary</option>
              <option value="sensitive">Sensitive (PII Redacted)</option>
            </select>
          </div>

          <Textarea
            placeholder="Paste your Teams transcript here..."
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            rows={14}
            aria-label="Meeting transcript"
            className="font-mono text-xs leading-relaxed"
          />

          <div className="flex items-center gap-2">
            <Button onClick={handleProcess} disabled={loading || !transcript.trim()} size="lg">
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Processing...
                </>
              ) : (
                "Process Transcript"
              )}
            </Button>
            <Button variant="outline" onClick={loadExample} size="lg">
              Load Example
            </Button>
          </div>

          {error && (
            <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 px-4 py-3 rounded-lg" role="alert">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Loading skeleton */}
      {loading && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <Skeleton className="h-10 w-10 rounded-lg" />
              <div className="space-y-2">
                <Skeleton className="h-5 w-64" />
                <Skeleton className="h-4 w-96" />
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <Skeleton className="h-10 w-80" />
            <Skeleton className="h-40 w-full" />
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {result && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500/10">
                <CheckCircle2 className="h-5 w-5 text-emerald-500" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <CardTitle>{result.insights.meeting_title}</CardTitle>
                  <Badge variant={result.tier === "sensitive" ? "destructive" : "secondary"}>
                    {result.tier}
                  </Badge>
                </div>
                <CardDescription className="mt-1">{result.insights.summary}</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="decisions">
              <TabsList className="w-full justify-start">
                <TabsTrigger value="decisions" className="gap-1.5">
                  <ListChecks className="h-3.5 w-3.5" />
                  Decisions ({result.insights.decisions.length})
                </TabsTrigger>
                <TabsTrigger value="actions" className="gap-1.5">
                  <ClipboardList className="h-3.5 w-3.5" />
                  Actions ({result.insights.action_items.length})
                </TabsTrigger>
                <TabsTrigger value="sentiment" className="gap-1.5">
                  <Users className="h-3.5 w-3.5" />
                  Sentiment ({result.sentiments.length})
                </TabsTrigger>
                <TabsTrigger value="audit" className="gap-1.5">
                  <MessageSquare className="h-3.5 w-3.5" />
                  Audit
                </TabsTrigger>
              </TabsList>

              <TabsContent value="decisions" className="mt-4">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Topic</TableHead>
                      <TableHead>Decision</TableHead>
                      <TableHead>Deciders</TableHead>
                      <TableHead className="w-20 text-right">Conf.</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {result.insights.decisions.map((d, i) => (
                      <TableRow key={i}>
                        <TableCell className="font-medium">{d.topic}</TableCell>
                        <TableCell>{d.decision}</TableCell>
                        <TableCell className="text-muted-foreground text-sm">
                          {d.deciders.join(", ")}
                        </TableCell>
                        <TableCell className="text-right">
                          <Badge variant="outline">{(d.confidence * 100).toFixed(0)}%</Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                    {result.insights.decisions.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={4} className="text-center text-muted-foreground">
                          No decisions extracted
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TabsContent>

              <TabsContent value="actions" className="mt-4">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Owner</TableHead>
                      <TableHead>Task</TableHead>
                      <TableHead>Deadline</TableHead>
                      <TableHead>Priority</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {result.insights.action_items.map((a, i) => (
                      <TableRow key={i}>
                        <TableCell className="font-medium">{a.owner}</TableCell>
                        <TableCell>{a.task}</TableCell>
                        <TableCell className="text-muted-foreground">{a.deadline || "\u2014"}</TableCell>
                        <TableCell>
                          {a.priority && <Badge variant="outline">{a.priority}</Badge>}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TabsContent>

              <TabsContent value="sentiment" className="mt-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {result.sentiments.map((s, i) => (
                    <div key={i} className="rounded-lg border p-4 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-sm">{s.speaker}</span>
                        <Badge
                          variant={
                            s.overall_sentiment === "positive"
                              ? "default"
                              : s.overall_sentiment === "negative"
                                ? "destructive"
                                : "secondary"
                          }
                        >
                          {s.overall_sentiment}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
                          <div
                            className="h-full rounded-full bg-primary transition-all"
                            style={{ width: `${s.confidence * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-muted-foreground w-10 text-right">
                          {(s.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      {s.key_phrases.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {s.key_phrases.map((p, j) => (
                            <span key={j} className="text-xs bg-muted px-2 py-0.5 rounded-full">
                              {p}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </TabsContent>

              <TabsContent value="audit" className="mt-4">
                <div className="space-y-2">
                  {result.audit_log.map((entry, i) => (
                    <div key={i} className="bg-muted/50 border p-3 rounded-lg font-mono text-xs">
                      <pre className="whitespace-pre-wrap">{JSON.stringify(entry, null, 2)}</pre>
                    </div>
                  ))}
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
