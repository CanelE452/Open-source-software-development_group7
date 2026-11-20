import httpx
from backend.app.core.config import get_settings

OLLAMA_CLOUD_BASE_URL = "https://ollama.com"

class OllamaClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.ollama_api_key
        self.model = settings.ollama_model

        if not self.api_key:
            raise ValueError("OLLAMA_API_KEY를 찾지 못했습니다.")

        self.client = httpx.Client(
            base_url=OLLAMA_CLOUD_BASE_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=120.0,
        )

    def chat(self, prompt: str) -> str:
        response = self.client.post(
            "/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
            },
        )

        response.raise_for_status()
        data = response.json()

        return data["message"]["content"]

    def close(self) -> None:
        self.client.close()