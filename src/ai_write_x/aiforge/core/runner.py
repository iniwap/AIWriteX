#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Optional, Dict, Any
from pathlib import Path
import traceback
from rich.console import Console


class AIForgeRunner:
    """AIForge任务运行器"""

    def __init__(self, workdir: str = "aiforge_work"):
        self.workdir = Path(workdir)
        self.workdir.mkdir(exist_ok=True)
        self.console = Console()
        self.current_task = None

    def prepare_environment(self) -> Dict[str, Any]:
        """准备执行环境"""
        # 设置工作目录
        import os

        os.chdir(self.workdir)

        # 准备全局变量
        globals_dict = {
            "__name__": "__main__",
            "__file__": str(self.workdir / "generated_code.py"),
            "print": print,
            "len": len,
            "range": range,
            "enumerate": enumerate,
            # 添加常用库的导入
        }

        return globals_dict

    def execute_code(self, code: str, globals_dict: Optional[Dict] = None) -> Dict[str, Any]:
        """执行生成的代码"""
        if globals_dict is None:
            globals_dict = self.prepare_environment()

        locals_dict = {}
        result = {"success": False, "result": None, "error": None}

        try:
            # 执行代码
            exec(code, globals_dict, locals_dict)

            # 查找结果
            if "__result__" in locals_dict:
                result["result"] = locals_dict["__result__"]
            elif "result" in locals_dict:
                result["result"] = locals_dict["result"]
            else:
                # 尝试获取最后一个非下划线开头的变量
                for key, value in locals_dict.items():
                    if not key.startswith("_"):
                        result["result"] = value
                        break

            result["success"] = True
            result["locals"] = locals_dict
            result["globals"] = globals_dict

        except Exception as e:
            result["error"] = str(e)
            result["traceback"] = traceback.format_exc()
            self.console.print(f"[red]代码执行错误: {e}[/red]")

        return result

    def save_code(self, code: str, filename: str = "generated_code.py") -> Path:
        """保存生成的代码到文件"""
        file_path = self.workdir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)
        return file_path

    def run_task_with_retry(self, task_func, max_retries: int = 3) -> Dict[str, Any]:
        """带重试机制的任务执行"""
        last_error = None

        for attempt in range(max_retries):
            try:
                result = task_func()
                if result.get("success"):
                    return result
                last_error = result.get("error", "Unknown error")
            except Exception as e:
                last_error = str(e)
                self.console.print(f"[yellow]第 {attempt + 1} 次尝试失败: {e}[/yellow]")

        return {
            "success": False,
            "error": f"所有重试都失败了。最后错误: {last_error}",
            "attempts": max_retries,
        }

    def cleanup(self):
        """清理临时文件"""
        try:
            # 清理临时生成的文件
            for file in self.workdir.glob("*.tmp"):
                file.unlink()
        except Exception as e:
            self.console.print(f"[yellow]清理警告: {e}[/yellow]")


class TaskContext:
    """任务执行上下文"""

    def __init__(self, instruction: str, runner: AIForgeRunner):
        self.instruction = instruction
        self.runner = runner
        self.history = []
        self.current_globals = {}
        self.current_locals = {}

    def add_execution_record(self, code: str, result: Dict[str, Any]):
        """添加执行记录"""
        record = {
            "code": code,
            "result": result,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        }
        self.history.append(record)

    def get_last_successful_result(self) -> Optional[Any]:
        """获取最后一次成功执行的结果"""
        for record in reversed(self.history):
            if record["result"].get("success"):
                return record["result"].get("result")
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.runner.cleanup()
