"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { searchMeetings } from "@/lib/api";

type SearchResult = {
  meeting_id: string;
  title: string;
  tier: string;
  summary: string;
  similarity: number;
};

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError("");
    setResults([]);
    setSearched(true);

    try {
      const data = await searchMeetings(query);
      setResults(data.results ?? []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-4xl space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Semantic Search</CardTitle>
          <CardDescription>
            Search across all processed meetings using natural language. Powered by OpenAI
            embeddings stored in Redis.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="flex gap-2">
            <Input
              placeholder="e.g. route optimization decisions, API monitoring alerts..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              aria-label="Search query"
              className="flex-1"
            />
            <Button type="submit" disabled={loading || !query.trim()}>
              {loading ? "Searching..." : "Search"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {loading && (
        <div className="space-y-3">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      )}

      {error && (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      )}

      {!loading && searched && results.length === 0 && !error && (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            No matching meetings found. Try a different query or process more transcripts.
          </CardContent>
        </Card>
      )}

      {results.length > 0 && (
        <div className="space-y-3">
          {results.map((r) => (
            <Card key={r.meeting_id}>
              <CardContent className="pt-6">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium text-sm">{r.title}</h3>
                      <Badge
                        variant={r.tier === "sensitive" ? "destructive" : "secondary"}
                      >
                        {r.tier}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{r.summary}</p>
                  </div>
                  <Badge variant="outline" className="shrink-0">
                    {(r.similarity * 100).toFixed(0)}% match
                  </Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
