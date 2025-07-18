#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import sys
from rich.console import Console
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style

from ..core.core import AIForgeCore


class AIForgeCLI:
    """AIForge命令行接口"""

    def __init__(self):
        self.console = Console(record=True)
        self.history = FileHistory(".aiforge_history")
        self.style = Style.from_dict(
            {
                "completion-menu.completion": "bg:#000000 #ffffff",
                "completion-menu.completion.current": "bg:#444444 #ffffff",
                "prompt": "green",
            }
        )

    def create_parser(self):
        """创建命令行参数解析器"""
        parser = argparse.ArgumentParser(
            description="AIForge - AI驱动的代码生成执行引擎",
            formatter_class=argparse.RawTextHelpFormatter,
        )
        parser.add_argument("-c", "--config", default="aiforge.toml", help="配置文件路径")
        parser.add_argument("--debug", action="store_true", help="启用调试模式")
        parser.add_argument("instruction", nargs="?", help="要执行的任务指令")
        return parser

    def run_interactive(self, forge):
        """运行交互式模式"""
        self.console.print("[bold cyan]🔥 AIForge - AI驱动编程引擎[/bold cyan]")
        self.console.print("输入指令或 'exit' 退出", style="green")

        session = PromptSession(history=self.history, style=self.style)

        while True:
            try:
                instruction = session.prompt(">> ").strip()
                if instruction.lower() in ["exit", "quit"]:
                    break
                if len(instruction) < 2:
                    continue

                result = forge.run_task(instruction)
                if result:
                    self.console.print(f"[green]执行成功:[/green] {result}")
                else:
                    self.console.print("[red]执行失败[/red]")

            except (EOFError, KeyboardInterrupt):
                break

        self.console.print("[yellow]再见![/yellow]")

    def main(self):
        """主入口函数"""
        parser = self.create_parser()
        args = parser.parse_args()

        try:
            forge = AIForgeCore(args.config)
        except Exception as e:
            self.console.print(f"[red]初始化失败: {e}[/red]")
            sys.exit(1)

        if args.instruction:
            # 单次执行模式
            result = forge.run_task(args.instruction)
            if result:
                self.console.print(result)
            else:
                sys.exit(1)
        else:
            # 交互式模式
            self.run_interactive(forge)


def main():
    """CLI入口点"""
    cli = AIForgeCLI()
    cli.main()


if __name__ == "__main__":
    main()
