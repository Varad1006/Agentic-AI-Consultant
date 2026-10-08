![Autonomous AI Consultant](docs/banner.png)

# 🤖 Autonomous AI Consultant

A multi-agent AI consulting platform that turns operational documents (SOPs, process docs, meeting notes) into a current-state analysis, an automation blueprint, an ROI estimate and an executive report — then lets you question the consultant about it.

Built with **LangGraph**, **FastAPI**, **Celery**, **Redis**, **ChromaDB** and **React**, running on **`openai/gpt-oss-120b` via Groq**.

![The app](docs/screenshot.png)

---

## ✨ Features

- **Multi-format input**: upload a PDF, DOCX, TXT, MD or CSV file, or paste text. There's a built-in sample SOP for trying it out.
- **Five specialised agents** in a LangGraph pipeline, each building on the previous one's output (see below).
- **Live progress**: the UI shows which agent is working, which are done and where a run failed.
- **Structured, validated outputs**: every agent returns a Pydantic schema, enforced by Groq's strict JSON-schema mode.
- **Consistent financials**: the ROI agent estimates cost and savings; payback period and 3-year ROI are calculated in code, so the numbers always agree.
- **Grounded follow-up chat**: the consultant answers using the report plus the most relevant passages of your document, and remembers the conversation.
- **Persistent jobs**: reports and chat history survive restarts, and every report has a shareable URL (`?job=<id>`).
- **Export**: download the report as Markdown or print it to PDF (light, print-friendly layout).

## 🧠 How it works

```mermaid
flowchart LR
    U[Upload / paste] --> API[FastAPI]
    API -->|chunk + embed| C[(ChromaDB)]
    API -->|queue job| R[(Redis)]
    R --> P

    subgraph P[Celery worker · LangGraph pipeline]
        direction LR
        A1[Context Retriever] --> A2[Business Analyst] --> A3[Solutions Architect] --> A4[ROI Analyst] --> A5[Report Writer]
    end

    A1 -. retrieves .-> C
    P -->|progress + results| J[(Job store)]
    API -->|status, report, chat| J
```

| Agent | What it does |
| --- | --- |
| **Context Retriever** | Sends the whole document to the analyst if it fits the context budget; otherwise runs four targeted searches (business model, tools, manual processes, volumes/costs) and assembles the best chunks in document order. |
| **Business Analyst** | Extracts the business model, current tools and every bottleneck with hours per week. |
| **Solutions Architect** | Designs one automation solution per bottleneck, with a tech stack and implementation steps. |
| **ROI Analyst** | Estimates build cost, hours saved and annual savings **for the proposed architecture**, and lists its assumptions. |
| **Report Writer** | Writes the executive summary and 3–5 priority actions. |

The pipeline stops at the first agent that fails, and the error is shown in the UI with the failing step highlighted.

## ⚙️ Tech stack

