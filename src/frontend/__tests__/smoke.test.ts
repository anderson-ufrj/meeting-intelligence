import { describe, it, expect } from "vitest";

describe("Frontend Smoke Tests", () => {
  it("lib/api exports all required functions", async () => {
    const api = await import("@/lib/api");

    expect(typeof api.processTranscript).toBe("function");
    expect(typeof api.searchMeetings).toBe("function");
    expect(typeof api.listMeetings).toBe("function");
    expect(typeof api.getMeeting).toBe("function");
    expect(typeof api.getTranscript).toBe("function");
    expect(typeof api.getStats).toBe("function");
    expect(typeof api.healthCheck).toBe("function");
  });

  it("lib/utils exports cn utility", async () => {
    const utils = await import("@/lib/utils");
    expect(typeof utils.cn).toBe("function");
  });

  it("cn merges class names correctly", async () => {
    const { cn } = await import("@/lib/utils");

    expect(cn("foo", "bar")).toBe("foo bar");
    expect(cn("foo", undefined, "bar")).toBe("foo bar");
    expect(cn("px-2", "px-4")).toBe("px-4"); // tailwind-merge resolves conflicts
  });
});
