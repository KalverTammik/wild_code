"""
OpenAI GPT-4o API client for chat completions.
"""
import os
import openai

class Gpt4oClient:
    def __init__(self, api_key: str = None, system_prompt: str = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.system_prompt = system_prompt or "Oled pakkumismootori abiline."
        # For openai>=1.0.0, use a client instance
        self._client = openai.OpenAI(api_key=self.api_key)

    def ask(self, user_message: str, messages=None) -> str:
        """
        Send a message to GPT-4o and return the response content. Compatible with openai>=1.0.0.
        """
        if messages is None:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_message}
            ]
        # openai>=1.0.0: use client.chat.completions.create
        response = self._client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        return response.choices[0].message.content

    def ask_with_token_usage(self, user_message: str, messages=None):
        """
        Like ask(), but also returns token usage info. Compatible with openai>=1.0.0.
        """
        if messages is None:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_message}
            ]
        response = self._client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        content = response.choices[0].message.content
        usage = response.usage.model_dump() if hasattr(response, "usage") else {}
        return content, usage