| Layer | Tools |
| --- | --- |
| LLM | `openai/gpt-oss-120b` on [Groq](https://console.groq.com) via `langchain-groq` |
| Orchestration | LangGraph |
| API & jobs | FastAPI, Celery, Redis |
| Retrieval | ChromaDB with local `all-MiniLM-L6-v2` embeddings (no embedding API key needed) |
| Frontend | React, Vite, Tailwind CSS, lucide-react |
| Infrastructure | Docker Compose (API, worker, Redis, Chroma server, frontend) |

## 🚀 Quick start (Docker)

1. Get a free API key from [console.groq.com/keys](https://console.groq.com/keys).
2. Create your `.env` and add the key:

   ```bash
   cp .env.example .env
   # then edit .env and set GROQ_API_KEY=...
   ```

3. Start everything:

   ```bash
   docker compose up --build
   ```

4. Open **http://localhost:3001**. The API runs on http://localhost:8000 (interactive docs at `/docs`).

## Free backend demo on Render + Vercel frontend

The repository includes `render.yaml` for a **free Python web service**. This uses
`DEMO_MODE=true`: the same five-agent LangGraph pipeline runs in one API process,
one analysis at a time. Redis and Celery workers are not required. Document excerpts
use keyword search instead of ChromaDB embeddings to fit the free service's memory.
The existing Docker/Celery setup remains the default when demo mode is off.

1. In [Render](https://dashboard.render.com/), choose **New → Blueprint** and select
   this repository and the branch containing `render.yaml`.
2. Confirm that the service plan is **Free**, and enter `GROQ_API_KEY` when prompted.
   Store the key only on the backend; never put it in a `VITE_` variable.
3. `CORS_ORIGINS` is preset to `https://agentic-ai-consultant.vercel.app`.
   Change it if your frontend URL differs (use the origin only, without a trailing
   slash; multiple origins are comma-separated).
4. After deployment, open `https://YOUR-SERVICE.onrender.com/api/v1/health`.
   Expect `execution_mode: "demo"` and `llm.configured: true`.
   `celery: "disabled"` is expected in this mode.
5. In your Vercel project's **Settings → Environment Variables**, set
   `VITE_API_URL=https://YOUR-SERVICE.onrender.com` for Production and redeploy the
   frontend from the branch containing demo support. Do not append `/api/v1`.

If using **New → Web Service** instead of a Blueprint, use these settings:

| Setting | Value |
| --- | --- |
| Repository root directory | Leave blank |
| Language | Python 3 (not Docker) |
| Plan | Free |
| Build command | `pip install -r requirements-demo.txt` |
| Start command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1` |
| Environment | Copy the variables in `render.yaml`; enter your own Groq key |

**Demo limits:** one service instance and one Uvicorn worker; simultaneous analysis
submissions return 429. The supplied settings cap uploads at 2 MB and documents at
30,000 characters. Reports and document excerpts are temporary: Render free services
lose local files when they restart, redeploy, or sleep. Interrupted jobs cannot
resume. Download reports you want to keep. See [Render's free-service limits](https://render.com/docs/free).

To test the demo locally:

```bash
pip install -r requirements-demo.txt
DEMO_MODE=true uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

Use your `.env` for `GROQ_API_KEY`, and allow your local frontend origin in
`CORS_ORIGINS`. Demo regression tests can run without Celery, Redis or ChromaDB:

```bash
pip install pytest httpx
DEMO_MODE=true CORS_ORIGINS=https://agentic-ai-consultant.vercel.app pytest -q tests/demo_cases.py
```

## 🛠 Local development (without Docker)

Requires Python 3.10+, Node 18+ and Redis.

```bash
# Backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env            # add your GROQ_API_KEY

redis-server                                                        # terminal 1
uvicorn app.main:app --reload --port 8000                           # terminal 2
celery -A app.celery_worker.celery_app worker --loglevel=info --pool=solo   # terminal 3

# Frontend (terminal 4)
cd frontend && npm install && npm run dev                           # http://localhost:5173
```

Without `CHROMA_HOST`, the backend uses an embedded ChromaDB in `data/chroma`. Job records live in `data/jobs`.

## 🔧 Configuration

All settings are environment variables (see `.env.example`).

| Variable | Default | Purpose |
| --- | --- | --- |
| `GROQ_API_KEY` | — | **Required.** Groq API key. |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Model used by every agent and the chat. |
| `GROQ_REASONING_EFFORT` | `medium` | `low`, `medium` or `high`. |
| `MAX_CONTEXT_CHARS` | `12000` | How much of the document the analyst reads. Groq's free tier allows 8K tokens/minute for gpt-oss-120b, so keep this low there and raise it on a paid plan. |
| `MAX_DOCUMENT_CHARS` | `150000` | Longer documents are truncated. |
| `MAX_UPLOAD_MB` | `10` | Upload size limit. |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | `redis://localhost:6379/0` and `/1` | Redis connections. |
| `CHROMA_HOST` / `CHROMA_PORT` | embedded / `8000` | Set to use a Chroma server (Docker Compose does). |
| `DATA_DIR` | `./data` | Job records and the embedded Chroma DB. |
| `CORS_ORIGINS` | `http://localhost:3001,http://localhost:5173` | Allowed frontend origins. |

> **Groq free tier:** runs make 4 LLM calls and may pause briefly for rate limits; the Groq SDK retries automatically using the `retry-after` header. A typical run takes 1–3 minutes.

## 📡 API

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/v1/health` | API, worker and LLM configuration status |
| `POST` | `/api/v1/upload` | Upload a document (multipart `file`) and start a job |
| `POST` | `/api/v1/consult` | Start a job from pasted text (`{"document_text": "..."}`) |
| `GET` | `/api/v1/consult/{job_id}` | Status, per-agent progress, results and chat history |
| `GET` | `/api/v1/consult/{job_id}/report` | The finished report as Markdown |
| `POST` | `/api/v1/consult/{job_id}/chat` | Ask a follow-up question (`{"question": "..."}`) |

## 📂 Project structure

```
app/
├── main.py            FastAPI endpoints
├── celery_worker.py   Celery app + task that runs the pipeline and records progress
├── graph.py           LangGraph workflow (sequential, stops on first failure)
├── nodes.py           The five agents
├── prompts.py         Agent and consultant prompts
├── schemas.py         Pydantic output schemas + ROI calculation
├── state.py           Shared LangGraph state
├── llm.py             Groq model setup and friendly error messages
├── vector_store.py    Chunking, local embeddings and retrieval (ChromaDB)
├── documents.py       PDF/DOCX/TXT extraction and clean-up
├── storage.py         Durable JSON job records (status, results, chat)
├── advisor.py         Follow-up chat grounded in the report + document
├── report.py          Markdown report rendering
└── config.py          Settings from environment variables
frontend/src/
├── App.jsx            Views: landing, live progress, failure, report + chat
├── components/        DocumentInput, AgentPipeline, ReportView, ChatPanel, ...
└── lib/               API client, agent definitions, formatting, sample SOP
tests/                 pytest suite (graph wiring, pipeline, API, retrieval, parsing)
```

## ✅ Tests

```bash
pip install -r requirements-dev.txt
pytest
```

The suite runs the full pipeline with a fake LLM, so it needs no API key.

## 📈 Roadmap

- Streaming chat responses
- Multi-document engagements
- Authentication and per-user workspaces
- Industry benchmarks for the ROI estimates
- Human review step before the final report

---

## 👨‍💻 Author

**Varad Adhyapak** · Computer Science (AI & ML)

Interested in AI engineering, agentic AI, backend systems, LLM infrastructure and distributed systems.

⭐ If you found this project interesting, consider giving it a star!
