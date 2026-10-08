"""
LLMService — abstraction layer for optional external LLM integration.
Supported providers: openai, gemini, watsonx.
Falls back gracefully if no key is configured.
"""
import os
from flask import current_app


class LLMService:
    def __init__(self):
        self.provider = (current_app.config.get('AI_PROVIDER') or '').lower()
        self.api_key = current_app.config.get('AI_API_KEY') or ''

    def is_available(self) -> bool:
        return bool(self.provider and self.api_key)

    def ask(self, question: str, context: str) -> str:
        """Send question + data context to the configured LLM."""
        system_prompt = (
            "You are FoodWise Assistant, an AI that helps food service organizations "
            "reduce food waste and improve redistribution. "
            "Use ONLY the provided data context to answer — never invent numbers. "
            "Be concise and actionable."
        )
        full_prompt = f"Data context:\n{context}\n\nUser question: {question}"

        if self.provider == 'openai':
            return self._openai(system_prompt, full_prompt)
        elif self.provider == 'gemini':
            return self._gemini(system_prompt, full_prompt)
        elif self.provider == 'watsonx':
            return self._watsonx(system_prompt, full_prompt)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def _openai(self, system: str, prompt: str) -> str:
        import openai
        client = openai.OpenAI(api_key=self.api_key)
        resp = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': prompt},
            ],
            max_tokens=400,
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()

    def _gemini(self, system: str, prompt: str) -> str:
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        full = f"{system}\n\n{prompt}"
        resp = model.generate_content(full)
        return resp.text.strip()

    def _watsonx(self, system: str, prompt: str) -> str:
        from ibm_watsonx_ai.foundation_models import ModelInference
        from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
        model = ModelInference(
            model_id='ibm/granite-13b-chat-v2',
            credentials={'apikey': self.api_key,
                         'url': current_app.config.get('WATSONX_URL')},
            project_id=current_app.config.get('WATSONX_PROJECT_ID'),
            params={GenParams.MAX_NEW_TOKENS: 400, GenParams.TEMPERATURE: 0.3},
        )
        full_prompt = f"{system}\n\n{prompt}"
        return model.generate_text(prompt=full_prompt)
