from abc import ABC, abstractmethod
from typing import Any, Optional

"""
# 基本使用 - 使用默认执行器
forge = AIForgeCore("aiforge.toml")
result, code = forge.generate_and_execute_with_cache("获取天气信息")

# 自定义执行器
class WeatherModuleExecutor(CachedModuleExecutor):
    def can_handle(self, module):
        return hasattr(module, 'get_weather')

    def execute(self, module, instruction, **kwargs):
        return module.get_weather(kwargs.get('city', 'Beijing'))

# 添加自定义执行器
forge.add_module_executor(WeatherModuleExecutor())

# 带参数执行
result, code = forge.generate_and_execute_with_cache(
    "获取天气信息",
    city="Shanghai"
)
"""


class CachedModuleExecutor(ABC):
    """缓存模块执行器接口"""

    @abstractmethod
    def execute(self, module: Any, instruction: str, **kwargs) -> Optional[Any]:
        """执行缓存的模块"""
        pass

    @abstractmethod
    def can_handle(self, module: Any) -> bool:
        """判断是否能处理该模块"""
        pass


class DefaultModuleExecutor(CachedModuleExecutor):
    """默认模块执行器"""

    def can_handle(self, module: Any) -> bool:
        return (
            hasattr(module, "__result__")
            or hasattr(module, "main")
            or callable(getattr(module, "run", None))
        )

    def execute(self, module: Any, instruction: str, **kwargs) -> Optional[Any]:
        # 优先级顺序：__result__ > main() > run() > 模块本身可调用
        if hasattr(module, "__result__"):
            return module.__result__

        if hasattr(module, "main") and callable(module.main):
            try:
                return module.main(instruction, **kwargs)
            except Exception:
                return None

        if hasattr(module, "run") and callable(module.run):
            try:
                return module.run(instruction, **kwargs)
            except Exception:
                return None

        if callable(module):
            try:
                return module(instruction, **kwargs)
            except Exception:
                return None

        return None


class FunctionBasedExecutor(CachedModuleExecutor):
    """基于特定函数的执行器"""

    def __init__(self, function_name: str):
        self.function_name = function_name

    def can_handle(self, module: Any) -> bool:
        return hasattr(module, self.function_name) and callable(getattr(module, self.function_name))

    def execute(self, module: Any, instruction: str, **kwargs) -> Optional[Any]:
        try:
            func = getattr(module, self.function_name)
            return func(instruction, **kwargs)
        except Exception:
            return None


class DataProcessingExecutor(CachedModuleExecutor):
    """数据处理模块执行器"""

    def can_handle(self, module: Any) -> bool:
        return (
            hasattr(module, "process_data")
            or hasattr(module, "analyze_data")
            or hasattr(module, "transform_data")
        )

    def execute(self, module: Any, instruction: str, **kwargs) -> Optional[Any]:
        for func_name in ["process_data", "analyze_data", "transform_data"]:
            if hasattr(module, func_name):
                try:
                    func = getattr(module, func_name)
                    return func(kwargs.get("data"), **kwargs)
                except Exception:
                    continue
        return None


class WebRequestExecutor(CachedModuleExecutor):
    """网络请求模块执行器"""

    def can_handle(self, module: Any) -> bool:
        return (
            hasattr(module, "fetch_data")
            or hasattr(module, "get_url")
            or hasattr(module, "scrape_web")
        )

    def execute(self, module: Any, instruction: str, **kwargs) -> Optional[Any]:
        for func_name in ["fetch_data", "get_url", "scrape_web"]:
            if hasattr(module, func_name):
                try:
                    func = getattr(module, func_name)
                    return func(kwargs.get("url", instruction), **kwargs)
                except Exception:
                    continue
        return None


class FileOperationExecutor(CachedModuleExecutor):
    """文件操作模块执行器"""

    def can_handle(self, module: Any) -> bool:
        return (
            hasattr(module, "process_file")
            or hasattr(module, "read_file")
            or hasattr(module, "write_file")
        )

    def execute(self, module: Any, instruction: str, **kwargs) -> Optional[Any]:
        for func_name in ["process_file", "read_file", "write_file"]:
            if hasattr(module, func_name):
                try:
                    func = getattr(module, func_name)
                    return func(kwargs.get("file_path"), **kwargs)
                except Exception:
                    continue
        return None


class APICallExecutor(CachedModuleExecutor):
    """API调用模块执行器"""

    def can_handle(self, module: Any) -> bool:
        return (
            hasattr(module, "call_api")
            or hasattr(module, "api_request")
            or hasattr(module, "invoke_service")
        )

    def execute(self, module: Any, instruction: str, **kwargs) -> Optional[Any]:
        for func_name in ["call_api", "api_request", "invoke_service"]:
            if hasattr(module, func_name):
                try:
                    func = getattr(module, func_name)
                    return func(**kwargs)
                except Exception:
                    continue
        return None
