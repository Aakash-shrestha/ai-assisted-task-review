from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.ai_service import AiProviderError
from app.main import create_app
from app.repository import SqliteTaskRepository


class FakeAi:
    async def analyse(self, task):
        return {
            "category": "DOCUMENT_REQUEST",
            "priority": "HIGH",
            "summary": "A document is missing.",
            "recommendedAction": "Request the document.",
        }


class FailingAi:
    async def analyse(self, task):
        raise AiProviderError("provider unavailable")


def client(ai=None):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    repository = SqliteTaskRepository(engine)
    return TestClient(create_app(repository=repository, ai_service=ai or FakeAi()))


def test_tasks_are_seeded_and_can_be_filtered():
    response = client().get("/tasks?status=NEW")

    assert response.status_code == 200
    assert len(response.json()["tasks"]) == 1
    assert response.json()["tasks"][0]["status"] == "NEW"


def test_valid_status_is_accepted():
    response = client().patch(
        "/tasks/task-1/status",
        json={"status": "IN_PROGRESS"},
    )

    assert response.status_code == 200
    assert response.json()["task"]["status"] == "IN_PROGRESS"


def test_invalid_status_is_rejected():
    response = client().patch(
        "/tasks/task-1/status",
        json={"status": "BLOCKED"},
    )

    assert response.status_code == 422


def test_ai_failure_returns_service_unavailable():
    response = client(FailingAi()).post("/tasks/task-1/analyse")

    assert response.status_code == 503
