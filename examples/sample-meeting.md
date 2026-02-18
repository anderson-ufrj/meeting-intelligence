--- Microsoft Teams Meeting Transcript ---
Meeting: StormGeo AI Platform — Technical Architecture Review
Date: 2025-02-18
Participants: Lars Erik Jordet, Luis Duarte, Anderson Silva, Nina Winther-Kaland, Erik Haugen

[00:00:12] Lars Erik Jordet: Good morning everyone. Today we're reviewing the proposed architecture for our new AI-powered weather intelligence platform. Luis, please walk us through the current state and the gaps we need to address.

[00:00:35] Luis Duarte: Thanks Lars. Currently our forecasting pipeline is a monolithic .NET application that processes meteorological data from 14 sources. The main bottleneck is that adding new data sources requires modifying the core pipeline — it takes about three weeks per integration. We need a modular architecture that allows plug-and-play data source connectors.

[00:01:10] Anderson Silva: I've been analyzing the requirements. I propose we move to an event-driven architecture with a multi-agent system. Each data source gets a dedicated ingestion agent that normalizes data into a common schema. A master orchestrator routes the data through the processing pipeline — quality checks, spatial interpolation, and model inference.

[00:01:45] Nina Winther-Kaland: What's the expected impact on time-to-market for new integrations?

[00:01:55] Anderson Silva: With the agent-based approach and standardized connectors, a new data source integration drops from three weeks to about two days. The connector template handles authentication, rate limiting, retry logic, and schema mapping. The agent registers itself with the orchestrator automatically.

[00:02:25] Lars Erik Jordet: That's impressive. What about the LLM components? Luis mentioned we want natural language querying of our forecast data.

[00:02:40] Luis Duarte: Right. Shipping clients want to ask questions like "What's the optimal route from Rotterdam to Singapore avoiding storms next week?" instead of navigating complex dashboards. We need a RAG system over our historical forecast data combined with real-time conditions.

[00:03:10] Anderson Silva: For the RAG pipeline, I recommend a hybrid approach. We use sentence-transformers for embedding the forecast summaries and route analyses into a vector store — Redis with the vector search module. For the generation layer, we use Claude with structured output via Instructor to ensure responses include confidence intervals and data citations.

[00:03:45] Erik Haugen: How do we handle the real-time aspect? Weather data changes every six hours for global models and hourly for regional models.

[00:04:00] Anderson Silva: The ingestion agents publish events to a message queue. The vector store has a time-weighted indexing strategy — recent embeddings get higher relevance scores. We also maintain a sliding window cache for the most queried routes and regions. Cache invalidation is triggered by new forecast cycles.

[00:04:35] Nina Winther-Kaland: What about data governance? Our energy clients have strict requirements about data residency and audit trails.

[00:04:50] Anderson Silva: We implement a two-tier data classification system. Ordinary data — public forecasts, general route suggestions — flows through the standard pipeline. Sensitive data — client-specific contracts, proprietary trading positions — gets PII redaction via Presidio and stays in region-specific storage. Every query is logged with full provenance tracking.

[00:05:20] Lars Erik Jordet: The two-tier approach makes sense. It mirrors how we handle data classification in our existing systems. What's the technology stack?

[00:05:38] Anderson Silva: Backend: FastAPI with Python for the AI pipeline, async processing with Redis queues. The agent framework uses a custom orchestrator with circuit breakers and health monitoring. Frontend: Next.js with TypeScript for the dashboard. Infrastructure: Docker on Railway for the AI services, with Azure for the core meteorological compute.

[00:06:10] Luis Duarte: I like that we keep Azure for the heavy compute but use Railway for the AI services. It gives us faster iteration cycles on the AI components without touching the production forecasting infrastructure.

[00:06:32] Nina Winther-Kaland: Timeline estimate?

[00:06:38] Anderson Silva: Phase one — core pipeline with three data sources and basic RAG: eight weeks. Phase two — full agent system with ten sources and natural language querying: additional six weeks. Phase three — production hardening, monitoring, and client onboarding: four weeks. Total: 18 weeks to production.

[00:07:05] Lars Erik Jordet: That's aggressive but achievable. I want to see a proof of concept with the RAG pipeline working on historical North Sea forecast data within two weeks. That will validate the core approach before we commit to the full timeline.

[00:07:28] Luis Duarte: Agreed. The North Sea data is well-structured and we have five years of historical forecasts. Perfect for a POC.

[00:07:42] Nina Winther-Kaland: Budget-wise, this fits within the AI initiative allocation. I'll approve the POC phase immediately. Full project approval after we see the POC results. Anderson, can you prepare a detailed technical specification by Friday?

[00:08:00] Anderson Silva: Absolutely. I'll include the architecture diagrams, API specifications, and the evaluation criteria for the POC.

[00:08:15] Lars Erik Jordet: Excellent. Let's reconvene in two weeks for the POC demo. Good discussion everyone.

--- End of Transcript ---
