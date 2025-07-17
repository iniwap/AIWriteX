from typing import Dict, Optional
from .llm_client import AIForgeLLMClient, AIForgeOllamaClient
from .config import AIForgeConfig
from rich.console import Console


class AIForgeLLMManager:
    """LLM客户端管理器"""

    def __init__(self, config: AIForgeConfig):
        self.config = config
        self.console = Console()
        self.clients = {}
        self.current_client = None
        self._init_clients()

    def _init_clients(self):
        """初始化所有LLM客户端"""
        llm_configs = self.config.config.get("llm", {})

        for name, llm_config in llm_configs.items():
            if not llm_config.get("enable", True):
                continue

            try:
                client = self._create_client(name, llm_config)
                if client and client.is_usable():
                    self.clients[name] = client

                    # 设置默认客户端
                    if llm_config.get("default", False) or not self.current_client:
                        self.current_client = client

            except Exception as e:
                self.console.print(f"[red]初始化LLM客户端 {name} 失败: {e}[/red]")

    def _create_client(self, name: str, config: Dict) -> Optional[AIForgeLLMClient]:
        """创建LLM客户端"""
        client_type = config.get("type", "openai")

        # 根据类型创建不同的客户端
        if client_type in ["openai", "deepseek", "grok", "gemini"]:
            return AIForgeLLMClient(
                name=name,
                api_key=config.get("api_key", ""),
                base_url=config.get("base_url"),
                model=config.get("model"),
                timeout=config.get("timeout", 30),
                max_tokens=config.get("max_tokens", 8192),
            )
        elif client_type == "ollama":
            return AIForgeOllamaClient(
                name=name,
                base_url=config.get("base_url", "http://localhost:11434"),
                model=config.get("model"),
                timeout=config.get("timeout", 30),
                max_tokens=config.get("max_tokens", 8192),
            )
        else:
            self.console.print(f"[yellow]不支持的LLM类型: {client_type}[/yellow]")
            return None

    def get_client(self, name: str = None) -> Optional[AIForgeLLMClient]:
        """获取指定的客户端"""
        if name:
            return self.clients.get(name)
        return self.current_client

    def switch_client(self, name: str) -> bool:
        """切换当前客户端"""
        if name in self.clients:
            self.current_client = self.clients[name]
            return True
        return False
