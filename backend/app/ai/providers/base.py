from abc import ABC, abstractmethod
from typing import AsyncGenerator

class BaseAIProvider(ABC):
    @abstractmethod
    async def generate_completion(self, prompt: str, system_prompt: str = None) -> str:
        pass

    @abstractmethod
    async def stream_completion(self, prompt: str, system_prompt: str = None) -> AsyncGenerator[str, None]:
        pass
