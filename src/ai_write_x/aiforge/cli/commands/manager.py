import shlex
from rich.console import Console


class CommandManager:
    """命令管理器"""

    def __init__(self, forge_core):
        self.forge_core = forge_core
        self.console = Console()
        self.commands = {
            "help": self._cmd_help,
            "list": self._cmd_list_providers,
            "use": self._cmd_use_provider,
            "cache": self._cmd_cache_info,
        }

    def execute(self, command_line: str) -> bool:
        """执行命令"""
        if not command_line.startswith("/"):
            return False

        try:
            parts = shlex.split(command_line[1:])  # 去掉开头的 /
            if not parts:
                return False

            cmd_name = parts[0]
            args = parts[1:]

            if cmd_name in self.commands:
                self.commands[cmd_name](args)
                return True
            else:
                self.console.print(f"[red]未知命令: {cmd_name}[/red]")
                return True

        except Exception as e:
            self.console.print(f"[red]命令执行错误: {e}[/red]")
            return True

    def _cmd_help(self, args):
        """显示帮助信息"""
        self.console.print("[bold]可用命令:[/bold]")
        for cmd, func in self.commands.items():
            self.console.print(f"  /{cmd} - {func.__doc__ or '无描述'}")

    def _cmd_list_providers(self, args):
        """列出所有LLM提供商"""
        providers = self.forge_core.list_providers()
        self.console.print("[bold]可用的LLM提供商:[/bold]")
        for name, model in providers.items():
            self.console.print(f"  {name}: {model}")

    def _cmd_use_provider(self, args):
        """切换LLM提供商"""
        if not args:
            self.console.print("[red]请指定提供商名称[/red]")
            return

        provider_name = args[0]
        if self.forge_core.switch_provider(provider_name):
            self.console.print(f"[green]已切换到: {provider_name}[/green]")
        else:
            self.console.print(f"[red]切换失败: {provider_name}[/red]")

    def _cmd_cache_info(self, args):
        """显示缓存信息"""
        if hasattr(self.forge_core, "code_cache") and self.forge_core.code_cache:
            # 这里可以添加缓存统计信息
            self.console.print("[green]缓存系统已启用[/green]")
        else:
            self.console.print("[yellow]缓存系统未启用[/yellow]")
