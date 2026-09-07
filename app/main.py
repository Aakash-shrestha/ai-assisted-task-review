from dotenv import load_dotenv

from app.ai_service import GeminiService
from app.domain import TaskStatus
from app.repository import SqliteTaskRepository, TaskRepository
from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.service import TaskService

load_dotenv()


def create_app(repository: TaskRepository | None = None, ai_service: GeminiService | None = None) -> FastAPI:
    app = FastAPI(title="AI-Assisted Task Review API", version = "1.0.0")
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])
    task_service = TaskService(repository or SqliteTaskRepository() , ai_service or GeminiService())

    def service() -> TaskService:
        return task_service

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/tasks")
    async def list_tasks(status: TaskStatus | None = Query(default=None), tasks: TaskService = Depends(service)):
        return {"tasks": tasks.list_tasks(status)}
