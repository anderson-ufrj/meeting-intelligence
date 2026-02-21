"""File parsers for meeting transcript uploads.

Supports VTT, DOCX, DOC, PDF, and Markdown formats.
"""

import io
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Optional

from pypdf import PdfReader

ALLOWED_EXTENSIONS = {".vtt", ".docx", ".doc", ".pdf", ".md"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@dataclass
class ParseResult:
    """Result of parsing a transcript file."""

    text: str
    detected_title: Optional[str] = None
    detected_date: Optional[str] = None
    format: str = "unknown"


# ── VTT parser ──────────────────────────────────────────────────────────


def parse_vtt(content: bytes) -> ParseResult:
    """Parse a WebVTT file (Microsoft Teams transcript format).

    Extracts ``<v Speaker>`` tags and timestamps, normalizing to
    ``[HH:MM:SS] Speaker: Text`` format. Consecutive cues from the same
    speaker are merged.
    """
    import webvtt

    buf = io.StringIO(content.decode("utf-8-sig"))
    captions = list(webvtt.from_buffer(buf))

    lines: list[str] = []
    prev_speaker: Optional[str] = None
    prev_timestamp: Optional[str] = None

    for caption in captions:
        raw = caption.raw_text if hasattr(caption, "raw_text") else caption.text
        # Teams VTT uses <v Speaker Name>text</v>
        match = re.match(r"<v\s+([^>]+)>(.*?)(?:</v>)?$", raw, re.DOTALL)
        if match:
            speaker = match.group(1).strip()
            text = match.group(2).strip()
        else:
            speaker = None
            text = caption.text.strip()

        if not text:
            continue

        ts = caption.start  # e.g. "00:01:23.456"
        ts_short = ts.split(".")[0] if ts else ""

        if speaker and speaker == prev_speaker and lines:
            # Merge with previous line from same speaker
            lines[-1] += " " + text
        elif speaker:
            lines.append(f"[{ts_short}] {speaker}: {text}")
            prev_speaker = speaker
            prev_timestamp = ts_short
        else:
            lines.append(f"[{ts_short}] {text}")
            prev_speaker = None

    return ParseResult(text="\n".join(lines), format="vtt")


# ── DOCX parser ─────────────────────────────────────────────────────────


def parse_docx(content: bytes) -> ParseResult:
    """Parse a .docx file.

    Detects Teams transcript speaker patterns (``Speaker  HH:MM``) and
    normalizes them. Falls back to raw paragraph text.
    """
    from docx import Document

    doc = Document(io.BytesIO(content))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

    detected_title: Optional[str] = None
    detected_date: Optional[str] = None

    # Try to detect Teams transcript format: "Speaker Name  0:15"
    speaker_pattern = re.compile(r"^(.+?)\s{2,}(\d{1,2}:\d{2}(?::\d{2})?)$")

    lines: list[str] = []
    current_speaker: Optional[str] = None
    current_ts: Optional[str] = None

    for para in paragraphs:
        match = speaker_pattern.match(para)
        if match:
            current_speaker = match.group(1).strip()
            raw_ts = match.group(2).strip()
            # Normalize to HH:MM:SS
            parts = raw_ts.split(":")
            if len(parts) == 2:
                current_ts = f"00:{parts[0].zfill(2)}:{parts[1]}"
            else:
                current_ts = ":".join(p.zfill(2) for p in parts)
        elif current_speaker:
            lines.append(f"[{current_ts}] {current_speaker}: {para}")
        else:
            # No speaker context yet — could be a title or preamble
            if not detected_title:
                detected_title = para
            lines.append(para)

    return ParseResult(
        text="\n".join(lines),
        detected_title=detected_title,
        format="docx",
    )


# ── DOC parser (via antiword) ───────────────────────────────────────────


def parse_doc(content: bytes) -> ParseResult:
    """Parse a legacy .doc file using antiword.

    Writes the content to a temp file, invokes ``antiword``, and applies
    the same heuristic as the DOCX parser on the resulting text.
    """
    with tempfile.NamedTemporaryFile(suffix=".doc", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            ["antiword", tmp_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(f"antiword failed: {result.stderr.strip()}")
        text = result.stdout
    finally:
        os.unlink(tmp_path)

    return ParseResult(text=text.strip(), format="doc")


# ── PDF parser ──────────────────────────────────────────────────────────


def parse_pdf(content: bytes) -> ParseResult:
    """Parse a PDF file extracting text page-by-page."""
    reader = PdfReader(io.BytesIO(content))
    pages: list[str] = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text.strip())

    return ParseResult(text="\n\n".join(pages), format="pdf")


# ── Markdown parser ─────────────────────────────────────────────────────

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_markdown(content: bytes) -> ParseResult:
    """Parse a Markdown file.

    Extracts YAML frontmatter ``title`` and ``date`` if present.
    """
    text = content.decode("utf-8-sig").strip()

    detected_title: Optional[str] = None
    detected_date: Optional[str] = None

    fm_match = _FRONTMATTER_RE.match(text)
    if fm_match:
        fm_block = fm_match.group(1)
        for line in fm_block.splitlines():
            if line.lower().startswith("title:"):
                detected_title = line.split(":", 1)[1].strip().strip("\"'")
            elif line.lower().startswith("date:"):
                detected_date = line.split(":", 1)[1].strip().strip("\"'")
        # Remove frontmatter from body
        text = text[fm_match.end():]

    return ParseResult(
        text=text.strip(),
        detected_title=detected_title,
        detected_date=detected_date,
        format="md",
    )


# ── Router ──────────────────────────────────────────────────────────────


def parse_file(content: bytes, filename: str) -> ParseResult:
    """Route to the correct parser based on file extension."""
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}")

    parsers = {
        ".vtt": parse_vtt,
        ".docx": parse_docx,
        ".doc": parse_doc,
        ".pdf": parse_pdf,
        ".md": parse_markdown,
    }

    return parsers[ext](content)
