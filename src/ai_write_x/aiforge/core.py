from .config import AIForgeConfig
from .llm_manager import AIForgeLLMManager
from .task_manager import AIForgeManager
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from .code_cache import AiForgeCodeCache
from .executor_interface import (
    DefaultModuleExecutor,
    FunctionBasedExecutor,
    CachedModuleExecutor,
    DataProcessingExecutor,
    WebRequestExecutor,
    FileOperationExecutor,
    APICallExecutor,
)


class AIForgeCore:
    """AIForge核心接口"""

    def __init__(self, config_file: str = "aiforge.toml"):
        self.config = AIForgeConfig(config_file)
        self.llm_manager = AIForgeLLMManager(self.config)
        self.task_manager = AIForgeManager(self.llm_manager, self.config.get_max_rounds())

        # 初始化缓存
        cache_config = self.config.get_cache_config("code")
        if cache_config.get("enabled", True):
            cache_dir = Path(self.config.get_work_dir()) / "cache"
            self.code_cache = AiForgeCodeCache(cache_dir, cache_config)
        else:
            self.code_cache = None

        # 初始化内置执行器（按优先级排序）
        self.module_executors = [
            DefaultModuleExecutor(),  # 默认执行器
            FunctionBasedExecutor("search_web"),  # 搜索功能
            DataProcessingExecutor(),  # 数据处理
            WebRequestExecutor(),  # 网络请求
            FileOperationExecutor(),  # 文件操作
            APICallExecutor(),  # API调用
            FunctionBasedExecutor("main"),  # 通用main函数
            FunctionBasedExecutor("run"),  # 通用run函数
        ]

    def add_module_executor(self, executor: CachedModuleExecutor):
        """添加自定义模块执行器"""
        self.module_executors.insert(0, executor)  # 插入到前面，优先使用

    def _execute_cached_module(self, module, instruction: str, **kwargs):
        """执行缓存的模块 - 使用策略模式"""
        for executor in self.module_executors:
            if executor.can_handle(module):
                result = executor.execute(module, instruction, **kwargs)
                if result is not None:
                    return result

        return None

    def generate_and_execute_with_cache(self, instruction: str, **kwargs) -> tuple:
        """带缓存的代码生成和执行"""
        # 自动清理检查
        if self.code_cache and self.code_cache.should_cleanup():
            self.code_cache.cleanup()

        # 尝试从缓存获取
        if self.code_cache:
            cached_modules = self.code_cache.get_cached_modules(instruction)

            for module_id, file_path, success_count, failure_count in cached_modules:
                module = self.code_cache.load_module(module_id)
                if module:
                    try:
                        # 使用策略模式执行缓存的代码
                        result = self._execute_cached_module(module, instruction, **kwargs)
                        if result:
                            self.code_cache.update_module_stats(module_id, True)
                            return result, self._get_module_code(file_path)
                        else:
                            self.code_cache.update_module_stats(module_id, False)
                    except Exception:
                        self.code_cache.update_module_stats(module_id, False)

        # 缓存未命中，使用AI生成
        result, code = self.generate_and_execute_with_code(instruction)

        # 保存成功的代码到缓存
        if self.code_cache and result and code:
            self.code_cache.save_code_module(instruction, code)

        return result, code

    def _get_module_code(self, file_path: str) -> str:
        """获取模块代码"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""

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
