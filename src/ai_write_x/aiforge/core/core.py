from ..config.config import AIForgeConfig
from ..llm.llm_manager import AIForgeLLMManager
from .task_manager import AIForgeManager
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from ..cache.template_cache import TemplateBasedCodeCache
from ..execution.executor_interface import (
    DefaultModuleExecutor,
    FunctionBasedExecutor,
    CachedModuleExecutor,
    DataProcessingExecutor,
    WebRequestExecutor,
    FileOperationExecutor,
    APICallExecutor,
)
from .runner import AIForgeRunner
import importlib.resources


class AIForgeCore:
    """AIForge核心接口 - 支持多种初始化方式"""

    def __init__(
        self,
        config_file: Optional[str] = None,
        api_key: Optional[str] = None,
        provider: str = "openrouter",
        **kwargs,
    ):
        """
        初始化AIForge核心

        Args:
            config_file: 配置文件路径（可选）
            api_key: API密钥（快速启动模式）
            provider: LLM提供商名称
            **kwargs: 其他配置参数（max_rounds, workdir等）
        """
        # 初始化配置
        self.config = self._init_config(config_file, api_key, provider, **kwargs)

        # 初始化核心组件
        self.llm_manager = AIForgeLLMManager(self.config)
        self.task_manager = AIForgeManager(self.llm_manager, self.config.get_max_rounds())
        self.runner = AIForgeRunner(self.config.get_workdir())

        # 初始化缓存（如果启用）
        self._init_cache()

        # 初始化执行器
        self._init_executors()

    def _init_cache(self):
        """初始化缓存 - 默认使用继承了增强功能的模板缓存"""
        cache_config = self.config.get_cache_config("code")
        if cache_config.get("enabled", True):
            cache_dir = Path(self.config.get_workdir()) / "cache"
            # 默认使用继承了增强功能的模板缓存
            self.code_cache = TemplateBasedCodeCache(cache_dir, cache_config)
        else:
            self.code_cache = None

    def generate_and_execute_with_cache(self, instruction: str, **kwargs) -> tuple:
        """带缓存的代码生成和执行 - 自动使用模板+增强缓存功能"""
        # 自动清理检查
        if self.code_cache and self.code_cache.should_cleanup():
            self.code_cache.cleanup()

        # 由于使用的是TemplateBasedCodeCache（继承了EnhancedAiForgeCodeCache），
        # 直接使用模板缓存逻辑，它会自动回退到增强缓存策略
        if isinstance(self.code_cache, TemplateBasedCodeCache):
            return self.generate_and_execute_with_template_cache(instruction, **kwargs)

        # 原有的普通缓存逻辑（作为最后的回退）
        if self.code_cache:
            cached_modules = self.code_cache.get_cached_modules(instruction)
            for module_id, file_path, success_count, failure_count in cached_modules:
                module = self.code_cache.load_module(module_id)
                if module:
                    try:
                        result = self._execute_cached_module(module, instruction, **kwargs)
                        if result:
                            self.code_cache.update_module_stats(module_id, True)
                            return result, self._get_module_code(file_path)
                        else:
                            self.code_cache.update_module_stats(module_id, False)
                    except Exception:
                        self.code_cache.update_module_stats(module_id, False)

        # 缓存未命中，使用AI生成
        result, code = self.generate_and_execute_with_code(
            instruction, kwargs.get("system_prompt", None), kwargs.get("provider", None)
        )

        # 保存成功的代码到缓存
        if self.code_cache and result and code:
            if isinstance(self.code_cache, TemplateBasedCodeCache):
                self.code_cache.save_template_module(instruction, code)
            else:
                self.code_cache.save_code_module(instruction, code)

        return result, code

    def generate_and_execute_with_template_cache(self, instruction: str, **kwargs) -> tuple:
        """使用模板缓存的代码生成和执行 - 享受模板+增强缓存的双重优势"""

        if not isinstance(self.code_cache, TemplateBasedCodeCache):
            # 如果不是模板缓存，回退到原始方法
            return self.generate_and_execute_with_cache(instruction, **kwargs)

        # 尝试从模板缓存获取（会自动回退到增强缓存策略）
        cached_modules = self.code_cache.get_cached_modules_by_template(instruction)

        if cached_modules:
            template_info = self.code_cache._extract_template_info(instruction)
            current_params = template_info["parameters"]

            for (
                module_id,
                file_path,
                success_count,
                failure_count,
                original_params,
            ) in cached_modules:
                try:
                    # 使用当前参数执行模板模块
                    result = self.code_cache.execute_template_module(module_id, current_params)

                    if result:
                        self.code_cache.update_module_stats(module_id, True)
                        return result, self._get_module_code(file_path)
                    else:
                        self.code_cache.update_module_stats(module_id, False)

                except Exception:
                    self.code_cache.update_module_stats(module_id, False)

        # 缓存未命中，使用AI生成
        result, code = self.generate_and_execute_with_code(
            instruction, kwargs.get("system_prompt", None), kwargs.get("provider", None)
        )

        # 保存成功的代码到模板缓存
        if self.code_cache and result and code:
            self.code_cache.save_template_module(instruction, code)

        return result, code

    # 其他方法保持不变...
    def _init_config(
        self, config_file: Optional[str], api_key: Optional[str], provider: str, **kwargs
    ) -> AIForgeConfig:
        """初始化配置"""
        if api_key:
            return self._create_quick_config(api_key, provider, **kwargs)
        elif config_file:
            return AIForgeConfig(config_file)
        else:
            return self._create_default_config(**kwargs)

    def _create_quick_config(self, api_key: str, provider: str, **kwargs) -> AIForgeConfig:
        """创建快速启动配置"""
        default_config = self._get_default_config()

        if provider in default_config.get("llm", {}):
            default_config["llm"][provider]["api_key"] = api_key
            default_config["default_llm_provider"] = provider

        for key, value in kwargs.items():
            if key in ["max_rounds", "max_tokens", "workdir"]:
                default_config[key] = value

        return AIForgeConfig.from_dict(default_config)

    def _create_default_config(self, **kwargs) -> AIForgeConfig:
        """创建默认配置"""
        default_config = self._get_default_config()

        for key, value in kwargs.items():
            if key in default_config:
                default_config[key] = value

        return AIForgeConfig.from_dict(default_config)

    def _get_default_config(self) -> Dict:
        """获取内置默认配置"""
        try:
            with importlib.resources.open_text("aiforge.config", "default.toml") as f:
                import tomlkit

                return tomlkit.load(f)
        except Exception:
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
                    }
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
            }

    def _init_executors(self):
        """初始化内置执行器"""
        self.module_executors = [
            DefaultModuleExecutor(),
            FunctionBasedExecutor("search_web"),
            DataProcessingExecutor(),
            WebRequestExecutor(),
            FileOperationExecutor(),
            APICallExecutor(),
            FunctionBasedExecutor("main"),
            FunctionBasedExecutor("run"),
        ]

    def run(
        self, instruction: str, system_prompt: Optional[str] = None, provider: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """执行任务 - 统一入口"""
        return self.run_task(instruction, system_prompt, provider)

    def __call__(self, instruction: str, **kwargs) -> Optional[Dict[str, Any]]:
        """支持直接调用"""
        return self.run(instruction, **kwargs)

    def run_task(
        self, instruction: str, system_prompt: str = None, provider: str = None
    ) -> Optional[Dict[str, Any]]:
        """任务执行入口"""
        if self.code_cache:
            result, _ = self.generate_and_execute_with_cache(
                instruction, system_prompt=system_prompt, provider=provider
            )
        else:
            result, _ = self.generate_and_execute_with_code(instruction, system_prompt, provider)
        return result

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

    # 保留其他必要的方法
    def _execute_cached_module(self, module, instruction: str, **kwargs):
        """执行缓存的模块 - 使用策略模式"""
        for executor in self.module_executors:
            if executor.can_handle(module):
                result = executor.execute(module, instruction, **kwargs)
                if result is not None:
                    return result
        return None

    def _get_module_code(self, file_path: str) -> str:
        """获取模块代码"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""

    def add_module_executor(self, executor: CachedModuleExecutor):
        """添加自定义模块执行器"""
        self.module_executors.insert(0, executor)

    def switch_provider(self, provider_name: str) -> bool:
        """切换LLM提供商"""
        return self.llm_manager.switch_client(provider_name)

    def list_providers(self) -> Dict[str, str]:
        """列出所有可用的提供商"""
        return {name: client.model for name, client in self.llm_manager.clients.items()}

    def execute_with_runner(self, code: str) -> Dict[str, Any]:
        """使用runner执行代码"""
        return self.runner.execute_code(code)
