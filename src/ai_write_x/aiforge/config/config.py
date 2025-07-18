import tomlkit
from pathlib import Path
from rich.console import Console
from typing import Optional, Dict
import importlib.resources


class AIForgeConfig:
    """AIForge配置管理器 - 支持多种初始化方式"""

    def __init__(self, config_file: Optional[str] = None):
        self.console = Console()

        if config_file:
            self.config_file = Path(config_file)
            self.config = self._load_from_file()
        else:
            self.config_file = None
            self.config = {}

    @classmethod
    def from_dict(cls, config_dict: Dict) -> "AIForgeConfig":
        """从字典创建配置实例"""
        instance = cls()
        instance.config = config_dict
        return instance

    @classmethod
    def from_api_key(cls, api_key: str, provider: str = "openrouter", **kwargs) -> "AIForgeConfig":
        """从API key快速创建配置"""
        default_config = cls._get_builtin_default_config()

        # 设置API key
        if provider in default_config.get("llm", {}):
            default_config["llm"][provider]["api_key"] = api_key
            default_config["default_llm_provider"] = provider

        # 应用其他参数
        for key, value in kwargs.items():
            if key in ["max_rounds", "max_tokens", "workdir"]:
                default_config[key] = value

        return cls.from_dict(default_config)

    def _load_from_file(self) -> Dict:
        """从文件加载配置"""
        if not self.config_file.exists():
            self.console.print(f"[red]配置文件 {self.config_file} 不存在[/red]")
            return {}

        try:
            with open(self.config_file, "rb") as f:
                config = tomlkit.load(f)
            return config
        except Exception as e:
            self.console.print(f"[red]加载配置文件失败: {e}[/red]")
            return {}

    @staticmethod
    def _get_builtin_default_config() -> Dict:
        """获取内置默认配置"""
        try:
            # 尝试从包内资源加载默认配置
            with importlib.resources.open_text("aiforge.config", "default.toml") as f:

                return tomlkit.load(f)
        except Exception:
            # 如果无法加载，返回硬编码的最小配置
            return {
                "workdir": "aiforge_work",
                "max_tokens": 4096,
                "max_rounds": 5,
                "default_llm_provider": "openrouter",
                "llm": {
                    "openrouter": {
                        "type": "openai",
                        "model": "deepseek/deepseek-chat-v3-0324:free",
                        "api_key": "",
                        "base_url": "https://openrouter.ai/api/v1",
                        "timeout": 30,
                        "max_tokens": 8192,
                        "enable": True,
                    },
                    "deepseek": {
                        "type": "deepseek",
                        "model": "deepseek-chat",
                        "api_key": "",
                        "base_url": "https://api.deepseek.com",
                        "timeout": 30,
                        "max_tokens": 8192,
                        "enable": True,
                    },
                    "ollama": {
                        "type": "ollama",
                        "model": "llama3",
                        "api_key": "",
                        "base_url": "http://localhost:11434",
                        "timeout": 30,
                        "max_tokens": 8192,
                        "enable": True,
                    },
                },
                "cache": {
                    "code": {
                        "enabled": True,
                        "max_modules": 20,
                        "failure_threshold": 0.8,
                        "max_age_days": 30,
                        "cleanup_interval": 10,
                    }
                },
                "optimization": {
                    "enabled": False,
                    "aggressive_minify": False,
                    "max_feedback_length": 200,
                    "compress_strings": True,
                    "obfuscate_variables": True,
                },
            }

    # 保留原有方法
    def get_llm_config(self, provider_name: str = None):
        """获取LLM配置"""
        llm_configs = self.config.get("llm", {})

        if provider_name:
            return llm_configs.get(provider_name, {})

        # 返回默认或第一个启用的提供商
        default_provider = self.config.get("default_llm_provider")
        if default_provider and default_provider in llm_configs:
            config = llm_configs[default_provider]
            if config.get("enable", True):
                return config

        # 查找第一个启用的提供商
        for name, config in llm_configs.items():
            if config.get("enable", True):
                return config

        return {}

    def get_workdir(self):
        """获取工作目录"""
        return Path(self.config.get("workdir", "aiforge_work"))

    def get_max_tokens(self):
        """获取最大token数"""
        return self.config.get("max_tokens", 4096)

    def get_max_rounds(self):
        """获取最大尝试次数"""
        return self.config.get("max_rounds", 5)

    def get_cache_config(self, cache_type):
        """获取缓存配置"""
        return self.config.get("cache", {}).get(cache_type, {})

    def get_default_llm_provider(self) -> str:
        """获取默认LLM提供商"""
        return self.config.get("default_llm_provider", "")

    def get(self, key: str, default=None):
        """获取配置值"""
        return self.config.get(key, default)

    def update(self, new_config: Dict):
        """更新配置"""
        self.config.update(new_config)

    def save_to_file(self, file_path: str):
        """保存配置到文件"""
        with open(file_path, "w", encoding="utf-8") as f:
            tomlkit.dump(self.config, f)
