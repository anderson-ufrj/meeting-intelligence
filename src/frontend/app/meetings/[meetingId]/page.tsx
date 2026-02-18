"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
import { getMeeting, getTranscript } from "@/lib/api";
import {
  ArrowLeft,
  ListChecks,
  ClipboardList,
  Users,
  HelpCircle,
  Tag,
  AlertTriangle,
  FileText,
  Loader2,
} from "lucide-react";

type Decision = {
  topic: string;
  decision: string;
  deciders: string[];
  confidence: number;
};

type ActionItem = {
  task: string;
  owner: string;
  deadline?: string;
  priority?: string;
};

type Topic = {
  name: string;
  importance: string;
};

type OpenQuestion = {
  question: string;
  context?: string;
};

type Sentiment = {
  speaker: string;
  overall_sentiment: string;
  confidence: number;
  key_phrases: string[];
};

type MeetingDetail = {
  document: string;
  metadata: {
    meeting_id: string;
    tier: string;
    namespace: string;
    processed_at: string;
    title: string;
  };
  processed_meeting: {
    meeting_id: string;
    tier: string;
    insights: {
      meeting_title: string;
      meeting_date: string;
      summary: string;
      decisions: Decision[];
      action_items: ActionItem[];
      key_topics: Topic[];
      open_questions: OpenQuestion[];
    };
    sentiments: Sentiment[];
  };
};

