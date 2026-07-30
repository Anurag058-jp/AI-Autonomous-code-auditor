import json
import httpx
from .config import settings


class LLMClient:
    def enabled(self) -> bool:
        return bool({"groq": settings.groq_api_key, "mistral": settings.mistral_api_key, "gemini": settings.gemini_api_key}.get(settings.audit_llm_provider))

    def draft(self, prompt: str) -> str:
        provider = settings.audit_llm_provider
        if provider == "groq":
            response = httpx.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {settings.groq_api_key}"}, json={"model": settings.audit_llm_model, "messages": [{"role": "system", "content": "You are a secure-code reviewer. Return only requested output."}, {"role": "user", "content": prompt}]}, timeout=60)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        if provider == "mistral":
            response = httpx.post("https://api.mistral.ai/v1/chat/completions", headers={"Authorization": f"Bearer {settings.mistral_api_key}"}, json={"model": settings.audit_llm_model or "mistral-small-latest", "messages": [{"role": "user", "content": prompt}]}, timeout=60)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        raise RuntimeError("Gemini support requires selecting a Gemini model adapter; use Groq or Mistral for this release.")

    def analyze(self, chunks: list[dict]) -> list[dict]:
        prompt = """Review these code chunks for OWASP Top 10 vulnerabilities, performance bottlenecks, and architectural smells. Return a JSON array only. Each object must contain severity (critical|high|medium|low), title, description, file_path, start_line, end_line, evidence, remediation, and confidence (0..1). Report only actionable, high-confidence findings. Chunks:\n""" + json.dumps(chunks)
        response = self.draft(prompt)
        start, end = response.find("["), response.rfind("]")
        if start < 0 or end < start:
            return []
        try:
            data = json.loads(response[start:end + 1])
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []
