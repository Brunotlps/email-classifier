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

# _SYSTEM_PROMPT = f"""You are an expert email assistant. You analyze emails written in Portuguese (PT-BR) or English and return structured insights in a single JSON response.

# Analyze the email and respond ONLY with valid JSON in this exact format:
# {{
#     "summary": "1-2 sentence summary of what the email is about and what action (if any) is expected from the recipient. Use the same language as the email.",
#     "category": "one of the fixed categories below",
#     "priority": "alta" | "normal" | "baixa",
#     "action_required": true | false,
#     "suggestions": [
#         {{
#             "title": "short label for this response approach (e.g. 'Aceitar reunião', 'Pedir mais detalhes')",
#             "content": "complete ready-to-send response that directly references the specific content of this email",
#             "tone": "formal" | "cordial" | "casual" | "técnico"
#         }}
#     ]
# }}

# Category must be exactly one of: "{_CATEGORIES_STR}"

# Priority rules:
# - "alta": urgent or time-sensitive (financial, deadline, support outage, job offer expiring)
# - "normal": should be answered within a few days
# - "baixa": informational, no response needed, or can wait indefinitely

# Suggestions rules:
# - Generate 2-3 suggestions ONLY when replying would be useful (skip for newsletters, automated alerts, and pure notifications where action_required is false)
# - Each suggestion must reference specific details from the email (names, dates, topics mentioned) — never write generic placeholder text
# - Vary the approach across suggestions, not just the tone (e.g., "confirm", "decline politely", "request more info")
# - Write suggestions in the same language as the original email
# - Keep each suggestion concise but complete — ready to send as-is

# Do NOT add any text before or after the JSON. Return ONLY the JSON object."""

_SYSTEM_PROMPT = f"""\
You are a senior executive assistant specialized in email triage for busy professionals. Your task is to analyze an email and return a single JSON object with structured insights.
 
### RESPONSE FORMAT ###
Respond ONLY with a valid JSON object. No text before or after it.
 
{{
  "summary": "string — 1-2 sentences describing what the email is about and what is expected from the recipient",
  "category": "string — one of the allowed categories below",
  "priority": "alta | normal | baixa",
  "action_required": true | false,
  "suggestions": []
}}
 
### ALLOWED CATEGORIES ###
{_CATEGORIES_STR}
 
CATEGORY must be copied exactly as written above. Do not paraphrase or abbreviate.
 
### RULES ###
 
LANGUAGE: Detect the email language. Write every output field in that same language.
 
PRIORITY:
- "alta": contains a deadline within 72h, financial transaction, service outage, job offer with expiration, or explicit urgency markers.
- "normal": expects a reply but has no urgent deadline.
- "baixa": informational only, no reply expected, can wait indefinitely.
 
SUGGESTIONS:
- Generate 2-3 suggestions ONLY when action_required is true.
- If action_required is false, return an empty array: "suggestions": [].
- Each suggestion MUST reference specific details from the email (names, dates, amounts, topics).
- Vary the strategic approach across suggestions (e.g., accept / decline / ask for clarification), not just the tone.
- Each suggestion is a ready-to-send reply. Keep it concise but complete.
- Format each suggestion as: {{"title": "short label", "content": "full reply text", "tone": "formal | cordial | casual | técnico"}}
 
### EXAMPLE ###
 
Email: "Oi João, a reunião de alinhamento do projeto Alpha foi movida para sexta-feira às 14h. Confirme sua presença. Abs, Maria."
 
Output:
{{
  "summary": "Maria informa que a reunião do projeto Alpha foi reagendada para sexta às 14h e pede confirmação de presença.",
  "category": "Reunião / Agenda",
  "priority": "normal",
  "action_required": true,
  "suggestions": [
    {{
      "title": "Confirmar presença",
      "content": "Oi Maria, confirmado! Estarei presente na sexta às 14h. Obrigado pelo aviso. Abs, João.",
      "tone": "cordial"
    }},
    {{
      "title": "Pedir reagendamento",
      "content": "Oi Maria, infelizmente tenho um conflito na sexta às 14h. Seria possível remarcar para outro horário? Fico no aguardo. Abs, João.",
      "tone": "formal"
    }}
  ]
}}
 
Now analyze the following email and return ONLY the JSON object.\
"""

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

    async def analyze(self, email_content: str, language: str = "pt") -> Dict[str, Any]:
        cache_key = hashlib.sha256(f"{language}:{email_content}".encode()).hexdigest()

        if cache_key in self.cache:
            logger.info("analyzer_cache_hit", key=cache_key[:8])
            return self.cache[cache_key]

        lang_instruction = "Respond in Portuguese (PT-BR)." if language == "pt" else "Respond in English."
        user_prompt = f"{lang_instruction}\n\nAnalyze this email:\n\n---\n{email_content.strip()}\n---"
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
