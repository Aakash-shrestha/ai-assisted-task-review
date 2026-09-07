import os
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Protocol

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from .domain import Task, TaskPriority, TaskStatus


class TaskRepository(Protocol):
    def find_all(self, status: Optional[TaskStatus] = None) -> list[Task]: ...
    def find_by_id(self, task_id: str) -> Optional[Task]: ...
    def update_status(self, task_id: str, status: TaskStatus) -> Optional[Task]: ...


class SqliteTaskRepository:
    """Persists tasks in a local SQLite database."""

    def __init__(self, engine: Engine | None = None):
        if engine is not None:
            self.engine = engine
        else:
            database_url = os.getenv("DATABASE_URL", "sqlite:///./task_review.db")
            self.engine = create_engine(database_url)
        self._create_table()
        self._seed_tasks()

    def _create_table(self) -> None:
        with self.engine.begin() as connection:
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    priority TEXT NOT NULL CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH')),
                    status TEXT NOT NULL CHECK (status IN ('NEW', 'IN_PROGRESS', 'COMPLETED')),
                    created_at TEXT NOT NULL
                )
            """))

    def _seed_tasks(self) -> None:
        with self.engine.begin() as connection:
            for task in seed_tasks():
                connection.execute(
                    text("""
                        INSERT OR IGNORE INTO tasks
                            (id, title, description, priority, status, created_at)
                        VALUES
                            (:id, :title, :description, :priority, :status, :created_at)
                    """),
                    {
                        "id": task.id,
                        "title": task.title,
                        "description": task.description,
                        "priority": task.priority.value,
                        "status": task.status.value,
                        "created_at": task.createdAt.isoformat(),
                    },
                )

    def find_all(self, status: Optional[TaskStatus] = None) -> list[Task]:
        query = "SELECT id, title, description, priority, status, created_at FROM tasks"
        parameters: dict[str, str] = {}

        if status is not None:
            query += " WHERE status = :status"
            parameters["status"] = status.value

        query += " ORDER BY created_at DESC"
        with self.engine.connect() as connection:
            rows = connection.execute(text(query), parameters).mappings()
            return [_task_from_rows(dict(row)) for row in rows]


    def find_by_id(self, task_id: str) -> Optional[Task]:
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
        priority=TaskPriority(data["priority"]),
        status=TaskStatus(data["status"]),
        createdAt=data["created_at"],
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
