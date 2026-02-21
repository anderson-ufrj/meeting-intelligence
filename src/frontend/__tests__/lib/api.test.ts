import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  processTranscript,
  uploadTranscriptFile,
  searchMeetings,
  listMeetings,
  getMeeting,
  getTranscript,
  getStats,
  healthCheck,
} from "@/lib/api";

// Mock global fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

beforeEach(() => {
  mockFetch.mockReset();
});

describe("processTranscript", () => {
  it("sends POST with correct body", async () => {
    const mockResponse = { meeting_id: "m1", status: "processed" };
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const result = await processTranscript({
      title: "Test Meeting",
      tier: "ordinary",
      transcript: "Alice: Hello",
    });

    expect(mockFetch).toHaveBeenCalledWith("/api/v1/meetings/process", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: "Test Meeting",
        tier: "ordinary",
        transcript: "Alice: Hello",
      }),
    });
    expect(result).toEqual(mockResponse);
  });

  it("throws on non-ok response", async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      text: () => Promise.resolve("Bad request"),
    });

    await expect(
      processTranscript({ title: "X", tier: "ordinary", transcript: "Y" })
    ).rejects.toThrow("Bad request");
  });
});

describe("uploadTranscriptFile", () => {
  it("sends POST with FormData (no explicit Content-Type)", async () => {
    const mockResponse = { meeting_id: "m1", status: "processed", source_format: "vtt" };
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const file = new File(["WEBVTT\n\n00:00:01.000 --> 00:00:05.000\nHello"], "meeting.vtt", {
      type: "text/vtt",
    });

    const result = await uploadTranscriptFile({
      file,
      title: "Sprint Review",
      tier: "ordinary",
    });

    expect(mockFetch).toHaveBeenCalledWith("/api/v1/meetings/upload", {
      method: "POST",
      body: expect.any(FormData),
    });
    // Should NOT have explicit Content-Type header (browser sets it with boundary)
    const callArgs = mockFetch.mock.calls[0][1];
    expect(callArgs.headers).toBeUndefined();
    expect(result).toEqual(mockResponse);
  });

  it("throws on non-ok response", async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      text: () => Promise.resolve("Unsupported file type"),
    });

    const file = new File(["bad"], "file.exe");

    await expect(
      uploadTranscriptFile({ file, title: "Test", tier: "ordinary" })
    ).rejects.toThrow("Unsupported file type");
  });
});

describe("searchMeetings", () => {
  it("sends GET with query param", async () => {
    const mockResponse = { query: "sprint", results: [] };
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const result = await searchMeetings("sprint");

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/v1/meetings/search?q=sprint"
    );
    expect(result).toEqual(mockResponse);
  });

  it("includes tier param when provided", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ query: "test", results: [] }),
    });

    await searchMeetings("test", "sensitive");

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/v1/meetings/search?q=test&tier=sensitive"
    );
  });

  it("throws on error", async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      text: () => Promise.resolve("Search failed"),
    });

    await expect(searchMeetings("fail")).rejects.toThrow("Search failed");
  });
});

describe("listMeetings", () => {
  it("defaults to ordinary tier", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ tier: "ordinary", meetings: [] }),
    });

    await listMeetings();

    expect(mockFetch).toHaveBeenCalledWith("/api/v1/meetings?tier=ordinary");
  });

  it("accepts custom tier", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ tier: "sensitive", meetings: [] }),
    });

    await listMeetings("sensitive");

    expect(mockFetch).toHaveBeenCalledWith("/api/v1/meetings?tier=sensitive");
  });
});

describe("getMeeting", () => {
  it("fetches specific meeting", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ metadata: { meeting_id: "m1" } }),
    });

    const result = await getMeeting("m1");

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/v1/meetings/m1?tier=ordinary"
    );
    expect(result.metadata.meeting_id).toBe("m1");
  });

  it("uses provided tier", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({}),
    });

    await getMeeting("m1", "sensitive");

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/v1/meetings/m1?tier=sensitive"
    );
  });
});

describe("getTranscript", () => {
  it("fetches transcript", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({ meeting_id: "m1", transcript: "Hello" }),
    });

    const result = await getTranscript("m1");
    expect(result.transcript).toBe("Hello");
  });

  it("returns null on error", async () => {
    mockFetch.mockResolvedValue({ ok: false });

    const result = await getTranscript("m1");
    expect(result).toBeNull();
  });
});

describe("getStats", () => {
  it("fetches stats", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ total_meetings: 5 }),
    });

    const result = await getStats();
    expect(result.total_meetings).toBe(5);
  });
});

describe("healthCheck", () => {
  it("fetches health status", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({ status: "healthy", redis: "connected" }),
    });

    const result = await healthCheck();
    expect(result.status).toBe("healthy");
  });
});
