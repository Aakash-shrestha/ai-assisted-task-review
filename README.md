# AI-Assisted Task Review

## Run locally

Requirements: Python 3.11+, Node.js 20+, and a Gemini API key from Google AI Studio.

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Put your Gemini key in .env
uvicorn app.main:app --reload --port 3000
```

In another terminal:

```bash
cd client
npm install
npm run dev
```

Open `http://localhost:5173`. The API is at `http://localhost:3000`. Run `pytest` for backend tests. The frontend can be production-built with `cd client && npm run build`.

## Testing

Run the backend tests from the project root:

```bash
PYTHONPATH=. .venv/bin/pytest -q
```

The test suite checks task filtering, valid status updates, rejection of invalid statuses, and safe handling of AI provider failures. You should see four passing tests.

To verify that the frontend compiles successfully for production:

```bash
cd client
npm run build
```

## Technologies and approach

The backend is Python with FastAPI, Pydantic, SQLAlchemy, SQLite, HTTPX, and pytest. The frontend is React, Vite, and TypeScript. Tasks are stored in a local SQLite database.

The backend uses a layered architecture:

- **Routes/controllers:** FastAPI endpoints handle HTTP requests, validation, status codes, and response formatting. This keeps HTTP-specific concerns out of the business logic.
- **Service layer:** `TaskService` contains the application use cases, such as listing tasks, updating a status, and requesting an analysis. This gives the main workflows one clear place to live.
- **Repository pattern:** `TaskRepository` defines the operations the application needs from storage, while `SqliteTaskRepository` contains the SQLite and SQLAlchemy code. This separates persistence details from the rest of the application and makes a different database easier to add later.
- **Dependency injection:** `create_app()` receives optional repository and AI-service implementations and injects them into `TaskService`. The production application receives `SqliteTaskRepository` and `GeminiService`; tests inject an isolated SQLite repository and fake AI services. This avoids hard-coded dependencies and makes tests deterministic without calling the real Gemini API.
- **Dependency inversion and protocols:** `TaskService` depends on the `TaskRepository` and `AiService` interfaces rather than concrete implementations. The service therefore depends on what an object can do, not on how it does it, which improves maintainability and testability.
- **Adapter pattern:** `GeminiService` adapts the external Gemini HTTP API to the application's small `AiService` interface. Provider-specific request formats and errors remain isolated from the service and routes.
- **Application factory:** `create_app()` builds and configures the FastAPI application. This allows tests to create separate application instances with controlled dependencies instead of relying on global state.
- **Schema validation:** Pydantic models and enums validate incoming status values and AI responses at the application boundary. Invalid data is rejected early, and the rest of the application can work with predictable structures.
- **Error translation:** Provider failures are converted into a controlled `503 Service Unavailable` response, while unknown tasks return `404`. This gives the frontend useful errors without exposing provider implementation details.

These choices keep each part focused, make the code easier to explain and test, and provide a reasonable foundation for extending the application without adding unnecessary complexity for this assessment.

Analysis uses a real Gemini API request. The API key and model come from environment variables and are never committed. The model is instructed to return JSON, and Pydantic validates the response before it reaches the frontend. Missing credentials, provider errors, malformed JSON, and invalid model output become a safe `503` response.

## Incoming tasks

For this assessment, incoming tasks are represented by sample records seeded into the local SQLite database when it is first created. These records provide tasks for the operations user to review through the task list, filter by status, update, and analyse with AI.

A production version could receive incoming tasks through a `POST /tasks` endpoint, a message queue, a scheduled import, or an integration with an upstream operations system. A separate task-ingestion system was not added because it is outside the scope of this assessment.

## What I would improve

For production I would add authentication and authorization, pagination, task creation, an audit trail, structured logging, rate limiting, retries with backoff, provider observability, and a migration tool such as Alembic. I would also add frontend tests and end-to-end tests.

## AI-assisted development

GitHub Copilot CLI was used to reason about the architecture, implementation, and documentation. Generated code was reviewed manually and checked with pytest, the frontend build, and API smoke testing. No API key is included in the repository.

## Submission format

- Name: Aakash Shrestha
- GitHub Repository: `https://github.com/Aakash-shrestha/ai-assisted-task-review`
- Backend Language: Python / FastAPI
- LLM Provider / Mock Used: Gemini API (`GEMINI_MODEL`, default `gemini-3.6-flash`)
- Approximate Time Spent: approx. 9 hours
