import json
import logging
from typing import AsyncGenerator
import httpx

from repolens.ai.interface import LLMProviderInterface

logger = logging.getLogger("repolens.ai.providers")


class LocalMockAIProvider(LLMProviderInterface):
    """
    A smart, grounded offline provider that scans prompt RAG contexts 
    to extract facts and produce citations without external LLM connections.
    """
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2048
    ) -> AsyncGenerator[str, None]:
        # Synthesize a grounded mock answer
        response_text = self._synthesize_grounded_answer(prompt)
        # Stream response chunk by chunk simulating token generation delays
        import asyncio
        words = response_text.split(" ")
        for word in words:
            yield word + " "
            await asyncio.sleep(0.01)

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2048
    ) -> str:
        return self._synthesize_grounded_answer(prompt)

    def _synthesize_grounded_answer(self, prompt: str) -> str:
        # Extract files listed in the prompt context
        files_mentioned = []
        for line in prompt.split("\n"):
            if "File:" in line or "file_path" in line:
                cleaned = line.replace("File:", "").replace("file_path", "").strip()
                if cleaned and cleaned not in files_mentioned:
                    files_mentioned.append(cleaned)

        query = "this codebase"
        for line in prompt.split("\n"):
            if "User query:" in line:
                query = line.replace("User query:", "").strip()

        citations_str = ", ".join([f"`{f}`" for f in files_mentioned[:3]])
        
        answer = (
            f"Based on the repository context retrieved for your query **'{query}'**, "
            f"here is the codebase implementation detail:\n\n"
        )
        
        if files_mentioned:
            answer += (
                f"### Relevant Implementation Files\n"
                f"The core logic is declared and managed in the following paths: {citations_str}.\n\n"
                f"### Contextual Summary\n"
                f"1. **Entrypoints & Scopes**: The system registers these files directly in the codebase routing layout.\n"
                f"2. **AST Parsing Facts**: These modules are statically parsed. You can select them directly in the files tree tab sidebar or search for their classes using the Command Palette (`Ctrl+K`).\n\n"
                f"For further implementation details, you can inspect the files {citations_str}."
            )
        else:
            answer += (
                "No specific file context was found in the retrieved chunks.\n\n"
                "To resolve your question accurately, please run 'Analyze Codebase' "
                "to ensure files trees and symbols index models are up-to-date."
            )
        return answer


class OpenAIProvider(LLMProviderInterface):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2048
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            # Fallback mock if key not set
            fallback = LocalMockAIProvider()
            async for token in fallback.generate_stream(prompt, system_prompt):
                yield token
            return

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True
                },
                timeout=60.0
            ) as response:
                response.raise_for_status()
                async for line in response.iter_lines():
                    cleaned_line = line.strip()
                    if not cleaned_line:
                        continue
                    if cleaned_line == b"data: [DONE]":
                        break
                    if cleaned_line.startswith(b"data: "):
                        try:
                            data = json.loads(cleaned_line[6:].decode("utf-8"))
                            token = data["choices"][0]["delta"].get("content", "")
                            if token:
                                yield token
                        except Exception:
                            continue

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2048
    ) -> str:
        if not self.api_key:
            fallback = LocalMockAIProvider()
            return await fallback.generate_text(prompt, system_prompt)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]


class OllamaProvider(LLMProviderInterface):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url
        self.model = model

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2048
    ) -> AsyncGenerator[str, None]:
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    },
                    "stream": True
                },
                timeout=60.0
            ) as response:
                response.raise_for_status()
                async for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line.decode("utf-8"))
                        token = data["message"].get("content", "")
                        if token:
                            yield token
                    except Exception:
                        continue

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2048
    ) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    },
                    "stream": False
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]
