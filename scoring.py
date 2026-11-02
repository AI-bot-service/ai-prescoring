import json
import logging
import re
from typing import Literal

from openai import AuthenticationError, OpenAI, OpenAIError
from pydantic import BaseModel, Field, ValidationError

import config

log = logging.getLogger(__name__)

Status = Literal["выполнен", "частично", "не выполнен", "нет данных"]


class Criterion(BaseModel):
    name: str
    status: Status
    required: bool = False
    evidence: str = ""


class Result(BaseModel):
    verdict: Literal["подходит", "не подходит"]
    score: int = Field(ge=1, le=10)
    comment: str
    criteria: list[Criterion] = []
    model: str = ""


class ScoringError(Exception):
    """Ошибка, текст которой можно показать пользователю."""


def _client() -> OpenAI:
    if not config.OPENAI_API_KEY:
        raise ScoringError("Не задан ключ OPENAI_API_KEY. Добавьте его в .env или в Secrets на Streamlit Cloud.")
    return OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL, timeout=config.REQUEST_TIMEOUT)


def _parse(raw: str) -> Result:
    # Модели иногда оборачивают JSON в ```json ... ``` или добавляют фразу до/после
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError("в ответе нет JSON")
    result = Result.model_validate(json.loads(match.group(0)))
    # Вердикт держим согласованным со шкалой и обязательными критериями, даже если модель ошиблась
    failed_required = any(c.required and c.status in ("не выполнен", "нет данных") for c in result.criteria)
    if result.verdict == "подходит" and (result.score < config.PASS_SCORE or failed_required):
        result.verdict = "не подходит"
    return result


def evaluate(candidate: str, criteria: str) -> Result:
    candidate, criteria = candidate.strip(), criteria.strip()
    if not candidate or not criteria:
        raise ScoringError("Заполните оба поля: информацию о кандидате и критерии отбора.")
    if len(candidate) > config.MAX_INPUT_LENGTH or len(criteria) > config.MAX_INPUT_LENGTH:
        raise ScoringError(f"Слишком длинный текст: в каждом поле не больше {config.MAX_INPUT_LENGTH} символов.")

    client = _client()
    messages = [
        {"role": "system", "content": config.SYSTEM_PROMPT},
        {"role": "user", "content": f"<candidate>\n{candidate}\n</candidate>\n\n<criteria>\n{criteria}\n</criteria>"},
    ]
    for model in config.MODELS:
        try:
            response = client.chat.completions.create(
                model=model, messages=messages, temperature=config.TEMPERATURE
            )
            result = _parse(response.choices[0].message.content or "")
            result.model = model
            return result
        except AuthenticationError:
            raise ScoringError("Ключ API не подошёл. Проверьте OPENAI_API_KEY.") from None
        except (OpenAIError, ValueError, ValidationError) as e:
            # Перегрузка, таймаут или битый JSON — пробуем следующую модель
            log.warning("Модель %s не ответила: %s", model, type(e).__name__)
    raise ScoringError("Все модели сейчас перегружены. Повторите через минуту.")
