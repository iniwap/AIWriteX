import json
import time
import requests
import re
from bs4 import BeautifulSoup
import importlib.util
from pathlib import Path
from aipyapp.aipy import TaskManager
from rich.console import Console

from src.ai_auto_wxgzh.config.config import Config
from src.ai_auto_wxgzh.utils import log


class SearchService:
    """搜索服务，支持持久化、多种搜索方法和纠错机制"""

    def __init__(self):
        self.console = Console()
        # 从配置中获取工作目录
        work_dir = Path(Config.get_instance().get_aipy_settings().get("workdir", "aipy_work"))

        # 确保工作目录存在
        if not work_dir.is_absolute():
            work_dir = Path.cwd() / work_dir
        work_dir.mkdir(parents=True, exist_ok=True)

        # 使用工作目录下的cache子目录
        self.cache_dir = work_dir / "cache"
        self.cache_dir.mkdir(exist_ok=True)

        # 其他目录和文件路径
        self.search_modules_dir = self.cache_dir / "search_modules"
        self.search_modules_dir.mkdir(exist_ok=True)
        self.modules_info_file = self.cache_dir / "modules_info.json"
        self.cache_file = self.cache_dir / "search_cache.json"
        self.error_log_file = self.cache_dir / "search_errors.json"

        # 加载数据
        self.default_cache_duration = 3600 * 24  # 超过1天的搜索结果缓存清除
        self.modules_info = self._load_modules_info()
        self.cache = self._load_cache()
        self._clean_cache()  # 加载后立即清理
        self.error_log = self._load_error_log()

        self.task_manager = None

        # 确保搜索模块存在
        self._ensure_search_modules()

    def _load_cache(self):
        """加载缓存数据并确保时间戳是浮点数"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)

                # 确保所有时间戳都是浮点数
                for key, data in cache_data.items():
                    if "timestamp" in data and isinstance(data["timestamp"], str):
                        try:
                            data["timestamp"] = float(data["timestamp"])
                        except ValueError:
                            data["timestamp"] = 0

                return cache_data
            except Exception as e:
                self.console.print(f"[yellow]警告: 无法加载缓存文件: {e}[/yellow]")
        return {}

    def _save_cache(self):
        """保存缓存数据"""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.console.print(f"[yellow]警告: 无法保存缓存文件: {e}[/yellow]")

    def _clean_cache(self):
        """清理过期的缓存条目"""
        current_time = time.time()
        cleaned_cache = {}

        # 只保留未过期的条目
        for key, data in self.cache.items():
            timestamp = data.get("timestamp", 0)
            # 确保timestamp是浮点数
            if isinstance(timestamp, str):
                try:
                    timestamp = float(timestamp)
                except ValueError:
                    timestamp = 0

            if current_time - timestamp < self.default_cache_duration:
                cleaned_cache[key] = data

        # 如果有条目被清理，更新缓存并保存
        if len(cleaned_cache) < len(self.cache):
            self.console.print(
                f"[yellow]已清理 {len(self.cache) - len(cleaned_cache)} 个过期缓存条目[/yellow]"
            )
            self.cache = cleaned_cache
            self._save_cache()

    def _load_modules_info(self):
        """加载模块信息"""
        if self.modules_info_file.exists():
            try:
                with open(self.modules_info_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                self.console.print(f"[yellow]警告: 无法加载模块信息文件: {e}[/yellow]")
        return {"modules": {}, "default_module": None, "success_rate": {}, "last_updated": {}}

    def _save_modules_info(self):
        """保存模块信息"""
        try:
            with open(self.modules_info_file, "w", encoding="utf-8") as f:
                json.dump(self.modules_info, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.console.print(f"[yellow]警告: 无法保存模块信息文件: {e}[/yellow]")

    def _load_error_log(self):
        """加载错误日志"""
        if self.error_log_file.exists():
            try:
                with open(self.error_log_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                self.console.print(f"[yellow]警告: 无法加载错误日志文件: {e}[/yellow]")
        return {"errors": []}

    def _save_error_log(self):
        """保存错误日志"""
        try:
            with open(self.error_log_file, "w", encoding="utf-8") as f:
                json.dump(self.error_log, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.console.print(f"[yellow]警告: 无法保存错误日志文件: {e}[/yellow]")

    def _log_error(self, module_name, error_type, error_message, topic=None):
        """记录错误"""
        error_entry = {
            "timestamp": time.time(),
            "module": module_name,
            "error_type": error_type,
            "error_message": str(error_message),
            "topic": topic,
        }
        self.error_log["errors"].append(error_entry)
        self._save_error_log()

        # 更新模块成功率
        if module_name in self.modules_info["success_rate"]:
            self.modules_info["success_rate"][module_name]["failures"] += 1
            self._save_modules_info()

    def _init_task_manager(self):
        """初始化TaskManager"""
        if not self.task_manager:
            try:
                self.task_manager = TaskManager(
                    Config.get_instance().get_aipy_settings(), console=self.console
                )
                # 验证TaskManager是否正常工作
                if not self.task_manager.llm:
                    self.console.print("[red]警告: TaskManager的LLM未正确初始化[/red]")
            except Exception as e:
                self.console.print(f"[red]TaskManager初始化失败: {e}[/red]")
                raise

    def _ensure_search_modules(self):
        """确保搜索模块文件存在，如果不存在则创建"""
        # 检查是否有任何搜索模块
        if not self.modules_info["modules"]:
            self._init_task_manager()

            # 生成多种搜索模块
            module_types = [
                ("baidu", "使用百度搜索引擎，添加时间筛选参数"),
                ("bing", "使用Bing搜索引擎，添加时间筛选参数"),
                ("scraper", "直接访问相关领域的权威网站并抓取最新内容"),
                ("duckduckgo", "使用DuckDuckGo搜索引擎，添加时间筛选参数"),
                ("google", "使用Google搜索引擎，仅在其他方法无法获取足够信息时使用"),
                ("combined", "结合多种搜索引擎的综合搜索，按优先级顺序尝试各种搜索方法"),
            ]

            for module_type, description in module_types:
                self._generate_search_module(module_type, description)

            # 设置默认模块
            if "combined" in self.modules_info["modules"]:
                self.modules_info["default_module"] = "combined"
            elif self.modules_info["modules"]:
                # 使用第一个可用模块作为默认
                self.modules_info["default_module"] = list(self.modules_info["modules"].keys())[0]

            self._save_modules_info()

    def _generate_via_direct_llm(self, search_instruction, module_type, description):
        """方法1: 直接使用LLM生成代码，不依赖Task系统"""
        self._init_task_manager()

        # 直接调用LLM
        response = self.task_manager.llm(search_instruction)

        if not response or not isinstance(response, str):
            return None

        # 使用AIPy的正则表达式模式进行匹配
        pattern = re.compile(r"^(`{4})(\w+)\s+([\w\-\.]+)\n(.*?)^\1\s*$", re.DOTALL | re.MULTILINE)

        code_blocks = {}
        for match in pattern.finditer(response):
            _, _, name, content = match.groups()
            code_blocks[name] = content.rstrip("\n")

        # 优先查找main块
        if "main" in code_blocks and "search_web" in code_blocks["main"]:
            return code_blocks["main"]

        # 如果没有main块，查找其他包含search_web的块
        for _, block_content in code_blocks.items():
            if "search_web" in block_content:
                return block_content

        # 统一的代码块匹配模式（支持3个或4个反引号）
        patterns = [
            # 三个反引号的python代码块
            r"```python\s*\n(.*?)\n```",
            # 四个反引号的python代码块
            r"````python\s*\n(.*?)\n````",
            # 三个反引号的任意代码块
            r"```\s*\n(.*?)\n```",
            # 四个反引号的任意代码块
            r"````\s*\n(.*?)\n````",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            for code_content in matches:
                if "def search_web" in code_content:
                    return code_content.strip()

        # 如果没有代码块标记，尝试提取整个响应作为代码（作为最终备选）
        if "def search_web" in response:
            return response.strip()

        return None

    def _generate_via_task_system(self, search_instruction, module_type, description):
        """方法2: 使用Task系统生成代码"""
        self._init_task_manager()

        task = self.task_manager.new_task(search_instruction)
        task.run()

        # 多种方式提取代码
        code = self._extract_code_from_task(task)

        task.done()
        return code

    def _generate_via_template(self, search_instruction, module_type, description):
        """方法3: 基于模板生成代码"""
        # 这里可以根据module_type提供一个基础模板
        template_code = f"""
            import requests
            import time
            import json
            from bs4 import BeautifulSoup
            import re
            from urllib.parse import urljoin, urlparse

            def search_web(topic, max_results=10):
                '''
                {description}
                '''
                try:
                    results = []
                    timestamp = time.time()

                    # 基础搜索逻辑 - 根据module_type定制
                    # TODO: 实现具体的搜索逻辑

                    return {{
                        "timestamp": timestamp,
                        "topic": topic,
                        "results": results,
                        "success": True,
                        "error": None
                    }}
                except Exception as e:
                    return {{
                        "timestamp": time.time(),
                        "topic": topic,
                        "results": [],
                        "success": False,
                        "error": str(e)
                    }}
            """
        return template_code

    def _extract_code_from_task(self, task):
        # 首先检查runner历史，这里包含实际执行的代码
        if hasattr(task, "runner") and task.runner.history:
            for entry in task.runner.history:
                if isinstance(entry, dict) and "code" in entry:
                    code = entry["code"]
                    if code and "def search_web" in str(code):
                        return code

        # 然后检查LLM历史
        if hasattr(task, "llm") and hasattr(task.llm, "history"):
            messages = task.llm.history.get_messages()
            for message in reversed(messages):
                # 直接访问字典的键，而不是使用hasattr和.属性访问
                msg_role = message.get("role")
                content = message.get("content")

                if msg_role == "assistant":
                    # 修正：确保content不为None，并且包含"def search_web"
                    if content is not None and "def search_web" in content:
                        # 使用AIPy的parse_reply方法
                        blocks = task.parse_reply(content)
                        if "main" in blocks:
                            return blocks["main"]
                        # 如果没有main块，尝试其他块
                        for _, block_content in blocks.items():
                            if "def search_web" in block_content:
                                return block_content

                        # 分别处理三个和四个反引号的情况
                        patterns = [
                            # 三个反引号的python代码块
                            r"```python\s*\n(.*?)\n```",
                            # 四个反引号的python代码块
                            r"````python\s*\n(.*?)\n````",
                            # 三个反引号的任意代码块
                            r"```\s*\n(.*?)\n```",
                            # 四个反引号的任意代码块
                            r"````\s*\n(.*?)\n````",
                        ]

                        for pattern in patterns:
                            matches = re.findall(pattern, content, re.DOTALL)
                            for code_content in matches:
                                if "def search_web" in code_content:
                                    return code_content.strip()

                        # 如果没有代码块标记，返回整个内容（作为最终备选）
                        return content.strip()

            return None

    def _validate_generated_code(self, code):
        """验证生成的代码是否有效"""
        try:
            # 基本语法检查
            compile(code, "<string>", "exec")

            # 检查必要的函数和结构
            if "def search_web(" not in code:
                return False

            if "topic" not in code or "max_results" not in code:
                return False

            return True
        except SyntaxError:
            return False
        except Exception:
            return False

    def _save_module_code(self, module_type, code, description):
        """保存模块代码"""
        try:
            # 生成模块ID
            module_id = f"{module_type}_{int(time.time())}"
            module_path = self.search_modules_dir / f"{module_id}.py"

            # 保存代码到模块文件
            with open(module_path, "w", encoding="utf-8") as f:
                f.write(code)

            # 更新模块信息
            self.modules_info["modules"][module_id] = {
                "type": module_type,
                "description": description,
                "path": str(module_path),
                "created_at": time.time(),
            }

            # 初始化成功率统计
            self.modules_info["success_rate"][module_id] = {"successes": 0, "failures": 0}

            self.modules_info["last_updated"][module_type] = time.time()
            self._save_modules_info()

            self.console.print(f"[green]搜索模块 {module_type} 已成功生成并保存[/green]")
            return module_id
        except Exception as e:
            self.console.print(f"[red]保存模块代码失败: {e}[/red]")
            return None

    def _build_search_instruction(self, module_type, description):
        """构建搜索指令"""
        search_instruction = f"""
            请生成一个完整的Python函数，用于执行网络搜索并返回结构化结果。

            这个模块应该专注于{description}。

            函数要求：
            1. 函数名为search_web，接受两个参数：topic(搜索主题)和max_results(最大结果数)
            2. 实现健壮的错误处理，包括：
                - 网络连接错误处理
                - 解析错误处理
                - 超时处理
                - 编码问题处理
            3. 对于每个搜索结果，必须访问原始网页并提取以下内容：
                - 详细的内容摘要（至少100字）
                - 准确的发布时间
                - 如果无法直接找到发布时间，尝试从URL、页面内容或其他元数据推断
            4. 使用多种方法提取时间信息：
                - 检查meta标签（如article:published_time）
                - 查找页面中的时间标记（如time标签或日期格式文本）
                - 分析页面结构中可能包含日期的区域（如文章头部）
            5. 实现适当的请求间隔，避免过快发送请求被网站封禁
            """

        # 为combined模块添加特殊指令
        if module_type == "combined":
            search_instruction += """
                6. 按照以下优先级顺序尝试各种搜索方法（不能使用需要API密钥的方式）：
                    a. 使用百度搜索，添加时间筛选参数
                    b. 使用bing搜索，添加时间筛选参数
                    c. 直接访问相关领域的权威网站并抓取最新内容
                    d. 使用DuckDuckGo搜索引擎，添加时间筛选参数
                    e. 只有在上述方法都无法获取足够信息时，才考虑使用Google搜索
                """

        search_instruction += """
            7. 搜索内容应包括：
                a. 关于搜索主题的最新数据和统计数字
                b. 最近的事件和时间点
                c. 当前趋势和发展
                d. 权威来源的观点和分析
            8. 确保搜索结果包含：
                - 来源URL
                - 发布时间
                - 内容摘要
            9. 对结果按发布时间从新到旧排序
            10. 验证信息的时效性，过滤掉旧信息，优先获取最近7天内的内容
            11. 返回格式为字典，包含以下字段：
                - timestamp: 搜索执行时间戳
                - topic: 搜索主题
                - results: 搜索结果列表，每个结果必须包含url、title、abstract和pub_time
                - success: 布尔值，表示搜索是否成功
                - error: 如果失败，包含错误信息

            只返回完整的Python代码，不要有任何解释。
            """
        return search_instruction

    def _generate_search_module(self, module_type, description):
        """通过LLM生成特定类型的搜索模块代码并保存"""

        search_instruction = self._build_search_instruction(module_type, description)

        # 定义代码生成方法和对应的名称
        generation_methods = [
            ("Task系统", self._generate_via_task_system),
            ("直接LLM调用", self._generate_via_direct_llm),
            ("模板生成", self._generate_via_template),
        ]

        for method_name, method in generation_methods:
            try:
                self.console.print(f"[yellow]尝试使用 {method_name} 生成搜索模块...[/yellow]")
                code = method(search_instruction, module_type, description)

                if code and "search_web" in code:
                    # 验证代码的有效性
                    if self._validate_generated_code(code):
                        return self._save_module_code(module_type, code, description)
                    else:
                        self.console.print(f"[yellow]{method_name} 生成的代码验证失败[/yellow]")
                else:
                    self.console.print(f"[yellow]{method_name} 未生成有效代码[/yellow]")

            except Exception as e:
                self.console.print(f"[yellow]{method_name} 失败: {e}[/yellow]")
                continue

        self.console.print(f"[red]所有方法都无法生成搜索模块 {module_type} 的代码[/red]")
        return None

    def _get_best_module(self):
        """根据历史成功率选择最佳模块"""
        if not self.modules_info["modules"]:
            return None

        # 计算每个模块的成功率
        success_rates = {}
        for module_id, stats in self.modules_info["success_rate"].items():
            if module_id in self.modules_info["modules"]:  # 确保模块仍然存在
                total = stats["successes"] + stats["failures"]
                if total > 0:
                    success_rates[module_id] = stats["successes"] / total
                else:
                    success_rates[module_id] = 0.5  # 默认值

        # 如果没有足够的数据，使用默认模块
        if not success_rates or max(success_rates.values()) < 0.1:
            return self.modules_info["default_module"]

        # 返回成功率最高的模块
        return max(success_rates, key=success_rates.get)

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
            self._log_error(module_id, "import_error", str(e))
            return None

    def _regenerate_module_if_needed(self, module_type):
        """如果模块出错率过高，重新生成模块"""
        # 查找该类型的最新模块
        latest_module_id = None
        latest_time = 0

        for module_id, info in self.modules_info["modules"].items():
            if info["type"] == module_type and info["created_at"] > latest_time:
                latest_module_id = module_id
                latest_time = info["created_at"]

        if not latest_module_id:
            return None

        # 检查成功率
        stats = self.modules_info["success_rate"].get(
            latest_module_id, {"successes": 0, "failures": 0}
        )
        total = stats["successes"] + stats["failures"]

        # 如果失败次数过多，重新生成
        if total >= 5 and stats["failures"] / total > 0.7:
            self.console.print(f"[yellow]模块 {module_type} 失败率过高，正在重新生成...[/yellow]")
            description = self.modules_info["modules"][latest_module_id]["description"]
            return self._generate_search_module(module_type, description)

        return latest_module_id

    def _validate_and_fix_results(self, results):
        """验证搜索结果并修复缺失的摘要和时间"""
        fixed_results = []

        for result in results:
            # 检查是否缺少摘要或发布时间
            if not result.get("abstract") or not result.get("pub_time"):
                url = result.get("url")
                if url:
                    self.console.print(f"[yellow]修复结果: 提取 {url} 的摘要和时间[/yellow]")

                    # 提取摘要和时间
                    try:
                        abstract, pub_time = self._extract_content_and_date(url)

                        # 更新结果
                        if not result.get("abstract") and abstract:
                            result["abstract"] = abstract

                        if not result.get("pub_time") and pub_time:
                            result["pub_time"] = pub_time
                    except Exception as e:
                        self.console.print(f"[red]无法修复结果: {str(e)}[/red]")

            # 添加到修复后的结果列表
            fixed_results.append(result)

        return fixed_results

    def _validate_and_fix_results_parallel(self, results):
        """并行验证和修复搜索结果"""
        from concurrent.futures import ThreadPoolExecutor

        def fix_result(result):
            if not result.get("abstract") or not result.get("pub_time"):
                url = result.get("url")
                if url:
                    try:
                        abstract, pub_time = self._extract_content_and_date(url)

                        if not result.get("abstract") and abstract:
                            result["abstract"] = abstract

                        if not result.get("pub_time") and pub_time:
                            result["pub_time"] = pub_time
                    except Exception:
                        pass
            return result

        with ThreadPoolExecutor(max_workers=5) as executor:
            fixed_results = list(executor.map(fix_result, results))

        return fixed_results

    def _extract_content_and_date(self, url):
        """从URL提取内容摘要和发布日期"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            # 使用正确的编码
            if response.encoding.lower() == "iso-8859-1":
                possible_encoding = requests.utils.get_encodings_from_content(response.text)
                if possible_encoding:
                    response.encoding = possible_encoding[0]
                else:
                    response.encoding = response.apparent_encoding

            soup = BeautifulSoup(response.text, "html.parser")

            # 提取发布日期 - 多种方法
            pub_date = None

            # 方法1: 检查meta标签
            meta_date = (
                soup.find("meta", property="article:published_time")
                or soup.find("meta", itemprop="datePublished")
                or soup.find("meta", attrs={"name": "pubdate"})
                or soup.find("meta", attrs={"name": "publishdate"})
            )
            if meta_date and meta_date.get("content"):
                pub_date = meta_date.get("content")

            # 方法2: 查找time标签
            if not pub_date:
                time_tag = soup.find("time")
                if time_tag and time_tag.get("datetime"):
                    pub_date = time_tag.get("datetime")

            # 方法3: 正则表达式查找日期格式
            if not pub_date:
                date_patterns = [
                    r"\d{4}-\d{2}-\d{2}",  # YYYY-MM-DD
                    r"\d{2}/\d{2}/\d{4}",  # MM/DD/YYYY
                    r"\d{4}年\d{1,2}月\d{1,2}日",  # YYYY年MM月DD日
                ]
                for pattern in date_patterns:
                    date_match = re.search(pattern, response.text)
                    if date_match:
                        pub_date = date_match.group(0)
                        break

            # 提取摘要
            abstract = ""

            # 方法1: 使用meta描述 - 这里已经正确使用了字典
            meta_desc = soup.find("meta", {"name": "description"}) or soup.find(
                "meta", {"property": "og:description"}
            )
            if meta_desc and meta_desc.get("content"):
                abstract = meta_desc.get("content")

            # 方法2: 提取文章正文
            if not abstract or len(abstract) < 100:
                # 尝试找到文章主体
                article = soup.find("article") or soup.find(
                    class_=re.compile("article|content|post|entry")
                )

                if article:
                    paragraphs = article.find_all("p")
                else:
                    paragraphs = soup.find_all("p")

                content = []
                for p in paragraphs:
                    text = p.get_text().strip()
                    if len(text) > 30:  # 忽略太短的段落
                        content.append(text)

                if content:
                    abstract = " ".join(content[:3])[:500]  # 取前三段，最多500字

            # 如果仍然没有摘要，使用页面标题
            if not abstract:
                title_tag = soup.find("title")
                if title_tag:
                    abstract = f"页面标题: {title_tag.get_text()}"

            # 标准化日期格式
            if pub_date:
                try:
                    # 尝试解析各种格式的日期
                    if "T" in pub_date:
                        pub_date = pub_date.split("T")[0]
                    elif "/" in pub_date:
                        date_parts = pub_date.split("/")
                        if len(date_parts[2]) == 4:  # MM/DD/YYYY
                            pub_date = f"{date_parts[2]}-{date_parts[0]}-{date_parts[1]}"
                    elif "年" in pub_date:
                        date_parts = re.findall(r"\d+", pub_date)
                        if len(date_parts) >= 3:
                            pub_date = (
                                f"{date_parts[0]}-{date_parts[1].zfill(2)}-{date_parts[2].zfill(2)}"
                            )
                except Exception:
                    # 如果日期解析失败，保留原始格式
                    pass

            return abstract, pub_date
        except Exception as e:
            log.print_traceback("从URL提取内容摘要和发布日期", e)
            return "", None

    def search(
        self,
        topic,
        max_results=10,
        use_cache=True,
        cache_duration=3600,
        force_module=None,
        use_fix_results_parallel=True,
    ):
        """执行搜索，支持缓存和多种搜索方法"""
        current_time = time.time()
        cache_key = f"{topic}_{max_results}"

        # 检查缓存
        if use_cache and cache_key in self.cache:
            cached_data = self.cache[cache_key]
            timestamp = cached_data.get("timestamp", 0)

            # 确保timestamp是浮点数
            if isinstance(timestamp, str):
                try:
                    timestamp = float(timestamp)
                except ValueError:
                    timestamp = 0

            if current_time - timestamp < cache_duration:
                self.console.print(f"[blue]使用缓存结果: {topic}[/blue]")
                return cached_data.get("results")

        # 确保任务管理器已初始化
        self._init_task_manager()

        # 选择搜索模块
        module_id = force_module or self._get_best_module()

        if not module_id or module_id not in self.modules_info["modules"]:
            self.console.print("[red]没有可用的搜索模块[/red]")
            return f"未能找到关于'{topic}'的搜索结果: 没有可用的搜索模块"

        # 获取模块类型
        module_type = self.modules_info["modules"][module_id]["type"]

        # 检查是否需要重新生成模块
        new_module_id = self._regenerate_module_if_needed(module_type)
        if new_module_id:
            module_id = new_module_id

        # 导入搜索模块
        search_module = self._import_module(module_id)
        if not search_module:
            self.console.print(f"[red]无法导入搜索模块 {module_id}[/red]")
            return f"未能找到关于'{topic}'的搜索结果: 无法导入搜索模块"

        # 执行搜索
        try:
            result = search_module.search_web(topic, max_results)

            # 检查搜索结果
            if result.get("success", False):
                # 验证并修复结果
                results = result.get("results", [])
                if results:
                    if use_fix_results_parallel:
                        fixed_results = self._validate_and_fix_results_parallel(results)
                    else:
                        fixed_results = self._validate_and_fix_results(results)

                    result["results"] = fixed_results

                # 更新模块成功率
                if module_id in self.modules_info["success_rate"]:
                    self.modules_info["success_rate"][module_id]["successes"] += 1
                    self._save_modules_info()

                # 更新缓存
                if use_cache:
                    self.cache[cache_key] = result
                    self._save_cache()

                return result.get("results")
            else:
                # 记录错误
                self._log_error(module_id, "search_failed", result.get("error", "未知错误"), topic)

                # 尝试使用备用模块
                if not force_module:
                    # 找到一个不同类型的模块
                    for alt_id in self.modules_info["modules"]:
                        if self.modules_info["modules"][alt_id]["type"] != module_type:
                            self.console.print(f"[yellow]尝试使用备用搜索模块: {alt_id}[/yellow]")
                            return self.search(
                                topic, max_results, use_cache, cache_duration, alt_id
                            )

                return f"未能找到关于'{topic}'的搜索结果: {result.get('error', '搜索失败')}"

        except Exception as e:
            # 记录错误
            self._log_error(module_id, "exception", str(e), topic)

            # 如果是第一次尝试，尝试使用备用模块
            if not force_module:
                # 找到一个不同类型的模块
                for alt_id in self.modules_info["modules"]:
                    if self.modules_info["modules"][alt_id]["type"] != module_type:
                        self.console.print(
                            f"[yellow]搜索出错，尝试使用备用搜索模块: {alt_id}[/yellow]"
                        )
                        return self.search(topic, max_results, use_cache, cache_duration, alt_id)

            self.console.print(f"[red]搜索执行错误: {str(e)}[/red]")
            return f"未能找到关于'{topic}'的搜索结果: {str(e)}"
