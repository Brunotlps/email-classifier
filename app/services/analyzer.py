import json
import re
import hashlib
import structlog

from tenacity import retry, stop_after_attempt, wait_exponential
from cachetools import TTLCache
from typing import Dict, Any

from app.utils.ai_client import get_ai_client
from app.models.schemas import CATEGORIES_LIST


logger = structlog.get_logger()

_CATEGORIES_STR = '", "'.join(CATEGORIES_LIST)

_SYSTEM_PROMPT = f"""You are an expert email assistant. You analyze emails written in Portuguese (PT-BR) or English and return structured insights in a single JSON response.

Analyze the email and respond ONLY with valid JSON in this exact format:
{{
    "summary": "1-2 sentence summary of what the email is about and what action (if any) is expected from the recipient. Use the same language as the email.",
    "category": "one of the fixed categories below",
    "priority": "alta" | "normal" | "baixa",
    "action_required": true | false,
    "suggestions": [
        {{
            "title": "short label for this response approach (e.g. 'Aceitar reunião', 'Pedir mais detalhes')",
            "content": "complete ready-to-send response that directly references the specific content of this email",
            "tone": "formal" | "cordial" | "casual" | "técnico"
        }}
    ]
}}

Category must be exactly one of: "{_CATEGORIES_STR}"

Priority rules:
- "alta": urgent or time-sensitive (financial, deadline, support outage, job offer expiring)
- "normal": should be answered within a few days
- "baixa": informational, no response needed, or can wait indefinitely

Suggestions rules:
- Generate 2-3 suggestions ONLY when replying would be useful (skip for newsletters, automated alerts, and pure notifications where action_required is false)
- Each suggestion must reference specific details from the email (names, dates, topics mentioned) — never write generic placeholder text
- Vary the approach across suggestions, not just the tone (e.g., "confirm", "decline politely", "request more info")
- Write suggestions in the same language as the original email
- Keep each suggestion concise but complete — ready to send as-is

Do NOT add any text before or after the JSON. Return ONLY the JSON object."""


class EmailAnalyzer:
    """
    Analisa emails em uma única chamada à IA, retornando resumo, categoria,
    prioridade e sugestões de resposta contextuais.
    """

    def __init__(self):
        self.ai_client = get_ai_client()
        self.cache = TTLCache(maxsize=100, ttl=3600)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10), reraise=True)
    async def _call_ai(self, user_prompt: str) -> str:
        return await self.ai_client.generate(user_prompt, _SYSTEM_PROMPT)

    async def analyze(self, email_content: str) -> Dict[str, Any]:
        cache_key = hashlib.sha256(email_content.encode()).hexdigest()

        if cache_key in self.cache:
            logger.info("analyzer_cache_hit", key=cache_key[:8])
            return self.cache[cache_key]

        user_prompt = f"Analyze this email:\n\n---\n{email_content.strip()}\n---"
        raw = await self._call_ai(user_prompt)
        result = self._parse(raw)

        self.cache[cache_key] = result
        logger.info("analyzer_cache_saved", key=cache_key[:8])
        return result

    def _parse(self, response: str) -> Dict[str, Any]:
        match = re.search(r'\{.*\}', response, re.DOTALL)
        text = match.group(0) if match else response.strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"AI response is not valid JSON: {response}") from e

        self._validate(data)
        return data

    def _validate(self, data: Dict[str, Any]) -> None:
        for field in ("summary", "category", "priority", "action_required"):
            if field not in data:
                raise ValueError(f"Missing required field: '{field}'")

        if data["category"] not in CATEGORIES_LIST:
            data["category"] = "Outro"

        if data["priority"] not in ("alta", "normal", "baixa"):
            data["priority"] = "normal"

        if not isinstance(data["action_required"], bool):
            data["action_required"] = bool(data["action_required"])

        if "suggestions" not in data or not isinstance(data["suggestions"], list):
            data["suggestions"] = []
