import re
from typing import Dict, Any, List
from rich.console import Console
import traceback

INIT_IMPORTS = """
import os
import re
import sys
import json
import time
import random
import requests
import urllib.parse
from urllib.parse import quote
from bs4 import BeautifulSoup
import datetime
from datetime import datetime, timedelta
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
"""


class AIForgeExecutor:
    """AIForge代码执行引擎"""

    def __init__(self):
        self.history = []
        self.console = Console()

    def _preprocess_code(self, code: str) -> str:
        """预处理代码"""
        # 移除整个代码块开头和结尾的空白字符
        code = code.strip()

        # 分行处理每一行
        lines = code.split("\n")
        processed_lines = []

        for line in lines:
            # 将制表符转换为空格
            line = line.expandtabs(4)
            # 保持行的原样（不要去除单行的空白以保持缩进）
            processed_lines.append(line)

        return "\n".join(processed_lines)

    def execute_python_code(self, code: str) -> Dict[str, Any]:
        """执行Python代码并返回结果"""
        try:
            exec_globals = {
                "__builtins__": __builtins__,
            }
            exec_locals = {}

            # 预处理代码
            code = self._preprocess_code(code)
            # 先尝试编译以捕获语法错误
            compile(code, "<string>", "exec")

            exec(INIT_IMPORTS, exec_globals)
            exec(code, exec_globals, exec_locals)

            result = self._extract_result(exec_locals)

            execution_result = {
                "success": True,
                "result": result,
                "locals": exec_locals,
                "code": code,
            }

            # 记录执行历史
            self.history.append({"code": code, "result": {"__result__": result}, "success": True})

            return execution_result

        except SyntaxError as e:
            return {
                "success": False,
                "error": f"语法错误: {str(e)} (行 {e.lineno})",
                "traceback": traceback.format_exc(),
                "code": code,
            }
        except Exception as e:
            error_result = {"success": False, "error": str(e), "code": code}

            self.history.append(
                {"code": code, "result": {"__result__": None, "error": str(e)}, "success": False}
            )

            return error_result

    def _extract_result(self, locals_dict: dict) -> Any:
        """智能提取执行结果"""
        if "__result__" in locals_dict:
            return locals_dict["__result__"]

        result_keys = ["result", "output", "data", "response", "return_value"]
        for key in result_keys:
            if key in locals_dict:
                return locals_dict[key]
        return None

    def extract_code_blocks(self, text: str) -> List[str]:
        """从LLM响应中提取代码块"""

        # 匹配 ```python...``` 格式
        pattern = r"```python\s*\n(.*?)\n```"
        matches = re.findall(pattern, text, re.DOTALL)

        if not matches:
            # 尝试 ```...``` 格式
            pattern = r"```\s*\n(.*?)\n```"
            matches = re.findall(pattern, text, re.DOTALL)

        # 清理每个代码块
        cleaned_matches = []
        for match in matches:
            # 去除开头和结尾的空白字符，确保格式正确
            cleaned_code = match.strip()
            cleaned_matches.append(cleaned_code)

        return cleaned_matches
