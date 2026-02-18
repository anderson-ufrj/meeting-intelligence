"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
    <div className="max-w-4xl space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Processed Meetings</CardTitle>
          <CardDescription>
            All meetings processed through the intelligence pipeline.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading && (
            <div className="space-y-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          )}

          {error && (
            <p className="text-sm text-destructive" role="alert">
              {error}
            </p>
          )}

          {!loading && !error && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Tier</TableHead>
                  <TableHead className="text-right">Decisions</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                  <TableHead className="text-right">Processed</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {meetings.map((m) => (
                  <TableRow key={m.meeting_id}>
                    <TableCell className="font-medium">
                      <Link
                        href={`/meetings/${m.meeting_id}`}
                        className="hover:underline"
                      >
                        {m.title}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Badge variant={m.tier === "sensitive" ? "destructive" : "secondary"}>
                        {m.tier}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">{m.decision_count}</TableCell>
                    <TableCell className="text-right">{m.action_count}</TableCell>
                    <TableCell className="text-right text-muted-foreground text-sm">
                      {new Date(m.processed_at).toLocaleDateString()}
                    </TableCell>
                  </TableRow>
                ))}
                {meetings.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                      No meetings processed yet. Go to{" "}
                      <Link href="/" className="underline">
                        Process
                      </Link>{" "}
                      to get started.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}

          {!loading && meetings.length > 0 && (
            <div className="mt-4 text-xs text-muted-foreground">
              {meetings.length} meeting{meetings.length !== 1 ? "s" : ""} stored in Redis
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
