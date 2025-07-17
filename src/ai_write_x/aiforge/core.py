from .config import AIForgeConfig
from .llm_manager import AIForgeLLMManager
from .task_manager import AIForgeManager
from typing import Optional, Dict, Any, Tuple


class AIForgeCore:
    """AIForge核心接口"""

    def __init__(self, config_file: str = "aiforge.toml"):
        self.config = AIForgeConfig(config_file)
        self.llm_manager = AIForgeLLMManager(self.config)
        self.task_manager = AIForgeManager(self.llm_manager, self.config.get_max_rounds())

    def generate_and_execute(
        self, instruction: str, system_prompt: str = None, provider: str = None
    ) -> Optional[Dict[str, Any]]:
        """生成并执行代码的一站式方法"""
        client = self.llm_manager.get_client(provider)
        if not client:
            return None

        task = None
        try:
            task = self.task_manager.new_task(instruction, client)
            task.run(instruction, system_prompt)

            # 返回最后一次成功执行的结果
            for entry in reversed(task.executor.history):
                if entry.get("success") and entry.get("result", {}).get("__result__"):
                    return entry["result"]["__result__"]

            return None
        finally:
            if task:
                task.done()

    def generate_and_execute_with_code(
        self, instruction: str, system_prompt: str = None, provider: str = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """生成并执行代码，同时返回结果和代码"""
        client = self.llm_manager.get_client(provider)
        if not client:
            return None, None

        task = None
        try:
            task = self.task_manager.new_task(instruction, client)
            task.run(instruction, system_prompt)

            # 查找最后一次成功执行的结果和对应的代码
            for entry in reversed(task.executor.history):
                if entry.get("success") and entry.get("result", {}).get("__result__"):
                    result = entry["result"]["__result__"]
                    code = entry.get("code", "")
                    return result, code

            return None, None
        finally:
            if task:
                task.done()

    def switch_provider(self, provider_name: str) -> bool:
        """切换LLM提供商"""
        return self.llm_manager.switch_client(provider_name)

    def list_providers(self) -> Dict[str, str]:
        """列出所有可用的提供商"""
        return {name: client.model for name, client in self.llm_manager.clients.items()}
