
import os, httpx
from pathlib import Path

def load_env_file() -> None:
    env_path = Path(__file__).resolve().parents[3] / ".env"

    if not env_path.is_file():
        raise ValueError("환경파일이 없습니다.")

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]

        if key:
            os.environ.setdefault(key, value)


class OllamaClient:
    def __init__(self) -> None:
        load_env_file()

        self.api_key = os.getenv("OLLAMA_API_KEY")
        self.model = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
        self.base_url = "https://ollama.com"

        if not self.api_key:
            raise ValueError("OLLAMA_API_KEY를 찾지 못했습니다.")

        self.client = httpx.Client(
            base_url=self.base_url,
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