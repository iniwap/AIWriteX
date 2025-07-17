import requests
from typing import Optional
from rich.console import Console


class AIForgeLLMClient:
    """AiForge LLM客户端基类"""

    def __init__(
        self,
        name: str,
        api_key: str,
        base_url: str = None,
        model: str = "gpt-3.5-turbo",
        timeout: int = 30,
        max_tokens: int = 8192,
    ):
        self.name = name
        self.api_key = api_key
        self.base_url = base_url or "https://api.openai.com/v1"
        self.model = model
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.console = Console()

    def is_usable(self) -> bool:
        """检查客户端是否可用"""
        return bool(self.api_key and self.model)

    def generate_code(self, instruction: str, system_prompt: str = None) -> Optional[str]:
        """生成代码的核心方法"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": instruction})

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": self.max_tokens,
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                self.console.print(f"[red]{self.name} API错误: {response.status_code}[/red]")
                return None

        except Exception as e:
            self.console.print(f"[red]{self.name} 请求失败: {e}[/red]")
            return None


class AIForgeOllamaClient(AIForgeLLMClient):
    """Ollama客户端实现"""

    def __init__(
        self, name: str, base_url: str, model: str, timeout: int = 30, max_tokens: int = 8192
    ):
        super().__init__(name, "", base_url, model, timeout, max_tokens)

    def is_usable(self) -> bool:
        """Ollama不需要API key"""
        return bool(self.model and self.base_url)

    def generate_code(self, instruction: str, system_prompt: str = None) -> Optional[str]:
        """Ollama特定的实现"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": instruction})

            payload = {"model": self.model, "messages": messages, "stream": False}

            response = requests.post(
                f"{self.base_url}/api/chat", json=payload, timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return result["message"]["content"]
            else:
                self.console.print(f"[red]{self.name} API错误: {response.status_code}[/red]")
                return None

        except Exception as e:
            self.console.print(f"[red]{self.name} 请求失败: {e}[/red]")
            return None
