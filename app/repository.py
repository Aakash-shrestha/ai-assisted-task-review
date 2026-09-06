import os
from datetime import datetime, timezone
from typing import Optional, Protocol, Any, Mapping
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from app.domain import Task, TaskStatus, TaskPriority


class TaskRepository(Protocol):
    def find_all(self, status: Optional[TaskStatus] = None) -> list[Task]: ...
    def find_by_id(self, task_id: str) -> list[Task]: ...
    def update_status(self, task_id: str, status: TaskStatus) -> Optional[Task]: ...

class MySqlRepository:
    """
    Persists the tasks in mysql database and exposes the application repositories
    """

    def __init__(self, engine: Engine | None = None):
        if engine is not None:
            self.engine = engine
            return
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError("database url is not configured!")

        self.engine = create_engine(database_url, pool_pre_ping=True)

    def find_all(self, status: Optional[TaskStatus] = None) -> list[Task]:
        query = "SELECT id, title, description, priority, status, created_at FROM tasks"
        parameters: dict[str, str] = {}

        if status is not None:
            query += " WHERE status = :status"
            parameters["status"] = status.value

        query += " ORDER by created_at DESC"
        with self.engine.connect() as connection:
            rows = connection.execute(text(query), parameters).mappings()
            return [_task_from_rows(dict(row)) for row in rows]


    def find_by_id(self, task_id: str) -> Task:
        query = "SELECT id, title, description, priority, status, created_at FROM tasks WHERE id = :id"
        with self.engine.connect() as connection:
            row = connection.execute(text(query), {"id": task_id}).mappings().first()
            return _task_from_rows(dict(row)) if row is not None else None

    def update_status(self, task_id: str, status: TaskStatus) -> Optional[Task]:
        with self.engine.begin() as connection:
            result = connection.execute(
                text("UPDATE tasks SET status = :status WHERE id = :id"),
                {"status": status.value, "id": task_id},
            )
            if result.rowcount == 0:
                return None

            row = connection.execute(
                text("SELECT id, title, description, priority, status, created_at "
                    "FROM tasks WHERE id = :id"),
                {"id": task_id},
            ).mappings().first()
            return _task_from_rows(dict(row)) if row else None



def _task_from_rows(data: Mapping[str, Any]) -> Task:
    return Task(
        id=data["id"],
        title=data["title"],
        description=data["description"],
        priority=data["priority"],
        status=data["status"],
        createdAt=data["created_at"]
    )

def seed_tasks() -> list[Task]:
    return [
        Task(id="task-1", title="Missing customer document",
             description="The customer submitted their application but has not provided their latest payslip.",
             priority=TaskPriority.HIGH, status=TaskStatus.NEW,
             createdAt=datetime(2026, 8, 28, 9, 30, tzinfo=timezone.utc)),
        Task(id="task-2", title="Verify address details",
             description="The address on the application does not match the address on the identity document.",
             priority=TaskPriority.MEDIUM, status=TaskStatus.IN_PROGRESS,
             createdAt=datetime(2026, 8, 29, 11, 15, tzinfo=timezone.utc)),
        Task(id="task-3", title="Application approved",
             description="All checks have passed and the customer can be notified of the approval.",
             priority=TaskPriority.LOW, status=TaskStatus.COMPLETED,
             createdAt=datetime(2026, 8, 30, 14, 45, tzinfo=timezone.utc)),
    ]
