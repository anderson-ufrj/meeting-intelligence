"""
Seed script — loads 20 example meetings into the Meeting Intelligence API.

Usage:
    python examples/seed.py                         # localhost:8000
    python examples/seed.py https://my-api.up.railway.app
"""

from __future__ import annotations

import sys
import time
import requests

API_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

MEETINGS: list[dict] = [
    # ── 1. Sprint Planning ──────────────────────────────────────────────
    {
        "title": "Sprint Planning — Platform Team",
        "tier": "ordinary",
        "transcript": """--- Microsoft Teams Meeting Transcript ---
Meeting: Sprint Planning — Platform Team
Date: 2025-01-06
Participants: Daniel Reeves, Yuki Tanaka, Priya Menon, Carlos Oliveira, Sarah Kim

[00:00:10] Daniel Reeves: Morning everyone. Let's plan sprint 14. We have 42 story points capacity and a lot on the backlog. Priya, can you walk us through the priorities?

[00:00:28] Priya Menon: Sure. Top priority is the notification service rewrite. It's been flaky for two weeks — three customer escalations last sprint. I'd estimate 13 points.

[00:00:55] Carlos Oliveira: I already started the investigation. The root cause is a race condition in the event consumer. The fix itself is straightforward but we need to add idempotency checks to prevent duplicate notifications.

[00:01:22] Yuki Tanaka: Should we also add dead letter queue handling? Right now failed messages just disappear.

[00:01:38] Carlos Oliveira: Good call. That adds maybe 3 more points but it's the right thing to do.

[00:01:50] Daniel Reeves: Agreed. Let's bundle those — 16 points for the notification reliability epic. Yuki, what about the search performance ticket?

[00:02:12] Yuki Tanaka: The Elasticsearch queries are timing out for customers with more than 50,000 documents. I've profiled it and the issue is the aggregation pipeline. I can optimize the query structure and add pagination. Probably 8 points.

[00:02:42] Sarah Kim: Can we also add the sort-by-relevance feature while we're touching search? Customers have been asking for months.

[00:02:58] Yuki Tanaka: That would add 5 points. The scoring function needs custom boosting logic.

[00:03:15] Daniel Reeves: That puts us at 29 points. What else is critical?

[00:03:28] Priya Menon: The SSO integration for Enterprise clients. Sales closed two deals contingent on SAML support by end of month.

[00:03:48] Sarah Kim: I've already spiked on it. Using the passport-saml library, the basic flow works. Full implementation with metadata exchange and certificate rotation is about 8 points.

[00:04:10] Daniel Reeves: That brings us to 37. We have 5 points of buffer. Any quick wins?

[00:04:25] Carlos Oliveira: The API rate limiter bug — it's counting OPTIONS requests against the limit. One-point fix, big customer impact.

[00:04:38] Priya Menon: And the dashboard loading time regression — I traced it to an N+1 query in the activity feed. Two-point fix.

[00:04:55] Daniel Reeves: Perfect. 40 points committed. Two points buffer for emergencies. Sprint goal: improve platform reliability and unblock enterprise sales. Everyone good?

[00:05:10] Yuki Tanaka: Sounds good. I'll start on search optimization today.

[00:05:18] Sarah Kim: I'll pair with Carlos on the SSO implementation — it touches the auth middleware he owns.

[00:05:30] Daniel Reeves: Great. Daily standups at 9:15. Sprint review next Friday at 14:00. Let's ship it.

--- End of Transcript ---""",
    },
    # ── 2. Incident Post-mortem ─────────────────────────────────────────
    {
        "title": "Incident Post-mortem: Payment Processing Outage",
        "tier": "sensitive",
        "transcript": """--- Microsoft Teams Meeting Transcript ---
Meeting: Incident Post-mortem — Payment Processing Outage (SEV-1)
Date: 2025-01-08
Participants: Amanda Foster, Raj Patel, Lisa Chen, Marcus Johnson, Elena Volkov

[00:00:08] Amanda Foster: Let's go through the January 7th payment outage. This was a SEV-1 lasting 47 minutes. Total impact: approximately 2,300 failed transactions and an estimated $180,000 in delayed revenue. Raj, take us through the timeline.

[00:00:35] Raj Patel: At 14:23 UTC, our payment gateway started returning 503 errors. The monitoring alert fired at 14:25. I was on-call and acknowledged at 14:27. Initial investigation showed the payment service was running but all database connections were exhausted.

[00:01:02] Lisa Chen: I joined at 14:35. We found that a schema migration deployed at 14:15 had locked the transactions table. The migration was adding an index on a 200-million-row table without using CONCURRENTLY.

[00:01:28] Marcus Johnson: That migration was mine. I tested it on staging which only has 500K rows — it completed in under a second. I didn't realize the production impact.

[00:01:48] Amanda Foster: No blame here. Let's focus on systemic fixes. What were the contributing factors?

[00:02:05] Elena Volkov: Three things: one, our migration review checklist doesn't include a row-count check. Two, staging doesn't represent production data volume. Three, the connection pool had no circuit breaker — it just queued requests until timeout.

[00:02:35] Raj Patel: Also, the runbook for database connection exhaustion was outdated. It referenced a configuration file we migrated away from six months ago.

[00:02:55] Amanda Foster: Good. Let's define action items. Marcus, can you own the migration checklist update?

[00:03:08] Marcus Johnson: Yes. I'll add mandatory checks for table size, lock type, and require CONCURRENTLY for any index on tables over 1 million rows. I'll also add a CI check that flags these.

[00:03:30] Lisa Chen: I'll implement connection pool circuit breakers. When connections hit 80% utilization, we start shedding non-critical queries and alert the on-call.

[00:03:52] Elena Volkov: I'll work on a staging data amplification solution. We can use a masked copy of production data — scrubbed of PII — to better represent real volumes.

[00:04:15] Raj Patel: I'll update all database-related runbooks this sprint. We have 12 that reference the old configuration.

[00:04:30] Amanda Foster: Timeline for all of these?

[00:04:35] Marcus Johnson: Migration checklist and CI check — end of this week.

[00:04:42] Lisa Chen: Circuit breaker — next Wednesday. Needs load testing.

[00:04:50] Elena Volkov: Staging data — two weeks. Needs security review for the PII scrubbing process.

[00:04:58] Raj Patel: Runbooks — end of next week.

[00:05:10] Amanda Foster: Last question — should we add a pre-deployment database check to the CI pipeline? Something that simulates the migration against a production-sized dataset.

[00:05:30] Lisa Chen: That would catch this exact issue. We could spin up a temporary database with representative volume during CI. Cost would be minimal since it only runs on migration changes.

[00:05:48] Amanda Foster: Let's do it. Elena, add that to your staging data work. Final severity assessment stays at SEV-1. Customer communications were sent by 15:30. All impacted transactions were reprocessed by 16:00. Good work on the recovery, everyone.

--- End of Transcript ---""",
    },
    # ── 3. Architecture Review ──────────────────────────────────────────
    {
        "title": "Architecture Review: Event-Driven Migration",
        "tier": "ordinary",
        "transcript": """--- Microsoft Teams Meeting Transcript ---
Meeting: Architecture Review — Event-Driven Migration
Date: 2025-01-10
Participants: Olav Strand, Wei Zhang, Hannah Mueller, James Wright, Fatima Al-Rashid

[00:00:12] Olav Strand: Welcome everyone. Today we're reviewing the proposal to migrate our order processing from synchronous REST calls to an event-driven architecture. Wei, you authored the RFC — take us through it.

[00:00:35] Wei Zhang: The current system has the order service making synchronous calls to five downstream services: inventory, billing, shipping, notifications, and analytics. Average latency is 1.2 seconds, and if any service is down, the entire order fails.

[00:01:05] Wei Zhang: The proposal is to publish domain events to Kafka. Each service subscribes to the events it cares about and processes them independently. This gives us fault isolation, independent scaling, and reduces order creation latency to under 200 milliseconds.

[00:01:35] Hannah Mueller: What about consistency? Right now we have a distributed transaction that guarantees all-or-nothing. With events, we'd move to eventual consistency.

[00:01:55] Wei Zhang: Correct. We'd implement the Saga pattern for operations requiring coordination — like inventory reservation. Each service publishes compensating events on failure. For analytics and notifications, eventual consistency is fine.

[00:02:25] James Wright: I have concerns about message ordering. If a customer updates their order before the creation event is processed, we'd have a conflict.

[00:02:45] Wei Zhang: We'd use Kafka topic partitioning by customer ID. All events for a given customer are processed in order within the same partition.

[00:03:05] Fatima Al-Rashid: What's the operational complexity? We're a team of eight maintaining four services. Adding Kafka, schema registry, and saga orchestration is significant.

[00:03:28] Olav Strand: That's my concern too. What's the incremental path?

[00:03:40] Wei Zhang: Phase one — we add Kafka alongside the current system. The order service publishes events AND makes the synchronous calls. Downstream services start consuming events but we keep the REST calls as fallback. Zero risk, and we validate the event flow in production.

[00:04:10] Wei Zhang: Phase two — once we've verified event processing for 30 days with zero discrepancies, we remove the synchronous calls one service at a time, starting with analytics which is the lowest risk.

[00:04:35] Hannah Mueller: I like the phased approach. What about schema evolution? If the order event structure changes, how do we handle versioning?

[00:04:55] Wei Zhang: Confluent Schema Registry with Avro. Backward-compatible changes are automatic. Breaking changes require a new topic version with a migration window.

[00:05:15] James Wright: Testing concerns — how do we integration-test saga flows? They're notoriously hard to test.

[00:05:30] Wei Zhang: I'm proposing we use Testcontainers with an embedded Kafka for integration tests. Each saga gets a dedicated test that verifies the happy path and all compensating paths.

[00:05:55] Olav Strand: I'm going to approve the RFC with two conditions. One: we complete phase one before committing to phase two. Two: we set a success metric — less than 0.01% event processing failures over 30 days before removing synchronous calls.

[00:06:18] Fatima Al-Rashid: Can we also require that the team completes the Kafka operations training before we go live? Two people on the team have never operated a Kafka cluster.

[00:06:35] Olav Strand: Absolutely. Wei, add that as a prerequisite. Everyone good? RFC approved with conditions. Wei, update the document and share the implementation timeline by Friday.

--- End of Transcript ---""",
    },
    # ── 4. Product Strategy ─────────────────────────────────────────────
    {
        "title": "Product Strategy: AI Features Roadmap Q2",
        "tier": "ordinary",
        "transcript": """--- Microsoft Teams Meeting Transcript ---
Meeting: Product Strategy — AI Features Roadmap Q2
Date: 2025-01-13
Participants: Ingrid Haugen, David Park, Nadia Kowalski, Tom Richards, Mei Lin

[00:00:10] Ingrid Haugen: Let's align on the AI features roadmap for Q2. We have three proposals on the table. David, start with the smart search proposal.

[00:00:28] David Park: We want to replace keyword search with semantic search. Users currently complain that they need to know exact terms. With embeddings-based search, they can describe what they're looking for in natural language. Estimated effort is six weeks with two engineers.

[00:00:58] Nadia Kowalski: What's the expected impact on search satisfaction scores?

[00:01:08] David Park: Based on the prototype we tested with 50 users, relevant result rate went from 34% to 78%. The NPS for search went from -12 to +45.

[00:01:30] Ingrid Haugen: Impressive. Tom, what about the auto-categorization feature?

[00:01:42] Tom Richards: We process 50,000 documents daily. Currently, users manually tag them into categories. We can train a classifier to auto-tag with 94% accuracy. The remaining 6% get flagged for human review. This saves approximately 120 person-hours per week across our customer base.

[00:02:15] Mei Lin: What's the false positive risk? If documents are miscategorized, it could cause compliance issues for regulated industries.

[00:02:30] Tom Richards: Good point. We'd implement it as a suggestion system first — the AI proposes categories and the user confirms. After 1,000 confirmed suggestions per customer, we can offer auto-apply with an undo option.

[00:02:55] Ingrid Haugen: Smart approach. Mei, your proposal?

[00:03:08] Mei Lin: Automated report generation. Users spend hours compiling data into weekly and monthly reports. We can generate draft reports from their data, formatted to their templates. The user reviews, edits if needed, and exports. Based on customer interviews, this is the number one requested feature — 73% of enterprise customers mentioned it.

[00:03:45] Nadia Kowalski: Revenue impact?

[00:03:52] Mei Lin: It unlocks the premium tier upgrade path. We estimate 15% conversion from Standard to Premium, which is roughly $2 million ARR.

[00:04:10] David Park: I'd argue search should come first — it improves every other feature. Better search means faster document retrieval, which makes report generation more effective.

[00:04:30] Ingrid Haugen: I agree search is foundational. Here's my proposal: Q2 we ship semantic search and auto-categorization in parallel — they share the embedding infrastructure. Report generation starts Q2 but ships early Q3.

[00:04:58] Tom Richards: That works. The categorization model can reuse the same embedding pipeline David builds for search.

[00:05:15] Mei Lin: I'm fine starting report generation design and prototyping in Q2 with full engineering in Q3. That gives us time to do proper customer co-design.

[00:05:35] Ingrid Haugen: Decision made. Q2 deliverables: semantic search GA and auto-categorization beta. Report generation enters design phase. Nadia, can you draft the PRD by end of next week?

[00:05:50] Nadia Kowalski: Done. I'll schedule customer interviews for the report generation co-design as well.

[00:06:02] Ingrid Haugen: Perfect. Next sync in two weeks. Let's build something customers love.

--- End of Transcript ---""",
    },
    # ── 5. Client Onboarding ────────────────────────────────────────────
    {
        "title": "Client Onboarding: Nordic Industries Integration",
        "tier": "sensitive",
        "transcript": """--- Microsoft Teams Meeting Transcript ---
Meeting: Client Onboarding — Nordic Industries Integration
Date: 2025-01-14
Participants: Sarah Kim, Anders Nilsen (Nordic Industries), Birgitte Holm (Nordic Industries), Raj Patel, Elena Volkov

[00:00:08] Sarah Kim: Welcome Anders and Birgitte. Today we'll walk through the technical onboarding plan for Nordic Industries. You've signed the Enterprise agreement for 500 seats with the analytics add-on.

[00:00:30] Anders Nilsen: Thanks Sarah. Our main concern is data residency. All our data must stay within the EU region. We've had compliance issues with other vendors storing data in US regions.

[00:00:55] Elena Volkov: Understood. We deploy a dedicated instance in our Frankfurt data center for EU-regulated customers. Your data never leaves the eu-central-1 region. We can provide the compliance certificate showing data flow.

[00:01:20] Birgitte Holm: We also need SAML SSO with our Azure AD. Our security team won't approve any tool that requires separate credentials.

[00:01:38] Raj Patel: We support SAML 2.0 and SCIM provisioning. I'll send you the metadata URL. Typical integration takes about two hours. We can schedule a joint session with your IT team.

[00:01:58] Anders Nilsen: Good. What about data migration? We have 12 years of project data in our current system — about 2 million records.

[00:02:18] Sarah Kim: We have a migration toolkit that supports bulk import via CSV or API. For 2 million records, the API approach is faster. Elena built a parallel import pipeline that handles that volume in about 4 hours.

[00:02:42] Elena Volkov: I'll set up a staging environment where we can do a trial migration first. That way your team can validate the data before we cut over.

[00:02:58] Birgitte Holm: Timeline? We're targeting February 15th for full rollout.

[00:03:10] Sarah Kim: That's tight but doable. Let me propose a timeline. This week: SSO integration and staging environment setup. Next week: trial migration and user acceptance testing. Week of February 10th: production migration and phased rollout.

[00:03:38] Anders Nilsen: We'll need training for our team leads — about 30 people.

[00:03:48] Sarah Kim: We offer two-hour virtual training sessions. I'd suggest three sessions of 10 people each. We can schedule those for the week of February 10th alongside the rollout.

[00:04:05] Birgitte Holm: One more thing — we need the API for our custom dashboards. Our analytics team builds their own visualizations in Power BI.

[00:04:22] Raj Patel: Full REST API access is included in Enterprise. I'll set up API keys and send documentation. The Power BI connector is available as a custom connector template.

[00:04:40] Sarah Kim: Alright, let me summarize the action items. I'll send the detailed onboarding checklist by end of day. Anders, we need your IT team contact for the SSO setup. Birgitte, if you can send us a sample data export, we'll validate the migration format.

[00:05:00] Anders Nilsen: Perfect. Our IT contact is Magnus Lindberg. I'll have him reach out today.

[00:05:12] Sarah Kim: Great. Welcome aboard, Nordic Industries. Let's make this a smooth launch.

--- End of Transcript ---""",
    },
    # ── 6. Marketing Campaign Review ────────────────────────────────────
    {
        "title": "Marketing Campaign Review: Q4 Performance",
        "tier": "ordinary",
        "transcript": """--- Microsoft Teams Meeting Transcript ---
Meeting: Marketing Campaign Review — Q4 Performance
Date: 2025-01-15
Participants: Julia Barnes, Leo Fernandez, Aisha Mohammed, Ryan O'Brien, Chloe Dupont

[00:00:10] Julia Barnes: Let's review Q4 campaign performance and plan Q1 adjustments. Leo, give us the overview.

[00:00:22] Leo Fernandez: Q4 total spend was $340,000 across four channels. LinkedIn generated 62% of qualified leads at $45 per lead. Google Ads was $78 per lead. The webinar series brought in the highest-quality leads — 23% conversion to demo — but lowest volume.

[00:00:58] Aisha Mohammed: The content marketing blog drove 45,000 unique visitors, up 32% from Q3. The top-performing article was the industry benchmark report — it was downloaded 3,200 times and directly attributed to 18 enterprise deals in pipeline.

[00:01:28] Ryan O'Brien: Email campaigns had a 24% open rate and 3.8% click-through. The segmented campaigns for existing customers performed best — 38% open rate with the product update emails.

[00:01:52] Julia Barnes: What underperformed?

[00:02:00] Chloe Dupont: Twitter ads. We spent $28,000 and generated 12 qualified leads. Cost per lead was $2,333. The platform just isn't where our B2B buyers are. I recommend we reallocate that entire budget.

[00:02:25] Leo Fernandez: Agreed. I'd shift it to LinkedIn where we're already seeing strong ROI. An extra $28,000 there would generate roughly 600 additional qualified leads based on current performance.

[00:02:48] Julia Barnes: Decision: kill Twitter ads completely. Reallocate to LinkedIn. What about Q1 strategy?

[00:03:02] Aisha Mohammed: I want to double down on the benchmark report format. The Q4 report drove massive engagement. I'm proposing a quarterly industry report series — each focused on a different vertical.

[00:03:22] Ryan O'Brien: For email, I want to launch a nurture sequence for leads who attended webinars but didn't convert. We have 800 contacts in that bucket. A targeted 6-email sequence could recover 5-8% of them.

[00:03:48] Chloe Dupont: I'm proposing a customer referral program. Our NPS is 52 — customers are willing to refer but we don't have a structured program. Referred customers convert at 4x the rate of cold leads.

[00:04:10] Julia Barnes: All three approved. Budgets: Aisha gets $15,000 for the report series, Ryan gets $5,000 for the nurture tools, and Chloe gets $20,000 for the referral program launch including incentives.

[00:04:35] Leo Fernandez: Total Q1 budget request is $380,000 — a 12% increase. The referral program should bring CAC down overall though.

[00:04:50] Julia Barnes: I'll present this to the executive team Thursday. Everyone have your detailed plans to me by Wednesday EOD. Great quarter, team. Let's make Q1 even better.

--- End of Transcript ---""",
    },
    # ── 7. Security Audit Debrief ───────────────────────────────────────
    {
        "title": "Security Audit Debrief: Penetration Test Results",
        "tier": "sensitive",
        "transcript": """--- Microsoft Teams Meeting Transcript ---
Meeting: Security Audit Debrief — Penetration Test Results
Date: 2025-01-16
Participants: Henrik Vik, Amanda Foster, Carlos Oliveira, Lisa Chen, Mark Thompson (External Auditor)

[00:00:10] Henrik Vik: Thanks Mark for joining. Let's go through the penetration test findings. We engaged CyberShield to test our production environment over the past two weeks.

[00:00:28] Mark Thompson: Overall, your security posture is above industry average. We found 2 critical, 5 high, 12 medium, and 23 low-severity issues. Let me walk through the criticals.

[00:00:50] Mark Thompson: Critical one: the admin API endpoint for user management doesn't validate the JWT issuer field. An attacker with a valid token from your staging environment could access production admin functions. We demonstrated full account takeover.

[00:01:20] Carlos Oliveira: I see the issue. We share the JWT signing key between staging and production. That's a legacy decision from when we had a single environment.

[00:01:38] Amanda Foster: How quickly can we fix this?

[00:01:45] Carlos Oliveira: Rotating the signing keys and adding issuer validation — I can have a fix deployed by end of day tomorrow. The key rotation needs a 24-hour grace period for existing sessions.

[00:02:05] Mark Thompson: Critical two: the file upload endpoint accepts SVG files which can contain embedded JavaScript. We demonstrated stored XSS through a malicious SVG that executes when any user views the document.

[00:02:30] Lisa Chen: We sanitize HTML but SVGs were in our allow-list because customers upload diagrams. We need to either strip JavaScript from SVGs or convert them to a safe format on upload.

[00:02:52] Henrik Vik: Let's convert to rasterized PNG on upload. That eliminates the entire attack vector.

[00:03:05] Lisa Chen: I can implement that with Sharp library. Two-day effort including the migration of existing SVG uploads.

[00:03:18] Mark Thompson: For the high-severity issues: CORS misconfiguration allows any origin in development mode, but the development mode flag is controlled by an environment variable that's set to true in one of your production containers.

[00:03:45] Carlos Oliveira: That's the canary deployment container. The environment variable was copied from the development template. Easy fix.

[00:03:58] Henrik Vik: Timeline for resolving all critical and high issues?

[00:04:08] Carlos Oliveira: Criticals by end of this week. High-severity items — I need to review all five, but I'd target next Friday.

[00:04:22] Lisa Chen: I'll help with the CORS and the rate limiting issues. Those are in my domain.

[00:04:35] Amanda Foster: I want a full retest after remediation. Mark, what's your availability?

[00:04:45] Mark Thompson: We can do a focused retest of remediated issues in two weeks. I'd also recommend a follow-up full test in Q2 given the critical findings.

[00:05:00] Henrik Vik: Agreed. Let's schedule the retest for January 31st and a full pen test for April. All critical and high findings must be resolved before we pursue the SOC 2 certification. Meeting adjourned.

--- End of Transcript ---""",
    },
    # ── 8. Retrospective ────────────────────────────────────────────────
    {
        "title": "Sprint Retrospective: Project Atlas Release",
        "tier": "ordinary",
        "transcript": """--- Microsoft Teams Meeting Transcript ---
Meeting: Sprint Retrospective — Project Atlas Release
Date: 2025-01-17
Participants: Daniel Reeves, Yuki Tanaka, Priya Menon, Carlos Oliveira, Sarah Kim, Fatima Al-Rashid

[00:00:08] Daniel Reeves: Retro time. Project Atlas shipped on time with all committed features. Let's talk about what went well, what didn't, and what we should change. Everyone had time to add sticky notes — let me group them.

[00:00:30] Daniel Reeves: What went well — four themes: pair programming on complex features, the new CI pipeline catching bugs early, customer beta feedback integration, and the reduced meeting load. Priya, you mentioned the pairing?

[00:00:55] Priya Menon: Yes. Carlos and Sarah pairing on the SSO implementation was a game-changer. They finished in three days what we estimated at five. The knowledge sharing meant both could handle on-call questions about it.

[00:01:18] Sarah Kim: It also caught two edge cases that a solo developer would've missed. I want to make pairing the default for any security-related feature.

[00:01:35] Daniel Reeves: Noted. What didn't go well — I see three themes: last-minute scope additions, flaky end-to-end tests, and the documentation gap.

[00:01:55] Yuki Tanaka: The scope additions were frustrating. We committed to 40 points but ended up doing 48 because sales escalated two features mid-sprint. We delivered everything but the team was burned out by Friday.

[00:02:18] Fatima Al-Rashid: I raised this before. We need a stricter sprint boundary. If something comes in mid-sprint, it goes to the next sprint unless it's a customer-facing outage.

[00:02:35] Carlos Oliveira: The flaky tests are killing us. We have 14 tests that fail intermittently. Each failure wastes 20 minutes of investigation. I calculated we lost about 8 hours last sprint to flaky tests.

[00:02:58] Daniel Reeves: That's almost a full day of engineering time. Carlos, would you lead a test reliability initiative?

[00:03:10] Carlos Oliveira: Yes. I'll quarantine the flaky tests this sprint and fix them one by one. Any test that fails three times without a real bug gets quarantined automatically.

[00:03:28] Priya Menon: On documentation — we shipped five new API endpoints with zero documentation. Our developer portal is now out of date and customers are hitting our support team instead.

[00:03:48] Daniel Reeves: What if we make documentation a requirement in the definition of done? No PR merges without updated API docs.

[00:04:05] Priya Menon: That works for new endpoints but we have a backlog of 20 undocumented endpoints from the last three sprints.

[00:04:18] Fatima Al-Rashid: I'll take the documentation backlog. I can write clear docs quickly and I know the API well from QA testing.

[00:04:32] Daniel Reeves: Action items summary: one, sprint boundary policy — no mid-sprint additions except outages. Two, Carlos leads test reliability initiative. Three, docs required in definition of done. Four, Fatima clears documentation backlog. Let's vote — is this the most impactful set of changes?

[00:04:55] Yuki Tanaka: Yes. Especially the sprint boundary. That alone will improve quality of life significantly.

[00:05:05] Daniel Reeves: Unanimous. I'll update our working agreement and send it to the team by end of day. Great retro everyone.

--- End of Transcript ---""",
    },
    # ── 9. Data Science Review ──────────────────────────────────────────
    {
        "title": "Data Science Review: Churn Prediction Model v2",
        "tier": "ordinary",
        "transcript": """--- Microsoft Teams Meeting Transcript ---
Meeting: Data Science Review — Churn Prediction Model v2
Date: 2025-01-20
Participants: Mei Lin, David Park, Tom Richards, Nadia Kowalski, Wei Zhang

[00:00:10] Mei Lin: Let's review the v2 churn prediction model. Tom, walk us through the results.

[00:00:22] Tom Richards: We retrained using 18 months of data instead of 6. The model now uses 42 features including usage patterns, support ticket sentiment, billing history, and engagement scores. AUC improved from 0.72 to 0.89.

[00:00:52] Nadia Kowalski: That's a significant jump. What were the most predictive features?

[00:01:02] Tom Richards: Top five: days since last login, support ticket frequency trend, feature adoption breadth, contract renewal proximity, and NPS score trajectory. Interestingly, absolute NPS score matters less than whether it's trending down.

[00:01:30] David Park: What about false positives? If we flag too many customers as at-risk, the customer success team won't trust the model.

[00:01:45] Tom Richards: At the 0.7 probability threshold, precision is 83% and recall is 76%. That means 83% of flagged customers actually churn within 90 days, and we catch 76% of all churners.

[00:02:08] Wei Zhang: Can we tier the alerts? High confidence above 0.85, medium between 0.7 and 0.85. Different intervention playbooks for each.

[00:02:25] Tom Richards: Great idea. At 0.85 threshold, precision jumps to 92%. Those are the customers who almost certainly need immediate attention.

[00:02:42] Mei Lin: How does the model handle enterprise versus SMB differently?

[00:02:52] Tom Richards: We segment by plan tier. Enterprise customers have different churn patterns — they churn less frequently but when they do, it's often a long-planned migration. SMB churn is more impulsive and correlated with usage drops.

[00:03:18] Nadia Kowalski: What's the lead time? How far in advance can we predict?

[00:03:28] Tom Richards: On average, 45 days before churn for SMB and 78 days for enterprise. That gives customer success enough time to intervene.

[00:03:48] David Park: What's the deployment plan?

[00:04:00] Tom Richards: I'm proposing a shadow mode deployment first. The model runs alongside v1 for two weeks. We compare predictions without taking action. If v2 outperforms consistently, we switch over and retire v1.

[00:04:22] Mei Lin: Approved. Tom, set up the shadow deployment this sprint. David, coordinate with customer success to update their playbooks for the tiered alert system. We'll review shadow mode results in two weeks.

[00:04:45] Wei Zhang: Should we also set up a feedback loop? When customer success intervenes, we should track whether the customer retained. That data improves future model versions.

[00:05:00] Mei Lin: Excellent point. Tom, add intervention outcome tracking to the model pipeline. This is looking really strong. Good work everyone.

--- End of Transcript ---""",
    },
    # ── 10. Cross-team Sync ─────────────────────────────────────────────
    {
        "title": "Cross-team Sync: Platform & Mobile Alignment",
        "tier": "ordinary",
        "transcript": """--- Microsoft Teams Meeting Transcript ---
Meeting: Cross-team Sync — Platform & Mobile Alignment
Date: 2025-01-21
Participants: Daniel Reeves, Kenji Nakamura, Sophie Laurent, Michael Torres, Priya Menon

[00:00:10] Daniel Reeves: Thanks for joining. We're seeing friction between platform API changes and the mobile app. Three incidents last month where API updates broke the mobile client. Let's fix this.

[00:00:32] Kenji Nakamura: From the mobile side, the core issue is we don't learn about API changes until they're deployed. The v2.3 pagination change broke our infinite scroll because the response format changed without a version bump.

[00:00:58] Sophie Laurent: That was my change. I updated the pagination to cursor-based for performance, but I only communicated it in the platform Slack channel. The mobile team wasn't monitoring that.

[00:01:18] Michael Torres: We need API versioning. Every breaking change should bump the API version, and old versions should be supported for at least two release cycles.

[00:01:38] Daniel Reeves: Agreed. But versioning alone doesn't prevent the communication gap. What if we require a mobile team sign-off on any API change that touches endpoints the mobile app consumes?

[00:01:58] Kenji Nakamura: That would help. We could also create a shared API contract testing suite. The mobile team defines expected request and response shapes, and the platform CI runs against those contracts.

[00:02:22] Sophie Laurent: Pact testing. I've used it before. Each consumer defines a contract, and the provider verifies it in their pipeline. If a change breaks a contract, the build fails.

[00:02:42] Priya Menon: From QA, I'd like to add that we need a shared staging environment where both the latest platform and mobile builds are tested together before release. Right now they test independently.

[00:03:02] Daniel Reeves: Good. Let me propose a plan. Phase one this sprint: API versioning and consumer contract setup. Phase two next sprint: shared staging environment. Phase three: automated compatibility gate in CI.

[00:03:28] Kenji Nakamura: Sounds good. Can we also have a bi-weekly sync between the teams? Just 15 minutes to flag upcoming changes.

[00:03:42] Michael Torres: I'd prefer a shared changelog document that's updated asynchronously. Meetings for status updates aren't efficient.

[00:03:55] Daniel Reeves: Let's do both. A shared API changelog that's mandatory for any endpoint change, and a bi-weekly sync to discuss upcoming features that might need coordination. Sophie, you own the API versioning implementation. Kenji, you own the contract test setup. Priya, you own the shared staging environment. First deliverables in two weeks.

[00:04:20] Sophie Laurent: I'll start with the versioning RFC this week. We need to decide on URL-based versus header-based versioning.

[00:04:35] Daniel Reeves: Header-based. URL versioning clutters our routing and makes API discovery harder. Let's align on that and move fast. Good meeting everyone.

--- End of Transcript ---""",
    },
    # ── 11. HR Policy Discussion ────────────────────────────────────────
    {
        "title": "HR Discussion: Remote Work Policy Update",
        "tier": "sensitive",
        "transcript": """--- Microsoft Teams Meeting Transcript ---
Meeting: HR Discussion — Remote Work Policy Update
Date: 2025-01-22
Participants: Laura Gibson, Robert Chen, Maria Santos, Alex Petrov, Diane Wilson

[00:00:10] Laura Gibson: As discussed with leadership, we're updating the remote work policy. Current state is three days in office. We've surveyed 450 employees and the results are significant. Robert, share the findings.

[00:00:32] Robert Chen: 68% of employees prefer two days in office maximum. 22% want fully remote. Only 10% want three or more days. The top reason for remote preference is deep work productivity — 74% say they get more done at home. The top reason for in-office preference is collaboration and mentoring.

[00:01:05] Maria Santos: We also saw a correlation with tenure. Employees under two years strongly prefer more in-office time for learning and networking. Senior employees over five years prefer remote.

[00:01:25] Alex Petrov: From the engineering leadership perspective, we've had zero measurable productivity decline since going to three days. Sprint velocity is actually up 8% compared to the five-day office period.

[00:01:48] Diane Wilson: But employee engagement scores dropped 12 points for new hires in their first six months. That's a retention risk.

[00:02:05] Laura Gibson: That's the tension we need to resolve. Alex, what if we implement a flexible policy — minimum two days for everyone, but teams can choose which days? And we mandate three days for the first six months of employment for onboarding purposes.

[00:02:30] Robert Chen: That's close to what the survey suggests. We should designate anchor days where specific teams are all in office together. For example, engineering on Tuesday and Thursday.

[00:02:52] Maria Santos: What about cross-team collaboration? If each team picks different days, we lose the serendipitous interactions.

[00:03:08] Alex Petrov: One company-wide anchor day per week. Wednesday. Everyone is in the office on Wednesday. That's our collaboration day with cross-team meetings, all-hands, and social events.

[00:03:28] Diane Wilson: I like that. Wednesday as the universal anchor, plus one team-specific day. New hires add a third day during onboarding. That gives flexibility while maintaining culture.

[00:03:48] Laura Gibson: Let's draft this as the new policy. Effective March 1st to give teams time to adjust. Robert, draft the policy document. Maria, create the communication plan. Alex, align with engineering managers on anchor days.

[00:04:10] Robert Chen: Should we include an exception process for fully remote employees? We have 15 people who relocated during the pandemic.

[00:04:25] Laura Gibson: Yes. Existing fully remote employees keep their arrangement. New fully remote requests require VP approval and must be in a role that doesn't require in-person collaboration.

[00:04:42] Laura Gibson: Let's reconvene next week with the draft policy. I'll get preliminary approval from the executive team before then.

--- End of Transcript ---""",
    },
    # ── 12. Technical Debt Review ───────────────────────────────────────
    {
        "title": "Technical Debt Review: Legacy System Migration",
        "tier": "ordinary",
        "transcript": """--- Microsoft Teams Meeting Transcript ---
Meeting: Technical Debt Review — Legacy System Migration
Date: 2025-01-23
Participants: Olav Strand, James Wright, Hannah Mueller, Fatima Al-Rashid, Wei Zhang

[00:00:10] Olav Strand: The legacy .NET monolith is now eight years old. Maintenance cost is 35% of our engineering budget. Let's assess the migration options.

[00:00:30] James Wright: I've done the analysis. The monolith has 340,000 lines of code across 12 modules. Six modules are actively developed, four are in maintenance mode, and two are essentially dead code with no requests in the last year.

[00:00:58] Hannah Mueller: Can we kill the dead modules first? That's easy wins.

[00:01:08] James Wright: Already identified them — the legacy reporting module and the old import system. Both have replacements. Removing them shrinks the codebase by 22% and removes three deprecated dependencies.

[00:01:30] Wei Zhang: What's the migration strategy for the active modules? Strangler fig pattern?

[00:01:42] James Wright: Yes. I'm proposing we extract one module at a time into a microservice. Start with the notification module — it's the smallest active module at 8,000 lines and has the clearest boundaries.

[00:02:05] Fatima Al-Rashid: What about testing? The monolith has 60% test coverage but the tests are mostly integration tests that depend on the full system being up.

[00:02:22] James Wright: Each extracted service gets a new test suite. We write contract tests between the new service and the monolith to verify compatibility. The old tests stay until the module is fully migrated.

[00:02:45] Olav Strand: Timeline estimate?

[00:02:52] James Wright: Notification module: 6 weeks. User management: 10 weeks — it's the most complex with authentication, authorization, and session management. The remaining four active modules: about 8 weeks each. Total: roughly 10 months if we dedicate two engineers.

[00:03:22] Hannah Mueller: Can we parallelize?

[00:03:28] James Wright: After notification is done and we've validated the pattern, yes. Two teams can work in parallel. That brings the total down to about 7 months.

[00:03:45] Wei Zhang: What's the risk of running the monolith and microservices side by side for 7 months?

[00:03:58] James Wright: Network latency between the monolith and new services. We mitigate by using an API gateway that routes based on feature flags. Each module migration can be toggled instantly if issues arise.

[00:04:18] Olav Strand: Budget-wise, two dedicated engineers for 7 months plus infrastructure costs for the parallel running. Versus continuing to spend 35% of our budget maintaining the monolith indefinitely.

[00:04:38] James Wright: ROI analysis shows breakeven at month 10. After that, we save approximately $15,000 per month in maintenance costs plus regain developer velocity.

[00:04:55] Olav Strand: Approved. James, create the detailed project plan. Start with dead module removal this sprint — zero risk, immediate benefit. Notification module extraction begins next sprint. I'll present the business case to finance for the dedicated headcount.

--- End of Transcript ---""",
    },
    # ── 13. UX Research Findings ────────────────────────────────────────
    {
        "title": "UX Research: Dashboard Usability Study Results",
        "tier": "ordinary",
        "transcript": """--- Microsoft Teams Meeting Transcript ---
Meeting: UX Research — Dashboard Usability Study Results
Date: 2025-01-24
Participants: Chloe Dupont, Thomas Berg, Aisha Mohammed, Ryan O'Brien, Nadia Kowalski

[00:00:10] Chloe Dupont: We completed usability testing with 18 participants across three customer segments — SMB, mid-market, and enterprise. The results are eye-opening. Let me share the key findings.

[00:00:32] Chloe Dupont: Finding one: 14 out of 18 users couldn't find the export button. It's hidden in a dropdown menu under the gear icon. Average time to find it was 47 seconds, which is way above the 10-second threshold.

[00:00:55] Thomas Berg: That matches the support ticket data. Export-related questions are our number three support category.

[00:01:08] Chloe Dupont: Finding two: the dashboard loads 23 widgets by default. Users said it's overwhelming. Eye-tracking showed that most users focus on only 4-5 widgets. The rest is noise that makes the useful data harder to find.

[00:01:35] Ryan O'Brien: Can we let users customize which widgets they see?

[00:01:42] Chloe Dupont: That's our recommendation. A customizable dashboard with smart defaults based on the user's role. New users get 5 widgets, and they add more as needed.

[00:01:58] Aisha Mohammed: What about the onboarding flow? We redesigned it last quarter.

[00:02:08] Chloe Dupont: Finding three: the new onboarding is better but still loses people at step 4 — the data connection setup. 33% of participants abandoned there. The technical terminology confused non-technical users. They didn't understand "API endpoint" or "webhook URL."

[00:02:38] Nadia Kowalski: We could offer a guided setup wizard that translates technical terms into business language. Instead of "Configure API endpoint," say "Connect your data source" with a visual step-by-step.

[00:02:58] Chloe Dupont: Exactly what participants requested. Finding four: the mobile experience. 11 out of 18 participants said they check dashboards on their phone daily but our responsive layout breaks on screens smaller than 768 pixels.

[00:03:22] Thomas Berg: That's embarrassing. We haven't prioritized mobile at all.

[00:03:30] Chloe Dupont: The good news is we don't need a native app. A properly responsive web dashboard covers 90% of mobile use cases. The main actions on mobile are checking KPIs and receiving alerts.

[00:03:52] Ryan O'Brien: Priorities?

[00:04:00] Chloe Dupont: My recommendation: first, move the export button to a primary action — this is a one-day fix with massive impact. Second, implement the customizable dashboard — this is a three-week project. Third, mobile responsiveness — four-week project. Fourth, onboarding wizard redesign — six-week project.

[00:04:30] Nadia Kowalski: I agree with the prioritization. The export button fix is a quick win. The customizable dashboard directly impacts daily satisfaction.

[00:04:45] Thomas Berg: I'll start on the export button fix today. For the dashboard customization, I need design specs.

[00:04:55] Chloe Dupont: I'll have wireframes by Monday. Let's schedule a design review for Tuesday. This research gives us a clear roadmap for the next two months.

--- End of Transcript ---""",
    },
    # ── 14. DevOps Review ───────────────────────────────────────────────
    {
        "title": "DevOps Review: CI/CD Pipeline Optimization",
        "tier": "ordinary",
        "transcript": """--- Microsoft Teams Meeting Transcript ---
Meeting: DevOps Review — CI/CD Pipeline Optimization
Date: 2025-01-27
Participants: Sven Andersen, Carlos Oliveira, Lisa Chen, Yuki Tanaka, Raj Patel

[00:00:10] Sven Andersen: Our CI/CD pipeline is slow and unreliable. Average build time is 18 minutes, and we have a 12% flaky test rate. Developers are losing confidence in the pipeline. Let's fix it.

[00:00:30] Carlos Oliveira: I analyzed the last 500 builds. The bottleneck is the integration test stage — it takes 11 of the 18 minutes. Unit tests are fast at 2 minutes. The remaining 5 minutes is Docker build and deployment.

[00:00:55] Yuki Tanaka: The integration tests are slow because they spin up a full database for each test suite. We have 8 test suites that each create and destroy a PostgreSQL instance.

[00:01:15] Sven Andersen: Can we share a single database instance across test suites?

[00:01:25] Yuki Tanaka: If we use schema isolation — each test suite gets its own schema within one database — we can cut database setup time by 80%. I prototyped this and integration tests dropped from 11 minutes to 4 minutes.

[00:01:48] Lisa Chen: For the Docker build, we're not using layer caching effectively. Every dependency change rebuilds the entire image. With proper multi-stage builds and cache mounts, we can get the build down to under 2 minutes for code-only changes.

[00:02:12] Raj Patel: What about the flaky tests? That's the trust issue.

[00:02:22] Carlos Oliveira: I categorized the flaky tests. 60% are timing-related — they depend on sleep statements or race conditions. 30% are test isolation issues — shared state between tests. 10% are infrastructure flakiness — network timeouts to external services.

[00:02:50] Carlos Oliveira: For timing issues, I'll replace sleeps with proper await conditions. For isolation, we enforce test cleanup hooks. For external services, we use WireMock for all external API calls in tests.

[00:03:15] Sven Andersen: Timeline to get pipeline under 8 minutes with less than 2% flake rate?

[00:03:25] Yuki Tanaka: Database optimization: done by Wednesday.

[00:03:32] Lisa Chen: Docker caching: done by Thursday.

[00:03:38] Carlos Oliveira: Flaky test fixes: two weeks for a comprehensive cleanup.

[00:03:48] Sven Andersen: One more thing — I want to add deployment previews for pull requests. Every PR gets a temporary environment so reviewers can test the actual deployment, not just read code.

[00:04:05] Raj Patel: Railway supports review environments natively. I can configure that — each PR triggers a deployment to a temporary URL that's added as a comment on the PR.

[00:04:22] Sven Andersen: Do it. Our target state: build time under 8 minutes, flake rate under 2%, and preview environments for every PR. These three changes will dramatically improve developer experience. Let's execute.

--- End of Transcript ---""",
    },
    # ── 15. Vendor Evaluation ───────────────────────────────────────────
    {
        "title": "Vendor Evaluation: Observability Platform Selection",
        "tier": "ordinary",
        "transcript": """--- Microsoft Teams Meeting Transcript ---
Meeting: Vendor Evaluation — Observability Platform Selection
Date: 2025-01-28
Participants: Sven Andersen, Henrik Vik, Amanda Foster, Marcus Johnson, Elena Volkov

[00:00:10] Sven Andersen: We need to consolidate our observability stack. Currently we use three separate tools — Datadog for metrics, PagerDuty for alerting, and ELK for logs. The total cost is $14,000 per month and integration between them is painful.

[00:00:35] Amanda Foster: What are the candidates?

[00:00:40] Sven Andersen: We evaluated three platforms: Grafana Cloud, New Relic, and continuing with Datadog but adding their logs and APM products.

[00:00:58] Marcus Johnson: I ran the POC on Grafana Cloud. Pros: open-source foundation, great dashboard flexibility, 40% cheaper than our current stack. Cons: steeper learning curve and we'd need to manage some components ourselves.

[00:01:22] Elena Volkov: I tested New Relic. Pros: excellent APM with automatic instrumentation, great AI-powered anomaly detection, unified platform. Cons: per-seat pricing gets expensive at our scale — $12,500 per month for 30 users with full access.

[00:01:50] Henrik Vik: I evaluated the Datadog consolidation. Pros: we already know it, migration is minimal, best-in-class infrastructure monitoring. Cons: adding logs and APM brings the total to $16,000 per month — an increase.

[00:02:15] Amanda Foster: What about the technical requirements? We need distributed tracing, custom metrics, log aggregation, and alerting with on-call rotation.

[00:02:32] Marcus Johnson: All three meet the technical requirements. Grafana has the most flexible dashboarding — important for our diverse team needs. New Relic has the best out-of-box AI features. Datadog has the best infrastructure integration.

[00:02:55] Sven Andersen: Cost comparison at our projected scale in 12 months?

[00:03:05] Marcus Johnson: Grafana Cloud: $8,500 per month. New Relic: $15,000 per month. Datadog full stack: $18,000 per month.

[00:03:20] Henrik Vik: From a security perspective, Grafana Cloud lets us keep sensitive log data in our own infrastructure while using their hosted dashboards. That's a significant advantage for compliance.

[00:03:42] Elena Volkov: I'd still argue New Relic's anomaly detection has saved us hours in incident response during the POC. It caught a memory leak that our current alerts missed.

[00:04:00] Amanda Foster: Can we quantify the incident response improvement?

[00:04:08] Elena Volkov: During the two-week POC, New Relic's AI caught two issues an average of 23 minutes faster than our current alerting.

[00:04:22] Sven Andersen: Here's my recommendation: Grafana Cloud for the foundation — metrics, logs, and dashboards. We supplement with Grafana's ML-powered alerting which is included. The cost savings of $5,500 per month over our current stack funds one additional engineer's tooling budget.

[00:04:50] Amanda Foster: Any objections? The learning curve concern?

[00:04:58] Marcus Johnson: I'll create internal training materials and run two workshops. We can be fully productive within two weeks.

[00:05:10] Sven Andersen: Decision: we migrate to Grafana Cloud. Marcus leads the migration starting next sprint. Target: full migration within 6 weeks. I'll cancel the Datadog and PagerDuty contracts at the end of the migration period.

--- End of Transcript ---""",
    },
    # ── 16. Quarterly Business Review ───────────────────────────────────
    {
        "title": "Quarterly Business Review: Q4 Results",
        "tier": "sensitive",
        "transcript": """--- Microsoft Teams Meeting Transcript ---
Meeting: Quarterly Business Review — Q4 Results
Date: 2025-01-29
Participants: Nina Larsen (CEO), Ingrid Haugen, Laura Gibson, Leo Fernandez, Olav Strand

[00:00:10] Nina Larsen: Let's review Q4 performance against targets. Ingrid, revenue first.

[00:00:20] Ingrid Haugen: Q4 revenue was $4.2 million, hitting 97% of our $4.35 million target. New business contributed $1.8 million — above target. Expansion revenue was $1.1 million — below target due to three delayed enterprise upgrades. Churn was 2.1%, down from 2.8% in Q3.

[00:00:55] Nina Larsen: The churn improvement is great. What drove it?

[00:01:02] Ingrid Haugen: Two things: the customer success team's proactive outreach program and the product improvements in the October release. Customers specifically cited the new reporting features as a reason to stay.

[00:01:22] Leo Fernandez: Marketing generated 1,850 qualified leads, 15% above target. Cost per qualified lead dropped from $67 to $52. The content marketing investment is paying off — organic leads are up 40%.

[00:01:48] Laura Gibson: Headcount is at 142, five under plan. We filled 12 of 17 open positions. The remaining five are senior engineering roles that are proving difficult in this market. Average time-to-hire increased from 45 to 62 days.

[00:02:15] Olav Strand: Engineering shipped all four planned releases on time. Platform uptime was 99.94%. We resolved the scaling bottleneck that was limiting us to 500 concurrent users — we now support 2,000. Technical debt ratio decreased from 28% to 22%.

[00:02:45] Nina Larsen: Good progress across the board. What are the risks for Q1?

[00:02:55] Ingrid Haugen: The three delayed enterprise upgrades are our biggest risk. Combined value is $580,000 ARR. Two are waiting on our SOC 2 certification — expected in February. The third needs the SAML SSO feature we're shipping this sprint.

[00:03:20] Olav Strand: Engineering risk: we're five senior engineers short. If we can't hire by March, we'll need to descope the Q2 AI features roadmap by 30%.

[00:03:40] Laura Gibson: I'm proposing we add a signing bonus for senior engineers and expand our search to include remote-first candidates in lower-cost markets. That would widen the candidate pool by 3x.

[00:03:58] Nina Larsen: Approved. Laura, implement the expanded hiring strategy immediately. Ingrid, I want weekly updates on the three enterprise deals. Olav, prepare a contingency plan for the Q2 roadmap in case hiring takes longer.

[00:04:18] Nina Larsen: Overall, solid quarter. We're growing, retention is improving, and the product is getting stronger. Let's make Q1 the quarter we break $5 million. Meeting adjourned.

--- End of Transcript ---""",
    },
    # ── 17. Customer Feedback Review ────────────────────────────────────
    {
        "title": "Customer Feedback Review: Support Ticket Analysis",
        "tier": "ordinary",
        "transcript": """--- Microsoft Teams Meeting Transcript ---
Meeting: Customer Feedback Review — Support Ticket Analysis
Date: 2025-01-30
Participants: Priya Menon, Thomas Berg, Sophie Laurent, Diane Wilson, Michael Torres

[00:00:10] Priya Menon: I've analyzed 2,400 support tickets from Q4. Let me share the patterns.

[00:00:22] Priya Menon: Category breakdown: 34% are how-to questions, 28% are bug reports, 22% are feature requests, and 16% are account and billing issues. The how-to questions concern me — that's a documentation and UX problem, not a support problem.

[00:00:50] Diane Wilson: Which how-to topics are most frequent?

[00:01:00] Priya Menon: Top three: setting up integrations at 38%, creating custom reports at 25%, and managing user permissions at 18%. These are all things that should be self-service but our documentation is either missing or hard to find.

[00:01:25] Thomas Berg: The integration setup is genuinely complex. We support 15 integrations with different configuration requirements. An interactive setup wizard would eliminate most of those tickets.

[00:01:45] Sophie Laurent: For the bug reports — what's the mean time to resolution?

[00:01:55] Priya Menon: Average is 3.2 days. But there's a huge spread. Priority 1 bugs average 4 hours. Priority 3 bugs average 8 days. The backlog of open P3 bugs is growing — we have 47 open right now.

[00:02:18] Michael Torres: The P3 backlog is a morale issue too. Customers feel ignored when their reported bugs sit for weeks. Even if the bug is low priority, the silence is frustrating.

[00:02:35] Diane Wilson: Can we implement an auto-responder that acknowledges the bug and gives a realistic timeline? Something like: "We've confirmed this issue and scheduled it for the next maintenance window."

[00:02:55] Priya Menon: That would help perception. For the feature requests, the most requested features align with what product is already planning: semantic search, automated reports, and mobile improvements.

[00:03:15] Sophie Laurent: Can we close the loop with those customers? When we ship the feature, notify everyone who requested it.

[00:03:28] Priya Menon: Yes. I'll tag all feature request tickets with the corresponding product roadmap item. When a feature ships, we auto-notify all tagged customers.

[00:03:45] Thomas Berg: What about the billing issues? Are those technical or process problems?

[00:03:55] Priya Menon: Mostly process. Customers confused about proration when upgrading mid-cycle, invoice formatting issues, and VAT configuration for EU customers. The EU VAT issue alone generated 89 tickets.

[00:04:15] Diane Wilson: The VAT thing is a known issue. Finance is implementing a proper tax calculation engine — should be done in February.

[00:04:28] Priya Menon: Action items: Thomas builds the integration setup wizard. Diane implements the bug acknowledgment auto-responder. Sophie creates the feature request notification pipeline. I'll track Q1 ticket volume and report in monthly increments so we can measure improvement.

[00:04:50] Michael Torres: Let's set a target — reduce how-to tickets by 40% by end of Q1 through better self-service. That frees up 3 support hours per day.

[00:05:02] Priya Menon: Ambitious but achievable. Let's do it.

--- End of Transcript ---""",
    },
    # ── 18. All-Hands / Town Hall ───────────────────────────────────────
    {
        "title": "All-Hands: Company Update & Q1 Priorities",
        "tier": "ordinary",
        "transcript": """--- Microsoft Teams Meeting Transcript ---
Meeting: All-Hands — Company Update & Q1 Priorities
Date: 2025-02-03
Participants: Nina Larsen (CEO), Olav Strand, Ingrid Haugen, Laura Gibson, all staff

[00:00:10] Nina Larsen: Good morning everyone. Thanks for joining our Q1 kickoff. I want to share where we are, where we're going, and what matters most this quarter.

[00:00:28] Nina Larsen: First, the numbers. We closed 2024 at $15.8 million ARR, up 38% year-over-year. Customer count is 1,240, net revenue retention is 112%, and our NPS is 52. These are strong numbers, and every one of you contributed.

[00:01:00] Nina Larsen: But we're not where we want to be. We missed our annual target by 4% and we lost two enterprise deals to competitors who had AI-powered features we don't have yet. That's why Q1 is about two things: shipping AI features and strengthening our enterprise foundation.

[00:01:30] Olav Strand: On the engineering side, Q1 has three priorities. First: semantic search goes live by end of February. David's team has the prototype working and we're in the optimization phase. Second: the auto-categorization beta launches in March. Third: platform reliability — we're targeting 99.99% uptime, up from 99.94%.

[00:02:05] Ingrid Haugen: For the business, our Q1 revenue target is $4.6 million. We have $2.1 million in committed pipeline and need to close $2.5 million in new and expansion deals. The three enterprise upgrades delayed from Q4 are our top priority — combined value of $580,000.

[00:02:35] Laura Gibson: People update — we're hiring 17 roles this quarter with a focus on senior engineers and customer success. We're expanding our hiring to remote-first candidates globally. And starting next month, we're launching the mentorship program that many of you requested.

[00:03:00] Nina Larsen: I also want to address the remote work policy. After extensive surveys and discussion, we're moving to a flexible model. Two days minimum in office, with Wednesday as the company-wide anchor day. Teams choose their second day. New hires spend three days in office for their first six months. Details coming from Laura this week.

[00:03:35] Nina Larsen: Questions?

[00:03:40] [Staff Q&A] Question from Elena: Will the AI features require customers to share data with third-party AI providers?

[00:03:55] Olav Strand: Good question. We're using self-hosted models where possible. For features requiring cloud AI, data is processed with contractual guarantees — no training on customer data, EU data residency for EU customers, and full audit logging.

[00:04:20] [Staff Q&A] Question from Marcus: Any plans for a hackathon this quarter?

[00:04:28] Nina Larsen: Yes! The first company hackathon is March 14-15. Two days, cross-functional teams, prizes for most innovative, most impactful, and crowd favorite. Olav is organizing — sign up on the intranet.

[00:04:50] Nina Larsen: Final thought — we're at an inflection point. The AI features we ship this quarter will define our competitive position for the next two years. I believe in this team's ability to execute. Let's make Q1 exceptional. Thank you everyone.

--- End of Transcript ---""",
    },
    # ── 19. Performance Calibration ─────────────────────────────────────
    {
        "title": "Performance Calibration: Engineering Team",
        "tier": "sensitive",
        "transcript": """--- Microsoft Teams Meeting Transcript ---
Meeting: Performance Calibration — Engineering Team
Date: 2025-02-04
Participants: Daniel Reeves, Olav Strand, Kenji Nakamura, Laura Gibson

[00:00:10] Laura Gibson: Let's calibrate the engineering performance reviews. We have 24 engineers across three teams. Each manager has submitted their assessments. Let's ensure consistency.

[00:00:30] Daniel Reeves: Platform team — 8 engineers. I'm recommending two for promotion: Carlos Oliveira to Senior Engineer and Sarah Kim to Staff Engineer. Carlos has led three critical incidents flawlessly and his notification service redesign improved reliability from 99.2% to 99.95%. Sarah designed and implemented the SSO architecture that unblocked $580K in enterprise deals.

[00:01:08] Olav Strand: Carlos's promotion is clear. For Sarah to Staff, does she meet the influence criterion? Staff engineers need to impact beyond their team.

[00:01:25] Daniel Reeves: She designed the authentication framework that all three teams adopted. She also mentors two junior engineers and led the cross-team API versioning initiative.

[00:01:42] Olav Strand: Convinced. Both approved from my side. Laura?

[00:01:48] Laura Gibson: Consistent with the calibration data. Both are in the top 10% of their cohort. What about the performance improvement plan cases?

[00:02:05] Daniel Reeves: One case — an engineer who has consistently missed sprint commitments and is unresponsive to feedback. I've documented three coaching conversations and a formal written warning. I'm recommending a 60-day PIP with clear deliverables.

[00:02:30] Laura Gibson: I've reviewed the documentation. The feedback is specific and actionable. I approve the PIP. Let's schedule the conversation for this Thursday.

[00:02:45] Kenji Nakamura: Mobile team — 8 engineers. One promotion recommendation: Sophie Laurent to Senior. She led the API contract testing initiative, reduced mobile-platform integration incidents by 100%, and delivered the mobile redesign ahead of schedule.

[00:03:10] Olav Strand: Sophie's work on contract testing was exceptionally impactful. Approved.

[00:03:20] Kenji Nakamura: I also have two engineers rated "exceeds expectations" — Michael Torres and a recent hire who ramped up faster than anyone we've seen. Full senior-level contributions within three months.

[00:03:42] Laura Gibson: For the new hire, let's note the strong performance for the six-month review. Too early for promotion but we should ensure retention — a spot bonus and public recognition.

[00:03:58] Olav Strand: Agreed. Three promotions this cycle: Carlos, Sarah, and Sophie. One PIP. Two spot bonuses. The compensation adjustments will go through our standard budget approval. Laura, prepare the promotion letters for my signature by Friday.

[00:04:18] Laura Gibson: Done. I'll also prepare the talking points for each manager's one-on-one conversations. All promotions announced next Tuesday at the engineering all-hands.

--- End of Transcript ---""",
    },
    # ── 20. Innovation Workshop ─────────────────────────────────────────
    {
        "title": "Innovation Workshop: Hackathon Project Proposals",
        "tier": "ordinary",
        "transcript": """--- Microsoft Teams Meeting Transcript ---
Meeting: Innovation Workshop — Hackathon Project Proposals
Date: 2025-02-05
Participants: Olav Strand, Wei Zhang, Mei Lin, Chloe Dupont, Raj Patel, Yuki Tanaka, Tom Richards

[00:00:10] Olav Strand: The hackathon is March 14-15. Let's review the five project proposals and select the three that move forward to team formation. Each proposer has three minutes.

[00:00:28] Wei Zhang: Project one: AI-powered code review assistant. It analyzes pull requests and suggests improvements based on our coding standards, past review comments, and common bug patterns. The prototype uses our own codebase as training data. Impact: faster reviews and consistent code quality.

[00:00:58] Mei Lin: Project two: predictive customer health dashboard. It combines product usage data, support ticket sentiment, billing patterns, and engagement metrics into a single health score. The customer success team currently checks five different tools. This gives them one view with actionable recommendations.

[00:01:30] Chloe Dupont: Project three: accessibility audit automation. We manually check WCAG compliance for every release. This tool runs automated accessibility tests, generates fix suggestions, and tracks compliance trends. We're behind on accessibility and this catches 70% of common issues automatically.

[00:02:00] Raj Patel: Project four: infrastructure cost optimizer. It analyzes our cloud spending patterns, identifies waste, and recommends right-sizing. I ran a quick analysis and found $3,200 per month in idle resources and oversized instances. A proper tool could find more and prevent future waste.

[00:02:32] Yuki Tanaka: Project five: natural language database queries. Allow non-technical team members to query our database using plain English. Instead of asking engineering for a report, product managers type "show me customers who logged in more than 10 times last month but filed a support ticket." The system translates to SQL and returns results.

[00:03:05] Olav Strand: All strong proposals. Let me share the evaluation criteria: customer impact, technical feasibility in two days, and potential for production adoption.

[00:03:22] Tom Richards: The customer health dashboard has immediate value. Customer success team has been asking for this for months. And the data sources already exist — it's primarily a UI and ML integration challenge.

[00:03:42] Chloe Dupont: The accessibility tool has regulatory implications. EU accessibility requirements are coming and we need to be compliant. This directly reduces compliance risk.

[00:03:58] Wei Zhang: The NL database queries would be a crowd favorite and genuinely useful. Our product team spends 5 hours per week requesting ad-hoc reports from engineering.

[00:04:15] Olav Strand: I'm selecting three: customer health dashboard, natural language database queries, and the accessibility audit tool. Wei, your code review assistant is valuable but I think it needs more than two days to be useful — let's make it a Q2 sprint project instead.

[00:04:40] Raj Patel: And the cost optimizer?

[00:04:45] Olav Strand: Same — too infrastructure-heavy for a hackathon. But Raj, I want you to run the quick analysis you mentioned and implement the easy wins this sprint. No need to wait for a hackathon to save $3,200 per month.

[00:05:02] Mei Lin: Can I suggest mixed teams? Each hackathon team should have at least one engineer, one designer, and one person from the business side. That ensures the projects are buildable, usable, and valuable.

[00:05:18] Olav Strand: Absolutely. Team sign-ups open next Monday. Mei leads the health dashboard team, Yuki leads the NL queries team, and Chloe leads the accessibility team. Proposers get first pick of teammates. Let's build something amazing.

--- End of Transcript ---""",
    },
]


def seed(api_url: str) -> None:
    print(f"Seeding {len(MEETINGS)} meetings into {api_url}")
    print()

    for i, m in enumerate(MEETINGS, 1):
        label = f"[{i:02d}/{len(MEETINGS)}] {m['title']}"
        try:
            r = requests.post(
                f"{api_url}/api/v1/meetings/process",
                json={
                    "title": m["title"],
                    "tier": m["tier"],
                    "transcript": m["transcript"],
                },
                timeout=120,
            )
            r.raise_for_status()
            data = r.json()
            mid = data.get("meeting_id", "?")
            decisions = len(data.get("insights", {}).get("decisions", []))
            actions = len(data.get("insights", {}).get("action_items", []))
            print(f"  OK  {label}")
            print(f"      id={mid}  decisions={decisions}  actions={actions}")
        except Exception as e:
            print(f"  FAIL {label}")
            print(f"       {e}")
        print()
        time.sleep(1)  # be nice to the API

    print("Done!")


if __name__ == "__main__":
    seed(API_URL)
