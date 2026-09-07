from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .ai_service import AiProviderError, AiService, GeminiService
from .domain import StatusUpdate, TaskStatus
from .repository import SqliteTaskRepository, TaskRepository
from .service import TaskNotFoundError, TaskService

load_dotenv()


def create_app(repository: TaskRepository | None = None, ai_service: AiService | None = None) -> FastAPI:
    app = FastAPI(title="AI-Assisted Task Review API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    task_service = TaskService(
        repository or SqliteTaskRepository(),
        ai_service or GeminiService(),
    )

    def service() -> TaskService:
        return task_service

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/tasks")
    async def list_tasks(
        status: TaskStatus | None = Query(default=None),
        tasks: TaskService = Depends(service),
    ):
        return {"tasks": tasks.list_tasks(status)}

    @app.patch("/tasks/{task_id}/status")
    async def update_status(task_id: str, payload: StatusUpdate, tasks: TaskService = Depends(service)):
        try:
            return {"task": tasks.update_status(task_id, payload.status)}
        except TaskNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.post("/tasks/{task_id}/analyse")
    async def analyse(task_id: str, tasks: TaskService = Depends(service)):
        try:
            return {"analysis": await tasks.analyse_task(task_id)}
        except TaskNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except AiProviderError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error

    return app


app = create_app()
