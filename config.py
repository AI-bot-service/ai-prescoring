import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# На Streamlit Cloud ключи из раздела Secrets попадают в переменные окружения
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip().strip("\"'")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")

# Бесплатные модели OpenRouter. Их иногда перегружают (ошибка 429),
# поэтому при сбое запрос уходит следующей модели из списка.
DEFAULT_MODELS = [
    "nvidia/nemotron-3.5-super-vl:free",
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "google/gemma-4-26b-a4b-it:free",
]
MODELS = [m.strip() for m in os.getenv("MODELS", "").split(",") if m.strip()] or DEFAULT_MODELS

# Низкая температура — один и тот же кандидат получает один и тот же балл
TEMPERATURE = 0.1
REQUEST_TIMEOUT = 60

# Балл, начиная с которого кандидат «подходит» (если выполнены все обязательные критерии)
PASS_SCORE = 7

MAX_INPUT_LENGTH = 6000
SYSTEM_PROMPT = (BASE_DIR / "prompts" / "system_prompt.md").read_text(encoding="utf-8")
