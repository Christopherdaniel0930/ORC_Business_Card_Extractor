import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class OllamaClient:
    """Client for an Ollama compatible chat completions endpoint."""

    def __init__(self):
        self.model = os.getenv("OLLAMA_MODEL")
        if not self.model:
            raise RuntimeError("OLLAMA_MODEL is not configured")
        self.client = OpenAI(
            api_key=os.getenv("OLLAMA_API_KEY", "ollama"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://ollama/v1"),
        )

    def extract(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Extract business card fields from OCR. Never invent information."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("Ollama returned an empty response")
        return content
