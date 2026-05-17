import aiohttp
import json
from typing import AsyncGenerator, Optional
from app.core.config import settings
from app.ai.providers.base import BaseAIProvider

# 60-second timeout prevents stalled OpenRouter connections from blocking threads
_AI_TIMEOUT = aiohttp.ClientTimeout(total=60, connect=10)

class OpenRouterProvider(BaseAIProvider):
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = settings.DEFAULT_AI_MODEL

    def _build_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://homeezy.com",
            "X-Title": "Homeezy AI",
            "Content-Type": "application/json"
        }

    def _build_messages(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[list] = None,
    ) -> list:
        """Build the messages array in OpenAI chat format, including history."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        # Replay conversation history so the model has memory
        if history:
            for turn in history:
                role = turn.get("role", "user")
                content = turn.get("content", "")
                if role in ("user", "assistant") and content:
                    messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": prompt})
        return messages

    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[list] = None,
    ) -> str:
        messages = self._build_messages(prompt, system_prompt, history)
        payload = {"model": self.model, "messages": messages}

        async with aiohttp.ClientSession(timeout=_AI_TIMEOUT) as session:
            async with session.post(self.base_url, headers=self._build_headers(), json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenRouter Error: {response.status} - {error_text}")
                data = await response.json()
                return data["choices"][0]["message"]["content"]

    async def stream_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[list] = None,
    ) -> AsyncGenerator[str, None]:
        messages = self._build_messages(prompt, system_prompt, history)
        payload = {"model": self.model, "messages": messages, "stream": True}

        async with aiohttp.ClientSession(timeout=_AI_TIMEOUT) as session:
            async with session.post(self.base_url, headers=self._build_headers(), json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenRouter Stream Error: {response.status} - {error_text}")

                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: ') and line != 'data: [DONE]':
                        try:
                            data = json.loads(line[6:])
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue

