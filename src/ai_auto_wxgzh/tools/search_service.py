import json
import time
import importlib.util
from pathlib import Path
from aipyapp.aipy import TaskManager
from rich.console import Console

from src.ai_auto_wxgzh.config.config import Config
from src.ai_auto_wxgzh.tools import search_template


class SearchService:
    """优化的搜索服务，专注于本地代码缓存和AI生成模式"""

    def __init__(self):
        self.console = Console()
        self._setup_directories()
        self._load_data()
        self._init_task_manager()
        self._auto_cleanup()

    def _setup_directories(self):
        """设置目录结构"""
        work_dir = Path(Config.get_instance().get_aipy_settings().get("workdir", "aipy_work"))
        if not work_dir.is_absolute():
            work_dir = Path.cwd() / work_dir
        work_dir.mkdir(parents=True, exist_ok=True)

        self.cache_dir = work_dir / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        self.search_modules_dir = self.cache_dir / "search_modules"
        self.search_modules_dir.mkdir(exist_ok=True)

        # 文件路径
        self.modules_info_file = self.cache_dir / "modules_info.json"

    def _load_data(self):
        """加载模块数据"""
        self.modules_info = self._load_modules_info()

    def _load_modules_info(self):
        """加载模块信息"""
        if self.modules_info_file.exists():
            try:
                with open(self.modules_info_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                self.console.print(f"[yellow]警告: 无法加载模块信息文件: {e}[/yellow]")
        return {"modules": {}, "success_rate": {}}

    def _load_cleanup_config(self):
        """加载清理配置"""
        return {
            "failure_threshold": 0.8,  # 失败率阈值
            "min_attempts": 3,  # 最小尝试次数
            "max_age_days": 30,  # 最大保留天数
            "max_modules": 20,  # 最大模块数量
            "cleanup_interval": 10,  # 清理间隔（搜索次数）
        }

    def _save_modules_info(self):
        """保存模块信息"""
        try:
            with open(self.modules_info_file, "w", encoding="utf-8") as f:
                json.dump(self.modules_info, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.console.print(f"[yellow]警告: 无法保存模块信息文件: {e}[/yellow]")

    def _init_task_manager(self):
        """初始化TaskManager"""
        try:
            self.task_manager = TaskManager(
                Config.get_instance().get_aipy_settings(), console=self.console
            )
            if not self.task_manager.llm:
                self.console.print("[red]警告: TaskManager的LLM未正确初始化[/red]")
        except Exception as e:
            self.console.print(f"[red]TaskManager初始化失败: {e}[/red]")
            raise

    def _clean_failed_modules(self, failure_threshold=0.7, min_attempts=5):
        """清理失败率过高的模块"""
        if not self.modules_info["modules"]:
            return

        modules_to_remove = []

        for module_id, stats in self.modules_info["success_rate"].items():
            if module_id not in self.modules_info["modules"]:
                continue

            total = stats["successes"] + stats["failures"]

            # 只清理有足够尝试次数的模块
            if total >= min_attempts:
                failure_rate = stats["failures"] / total

                if failure_rate >= failure_threshold:
                    modules_to_remove.append(module_id)
                    self.console.print(
                        f"[yellow]标记清理模块 {module_id}: 失败率 {failure_rate:.2%}[/yellow]"
                    )

        # 执行清理
        for module_id in modules_to_remove:
            self._remove_module(module_id)

        if modules_to_remove:
            self.console.print(f"[green]已清理 {len(modules_to_remove)} 个失败率过高的模块[/green]")

    def _remove_module(self, module_id):
        """移除指定模块"""
        try:
            # 删除模块文件
            if module_id in self.modules_info["modules"]:
                module_path = Path(self.modules_info["modules"][module_id]["path"])
                if module_path.exists():
                    module_path.unlink()

                # 从记录中移除
                del self.modules_info["modules"][module_id]

            # 移除成功率统计
            if module_id in self.modules_info["success_rate"]:
                del self.modules_info["success_rate"][module_id]

            self._save_modules_info()
            self.console.print(f"[blue]已移除模块: {module_id}[/blue]")

        except Exception as e:
            self.console.print(f"[red]移除模块失败 {module_id}: {e}[/red]")

    def _clean_old_modules(self, max_age_days=30, max_modules=50):
        """清理过旧的模块，保持模块数量在合理范围内"""
        if not self.modules_info["modules"]:
            return

        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 3600

        # 按创建时间排序，最新的在前
        sorted_modules = sorted(
            self.modules_info["modules"].items(),
            key=lambda x: x[1].get("created_at", 0),
            reverse=True,
        )

        modules_to_remove = []

        # 清理过旧的模块
        for module_id, info in sorted_modules:
            created_at = info.get("created_at", 0)
            age = current_time - created_at

            if age > max_age_seconds:
                modules_to_remove.append(module_id)

        # 如果模块数量超过限制，清理最旧的
        if len(sorted_modules) > max_modules:
            excess_modules = sorted_modules[max_modules:]
            for module_id, _ in excess_modules:
                if module_id not in modules_to_remove:
                    modules_to_remove.append(module_id)

        # 执行清理
        for module_id in modules_to_remove:
            self._remove_module(module_id)

        if modules_to_remove:
            self.console.print(f"[green]已清理 {len(modules_to_remove)} 个过旧模块[/green]")

    def _auto_cleanup(self):
        """自动清理：结合失败率和年龄策略"""
        self.console.print("[blue]开始自动清理本地失败过多或无效模块...[/blue]")

        # 加载清理配置
        config = self._load_cleanup_config()

        # 使用配置参数清理失败率过高的模块
        self._clean_failed_modules(
            failure_threshold=config["failure_threshold"], min_attempts=config["min_attempts"]
        )

        # 使用配置参数清理过旧的模块
        self._clean_old_modules(
            max_age_days=config["max_age_days"], max_modules=config["max_modules"]
        )

    def _get_best_module(self):
        """根据历史成功率选择最佳模块"""
        if not self.modules_info["modules"]:
            return None

        best_module = None
        best_rate = -1

        for module_id, stats in self.modules_info["success_rate"].items():
            if module_id in self.modules_info["modules"]:
                total = stats["successes"] + stats["failures"]
                success_rate = stats["successes"] / total if total > 0 else 0.5
                if success_rate > best_rate:
                    best_rate = success_rate
                    best_module = module_id

        return best_module

    def _import_module(self, module_id):
        """导入指定的搜索模块"""
        if module_id not in self.modules_info["modules"]:
            return None

        module_path = self.modules_info["modules"][module_id]["path"]
        try:
            spec = importlib.util.spec_from_file_location(f"search_module_{module_id}", module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        except Exception as e:
            error_msg = str(e)
            self.console.print(f"[red]导入模块失败: {e}[/red]")

            # 检查 AIPy 环境依赖错误
            aipy_errors = ["name 'runtime' is not defined"]

            if any(error in error_msg for error in aipy_errors):
                self.console.print(
                    f"[red]检测到 AIPy 环境依赖错误，立即清理模块: {module_id}[/red]"
                )
                self._remove_module(module_id)

            return None

    def _generate_with_ai(self, topic, max_results, min_results, generation_mode):
        """使用AI生成搜索模块代码并保存"""
        if generation_mode == "ai_guided":
            search_instruction = search_template.get_template_guided_search_instruction(
                topic, max_results, min_results
            )
        elif generation_mode == "ai_free":
            search_instruction = search_template.get_free_form_ai_search_instruction(
                topic, max_results, min_results
            )
        else:
            return None

        task = None
        try:
            task = self.task_manager.new_task(search_instruction)
            task.run()

            # 直接从runner历史获取结果
            if hasattr(task, "runner") and task.runner.history:
                for entry in reversed(task.runner.history):
                    if isinstance(entry, dict) and "result" in entry:
                        result = entry["result"]
                        if "__result__" in result and result["__result__"]:
                            # 验证搜索结果质量
                            search_result = result["__result__"]
                            if search_template.simple_validate_search_result(
                                search_result, min_results, generation_mode
                            ):
                                code = entry.get("code", "")
                                if code and "def search_web" in code:
                                    return self._save_module_code(code, generation_mode)

            self.console.print(f"[yellow]{generation_mode}模式未生成有效的搜索代码[/yellow]")
            return None

        except Exception as e:
            self.console.print(f"[red]{generation_mode}模式生成代码失败: {e}[/red]")
            return None
        finally:
            if task:
                task.done()

    def _validate_code_before_save(self, code):
        """在保存前验证代码的可执行性"""
        try:
            aipy_globals = ["runtime"]

            for global_var in aipy_globals:
                if global_var in code:
                    self.console.print(
                        f"[yellow]检测到 AIPy 全局变量 {global_var}，代码可能无法独立运行[/yellow]"
                    )
                    return False

            # 尝试编译代码检查语法
            compile(code, "<string>", "exec")

            # 检查必要的函数是否存在
            if "def search_web" not in code:
                return False

            return True
        except SyntaxError as e:
            self.console.print(f"[red]代码语法错误: {e}[/red]")
            return False
        except Exception as e:
            self.console.print(f"[red]代码验证失败: {e}[/red]")
            return False

    def _save_module_code(self, code, source):
        """保存模块代码"""
        try:
            # 在保存前验证代码
            if not self._validate_code_before_save(code):
                self.console.print("[red]代码验证失败，跳过保存[/red]")
                return None

            module_id = f"search_{source}_{int(time.time())}"
            module_path = self.search_modules_dir / f"{module_id}.py"

            with open(module_path, "w", encoding="utf-8") as f:
                f.write(code)

            self.modules_info["modules"][module_id] = {
                "path": str(module_path),
                "source": source,
                "created_at": time.time(),
            }

            self.modules_info["success_rate"][module_id] = {"successes": 0, "failures": 0}
            self._save_modules_info()

            self.console.print(f"[green]搜索模块已成功生成并保存: {module_id} ({source})[/green]")
            return module_id
        except Exception as e:
            self.console.print(f"[red]保存模块代码失败: {e}[/red]")
            return None

    def _try_local_modules(self, topic, max_results, min_results):
        """尝试使用本地模块进行搜索"""
        # 按成功率排序所有模块
        sorted_modules = []
        for module_id, stats in self.modules_info["success_rate"].items():
            if module_id in self.modules_info["modules"]:
                total = stats["successes"] + stats["failures"]
                success_rate = stats["successes"] / total if total > 0 else 0.5
                sorted_modules.append((module_id, success_rate))

        sorted_modules.sort(key=lambda x: x[1], reverse=True)

        # 依次尝试每个模块
        for module_id, _ in sorted_modules:
            self.console.print(f"[blue]尝试使用本地模块: {module_id}[/blue]")
            module = self._import_module(module_id)
            if module:
                try:
                    result = module.search_web(topic, max_results)

                    module_source = self.modules_info["modules"][module_id].get(
                        "source", "ai_guided"
                    )
                    validation_type = "ai_guided" if module_source == "ai_guided" else "ai_free"

                    if search_template.validate_search_result(result, min_results, validation_type):
                        self.modules_info["success_rate"][module_id]["successes"] += 1
                        self._save_modules_info()
                        return result
                    else:
                        self.console.print(f"[yellow]模块 {module_id} 搜索结果未通过验证[/yellow]")
                        self.modules_info["success_rate"][module_id]["failures"] += 1
                        self._save_modules_info()

                except Exception as e:
                    error_msg = str(e)
                    self.console.print(f"[yellow]模块执行失败: {e}[/yellow]")

                    # 只处理非 AIPy 的 ImportError（AIPy 错误已在 _import_module 中处理）
                    if "ImportError" in str(type(e)) and not any(
                        aipy_error in error_msg for aipy_error in ["name 'runtime' is not defined"]
                    ):
                        self.console.print(f"[red]检测到导入错误，立即清理模块: {module_id}[/red]")
                        self._remove_module(module_id)
                        continue

                    self.modules_info["success_rate"][module_id]["failures"] += 1
                    self._save_modules_info()

        return None

    def _try_new_module(self, module_id, topic, max_results, min_results):
        """尝试使用新生成的模块"""
        module = self._import_module(module_id)
        if module:
            try:
                result = module.search_web(topic, max_results)

                module_source = self.modules_info["modules"][module_id].get("source", "ai_guided")
                validation_type = "ai_guided" if module_source == "ai_guided" else "ai_free"

                if search_template.validate_search_result(result, min_results, validation_type):
                    self.modules_info["success_rate"][module_id]["successes"] += 1
                    self._save_modules_info()
                    return result.get("results")
                else:
                    self.console.print(
                        f"[yellow]新生成的模块 {module_id} 搜索结果未通过验证[/yellow]"
                    )
                    self.modules_info["success_rate"][module_id]["failures"] += 1
                    self._save_modules_info()

            except Exception as e:
                self.console.print(f"[red]新生成的模块执行失败: {e}[/red]")
                self.modules_info["success_rate"][module_id]["failures"] += 1
                self._save_modules_info()
        return None

    def aipy_search(self, topic, max_results=10, min_results=1):
        """主搜索方法 - 移除了结果缓存，专注于模块缓存"""

        # 加载清理配置
        config = self._load_cleanup_config()

        # 使用配置的清理间隔
        search_count = getattr(self, "_search_count", 0) + 1
        self._search_count = search_count

        if search_count % config["cleanup_interval"] == 0:
            self._auto_cleanup()

        # 1. 优先尝试本地模块
        if self.modules_info["modules"]:
            result = self._try_local_modules(topic, max_results, min_results)
            if result:
                return result.get("results")

        # 2. 本地模块都失败，依次尝试两种AI生成模式
        self.console.print("[yellow]本地模块都无法获取结果，正在使用AI生成新的搜索模块...[/yellow]")

        # 先尝试模板指导生成
        new_module_id = self._generate_with_ai(topic, max_results, min_results, "ai_guided")
        if new_module_id:
            result = self._try_new_module(new_module_id, topic, max_results, min_results)
            if result:
                return result

        # 如果模板指导失败，尝试AI自由生成
        self.console.print("[yellow]模板指导生成失败，尝试AI自由生成...[/yellow]")
        new_module_id = self._generate_with_ai(topic, max_results, min_results, "ai_free")
        if new_module_id:
            result = self._try_new_module(new_module_id, topic, max_results, min_results)
            if result:
                return result

        self.console.print(f"[red]未能找到关于'{topic}'的搜索结果[/red]")
        return None
