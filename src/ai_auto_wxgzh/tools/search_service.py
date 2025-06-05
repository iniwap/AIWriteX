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
from src.ai_auto_wxgzh.tools import search_template


class SearchService:
    """搜索服务，支持持久化、多种搜索方法和纠错机制"""

    def __init__(self):
        self.console = Console()
        self._setup_directories()
        self._load_data()
        self._init_task_manager()

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
        self.cache_file = self.cache_dir / "search_cache.json"
        self.error_log_file = self.cache_dir / "search_errors.json"

    def _load_data(self):
        """加载所有数据"""
        self.default_cache_duration = 3600 * 24
        self.modules_info = self._load_modules_info()
        self.cache = self._load_cache()
        self._clean_cache()
        self.error_log = self._load_error_log()

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

    def _ensure_ai_modules_exist(self):
        """确保搜索模块文件存在，如果不存在则创建"""
        # 检查是否有任何搜索模块
        if not self.modules_info["modules"]:
            # 生成多种搜索模块
            module_types = [
                ("baidu", "通过解析百度搜索结果页面获取信息，使用网页爬取技术"),
                ("bing", "通过解析bing搜索结果页面获取信息，使用网页爬取技术"),
                ("sougou", "通过解析搜狗搜索结果页面获取信息，使用网页爬取技术"),
                ("360", "通过解析360搜索结果页面获取信息，使用网页爬取技术"),
                ("combined", "综合多种国内搜索引擎，按优先级尝试"),
            ]

            for module_type, description in module_types:
                self._generate_search_module(module_type, description)

            # 设置默认模块
            if self.modules_info["modules"]:
                self.modules_info["default_module"] = list(self.modules_info["modules"].keys())[0]
                self._save_modules_info()

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

    def _save_module_code(self, module_type, code, description, source="ai"):
        """保存模块代码，添加来源标识"""
        try:
            module_id = f"{module_type}_{source}_{int(time.time())}"

            module_path = self.search_modules_dir / f"{module_id}.py"

            # 保存代码到模块文件
            with open(module_path, "w", encoding="utf-8") as f:
                f.write(code)

            # 更新模块信息
            self.modules_info["modules"][module_id] = {
                "type": module_type,
                "source": source,  # 新增：标识代码来源
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

    def _generate_search_module(self, module_type, description):
        """通过LLM生成特定类型的搜索模块代码并保存"""

        # 直接使用AI生成，不再检查模板
        # 先尝试基于模板的约束性生成
        constrained_result = self._try_template_guided_generation(module_type, description)
        if constrained_result:
            return constrained_result

        # 最后尝试完全自由的AI生成
        return self._try_free_form_generation(module_type, description)

    def _generate_with_instruction(self, instruction, module_type, description, source="ai"):
        """使用给定的指令通过AI生成代码并保存"""
        task = None
        try:
            task = self.task_manager.new_task(instruction)
            task.run()

            code = self._extract_code_from_task(task)

            if code and "search_web" in code:
                if self._validate_generated_code(code):
                    return self._save_module_code(module_type, code, description, source=source)
                else:
                    self.console.print("[yellow]AI生成代码验证失败[/yellow]")
            else:
                self.console.print("[yellow]AI未生成有效代码[/yellow]")
            return None
        finally:
            if task:
                task.done()

    def _try_template_guided_generation(self, module_type, description):
        """基于模板模式的约束性AI生成"""
        # 从您的模板中提取关键模式
        search_instruction = """
        请生成一个搜索函数，能够从四种搜索引擎（不要使用API密钥方式）获取结果。参考以下成功配置：

        # 搜索引擎URL模式：
        - 百度: https://www.baidu.com/s?wd={{quote(topic)}}&rn={{max_results}}
        - Bing: https://www.bing.com/search?q={{quote(topic)}}&count={{max_results}}
        - 360: https://www.so.com/s?q={{quote(topic)}}&rn={{max_results}}
        - 搜狗: https://www.sogou.com/web?query={{quote(topic)}}

        # 关键CSS选择器：
        百度结果容器: ["div.result", "div.c-container", "div[class*='result']"]
        百度标题: ["h3", "h3 a", ".t", ".c-title"]
        百度摘要: ["div.c-abstract", ".c-span9", "[class*='abstract']"]

        Bing结果容器: ["li.b_algo", "div.b_algo", "li[class*='algo']"]
        Bing标题: ["h2", "h3", "h2 a", ".b_title"]
        Bing摘要: ["p.b_lineclamp4", "div.b_caption", ".b_snippet"]

        360结果容器: ["li.res-list", "div.result", "li[class*='res']"]
        360标题: ["h3.res-title", "h3", ".res-title"]
        360摘要: ["p.res-desc", "div.res-desc", ".res-summary"]

        搜狗结果容器: ["div.vrwrap", "div.results", "div.result"]
        搜狗标题: ["h3.vr-title", "h3.vrTitle", "a.title", "h3"]
        搜狗摘要: ["div.str-info", "div.str_info", "p.str-info"]

        # 重要处理逻辑：
        1. 按优先级依次尝试四个搜索引擎，直到获取到有效结果（至少有一条摘要不为空），停止尝试生成
        2. 使用 concurrent.futures.ThreadPoolExecutor 并行访问页面提取详细内容
        3. 从页面提取发布时间，遵从以下策略：
            - 优先meta标签：article:published_time、datePublished、pubdate、publishdate等
            - 备选方案：time标签、日期相关class、页面文本匹配
            - 支持多种日期格式：YYYY-MM-DD、中文日期等
        4. 按发布时间排序，优先最近7天内容

        # 返回数据格式（严格遵守）：
        {{
            "timestamp": time.time(),
            "topic": "搜索主题",
            "results": [
                {{
                    "title": "标题",
                    "url": "链接",
                    "abstract": "详细摘要（去除空格换行，至少200字）",
                    "pub_time": "发布时间"
                }}
            ],
            "success": True/False,
            "error": 错误信息或None
        }}

        只返回完整的Python代码，不要有任何解释。
        """

        return self._generate_with_instruction(
            search_instruction, module_type, description, source="ai_guided"
        )

    def _try_free_form_generation(self, module_type, description):
        """完全自由的AI生成"""
        search_instruction = """
        请创新性地生成搜索函数，获取最新相关信息：

        # 可选搜索策略：
        1. 依次尝试不同搜索引擎（百度、Bing、360、搜狗）,直到获取到有效结果（至少有一条摘要不为空），停止尝试生成
        2. 使用新闻聚合API（如NewsAPI、RSS源）
        3. 尝试社交媒体平台搜索
        4. 使用学术搜索引擎

        # 核心要求：
        - 函数名为search_web，参数topic和max_results
        - 实现多重容错机制，至少尝试2-3种不同方法
        - 对每个结果访问原始页面提取完整信息
        - 优先获取最近7天内的新鲜内容，按发布时间排序
        - 摘要长度至少100字，包含关键信息
        - 不能使用需要API密钥的方式
        - 过滤掉验证页面和无效内容，正确处理编码，结果不能包含乱码

        # 时间提取策略：
        - 优先meta标签：article:published_time、datePublished、pubdate、publishdate等
        - 备选方案：time标签、日期相关class、页面文本匹配
        - 支持多种日期格式：YYYY-MM-DD、中文日期等

        # 返回数据格式（严格遵守）：
        {{
            "timestamp": time.time(),
            "topic": "搜索主题",
            "results": [
                {{
                    "title": "标题",
                    "url": "链接",
                    "abstract": "详细摘要（去除空格换行，至少200字）",
                    "pub_time": "发布时间"
                }}
            ],
            "success": True/False,
            "error": 错误信息或None
        }}
        只返回完整的Python代码，不要有任何解释。
        """

        return self._generate_with_instruction(
            search_instruction, module_type, description, source="ai_free"
        )

    def _get_best_module(self):
        """根据历史成功率选择最佳AI模块"""
        if not self.modules_info["modules"]:
            return None

        # 只考虑AI模块的成功率，不再区分模板和AI
        ai_modules = {}

        for module_id, stats in self.modules_info["success_rate"].items():
            if module_id in self.modules_info["modules"]:
                total = stats["successes"] + stats["failures"]
                success_rate = stats["successes"] / total if total > 0 else 0.5
                ai_modules[module_id] = success_rate

        # 选择成功率最高的AI模块
        if ai_modules:
            return max(ai_modules, key=ai_modules.get)

        return self.modules_info["default_module"]

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
        if total >= 4 and stats["failures"] / total > 0.6:
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
        """执行搜索，采用递进策略"""

        # 第一优先级：本地模板搜索
        template_result = self._try_template_search(topic, max_results)
        if template_result and search_template.validate_search_result(template_result, "local"):
            return template_result.get("results")

        # 第二优先级：AI搜索
        return self._ai_search(
            topic, max_results, use_cache, cache_duration, force_module, use_fix_results_parallel
        )

    def _try_template_search(self, topic, max_results):
        """执行搜索，优化缓存策略"""
        try:
            template_result = search_template.search_web(topic, max_results)
            if template_result:
                self.console.print(f"[green]使用本地模板搜索成功: {topic}[/green]")
                return template_result  # 返回完整的字典
            else:
                self.console.print("[yellow]本地模板搜索失败，启用AI生成代码搜索[/yellow]")
        except Exception as e:
            self.console.print(f"[yellow]本地模板搜索异常: {e}，启用AI生成代码搜索[/yellow]")
        return None  # 确保在失败时返回 None

    def _get_cache_key(self, topic, max_results, module_id=None):
        """生成缓存键"""
        if module_id and module_id in self.modules_info["modules"]:
            module_source = self.modules_info["modules"][module_id].get("source", "ai")
            return f"{topic}_{max_results}_{module_source}"
        return f"{topic}_{max_results}"

    def _ai_search(
        self,
        topic,
        max_results,
        use_cache,
        cache_duration,
        force_module,
        use_fix_results_parallel,
    ):
        """AI搜索的完整逻辑"""
        current_time = time.time()

        # AI搜索前确保有可用模块
        self._ensure_ai_modules_exist()

        # 缓存键包含模块来源信息
        module_id = force_module or self._get_best_module()
        cache_key = self._get_cache_key(topic, max_results, module_id)

        # 检查缓存
        if use_cache and cache_key in self.cache:
            cached_data = self.cache[cache_key]
            timestamp = cached_data.get("timestamp", 0)
            if isinstance(timestamp, str):
                try:
                    timestamp = float(timestamp)
                except ValueError:
                    timestamp = 0

            if current_time - timestamp < cache_duration:
                self.console.print(f"[blue]使用缓存结果: {topic}[/blue]")

                return cached_data.get("results")

        if not module_id or module_id not in self.modules_info["modules"]:
            self.console.print(f"[red]未能找到关于'{topic}'的搜索结果: 没有可用的搜索模块[/red]")
            return None

        # 获取模块类型
        module_type = self.modules_info["modules"][module_id]["type"]

        # 检查是否需要重新生成模块（恢复原有功能）
        if module_id and not force_module:
            new_module_id = self._regenerate_module_if_needed(module_type)
            if new_module_id:
                module_id = new_module_id

        # 尝试执行搜索
        search_result = self._execute_search_with_fallback(
            module_id, module_type, topic, max_results
        )

        if search_result and search_result.get("success") and search_result.get("results"):
            # 验证并修复结果
            results = search_result.get("results", [])
            if use_fix_results_parallel:
                fixed_results = self._validate_and_fix_results_parallel(results)
            else:
                fixed_results = self._validate_and_fix_results(results)

            search_result["results"] = fixed_results

            # 更新模块成功率
            if module_id in self.modules_info["success_rate"]:
                self.modules_info["success_rate"][module_id]["successes"] += 1
                self._save_modules_info()

            # 更新缓存
            if use_cache:
                self.cache[cache_key] = search_result
                self._save_cache()

            return search_result.get("results")
        else:
            # 记录搜索失败，用于后续模块质量评估
            if module_id in self.modules_info["success_rate"]:
                self.modules_info["success_rate"][module_id]["failures"] += 1
                self._save_modules_info()

            self.console.print(f"[red]未能找到关于'{topic}'的搜索结果: 所有搜索方法都失败了[/red]")
            return None

    def _find_alternative_modules(self, module_type, exclude_module_id):
        """查找同类型的备选模块"""
        alternatives = []
        for module_id, info in self.modules_info["modules"].items():
            if info["type"] == module_type and module_id != exclude_module_id:
                alternatives.append(module_id)
        return alternatives

    def _regenerate_module_with_enhanced_prompt(self, module_type):
        """使用增强提示重新生成模块"""
        description = f"重新生成的{module_type}搜索模块"
        return self._generate_search_module(module_type, description)

    def _execute_search_with_fallback(self, module_id, module_type, topic, max_results):
        """执行搜索，优化回退策略"""

        # 获取模块来源信息
        module_source = self.modules_info["modules"][module_id].get("source", "ai")

        # 根据来源确定验证类型
        if module_source == "ai_guided":
            validation_type = "ai_guided"
        elif module_source == "ai_free":
            validation_type = "ai_free"
        else:
            validation_type = "local"

        # 第一次尝试：使用现有模块
        result = self._try_module_with_validation(module_id, topic, max_results, validation_type)
        if result:
            return result

        # 第二次尝试：查找同类型的其他模块
        alternative_modules = self._find_alternative_modules(module_type, module_id)
        for alt_id in alternative_modules:
            alt_source = self.modules_info["modules"][alt_id].get("source", "ai")
            alt_validation_type = "ai_guided" if alt_source == "ai_guided" else "ai_free"

            result = self._try_module_with_validation(
                alt_id, topic, max_results, alt_validation_type
            )
            if result:
                return result

        # 第三次尝试：重新生成模块
        new_module_id = self._regenerate_module_with_enhanced_prompt(module_type)
        if new_module_id:
            result = self._try_module_with_validation(
                new_module_id, topic, max_results, "ai_guided"
            )
            if result:
                return result

        return None

    def _try_module_with_validation(self, module_id, topic, max_results, validation_type="local"):
        """尝试使用模块并验证结果"""
        module = self._import_module(module_id)
        if module:
            try:
                result = module.search_web(topic, max_results)
                if search_template.validate_search_result(result, validation_type):
                    return result
                else:
                    self._log_error(
                        module_id,
                        "poor_quality_result",
                        f"搜索结果不满足{validation_type}验证",
                        topic,
                    )
            except Exception as e:
                self._log_error(module_id, "execution_error", str(e), topic)
        return None
