# Document Chat — RAG Assistant

A production-grade Retrieval-Augmented Generation (RAG) application. Upload PDFs, DOCX, TXT, or
Markdown files; ask questions in a streaming, ChatGPT-style interface; get answers grounded in
your documents, with clickable citations back to the exact source chunk.

Built with **FastAPI + LangChain + FAISS + Groq** on the backend, and **React (Vite) + Tailwind
CSS v4** on the frontend.

![Status](https://img.shields.io/badge/status-complete-brightgreen) ![Backend tests](https://img.shields.io/badge/backend%20tests-42%20passing-brightgreen) ![Frontend tests](https://img.shields.io/badge/frontend%20tests-38%20passing-brightgreen)

## Features

- **Upload** PDF, DOCX, TXT, or Markdown documents (drag-and-drop or click-to-browse)
- **Ask questions** in natural language, answered strictly from your documents' content
- **Streaming responses** token-by-token over Server-Sent Events
- **Citations** — every claim links back to a specific document + chunk, with a hover/click
  popover showing the exact excerpt and match confidence
- **Conversation history** — persists across page refresh, clearable, downloadable as Markdown
- **Document management** — rename, delete, see size/date/status/chunk count per document
- **Markdown rendering + syntax-highlighted code blocks** in assistant responses
- **Dark mode**, fully responsive (mobile sidebar becomes a slide-over drawer)
- **Suggested questions** for a fast first interaction
- **Configurable retrieval** — chunk size, chunk overlap, `TOP_K`, and similarity threshold are
  all environment variables, not hardcoded
- **Swappable LLM provider** — Groq (default) or OpenAI, one `.env` line to switch

## Architecture

```
document-chat-rag/
├── backend/                       FastAPI + LangChain RAG service
│   ├── app/
│   │   ├── api/routes/            HTTP route handlers (thin — no business logic)
│   │   │   ├── documents.py       upload / list / rename / delete
│   │   │   ├── chat.py            chat (blocking + streaming) / history / clear
│   │   │   └── health.py
│   │   ├── services/              Orchestration layer between routes and rag/
│   │   │   ├── document_service.py
│   │   │   └── chat_service.py
│   │   ├── rag/                   The actual RAG pipeline
│   │   │   ├── loader.py          PDF / DOCX / TXT / MD text extraction
│   │   │   ├── chunker.py         RecursiveCharacterTextSplitter
│   │   │   ├── embeddings.py      Sentence-Transformers embedding model (cached singleton)
│   │   │   ├── vectorstore.py     FAISS index: add / delete / search / persist
│   │   │   ├── retriever.py       TOP_K + similarity-threshold filtering → citations
│   │   │   ├── llm.py             Groq/OpenAI chat model factory
│   │   │   └── pipeline.py        Orchestrates the above; prompt construction
│   │   ├── models/                Internal domain models (DocumentRecord, ConversationTurn, …)
│   │   ├── schemas/                Pydantic v2 request/response contracts
│   │   ├── core/                   exceptions.py, logging.py, storage.py
│   │   └── config.py                Single source of truth for settings (.env-driven)
│   ├── tests/                      pytest suite (42 tests, fully offline/mocked)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
└── frontend/                       React (Vite) + Tailwind v4
    ├── src/
    │   ├── api/                    Axios + fetch-based SSE client
    │   ├── components/
    │   │   ├── Sidebar/            Upload zone, document list/item
    │   │   ├── Chat/               Message list/bubble, citation chips, input
    │   │   ├── Layout/             Header, responsive main layout
    │   │   └── common/             Button, Modal, Spinner, StatusBadge
    │   ├── context/                Chat / Document / Theme / Toast state
    │   ├── hooks/                  useChat, useDocuments, useTheme, useToast
    │   ├── utils/                  formatters, citation parsing, conversation download
    │   └── pages/Dashboard.jsx
    ├── package.json
    ├── Dockerfile
    ├── nginx.conf
    └── .env.example
├── docker-compose.yml
└── README.md
```

### Design principles

- **Clean architecture** — routes never touch FAISS, embeddings, or the LLM directly; they call
  `services/`, which orchestrate `rag/`. Swapping the vector store or LLM provider only touches
  one file each.
- **Swappable LLM provider** — `LLM_PROVIDER=groq|openai` in `.env`, no code changes needed.
  Default Groq model is `openai/gpt-oss-120b` — Groq deprecated `llama-3.3-70b-versatile` on
  2026-06-17, so the older default seen in a lot of tutorials/templates will fail on a fresh key.
- **Config-driven RAG** — chunk size, overlap, `TOP_K`, similarity threshold are all env vars.
- **Testable by construction** — RAG modules look up their embedding/LLM dependencies through
  their owning module rather than a frozen `from x import y` binding, specifically so tests can
  monkeypatch them regardless of import order (see `app/rag/vectorstore.py` / `pipeline.py`).

## Design system

White/slate/blue SaaS palette, defined as CSS custom properties in `frontend/src/index.css`
(Tailwind v4's `@theme` block), with a full dark-mode override set. One deliberate signature
choice: a distinct **cyan "citation" accent**, reserved exclusively for source-grounding UI
(the numbered citation chips, retrieved snippets) — separate from ordinary interactive blue — so
"this claim is backed by a document" reads as unmistakable at a glance. Inter for UI text;
JetBrains Mono for anything citation/reference-adjacent, reinforcing the "precise source" feel.

## Getting started

### Option A — Docker Compose (recommended)

1. **Get a free Groq API key** at [console.groq.com/keys](https://console.groq.com/keys).
2. Copy the backend env file and add your key:
   ```bash
   cp backend/.env.example backend/.env
   # edit backend/.env and set GROQ_API_KEY=your_actual_key
   ```
3. Build and start everything:
   ```bash
   docker compose up --build
   ```
4. Open **http://localhost:3000**. The backend is also reachable directly at
   `http://localhost:8000` (interactive API docs at `http://localhost:8000/docs`).

Uploaded documents, the FAISS index, and document metadata persist in a named Docker volume
(`backend-data`) across restarts and rebuilds.

> **Note on this repo's own testing**: the Dockerfiles and `docker-compose.yml` follow standard,
> well-established patterns (multi-stage Node→nginx build, standard FastAPI/uvicorn image), but
> could not be built/run in the sandbox this project was authored in — no Docker daemon was
> available there, and the Ubuntu package mirror didn't have `nginx` available to test the config
> file standalone either. Everything else in this README *was* run and verified; this one piece
> is asking for your first real-world check. If something's off, it's most likely a path or port
> mismatch — see Troubleshooting below.

### Option B — Run locally without Docker

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and set GROQ_API_KEY=your_actual_key
uvicorn app.main:app --reload --port 8000
```

**Frontend** (in a second terminal):
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — Vite's dev server proxies `/api/*` to the backend on `:8000`
automatically (see `vite.config.js`), so no CORS setup is needed in dev.

## Environment variables

All variables live in `backend/.env` (copy from `.env.example`). Key ones:

| Variable | Default | Purpose |
|---|---|---|
| `LLM_PROVIDER` | `groq` | `groq` or `openai` — no code changes needed to switch |
| `GROQ_API_KEY` | — | Required if using Groq. Free tier at console.groq.com |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Groq-hosted model to use |
| `OPENAI_API_KEY` | — | Required only if `LLM_PROVIDER=openai` |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | HuggingFace embedding model |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `1000` / `150` | Text splitting parameters (characters) |
| `TOP_K` | `4` | How many chunks to retrieve per question |
| `SIMILARITY_THRESHOLD` | `0.2` | Minimum cosine similarity (0–1) for a chunk to be cited |
| `MAX_UPLOAD_SIZE_MB` | `20` | Upload size limit |

Full list with comments: `backend/.env.example`.

## API reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Service status, provider, embedding model, doc count |
| `POST` | `/documents/upload` | Upload + index a document (`multipart/form-data`, field `file`) |
| `GET` | `/documents` | List all documents |
| `GET` | `/documents/{id}` | Get a single document |
| `PATCH` | `/documents/{id}` | Rename (`{"new_filename": "..."}`) |
| `DELETE` | `/documents/{id}` | Delete a document and its indexed vectors |
| `POST` | `/chat` | Ask a question, get a complete (non-streaming) answer + citations |
| `POST` | `/chat/stream` | Same, streamed as SSE (`token` / `citations` / `done` / `error` events) |
| `GET` | `/chat/history` | Full conversation history |
| `DELETE` | `/chat` | Clear the conversation |

Interactive docs (Swagger UI) are available at `/docs` whenever the backend is running.

## Testing

**Backend** — 42 tests, fully offline (fake embeddings + fake LLM, no network/API key needed):
```bash
cd backend
pip install -r requirements.txt
pytest -v
```
Covers document upload/validation/rename/delete, chat (blocking + streaming, including the
readiness-check-before-stream-opens edge case, concurrent-request rejection, and streaming-failure
history cleanup), conversation history/clearing/capping, and RAG internals directly (loaders per
format, chunking, FAISS add/search/filter/delete/persistence at a scale large enough to exercise
`fetch_k` edge cases, similarity threshold filtering).

**Frontend** — 38 tests (Vitest + Testing Library):
```bash
cd frontend
npm install
npm run test
```
Covers formatting utilities, the citation-linkification logic that turns `[Source N]` into
clickable chips, interactive component behavior (Enter-to-send vs. Shift+Enter, disabled states,
button loading states, status badges), and the upload flow's status-aware success/error toasts.

**Linting:**
```bash
cd frontend && npm run lint   # oxlint — 0 errors
```

## Bugs found and fixed during development

Documenting these because they're the kind of thing that's easy to ship silently broken:

1. **FAISS similarity-score miscalibration.** The installed `langchain-community` version's
   `DistanceStrategy.COSINE` silently falls back to a plain `IndexFlatL2` index (its own source
   comment says "other metric types not initialized"), and the paired relevance-score function
   treats raw squared-L2 distance as if it were bounded cosine distance — the result is actually
   `2·cos_sim − 1`, unbounded below zero, which would have silently miscalibrated
   `SIMILARITY_THRESHOLD` and dropped genuinely relevant matches. Fixed by computing cosine
   similarity explicitly from raw squared-L2 distance (`app/rag/vectorstore.py`), verified against
   both random and content-aware fake embeddings before/after the fix.
2. **A full major-version LangChain ecosystem jump.** Initially pinned to the 0.3.x line;
   discovered mid-build that the whole ecosystem had moved to v1.x (`langchain-core` 1.5.2 at time
   of writing) and that `langchain-community` was archived/sunset on 2026-06-17. Upgraded every
   package and re-ran the full test suite to confirm no breaking changes — FAISS has no dedicated
   standalone partner package (it's not a commercial vendor), so it's still sourced from
   `langchain-community`'s compatibility releases; documented in `requirements.txt`.
3. **A dependency conflict from over-pinning.** `requirements.txt` initially pinned `groq` directly
   alongside `langchain-groq`, which manages that dependency internally — the two pins conflicted.
   Removed the redundant direct pin.
4. **`react-syntax-highlighter`'s default bundle.** Importing `{ Prism }` from the package root
   pulls its entire language bundle, more than doubling the production JS bundle unnecessarily.
   Switched to `PrismLight` with only the languages actually needed registered (JS/TS/JSX/Python/
   Bash/JSON/SQL/YAML/Markdown), cutting the bundle from 1.1MB to 548KB, then further lazy-loaded
   `MessageBubble` (the component that needs markdown/syntax-highlighting at all) to defer that
   cost out of the initial page load entirely — final initial bundle: 311KB.
5. **A generator return-value trap.** The streaming RAG pipeline originally tried to return
   citations via a generator's `StopIteration` value after `yield`ing tokens — that value doesn't
   survive a `yield from` in the calling layer, so citations silently vanished from streamed
   responses. Restructured to yield typed `{"type": ...}` events instead, which any layer can
   forward with a plain `for` loop.
6. **Deprecated Groq model in `.env.example`.** Cross-referenced a related public project's
   changelog and confirmed `llama-3.3-70b-versatile` was deprecated by Groq on 2026-06-17 — the
   default in this repo (and a lot of older tutorials) would fail on a fresh API key. Set the
   default to Groq's current recommended replacement instead.

## Production readiness audit

A separate, deeper review pass — assuming nothing was correct and re-verifying everything against
the running app rather than trusting prior test runs — found and fixed several issues invisible
to the original test suite:

1. **Blocking work inside async routes.** Document upload/indexing and the non-streaming `/chat`
   endpoint ran CPU/IO-bound work (file I/O, chunking, embedding inference, FAISS indexing, the
   LLM network call) directly on the event loop with no thread offload — under concurrent load,
   one slow request blocked *every other request*, including `/health`. Fixed via
   `fastapi.concurrency.run_in_threadpool`. (Streaming chat was **not** actually affected — verified
   by reading Starlette's source: `StreamingResponse` already runs sync generators through
   `anyio.to_thread.run_sync` per chunk.)
2. **FAISS `document_ids` filtering silently under-returned results at scale.**
   `similarity_search_with_score(..., filter=...)` fetches the top-20 nearest neighbors *globally*
   before filtering (langchain-community's own default `fetch_k`), so a document-scoped question
   could come back empty even when that document clearly contained the answer, once the index held
   more than ~20 chunks. Fixed by widening `fetch_k` to the full index size whenever a filter is
   active. Caught only by a new test with a 26-chunk corpus — the original test used 2 chunks and
   couldn't have caught it.
3. **Upload read the entire file before checking the size limit** — an unbounded-read DoS vector
   with no nginx in front (the backend's own port is also exposed directly in `docker-compose.yml`).
   Fixed with a bounded, chunked read that aborts as soon as the configured limit is exceeded.
4. **A shared global conversation with no concurrency guard.** Two simultaneous chat requests
   (e.g. two browser tabs) could interleave their history appends and misattribute answers to the
   wrong questions. Added a request-level lock; a second concurrent request now gets a clear 429
   instead of corrupting shared state. Verified with a real two-thread test.
5. **Streaming failures left orphaned turns in history.** A mid-stream error previously left the
   user's question in history with no matching answer, corrupting the next question's prompt
   context. Fixed to clean up on failure, matching the non-streaming path's existing behavior.
6. **`sentence-transformers` pulls full CUDA `torch` by default** — several GB of unused
   `nvidia-*` packages for an app that only ever runs on CPU. Attempted the standard
   `--extra-index-url` fix, then *empirically disproved it works reliably* (pip still resolved the
   CUDA build in testing) and documented the actual guaranteed fix in Troubleshooting below instead
   of claiming something unverified.
7. **A misleading frontend success toast.** The backend can return HTTP 201 with the embedded
   document's `status: "failed"` (upload succeeded; indexing didn't). The frontend showed
   "uploaded and indexed" regardless, so a user could be told a corrupt/encrypted PDF succeeded.
   Fixed to check `status` before choosing success vs. error.
8. **A documented-but-dead config setting.** `MAX_CHAT_HISTORY_TURNS` existed in `.env.example` and
   `config.py` but was never read anywhere — the prompt-history window used a separate hardcoded
   constant, and the stored history itself grew unbounded for the life of the process. Wired the
   setting up to actually cap stored history, fixing both problems together.
9. **Non-atomic metadata writes.** A crash mid-write to the JSON document-metadata store could
   leave it truncated; the read path then silently returned an empty store, losing every document
   record. Fixed with write-to-temp-file-then-atomic-rename.
10. **No client-side timeout on streaming chat.** A hung connection left the UI stuck "sending"
    forever with no recovery but a page reload. Added an `AbortController`-based timeout.
11. **A flaky test in the test suite itself.** The RAG test fixtures' "deterministic" fake
    embeddings used Python's built-in `hash()` for word bucketing — which is randomized per
    *process* since Python 3.3 (`PYTHONHASHSEED`), not actually deterministic across separate test
    runs. One test failed in roughly 1 of every 5 full-suite runs as a result, confirmed by running
    the suite 8+ times and by varying `PYTHONHASHSEED` directly. Fixed by switching to
    `zlib.crc32`, which has no such randomization; reran the suite 8 consecutive times afterward
    with zero failures.

Also verified and confirmed **not** to be issues, despite initial suspicion: no path traversal (
renaming never touches the on-disk file path; filenames are sanitized via `Path().name`), no
leaked secrets, CORS is a safe explicit allowlist, and the broad `except Exception` blocks in the
RAG pipeline are intentional (converting failures to typed status/errors) rather than silently
swallowing bugs.

## Troubleshooting

- **"GROQ_API_KEY is not set"** — copy `.env.example` to `.env` in `backend/` and fill it in; the
  container/process needs to be restarted after editing `.env`.
- **Chat says "no documents indexed"** — wait for the document's status badge in the sidebar to
  turn "Ready"; indexing happens synchronously during upload and is normally fast, but larger PDFs
  take longer.
- **Docker: frontend can't reach the backend** — confirm both containers are on the same compose
  network (default when using `docker compose up`) and that `nginx.conf`'s `proxy_pass` targets
  match the service name (`backend`) in `docker-compose.yml`.
- **Streaming responses appear to buffer/arrive all at once behind Docker/nginx** — check that
  `location /api/chat/stream` in `nginx.conf` has `proxy_buffering off;` (it does by default in
  this repo) and that no other reverse proxy in front of it re-enables buffering.
- **`pip install` pulls several GB of `nvidia-*`/CUDA packages** — `sentence-transformers` depends
  on `torch`, and pip doesn't reliably prefer the CPU-only build over PyPI's default CUDA build
  just from the `--extra-index-url` in `requirements.txt` (both satisfy the same version
  constraint, so which one you get isn't guaranteed). This app only ever uses
  `EMBEDDING_DEVICE=cpu` and never needs CUDA. For a guaranteed CPU-only install, install torch
  explicitly *before* the rest of the requirements:
  ```bash
  pip install torch --index-url https://download.pytorch.org/whl/cpu
  pip install -r requirements.txt
  ```
  Since torch is already satisfied by the time `requirements.txt` installs, pip won't try to
  replace it with a different build.
- **`pip install` fails on `sentence-transformers`/`torch` entirely** — make sure you have a few
  GB of free disk and normal internet access to `download.pytorch.org` (some restricted/corporate
  or sandboxed networks block it — if so, use the default PyPI `torch` build instead, which works
  fine, just larger).

## Tech stack

| Layer | Choice |
|---|---|
| Backend framework | FastAPI |
| LLM orchestration | LangChain (v1.x, one-provider-one-package architecture) |
| LLM provider | Groq (default), OpenAI (optional) |
| Vector store | FAISS |
| Embeddings | Sentence Transformers (`all-MiniLM-L6-v2`) |
| Frontend | React (Vite) + Tailwind CSS v4 |
| HTTP client | Axios + native `fetch` (for SSE) |
| Backend tests | pytest + httpx |
| Frontend tests | Vitest + Testing Library |
| Containerization | Docker + Docker Compose (multi-stage frontend build → nginx) |

## License

MIT — see [LICENSE](LICENSE).
