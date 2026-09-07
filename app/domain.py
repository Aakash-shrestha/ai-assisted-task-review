from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

class TaskStatus(str, Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"

class TaskPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class Task(BaseModel):
    id: str
    title: str
    description: str
    priority: TaskPriority
    status: TaskStatus
    createdAt: datetime

class TaskAnalysis(BaseModel):
    category: str = Field(min_length=1)
    priority: TaskPriority
    summary: str = Field(min_length=1)
    recommendedAction: str = Field(min_length=1)

class StatusUpdate(BaseModel):
    status: TaskStatus
