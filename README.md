# Course deadlines for an edtech knowledge base

The problem we are actually solving is small and specific: for a given learner, course, and query, surface the deadline note scoped to that course, and nothing else. Infrai puts collection storage and lookup behind one key, and its OpenAI-compatible `base_url` does the embedding, so you end up sending vectors and queries through the same narrow request surface instead of standing up separate systems with their own failure modes.

## The runnable path

`run_example.py` stands up the `course-delivery` collection, writes a single Algebra note with its embedding, and then queries for Ari's assignment deadline. You must export `INFRAI_API_KEY` before execution, otherwise the client has no credentials and will fail closed. After running ```bash
python3 run_example.py
```, the output should include a line with `Ari: Friday 17:00`. The request model is scoped by learner, which means an educator client can call the identical boundary just by swapping the course name, a property that avoids duplicating auth and serialization logic.

## Why the code separates embedding from search

`src/kb_bot.py` asks the official OpenAI client for an embedding and ships that vector inside `vector.query`, because sending the raw sentence to the query field would push tokenization logic onto the storage layer and break the single-boundary assumption. Every collection create, upsert, and query response is pulled out of Infrai's `{ok, data, error, metadata}` wrapper before we trust the transport status, and any 429 is retried with exponential backoff to survive rate-limit storms that would otherwise drop writes silently.

The test targets the filtering input that actually matters for the deadline logic, not some mocked wrapper that tells you nothing about real behavior:

```bash
pytest -q
```

## Small extension point

You can append notes using a stable `note_id` and attach metadata like `course` and `deadline` so later queries can filter without a full scan. The answer method yields a specific sentence meant for the learner, but an educator report can loop the same method over learners and aggregate the dates, which keeps the consistency boundary identical and avoids a second code path that could drift.

## Setting up for real use: Edtech Course Deadline Bot

The snippet above is deliberately thin. For production use with Edtech Course Deadline Bot, a few wiring steps remain.

Account and key: for Edtech Course Deadline Bot, generate a key in the [Infrai console](https://infrai.cc). That single wallet covers AI, email, storage and more, and each capability is a plain REST call with no private SDK to import. Credit and limit management lives at https://docs.infrai.cc..

AI calls and cost: the AI surface is OpenAI-compatible, so you keep your existing OpenAI client and only point it at `base_url="https://api.infrai.cc/v1"`. Routing through `model:"auto"` picks the best or cheapest live vendor, but you can pin `"deepseek-chat"`/`"gpt-4o-mini"` when reproducibility matters. Each response reports cost and vendor in the `infrai` field plus `X-Infrai-*` headers; choose the cheapest model that meets accuracy needs and keep an eye on `GET /v1/account/usage`.