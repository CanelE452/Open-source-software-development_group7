import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_DIR))

from app.integrations.ollama import OllamaClient

ollama = OllamaClient()

try:
    summary = ollama.chat("Hello World!")
    print(summary)
finally:
    ollama.close()