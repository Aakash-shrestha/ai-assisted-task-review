import os
import httpx
from app.domain import Task, TaskAnalysis
import json

class AiProviderError(Exception):
    pass

class GeminiService:
    """
    Adapter for gemini api
    """
    def __init__(self, api_key: str|None = None, model: str|None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
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
                content = response.json()["candidate"][0]["content"]["parts"][0]["text"]
                return TaskAnalysis.model_validate(json.loads(content))

        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as error:
            raise AiProviderError(
                "The AI provider returned an invalid or unavailable response."
            ) from error