export default function MeetingDetailPage() {
  const params = useParams();
  const meetingId = params.meetingId as string;
  const [data, setData] = useState<MeetingDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [transcript, setTranscript] = useState<string | null>(null);
  const [transcriptOpen, setTranscriptOpen] = useState(false);
  const [transcriptLoading, setTranscriptLoading] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        let res;
        try {
          res = await getMeeting(meetingId, "ordinary");
        } catch {
          res = await getMeeting(meetingId, "sensitive");
        }
        setData(res);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to load meeting");
      } finally {
        setLoading(false);
      }
    }
    if (meetingId) load();
  }, [meetingId]);

  if (loading) {
    return (
      <div className="max-w-5xl space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-5xl space-y-4">
        <Link href="/meetings">
          <Button variant="ghost" size="sm" className="gap-2">
            <ArrowLeft className="h-4 w-4" /> Back to meetings
          </Button>
        </Link>
        <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 px-4 py-3 rounded-lg" role="alert">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          {error || "Meeting not found"}
        </div>
      </div>
    );
  }

  const { insights, sentiments } = data.processed_meeting;
  const { metadata } = data;

  async function toggleTranscript() {
    if (transcriptOpen) {
      setTranscriptOpen(false);
      return;
    }
    if (transcript !== null) {
      setTranscriptOpen(true);
      return;
    }
    setTranscriptLoading(true);
    try {
      const res = await getTranscript(meetingId, metadata.tier);
      if (res?.transcript) {
        setTranscript(res.transcript);
        setTranscriptOpen(true);
      } else {
        setTranscript("");
      }
    } catch {
      setTranscript("");
    } finally {
      setTranscriptLoading(false);
    }
  }

  return (
    <div className="max-w-5xl space-y-6">
      {/* Back + Title */}
      <div className="space-y-3">
        <Link href="/meetings">
          <Button variant="ghost" size="sm" className="gap-2 -ml-2">
            <ArrowLeft className="h-4 w-4" /> Back to meetings
          </Button>
        </Link>
        <div className="flex items-start gap-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-xl font-bold">{insights.meeting_title}</h1>
              <Badge variant={metadata.tier === "sensitive" ? "destructive" : "secondary"}>
                {metadata.tier}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              Processed {new Date(metadata.processed_at).toLocaleString()}
              {insights.meeting_date && (
                <> &middot; Meeting date: {new Date(insights.meeting_date).toLocaleDateString()}</>
              )}
            </p>
          </div>
          <Badge variant="outline" className="font-mono text-[10px] shrink-0">
            {metadata.meeting_id}
          </Badge>
        </div>
      </div>

      {/* Summary */}
      <Card>
        <CardContent className="pt-6">
          <p className="text-sm leading-relaxed">{insights.summary}</p>
        </CardContent>
      </Card>

      {/* Transcript toggle */}
      <div className="flex justify-end">
        <Button
          variant="outline"
          size="sm"
          className="gap-2"
          onClick={toggleTranscript}
          disabled={transcriptLoading}
        >
          {transcriptLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <FileText className="h-4 w-4" />
          )}
          {transcriptOpen ? "Hide Transcript" : "View Full Transcript"}
        </Button>
      </div>

      {transcriptOpen && transcript !== null && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <FileText className="h-4 w-4" /> Full Transcript
            </CardTitle>
            <CardDescription>Original meeting transcript as submitted</CardDescription>
          </CardHeader>
          <CardContent>
            {transcript ? (
              <pre className="whitespace-pre-wrap text-xs leading-relaxed font-mono bg-muted p-4 rounded-lg max-h-[500px] overflow-y-auto">
                {transcript}
              </pre>
            ) : (
              <p className="text-sm text-muted-foreground py-4 text-center">
                Transcript not available for this meeting.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Card>
        <CardContent className="pt-6">
          <Tabs defaultValue="decisions">
            <TabsList className="w-full justify-start flex-wrap">
              <TabsTrigger value="decisions" className="gap-1.5">
                <ListChecks className="h-3.5 w-3.5" />
                Decisions ({insights.decisions.length})
              </TabsTrigger>
              <TabsTrigger value="actions" className="gap-1.5">
                <ClipboardList className="h-3.5 w-3.5" />
                Actions ({insights.action_items.length})
              </TabsTrigger>
              <TabsTrigger value="topics" className="gap-1.5">
                <Tag className="h-3.5 w-3.5" />
                Topics ({insights.key_topics.length})
              </TabsTrigger>
              {sentiments && sentiments.length > 0 && (
                <TabsTrigger value="sentiment" className="gap-1.5">
                  <Users className="h-3.5 w-3.5" />
                  Sentiment ({sentiments.length})
                </TabsTrigger>
              )}
              {insights.open_questions && insights.open_questions.length > 0 && (
                <TabsTrigger value="questions" className="gap-1.5">
                  <HelpCircle className="h-3.5 w-3.5" />
                  Questions ({insights.open_questions.length})
                </TabsTrigger>
              )}
            </TabsList>

            {/* Decisions */}
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
                  {insights.decisions.map((d, i) => (
                    <TableRow key={i}>
                      <TableCell className="font-medium">{d.topic}</TableCell>
                      <TableCell>{d.decision}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {d.deciders.join(", ")}
                      </TableCell>
                      <TableCell className="text-right">
                        <Badge variant="outline">{(d.confidence * 100).toFixed(0)}%</Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TabsContent>

            {/* Actions */}
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
                  {insights.action_items.map((a, i) => (
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

            {/* Topics */}
            <TabsContent value="topics" className="mt-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {insights.key_topics.map((t, i) => (
                  <div key={i} className="flex items-center justify-between border rounded-lg px-4 py-3">
                    <span className="text-sm font-medium">{t.name}</span>
                    <Badge
                      variant={
                        t.importance === "high" ? "default" :
                        t.importance === "medium" ? "secondary" : "outline"
                      }
                    >
                      {t.importance}
                    </Badge>
                  </div>
                ))}
              </div>
            </TabsContent>

            {/* Sentiment */}
            {sentiments && sentiments.length > 0 && (
              <TabsContent value="sentiment" className="mt-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {sentiments.map((s, i) => (
                    <div key={i} className="rounded-lg border p-4 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-sm">{s.speaker}</span>
                        <Badge
                          variant={
                            s.overall_sentiment === "positive" ? "default" :
                            s.overall_sentiment === "negative" ? "destructive" : "secondary"
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
            )}

            {/* Open Questions */}
            {insights.open_questions && insights.open_questions.length > 0 && (
              <TabsContent value="questions" className="mt-4">
                <div className="space-y-3">
                  {insights.open_questions.map((q, i) => (
                    <div key={i} className="border rounded-lg px-4 py-3 space-y-1">
                      <p className="text-sm font-medium">{q.question}</p>
                      {q.context && (
                        <p className="text-xs text-muted-foreground">{q.context}</p>
                      )}
                    </div>
                  ))}
                </div>
              </TabsContent>
            )}
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
