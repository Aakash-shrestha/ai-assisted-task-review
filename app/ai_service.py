import json
import logging
import os
from typing import Protocol

import httpx

from .domain import Task, TaskAnalysis

logger = logging.getLogger(__name__)


class AiProviderError(Exception):
    pass


class AiService(Protocol):
    async def analyse(self, task: Task) -> TaskAnalysis: ...


class GeminiService:
    """Adapter for the Gemini API."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def analyse(self, task: Task) -> TaskAnalysis:
        if not self.api_key:
            raise AiProviderError("Gemini API key is not set. Please set the GEMINI_API_KEY environment variable.")

        system_prompt = (
            "You review operations tasks. Return only valid JSON with exactly these keys: "
            "category (string), priority (LOW, MEDIUM, or HIGH), summary (string), "
            "recommendedAction (string). Do not include markdown."
        )
        user_prompt = (
            f"Title: {task.title}\nDescription: {task.description}\n"
            f"Existing priority: {task.priority.value}"
        )

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(
                    f"{self.base_url}/models/{self.model}:generateContent",
                    params={"key": self.api_key},
                    json={
                        "systemInstruction": {"parts": [{"text": system_prompt}]},
                        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                        "generationConfig": {
                            "temperature": 0.2,
                            "responseMimeType": "application/json",
                        },
                    },
                )

                response.raise_for_status()
                content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                return TaskAnalysis.model_validate(json.loads(content))

        except httpx.HTTPStatusError as error:
            status_code = error.response.status_code
            logger.error(
                "Gemini request failed with status %s: %s",
                status_code,
                error.response.text[:500],
            )
            if status_code in {401, 403}:
                message = "Gemini rejected the API key. Check GEMINI_API_KEY and its permissions."
            elif status_code == 404:
                message = f"Gemini model '{self.model}' was not found or is unavailable."
            elif status_code == 429:
                message = "Gemini quota or rate limit reached. Please try again later."
            elif status_code == 503:
                message = "Gemini is temporarily unavailable. Please try again later."
            else:
                message = "Gemini rejected the analysis request. Please try again later."
            raise AiProviderError(
                message
            ) from error
        except httpx.RequestError as error:
            logger.error("Gemini request could not be completed: %s", error)
            raise AiProviderError(
                "Gemini could not be reached. Please try again."
            ) from error
        except (KeyError, IndexError, TypeError, ValueError) as error:
            logger.exception("Gemini returned an unexpected response format.")
            raise AiProviderError(
                "Gemini returned an invalid response. Please try again."
            ) from error
