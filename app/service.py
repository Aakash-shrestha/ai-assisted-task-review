from .ai_service import AiService
from .domain import Task, TaskAnalysis, TaskStatus
from .repository import TaskRepository


class TaskNotFoundError(Exception):
    pass


class TaskService:
    def __init__(self, repository: TaskRepository, ai_service: AiService):
        self.repository = repository
        self.ai_service = ai_service

    def list_tasks(self, status: TaskStatus | None = None) -> list[Task]:
        return self.repository.find_all(status)

    def update_status(self, task_id: str, status: TaskStatus) -> Task:
        task = self.repository.update_status(task_id, status)
        if task is None:
            raise TaskNotFoundError(f"Task with ID {task_id} not found.")
        return task

    async def analyse_task(self, task_id: str) -> TaskAnalysis:
        task = self.repository.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(f"Task with ID {task_id} not found.")
        return await self.ai_service.analyse(task)
