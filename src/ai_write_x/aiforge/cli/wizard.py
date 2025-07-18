def create_config_wizard():
    """配置向导"""
    from rich.console import Console
    from rich.prompt import Prompt, Confirm
    from ..core.core import AIForgeCore

    console = Console()
    console.print("[bold cyan]🔥 AIForge 配置向导[/bold cyan]")
    console.print("选择配置方式：")
    console.print("1. 快速开始（推荐）- 只需要API Key")
    console.print("2. 完整配置 - 创建配置文件")

    choice = Prompt.ask("请选择", choices=["1", "2"], default="1")

    if choice == "1":
        console.print("\n[yellow]推荐使用 OpenRouter，支持多种模型且价格便宜[/yellow]")
        console.print("[dim]获取API Key: https://openrouter.ai/keys[/dim]")

        api_key = Prompt.ask("请输入您的 OpenRouter API Key")

        # 可选参数配置
        advanced = Confirm.ask("是否配置高级选项？", default=False)
        kwargs = {}

        if advanced:
            workdir = Prompt.ask("工作目录", default="aiforge_work")
            max_rounds = int(Prompt.ask("最大执行轮数", default="5"))
            kwargs.update({"workdir": workdir, "max_rounds": max_rounds})

        try:
            # 创建并测试配置
            forge = AIForgeCore(api_key=api_key, **kwargs)

            # 简单测试
            console.print("[dim]正在测试配置...[/dim]")
            test_result = forge("print('Hello AIForge!')")

            if test_result:
                console.print("[green]✅ 配置成功！可以开始使用了[/green]")
                return forge
            else:
                console.print("[yellow]⚠️ 配置完成，但测试未通过，请检查API Key[/yellow]")
                return forge

        except Exception as e:
            console.print(f"[red]❌ 配置失败: {e}[/red]")
            return None
    else:
        # 引导用户创建完整配置文件
        return create_full_config(console)


def create_full_config(console):
    """创建完整配置文件"""
    from rich.prompt import Prompt, Confirm
    import tomlkit

    console.print("\n[bold]创建完整配置文件[/bold]")

    # 基础配置
    workdir = Prompt.ask("工作目录", default="aiforge_work")
    max_rounds = int(Prompt.ask("最大执行轮数", default="5"))
    max_tokens = int(Prompt.ask("最大Token数", default="4096"))

    # LLM提供商配置
    providers = {}
    console.print("\n[bold]配置LLM提供商[/bold]")

    # OpenRouter配置
    if Confirm.ask("配置 OpenRouter？", default=True):
        api_key = Prompt.ask("OpenRouter API Key")
        providers["openrouter"] = {
            "type": "openai",
            "model": "deepseek/deepseek-chat-v3-0324:free",
            "api_key": api_key,
            "base_url": "https://openrouter.ai/api/v1",
            "timeout": 30,
            "max_tokens": 8192,
            "enable": True,
        }

    # 其他提供商配置...
    if Confirm.ask("配置其他提供商？", default=False):
        # 可以添加更多提供商配置逻辑
        pass

    # 构建配置字典
    config_dict = {
        "workdir": workdir,
        "max_tokens": max_tokens,
        "max_rounds": max_rounds,
        "default_llm_provider": "openrouter",
        "llm": providers,
        "cache": {
            "code": {
                "enabled": True,
                "max_modules": 20,
                "failure_threshold": 0.8,
                "max_age_days": 30,
                "cleanup_interval": 10,
            }
        },
        "optimization": {"enabled": False, "aggressive_minify": False, "max_feedback_length": 200},
    }

    # 保存配置文件
    config_file = "aiforge.toml"
    with open(config_file, "w", encoding="utf-8") as f:
        tomlkit.dump(config_dict, f)

    console.print(f"[green]✅ 配置文件已保存到 {config_file}[/green]")

    # 创建AIForgeCore实例
    from ..core.core import AIForgeCore

    return AIForgeCore(config_file=config_file)
