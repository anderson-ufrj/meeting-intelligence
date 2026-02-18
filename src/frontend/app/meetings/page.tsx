"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { listMeetings } from "@/lib/api";
import { LayoutDashboard, AlertTriangle, Inbox } from "lucide-react";

type MeetingSummary = {
  meeting_id: string;
  title: string;
  tier: string;
  processed_at: string;
  decision_count: number;
  action_count: number;
};

export default function MeetingsPage() {
  const [meetings, setMeetings] = useState<MeetingSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const data = await listMeetings();
        setMeetings(data.meetings ?? []);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to load meetings");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="max-w-5xl space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
              <LayoutDashboard className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle>Processed Meetings</CardTitle>
              <CardDescription>
                All meetings processed through the intelligence pipeline.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading && (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          )}

          {error && (
            <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 px-4 py-3 rounded-lg" role="alert">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          )}

          {!loading && !error && meetings.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <Inbox className="h-12 w-12 mb-3 opacity-50" />
              <p className="text-sm font-medium">No meetings processed yet</p>
              <p className="text-xs mt-1">
                Go to{" "}
                <Link href="/" className="text-primary underline">
                  Process
                </Link>{" "}
                to get started.
              </p>
            </div>
          )}

          {!loading && !error && meetings.length > 0 && (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Title</TableHead>
                    <TableHead className="w-24">Tier</TableHead>
                    <TableHead className="w-40 text-right">Processed</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {meetings.map((m) => (
                    <TableRow key={m.meeting_id} className="group">
                      <TableCell>
                        <Link
                          href={`/meetings/${m.meeting_id}`}
                          className="font-medium hover:text-primary transition-colors"
                        >
                          {m.title}
                        </Link>
                      </TableCell>
                      <TableCell>
                        <Badge variant={m.tier === "sensitive" ? "destructive" : "secondary"}>
                          {m.tier}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right text-muted-foreground text-sm whitespace-nowrap">
                        {new Date(m.processed_at).toLocaleString()}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              <div className="mt-4 pt-4 border-t flex items-center justify-between text-xs text-muted-foreground">
                <span>
                  {meetings.length} meeting{meetings.length !== 1 ? "s" : ""} in Redis
                </span>
                <span className="font-mono">namespace: ordinary</span>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
