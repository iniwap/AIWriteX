from typing import Dict, Optional
from .llm_client import AIForgeLLMClient, AIForgeOllamaClient
from ..config.config import AIForgeConfig
from rich.console import Console


class AIForgeLLMManager:
    """LLM客户端管理器 - 懒加载策略"""

    def __init__(self, config: AIForgeConfig):
        self.config = config
        self.console = Console()
        self.clients = {}  # 缓存已创建的客户端
        self.current_client = None
        self._init_default_client()

    def _init_default_client(self):
        """只初始化默认LLM客户端"""
        llm_configs = self.config.config.get("llm", {})
        default_provider_name = self.config.config.get("default_llm_provider")

        # 首先尝试创建指定的默认客户端
        if default_provider_name and default_provider_name in llm_configs:
            default_config = llm_configs[default_provider_name]
            if default_config.get("enable", True):
                client = self._create_client(default_provider_name, default_config)
                if client and client.is_usable():
                    self.clients[default_provider_name] = client
                    self.current_client = client
                    return
                else:
                    self.console.print(
                        f"[yellow]默认LLM客户端 '{default_provider_name}' 不可用[/yellow]"
                    )

        # 如果默认客户端不可用，尝试第一个可用的客户端
        for name, llm_config in llm_configs.items():
            if not llm_config.get("enable", True):
                continue

            try:
                client = self._create_client(name, llm_config)
                if client and client.is_usable():
                    self.clients[name] = client
                    self.current_client = client
                    self.console.print(f"[green]使用第一个可用的LLM客户端: {name}[/green]")
                    return
            except Exception as e:
                self.console.print(f"[red]初始化LLM客户端 {name} 失败: {e}[/red]")

        self.console.print("[red]没有找到可用的LLM客户端[/red]")

    def _create_client(self, name: str, config: Dict) -> Optional[AIForgeLLMClient]:
        """创建LLM客户端"""
        client_type = config.get("type", "openai")

        if client_type in ["openai", "deepseek", "grok", "gemini", "qwen"]:
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
        """获取客户端 - 懒加载实现"""
        # 如果没有指定名称，返回当前客户端
        if not name:
            return self.current_client

        # 如果客户端已经创建，直接返回
        if name in self.clients:
            return self.clients[name]

        # 懒加载：按需创建客户端
        llm_configs = self.config.config.get("llm", {})
        if name in llm_configs:
            llm_config = llm_configs[name]
            if llm_config.get("enable", True):
                try:
                    client = self._create_client(name, llm_config)
                    if client and client.is_usable():
                        self.clients[name] = client
                        self.console.print(f"[green]懒加载创建LLM客户端: {name}[/green]")
                        return client
                    else:
                        self.console.print(f"[yellow]LLM客户端 '{name}' 不可用[/yellow]")
                except Exception as e:
                    self.console.print(f"[red]创建LLM客户端 {name} 失败: {e}[/red]")

        return None

    def switch_client(self, name: str) -> bool:
        """切换当前客户端"""
        client = self.get_client(name)  # 使用懒加载获取客户端
        if client:
            self.current_client = client
            self.console.print(f"[green]已切换到LLM客户端: {name}[/green]")
            return True
        else:
            self.console.print(f"[red]切换失败，客户端 '{name}' 不可用[/red]")
            return False

    def list_available_providers(self) -> Dict[str, str]:
        """列出所有配置的提供商（不创建客户端）"""
        llm_configs = self.config.config.get("llm", {})
        providers = {}
        for name, config in llm_configs.items():
            if config.get("enable", True):
                providers[name] = config.get("model", "unknown")
        return providers

    def list_active_clients(self) -> Dict[str, str]:
        """列出已创建的客户端"""
        return {name: client.model for name, client in self.clients.items()}

    def preload_clients(self, client_names: list = None):
        """预加载指定的客户端"""
        if client_names is None:
            # 预加载所有可用的客户端
            llm_configs = self.config.config.get("llm", {})
            client_names = [
                name for name, config in llm_configs.items() if config.get("enable", True)
            ]

        for name in client_names:
            if name not in self.clients:
                self.get_client(name)  # 触发懒加载

    def cleanup_unused_clients(self):
        """清理未使用的客户端（保留当前客户端）"""
        if self.current_client:
            current_name = self.current_client.name
            self.clients = {current_name: self.current_client}
            self.console.print(f"[green]已清理未使用的客户端，保留: {current_name}[/green]")
