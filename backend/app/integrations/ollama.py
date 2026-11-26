import httpx
from backend.app.core.config import get_settings

class OllamaClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.model = settings.ollama_model
        self.client = httpx.Client(
            base_url=settings.ollama_base_url,
            timeout=300.0,
        )

    def chat(self, prompt: str) -> str:
        response = self.client.post(
            "/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "format": "json",
                "think": False,
                "stream": False,
                "options": {
                    "num_ctx": 8192,
                    "num_predict": 1800,
                    "temperature": 0.1,
                },
            },
        )

        response.raise_for_status()
        data = response.json()

        return data["message"]["content"]

    def close(self) -> None:
        self.client.close()