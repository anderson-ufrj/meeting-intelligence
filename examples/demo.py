"""Demo script showing the full pipeline end-to-end."""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from backend import MeetingPipeline
from backend.models import MeetingTranscript, TierClassification


console = Console()


def load_transcript(path: Path) -> str:
    """Load a transcript file."""
    with open(path, "r") as f:
        return f.read()


def demo_ordinary_meeting(pipeline: MeetingPipeline):
    """Process an ordinary tier meeting."""
    console.print(Panel("[bold green]ORDINARY TIER: Weekly Standup", expand=False))
    
    # Load transcript
    transcript_path = Path(__file__).parent / "ordinary" / "weekly_standup.txt"
    raw_text = load_transcript(transcript_path)
    
    # Create transcript model
    transcript = MeetingTranscript(
        meeting_id="standup_2025_01_15",
        title="Weekly Standup — Shipping Route Optimization",
        tier=TierClassification.ORDINARY,
        raw_text=raw_text
    )
    
    console.print("[dim]Processing through pipeline...[/dim]\n")
    
    # Process
    result = pipeline.process(transcript, user="demo_user")
    
    # Display results
    console.print(f"[bold]Meeting:[/bold] {result.insights.meeting_title}")
    console.print(f"[bold]Summary:[/bold] {result.insights.summary}\n")
    
    # Decisions table
    if result.insights.decisions:
        table = Table(title="Decisions")
        table.add_column("Topic", style="cyan")
        table.add_column("Decision", style="green")
        table.add_column("Deciders", style="yellow")
        
        for d in result.insights.decisions:
            table.add_row(d.topic, d.decision, ", ".join(d.deciders))
        
        console.print(table)
        console.print()
    
    # Action items table
    if result.insights.action_items:
        table = Table(title="Action Items")
        table.add_column("Owner", style="cyan")
        table.add_column("Task", style="green")
        table.add_column("Deadline", style="yellow")
        
        for a in result.insights.action_items:
            deadline = a.deadline or "—"
            table.add_row(a.owner, a.task, deadline)
        
        console.print(table)
        console.print()
    
    # Sentiment
    if result.sentiments:
        table = Table(title="Sentiment Analysis")
        table.add_column("Speaker", style="cyan")
        table.add_column("Sentiment", style="green")
        table.add_column("Confidence", style="yellow")
        
        for s in result.sentiments:
            emoji = {"positive": "😊", "neutral": "😐", "negative": "😞"}.get(
                s.overall_sentiment, "❓"
            )
            table.add_row(s.speaker, f"{emoji} {s.overall_sentiment}", 
                         f"{s.confidence:.2f}")
        
        console.print(table)
        console.print()
    
    console.print(f"[dim]Stored with vector ID: {result.vector_id}[/dim]\n")
    console.print("─" * 80 + "\n")


def demo_sensitive_meeting(pipeline: MeetingPipeline):
    """Process a sensitive tier meeting."""
    console.print(Panel("[bold red]SENSITIVE TIER: Executive Review (PII Redacted)", 
                       expand=False))
    
    # Load transcript
    transcript_path = Path(__file__).parent / "sensitive" / "executive_review.txt"
    raw_text = load_transcript(transcript_path)
    
    # Create transcript model
    transcript = MeetingTranscript(
        meeting_id="exec_review_2025_01_10",
        title="Q4 Executive Review",
        tier=TierClassification.SENSITIVE,
        raw_text=raw_text
    )
    
    console.print("[dim]Processing with PII redaction...[/dim]\n")
    
    # Process
    result = pipeline.process(transcript, user="demo_user")
    
    # Display results
    console.print(f"[bold]Meeting:[/bold] {result.insights.meeting_title}")
    console.print(f"[bold]Summary:[/bold] {result.insights.summary}\n")
    
    # Show audit trail
    table = Table(title="Audit Trail")
    table.add_column("Step", style="cyan")
    table.add_column("Details", style="green")
    table.add_column("Timestamp", style="dim")
    
    for entry in result.audit_log:
        details = []
        for k, v in entry.items():
            if k not in ["step", "timestamp"]:
                details.append(f"{k}: {v}")
        
        table.add_row(
            entry.get("step", "—"),
            "\n".join(details) if details else "—",
            entry.get("timestamp", "—")[:19]
        )
    
    console.print(table)
    console.print()
    
    # Show tier-specific storage
    console.print(f"[yellow]🔒 Stored in isolated namespace: {result.tier.value}[/yellow]")
    console.print(f"[dim]Vector ID: {result.vector_id}[/dim]\n")
    console.print("─" * 80 + "\n")


def demo_semantic_search(pipeline: MeetingPipeline):
    """Demonstrate semantic search across meetings."""
    console.print(Panel("[bold blue]SEMANTIC SEARCH", expand=False))
    
    queries = [
        "What decisions were made about route optimization?",
        "Who is responsible for compliance issues?",
        "What are the deadlines mentioned?"
    ]
    
    for query in queries:
        console.print(f"\n[bold]Query:[/bold] {query}")
        
        results = pipeline.search_meetings(query, n_results=2)
        
        if results:
            for r in results:
                tier_color = "green" if r["tier"] == "ordinary" else "red"
                console.print(f"  [{tier_color}]{r['tier'].upper()}[/{tier_color}] "
                            f"{r['title']} (score: {r['score']:.3f})")
                console.print(f"     {r['content_preview']}")
        else:
            console.print("  [dim]No results found[/dim]")
    
    console.print("\n" + "─" * 80 + "\n")


def main():
    """Run the full demo."""
    console.print(Panel.fit(
        "[bold]Meeting Intelligence Pipeline Demo[/bold]\n"
        "Two-tier architecture for StormGeo use case",
        border_style="blue"
    ))
    console.print()
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        console.print("[yellow]⚠ Warning: OPENAI_API_KEY not set. "
                     "Set it to run LLM extraction.[/yellow]\n")
    
    # Initialize pipeline
    console.print("[dim]Initializing pipeline...[/dim]\n")
    pipeline = MeetingPipeline()
    
    # Run demos
    demo_ordinary_meeting(pipeline)
    demo_sensitive_meeting(pipeline)
    demo_semantic_search(pipeline)
    
    console.print(Panel.fit(
        "[bold green]Demo complete![/bold green]\n"
        "Check the examples/ directory for transcript files and docs/ for architecture.",
        border_style="green"
    ))


if __name__ == "__main__":
    main()
