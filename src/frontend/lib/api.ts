export async function processTranscript(data: {
  title: string;
  tier: string;
  transcript: string;
}) {
  const res = await fetch("/api/v1/meetings/process", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function searchMeetings(query: string, tier?: string) {
  const params = new URLSearchParams({ q: query });
  if (tier) params.set("tier", tier);
  const res = await fetch(`/api/v1/meetings/search?${params}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function listMeetings(tier = "ordinary") {
  const res = await fetch(`/api/v1/meetings?tier=${tier}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getMeeting(meetingId: string, tier = "ordinary") {
  const res = await fetch(`/api/v1/meetings/${meetingId}?tier=${tier}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getTranscript(meetingId: string, tier = "ordinary") {
  const res = await fetch(`/api/v1/meetings/${meetingId}/transcript?tier=${tier}`);
  if (!res.ok) return null;
  return res.json();
}

export async function healthCheck() {
  const res = await fetch("/api/health");
  return res.json();
}
