"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { searchMeetings } from "@/lib/api";
import { Search, Loader2, Inbox } from "lucide-react";

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

  function getSimilarityColor(score: number) {
    if (score >= 0.8) return "text-emerald-600 dark:text-emerald-400";
    if (score >= 0.5) return "text-amber-600 dark:text-amber-400";
    return "text-muted-foreground";
  }

  return (
    <div className="max-w-5xl space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
              <Search className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle>Semantic Search</CardTitle>
              <CardDescription>
                Search across all processed meetings using natural language.
                Powered by sentence-transformers embeddings stored in Redis.
              </CardDescription>
            </div>
          </div>
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
            <Button type="submit" disabled={loading || !query.trim()} size="lg">
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Search"
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {loading && (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-28 w-full" />
          ))}
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 px-4 py-3 rounded-lg" role="alert">
          {error}
        </div>
      )}

      {!loading && searched && results.length === 0 && !error && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-muted-foreground">
            <Inbox className="h-12 w-12 mb-3 opacity-50" />
            <p className="text-sm font-medium">No matching meetings found</p>
            <p className="text-xs mt-1">Try a different query or process more transcripts.</p>
          </CardContent>
        </Card>
      )}

      {results.length > 0 && (
        <div className="space-y-3">
          {results.map((r, idx) => (
            <Card key={r.meeting_id} className="transition-shadow hover:shadow-md">
              <CardContent className="pt-5 pb-4">
                <div className="flex items-start gap-4">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted text-xs font-mono font-bold shrink-0">
                    {idx + 1}
                  </div>
                  <div className="flex-1 min-w-0 space-y-1.5">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="font-semibold text-sm">{r.title}</h3>
                      <Badge
                        variant={r.tier === "sensitive" ? "destructive" : "secondary"}
                      >
                        {r.tier}
                      </Badge>
                    </div>
                    {r.summary && (
                      <p className="text-sm text-muted-foreground line-clamp-2">{r.summary}</p>
                    )}
                  </div>
                  <div className="text-right shrink-0">
                    <div className={`text-lg font-bold font-mono ${getSimilarityColor(r.similarity)}`}>
                      {(r.similarity * 100).toFixed(0)}%
                    </div>
                    <div className="text-[10px] text-muted-foreground">similarity</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
