import requests
import re
from typing import Optional
from rich.console import Console


class AIForgeLLMClient:
    """AIForge LLM客户端基类"""

    def __init__(
        self,
        name: str,
        api_key: str,
        base_url: str = None,
        model: str = "gpt-3.5-turbo",
        timeout: int = 30,
        max_tokens: int = 8192,
        client_type: str = "openai",
    ):
        self.name = name
        self.api_key = api_key
        self.base_url = base_url or "https://api.openai.com/v1"
        self.model = model
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.console = Console()
        self.client_type = client_type

        # 新增：对话历史和使用统计
        self.conversation_history = []
        self.usage_stats = {"total_tokens": 0, "rounds": 0}

    def is_usable(self) -> bool:
        """检查客户端是否可用"""
        if hasattr(self, "client_type") and self.client_type == "ollama":
            return bool(self.model and self.base_url)
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

                # 更新使用统计
                if "usage" in result:
                    usage = result["usage"]
                    self.usage_stats["total_tokens"] += usage.get("total_tokens", 0)
                self.usage_stats["rounds"] += 1

                return result["choices"][0]["message"]["content"]
            else:
                self.console.print(f"[red]{self.name} API错误: {response.status_code}[/red]")
                return None

        except Exception as e:
            self.console.print(f"[red]{self.name} 请求失败: {e}[/red]")
            return None

    def generate_code_with_history(
        self, instruction: str, system_prompt: str = None
    ) -> Optional[str]:
        """带历史上下文的代码生成"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            # 添加历史对话
            messages.extend(self.conversation_history)

            # 添加当前指令（如果不是重复的）
            if not messages or messages[-1]["content"] != instruction:
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
                assistant_response = result["choices"][0]["message"]["content"]

                # 将AI响应添加到历史记录
                self.conversation_history.append(
                    {"role": "assistant", "content": assistant_response}
                )

                # 更新使用统计
                if "usage" in result:
                    usage = result["usage"]
                    self.usage_stats["total_tokens"] += usage.get("total_tokens", 0)
                self.usage_stats["rounds"] += 1

                return assistant_response
            else:
                self.console.print(f"[red]{self.name} API错误: {response.status_code}[/red]")
                return None

        except Exception as e:
            self.console.print(f"[red]{self.name} 请求失败: {e}[/red]")
            return None

    def send_feedback(self, feedback: str):
        """发送反馈信息给LLM"""
        self.conversation_history.append({"role": "user", "content": feedback})

        # 使用历史上下文生成响应
        response = self.generate_code_with_history(feedback)
        if response:
            self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def get_usage_stats(self):
        """获取使用统计"""
        return self.usage_stats.copy()

    def reset_usage_stats(self):
        """重置使用统计"""
        self.usage_stats = {"total_tokens": 0, "rounds": 0}

    def _compress_error(self, error_msg: str, max_length: int = 200) -> str:
        """压缩错误信息以减少token消耗"""
        if not error_msg or len(error_msg) <= max_length:
            return error_msg

        # 提取关键错误信息的正则模式
        key_patterns = [
            r"(NameError|TypeError|ValueError|AttributeError|ImportError|SyntaxError): (.+)",
            r"line (\d+)",
            r'File "([^"]+)"',
            r"in (.+)",
            r"(\w+Exception): (.+)",
        ]

        compressed_parts = []

        # 按优先级提取关键信息
        for pattern in key_patterns:
            matches = re.findall(pattern, error_msg)
            if matches:
                for match in matches[:2]:  # 最多保留2个匹配项
                    if isinstance(match, tuple):
                        compressed_parts.extend([str(m) for m in match])
                    else:
                        compressed_parts.append(str(match))

        # 如果没有匹配到关键模式，截取开头部分
        if not compressed_parts:
            return error_msg[:max_length] + "..." if len(error_msg) > max_length else error_msg

        # 组合压缩后的信息
        compressed = " | ".join(compressed_parts[:5])  # 最多保留5个关键信息

        # 确保不超过最大长度
        if len(compressed) > max_length:
            compressed = compressed[: max_length - 3] + "..."

        return compressed


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

    def send_feedback(self, feedback: str):
        """发送反馈信息给LLM"""
        # 将反馈作为下一轮对话的上下文
        self.conversation_history.append({"role": "user", "content": feedback})

        # 或者直接发送给LLM获取响应
        response = self.generate_code(feedback, system_prompt=None)
        return response
