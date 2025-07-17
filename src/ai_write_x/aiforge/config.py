import tomllib
from pathlib import Path
from rich.console import Console


class AIForgeConfig:
    """AIForge配置管理器"""

    def __init__(self, config_file: str = "aiforge.toml"):
        self.config_file = Path(config_file)
        self.console = Console()
        self.config = self._load_config()

    def _load_config(self):
        """加载TOML配置文件"""
        if not self.config_file.exists():
            self.console.print(f"[red]配置文件 {self.config_file} 不存在[/red]")
            return {}

        try:
            with open(self.config_file, "rb") as f:
                config = tomllib.load(f)
            return config
        except Exception as e:
            self.console.print(f"[red]加载配置文件失败: {e}[/red]")
            return {}

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
