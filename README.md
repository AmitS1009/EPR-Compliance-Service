# GreenPack Industries EPR Compliance Service

Small FastAPI backend for GreenPack Industries, a fictional Indian plastic packaging producer. It accepts monthly plastic declarations, reconciles them against mock ERP procurement records, and answers plain-English EPR questions using a small RAG corpus.

## What Is Included

- `POST /submit`: deterministic payload validation and declaration storage. No LLM call is made here.
- `GET /summary/{producer_id}/{month}`: reconciles declaration quantities against ERP procurement and uses Groq to produce a short compliance narrative.
- `POST /ask`: answers EPR questions from a local RAG corpus with document/section citations, or returns `I do not know based on the provided documents`.

## Tech Choices

- API framework: FastAPI with Pydantic validation.
- Storage: SQLite at `data/greenpack.sqlite3`. It is simple, file-backed, and enough for a small assignment service.
- ERP feed: CSV at `data/mock_erp_feed.csv`.
- LLM: Groq chat completions, default model `llama-3.1-8b-instant`. I chose Groq because it is fast, inexpensive for demos, and has a simple OpenAI-like chat flow.
- Embedding model: local TF-IDF bag-of-words embeddings implemented in `app/rag.py`. I chose this over a hosted embedding API so the RAG retrieval layer is auditable, deterministic, and runnable without another vendor key.
- Vector store: in-memory local vector store built from `data/rag_corpus/policy_docs.json` at app startup.
- AI coding assistant: Codex was used to scaffold the FastAPI service, refactor the endpoint boundaries, and write the README/demo script.

The policy corpus is intentionally small and mock/fabricated for the assignment. Source notes are embedded in `data/rag_corpus/policy_docs.json`; in production I would replace these with official CPCB notifications, Gazette rules, and company-approved SOPs.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set:

```bash
GROQ_API_KEY=your_actual_groq_key
```

The app has an offline fallback when the key is missing so local smoke tests still run, but the intended LLM provider is Groq.

## Run The API

```bash
uvicorn app.main:app --reload
```

Open the docs at:

```text
http://127.0.0.1:8000/docs
```

## Demo Script

In another terminal:

```bash
chmod +x scripts/demo.sh
./scripts/demo.sh
```

The script calls all three assignment endpoints in sequence: submit, summary, and ask.

## Sample Curl Calls

Submit a declaration:

```bash
curl -X POST http://127.0.0.1:8000/submit \
  -H "Content-Type: application/json" \
  -d '{
    "producer_id": "GREENPACK-001",
    "month": "2026-04",
    "declared_quantities_kg": {
      "rigid_plastic": 12000,
      "flexible_plastic": 8500,
      "multilayer_plastic": 3200
    }
  }'
```

Get reconciliation summary:

```bash
curl http://127.0.0.1:8000/summary/GREENPACK-001/2026-04
```

Ask an EPR question:

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What should GreenPack do when a monthly category variance is greater than five percent?"}'
```

## Reconciliation Logic

The service compares declared kilograms with procured kilograms for each supported category:

- `rigid_plastic`
- `flexible_plastic`
- `multilayer_plastic`

A category is flagged when the absolute variance is greater than 5% of ERP procurement quantity. The LLM receives the already computed reconciliation JSON and is asked only to write the 3-5 sentence human-readable narrative.

## Run Tests

```bash
pytest
```

## Loom Video Checklist

Record a 90-second Loom covering:

1. Quick demo of one endpoint working end-to-end, preferably `POST /submit` followed by `GET /summary/GREENPACK-001/2026-04`.
2. A short clip of the AI coding assistant interaction that produced or refactored a section of the code.
3. One architecture trade-off: this implementation uses SQLite plus a local TF-IDF vector store instead of Postgres plus hosted embeddings, because the assignment benefits from a small, transparent service that reviewers can run quickly.

## What I Would Do Differently With Another Day

I would replace the mock policy corpus with official CPCB/Gazette documents, add document ingestion with chunk metadata, move declarations to Postgres, and add authenticated users plus role-based access for compliance officers.

## GitHub Submission

This folder is ready to become a public GitHub repository:

```bash
git init
git add .
git commit -m "Build GreenPack EPR compliance service"
git branch -M main
git remote add origin https://github.com/<your-user>/greenpack-epr-service.git
git push -u origin main
```
