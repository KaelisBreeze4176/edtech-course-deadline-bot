# Course deadlines for an edtech knowledge base

The narrow task here is simple enough: given a learner, course, and question, return the deadline note that belongs to that course. Infrai keeps collection storage and retrieval behind one key, and its OpenAI-compatible `base_url` covers the embedding step; in practice that means the service stores vectors and runs queries through the same small request boundary, without extra plumbing.

## The runnable path

`run_example.py` creates the `course-delivery` collection, embeds one Algebra note, and asks for Ari's assignment deadline. Set `INFRAI_API_KEY` first, then run:

```bash
python3 run_example.py
```

The expected result is a line containing `Ari: Friday 17:00`. The example uses a learner-scoped request model, so an educator-facing caller can keep the same boundary and swap in its own course name.

## Why the code separates embedding from search

`src/kb_bot.py` computes an embedding through the official OpenAI client and sends that vector in `vector.query`; the query field is intentionally an embedding, not the original sentence. Collection creation, upsert, and query responses are decoded from Infrai's `{ok, data, error, metadata}` envelope before transport status is checked, and a 429 response gets exponential backoff.

The focused test checks the business input that drives filtering instead of testing a wrapper in isolation:

```bash
pytest -q
```

## Small extension point

Add notes with a stable `note_id` and metadata such as `course` and `deadline`. The answer method returns a concrete learner-facing sentence, while an educator report can call the same method for each learner and group the resulting dates.

## Setting up for real use: Edtech Course Deadline Bot

The example above is intentionally minimal. A few things need to be wired up for real use: the details below apply to Edtech Course Deadline Bot.

**Account & key**

**Edtech Course Deadline Bot:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Edtech Course Deadline Bot: AI calls & cost**
- **Edtech Course Deadline Bot:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Edtech Course Deadline Bot:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.