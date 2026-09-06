# AI-Assisted Task Review

## Run locally

Requirements: Python 3.11+, Node.js 20+, and an OpenAI API key.

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Put your key in .env, then load it into the current shell
set -a; source .env; set +a
uvicorn app.main:app --reload --port 3000
```

In another terminal:

```bash
cd client
npm install
npm run dev
```

Open `http://localhost:5173`. The API is at `http://localhost:3000`. Run `pytest` for backend tests. The frontend can be production-built with `cd client && npm run build`.

## Technologies and approach

The backend is Python with FastAPI, Pydantic, HTTPX, and pytest. The frontend is React, Vite, and TypeScript. Tasks are stored in memory because that is explicitly allowed and keeps the assessment easy to run. The backend uses a layered design: FastAPI routes handle HTTP concerns, `TaskService` owns use cases, `TaskRepository` owns storage, and `OpenAiService` is the provider adapter.

Analysis uses a real OpenAI-compatible Chat Completions request. The API key, model, and base URL come from environment variables and are never committed. The model is instructed to return JSON, and Pydantic validates the response before it reaches the frontend. Missing credentials, provider errors, malformed JSON, and invalid model output become a safe `503` response.

## What I would improve

For production I would add SQLite/PostgreSQL persistence, authentication and authorization, pagination, task creation, an audit trail, structured logging, rate limiting, retries with backoff, provider observability, and a schema/tool-calling approach supported by the selected model. I would also add frontend tests and end-to-end tests.

## AI-assisted development

GitHub Copilot CLI was used to reason about the architecture, implementation, and documentation. Generated code was reviewed manually and checked with pytest, the frontend build, and API smoke testing. No API key is included in the repository.

## Submission format

- Name: Aakash Shrestha
- GitHub Repository: `https://github.com/Aakash-shrestha/ai-assisted-task-review`
- Backend Language: Python / FastAPI
- LLM Provider / Mock Used: OpenAI API (`OPENAI_MODEL`, default `gpt-4o-mini`)
- Approximate Time Spent: _Fill in before submission_
