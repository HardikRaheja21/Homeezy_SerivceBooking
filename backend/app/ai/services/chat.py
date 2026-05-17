from typing import AsyncGenerator, Optional
from app.ai.providers.openrouter import OpenRouterProvider
from app.ai.prompts.assistant import SYSTEM_PROMPT_ASSISTANT

class AIChatService:
    def __init__(self):
        self.provider = OpenRouterProvider()

    async def stream_chat(
        self,
        message: str,
        history: Optional[list] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream a chat response, maintaining conversation history."""
        async for chunk in self.provider.stream_completion(
            prompt=message,
            system_prompt=SYSTEM_PROMPT_ASSISTANT,
            history=history,
        ):
            yield chunk
