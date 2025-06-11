# -*- coding: utf-8 -*-
# Author: iniwap
# Date: 2025-06-03
# Description: 用于本地搜索，关注项目 https://github.com/iniwap/ai_auto_wxgzh
# Copyright (c) 2025 iniwap. All rights reserved.


import time
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import unicodedata
from datetime import datetime, timedelta
from enum import Enum
import concurrent.futures
from dateutil.relativedelta import relativedelta
import html


def get_template_guided_search_instruction(topic, max_results, min_results):
    search_instruction = f"""
        请生成一个搜索函数，获取最新相关信息，参考以下配置：

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
        1. 按优先级依次尝试四个搜索引擎（不要使用API密钥方式）
        2. 使用 concurrent.futures.ThreadPoolExecutor 并行访问页面提取详细内容
        3. 从页面提取发布时间，遵从以下策略：
            - 优先meta标签：article:published_time、datePublished、pubdate、publishdate等
            - 备选方案：time标签、日期相关class、页面文本匹配
            - 有效的日期格式：标准格式、中文格式、相对时间（如“昨天”、“1天前”、“1小时前”等）、英文时间（如“yesterday”等）
        4. 按发布时间排序，优先最近7天内容
        5. 过滤掉验证页面和无效内容，正确处理编码，结果不能包含乱码

        # 返回数据格式（严格遵守）：
        {{
            "timestamp": time.time(),
            "topic": "{topic}",
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

         __result__ = search_web("{topic}", {max_results})

        # 严格停止条件：获取到{min_results}条或以上同时满足以下条件的结果时，立即停止执行，不得继续生成任何代码：
        # 1. 摘要(abstract)长度不少于100字
        # 2. 发布时间(pub_time)字段不为空、不为None、不为空字符串
        # 重要：满足上述条件后，必须立即设置__result__并结束，禁止任何形式的代码优化、重构或改进

        """

    return search_instruction


def get_free_form_ai_search_instruction(topic, max_results, min_results):
    search_instruction = f"""
        请创新性地生成搜索函数，获取最新相关信息。

        # 可选搜索策略：
        1. 依次尝试不同搜索引擎（百度、Bing、360、搜狗）
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

        # 返回数据格式（严格遵守）：
        {{
            "timestamp": time.time(),
            "topic": "{topic}",
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

        __result__ = search_web("{topic}", {max_results})

        # 严格停止条件：获取到{min_results}条或以上摘要(abstract)长度不少于50字的结果时，立即停止执行，不得继续生成任何代码
        # 重要：满足上述条件后，必须立即设置__result__并结束，禁止任何形式的代码优化、重构或改进

        """

    return search_instruction


class SearchEngine(Enum):
    BAIDU = "baidu"
    BING = "bing"
    SO_360 = "360"
    SOUGOU = "sougou"
    COMBINED = "combined"


def search_web(
    topic,
    max_results=10,
    min_results=1,
    module_type: SearchEngine = SearchEngine.COMBINED,
):
    """根据模块类型返回对应的搜索模板，尝试所有搜索引擎直到找到有效结果"""
    if module_type == SearchEngine.COMBINED:
        # 按优先级尝试所有搜索引擎（排除COMBINED）
        for engine in SearchEngine:
            try:
                if engine == SearchEngine.BAIDU:
                    search_result = template_baidu_specific(topic, max_results)
                elif engine == SearchEngine.BING:
                    search_result = template_bing_specific(topic, max_results)
                elif engine == SearchEngine.SO_360:
                    search_result = template_360_specific(topic, max_results)
                elif engine == SearchEngine.SOUGOU:
                    search_result = template_sougou_specific(topic, max_results)
                else:
                    continue

                # 验证搜索结果质量
                if validate_search_result(search_result, min_results):
                    return search_result
            except Exception as e:  # noqa 841
                continue

        # 所有搜索引擎都失败，返回 None
        return None

    elif module_type == SearchEngine.BAIDU:
        result = template_baidu_specific(topic, max_results)
        return result if validate_search_result(result, min_results) else None
    elif module_type == SearchEngine.BING:
        result = template_bing_specific(topic, max_results)
        return result if validate_search_result(result, min_results) else None
    elif module_type == SearchEngine.SO_360:
        result = template_360_specific(topic, max_results)
        return result if validate_search_result(result, min_results) else None
    elif module_type == SearchEngine.SOUGOU:
        result = template_sougou_specific(topic, max_results)
        return result if validate_search_result(result, min_results) else None
    else:
        return None


def simple_validate_search_result(result, min_results, search_type="ai_guided"):
    """
    验证搜索结果质量，确保至少min_results条结果满足指定搜索类型的完整性条件

    Args:
        result: 搜索结果字典
        search_type: 搜索类型 ("ai_guided" 或 "ai_free")

    Returns:
        bool: 是否有效
    """
    # 快速失败检查
    if not result or not isinstance(result, dict):
        return False

    if not result.get("success", False):
        return False

    results = result.get("results", [])
    if not results or len(results) < min_results:
        return False

    # 定义验证规则
    validation_rules = {
        "ai_guided": {"abstract_min_length": 100, "require_date": True},
        "ai_free": {"abstract_min_length": 50, "require_date": False},
    }

    # 获取当前搜索类型的规则
    rules = validation_rules.get(search_type, validation_rules["ai_guided"])

    # 验证结果项
    for item in results:
        if not isinstance(item, dict):
            continue

        abstract = item.get("abstract", "")
        if not abstract or len(abstract.strip()) < rules["abstract_min_length"]:
            continue

        # 如果需要验证日期
        if rules["require_date"]:
            pub_time = item.get("pub_time", "")
            if not pub_time or not is_valid_date(pub_time):
                continue

        # 找到一个有效结果就返回True
        return True

    return False


def validate_search_result(result, min_results=1, search_type="local"):
    """验证搜索结果质量，确保至少min_results条结果满足指定搜索类型的完整性条件，并返回转换后的日期格式"""
    if not isinstance(result, dict) or not result.get("success", False):
        return False

    results = result.get("results", [])
    if not results or len(results) < min_results:
        return False

    timestamp = result.get("timestamp", time.time())

    for item in results:
        pub_time = item.get("pub_time", "")
        abstract = item.get("abstract", "")

        # 尝试从 pub_time 转换
        if pub_time:
            if re.match(r"^\d{4}-\d{2}-\d{2}$", pub_time):
                try:
                    datetime.strptime(pub_time, "%Y-%m-%d")
                    continue
                except ValueError:
                    pass
            # 处理带时分秒的格式
            if re.match(r"^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}(?::\d{2})?$", pub_time):
                try:
                    actual_date = datetime.strptime(pub_time, "%Y-%m-%d %H:%M:%S")
                    item["pub_time"] = actual_date.strftime("%Y-%m-%d")
                    continue
                except ValueError:
                    try:
                        actual_date = datetime.strptime(pub_time, "%Y-%m-%d %H:%M")
                        item["pub_time"] = actual_date.strftime("%Y-%m-%d")
                        continue
                    except ValueError:
                        pass
            if timestamp:
                try:
                    actual_date = calculate_actual_date(pub_time, timestamp)
                    if actual_date:
                        item["pub_time"] = actual_date.strftime("%Y-%m-%d")
                    else:
                        item["pub_time"] = ""
                except Exception:
                    item["pub_time"] = ""

        # 兜底：从 abstract 提取日期
        if not item["pub_time"] and abstract:
            for pattern in [
                r"\d{4}\s*[-/年\.]?\s*\d{1,2}\s*[-/月\.]?\s*\d{1,2}\s*(?:日)?(?:\s+\d{1,2}:\d{1,2}(?::\d{1,2})?)?",  # noqa 501
                r"\d{1,2}\s*[月]\s*\d{1,2}\s*[日]?",
                r"(?:\d+\s*(?:秒|一分钟|分钟|分|小时|个小时|天|日|周|星期|个月|月|年)前|刚刚|今天|昨天|前天|上周|上星期|上个月|上月|去年)",
                r"\d{4}年\d{1,2}月\d{1,2}日",
            ]:
                match = re.search(pattern, abstract, re.IGNORECASE)
                if match:
                    pub_time = match.group(0)
                    if is_valid_date(pub_time):
                        pub_time_date = calculate_actual_date(pub_time, timestamp)
                        if pub_time_date:
                            item["pub_time"] = pub_time_date.strftime("%Y-%m-%d")
                            break

    validation_rules = {
        "local": ["title", "url", "abstract", "pub_time"],
        "ai_guided": ["title", "url", "abstract"],
        "ai_free": ["title", "abstract"],
    }

    quality_rules = {
        "local": {"abstract_min_length": 200, "require_valid_date": True},
        "ai_guided": {"abstract_min_length": 100, "require_valid_date": True},
        "ai_free": {"abstract_min_length": 50, "require_valid_date": False},
    }

    required_fields = validation_rules.get(search_type, validation_rules["local"])
    quality_req = quality_rules.get(search_type, quality_rules["local"])

    for item in results:
        if not all(item.get(field, "").strip() for field in required_fields):
            continue

        abstract = item.get("abstract", "")
        if len(abstract.strip()) < quality_req["abstract_min_length"]:
            continue

        if quality_req["require_valid_date"] and search_type != "ai_guided":
            pub_time = item.get("pub_time", "")
            if not pub_time or not re.match(r"^\d{4}-\d{2}-\d{2}$", pub_time):
                continue
            try:
                datetime.strptime(pub_time, "%Y-%m-%d")
            except ValueError:
                continue

        return True

    return False


def is_valid_date(date_str, timestamp=None):
    """验证日期字符串是否可转换为有效日期"""
    if not date_str or date_str in [None, "", "None", "未知"]:
        return False

    date_str = clean_date_text(str(date_str))

    if timestamp is None:
        timestamp = time.time()

    date_patterns = [
        # 完整日期时间（支持带空格的中文格式）
        r"\d{4}\s*[-/年\.]?\s*\d{1,2}\s*[-/月\.]?\s*\d{1,2}\s*(?:日)?(?:\s+\d{1,2}:\d{1,2}(?::\d{1,2})?)?",  # noqa 501
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})?",
        r"\d{1,2}[-/]\d{1,2}[-/]\d{4}\s+\d{1,2}:\d{1,2}(?::\d{1,2})?",
        # 完整日期
        r"\d{4}\s*[-/年\.]?\s*\d{1,2}\s*[-/月\.]?\s*\d{1,2}\s*(?:日)?",
        r"\d{1,2}[-/]\d{1,2}[-/]\d{4}",
        # 相对时间
        r"(\d+)\s*(秒|分钟|分|小时|个小时|天|日|周|星期|个月|月|年)前",
        r"(刚刚|今天|昨天|前天|上周|上星期|上个月|上月|去年)",
        # 不完整日期
        r"\d{1,2}\s*[-/\.月]?\s*\d{1,2}\s*(?:日)?",
        # Unix 时间戳
        r"^\d{10}$",
        r"^\d{13}$",
        # 英文格式
        r"\d+\s*(second|seconds|minute|minutes|hour|hours|day|days|week|weeks|month|months|year|years)\s*ago",  # noqa 501
        r"(yesterday|today|just\s*now|last\s*(week|month|year)|this\s*(week|month|year))",
    ]

    for pattern in date_patterns:
        if re.search(pattern, date_str, re.IGNORECASE):
            return True

    return False


def calculate_actual_date(pub_time, timestamp):
    """将发布日期转换为 datetime 对象"""
    if not pub_time or not timestamp:
        return None

    try:
        pub_time = clean_date_text(str(pub_time))
        reference_date = datetime.fromtimestamp(timestamp)

        # 1. 相对时间
        relative_patterns = [
            (r"(\d+)\s*秒前", lambda n: reference_date - timedelta(seconds=n)),
            (r"(\d+)\s*(分钟|分)前", lambda n: reference_date - timedelta(minutes=n)),
            (r"(\d+)\s*(小时|个小时)前", lambda n: reference_date - timedelta(hours=n)),
            (r"(\d+)\s*(天|日)前", lambda n: reference_date - timedelta(days=n)),
            (r"(\d+)\s*(周|星期)前", lambda n: reference_date - timedelta(weeks=n)),
            (r"(\d+)\s*(个月|月)前", lambda n: reference_date - relativedelta(months=n)),
            (r"(\d+)\s*年前", lambda n: reference_date - relativedelta(years=n)),
        ]

        for pattern, calc_func in relative_patterns:
            match = re.search(pattern, pub_time, re.IGNORECASE)
            if match:
                num = int(match.group(1))
                return calc_func(num)

        # 2. 特殊相对时间
        special_relative = {
            "刚刚": reference_date,
            "今天": reference_date.replace(hour=0, minute=0, second=0, microsecond=0),
            "昨天": reference_date - timedelta(days=1),
            "前天": reference_date - timedelta(days=2),
            "上周": reference_date - timedelta(weeks=1),
            "上星期": reference_date - timedelta(weeks=1),
            "上个月": reference_date - relativedelta(months=1),
            "上月": reference_date - relativedelta(months=1),
            "去年": reference_date - relativedelta(years=1),
        }

        for key, calc_date in special_relative.items():
            if key in pub_time:
                return calc_date

        # 3. 英文相对时间
        english_relative = [
            (r"(\d+)\s*seconds?\s*ago", lambda n: reference_date - timedelta(seconds=n)),
            (r"(\d+)\s*minutes?\s*ago", lambda n: reference_date - timedelta(minutes=n)),
            (r"(\d+)\s*hours?\s*ago", lambda n: reference_date - timedelta(hours=n)),
            (r"(\d+)\s*days?\s*ago", lambda n: reference_date - timedelta(days=n)),
            (r"(\d+)\s*weeks?\s*ago", lambda n: reference_date - timedelta(weeks=n)),
            (r"(\d+)\s*months?\s*ago", lambda n: reference_date - relativedelta(months=n)),
            (r"(\d+)\s*years?\s*ago", lambda n: reference_date - relativedelta(years=n)),
            (r"yesterday", lambda: reference_date - timedelta(days=1)),
            (r"just\s*now", lambda: reference_date),
            (r"last\s*week", lambda: reference_date - timedelta(weeks=1)),
            (r"last\s*month", lambda: reference_date - relativedelta(months=1)),
            (r"last\s*year", lambda: reference_date - relativedelta(years=1)),
        ]

        for pattern, calc_func in english_relative:
            match = re.search(pattern, pub_time, re.IGNORECASE)
            if match:
                if match.groups():
                    num = int(match.group(1))
                    return calc_func(num)
                return calc_func()

        # 4. 不完整日期
        incomplete_patterns = [
            r"(\d{1,2})\s*[-/\.月]?\s*(\d{1,2})\s*(?:日)?",
        ]

        for pattern in incomplete_patterns:
            match = re.search(pattern, pub_time)
            if match:
                month, day = map(int, match.groups())
                if 1 <= month <= 12 and 1 <= day <= 31:
                    current_year = reference_date.year
                    try_date = reference_date.replace(year=current_year, month=month, day=day)
                    if try_date > reference_date:
                        try_date = try_date.replace(year=current_year - 1)
                    # 验证日期合理性
                    if abs((try_date - reference_date).days) > 365:
                        try_date_alt = try_date.replace(
                            year=current_year - 1 if try_date > reference_date else current_year + 1
                        )
                        if abs((try_date_alt - reference_date).days) < abs(
                            (try_date - reference_date).days
                        ):
                            try_date = try_date_alt
                    return try_date

        # 5. 完整日期
        complete_patterns = [
            (r"(\d{4})\s*[-/年\.]?\s*\d{1,2}\s*[-/月\.]?\s*\d{1,2}\s*(?:日)?", "%Y-%m-%d"),
            (r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", "%m/%d/%Y"),
        ]

        for pattern, date_format in complete_patterns:
            match = re.search(pattern, pub_time)
            if match:
                date_str = match.group(0)
                return datetime.strptime(date_str, date_format)

        # 6. Unix 时间戳
        if re.match(r"^\d{10}$", pub_time):
            return datetime.fromtimestamp(int(pub_time))
        if re.match(r"^\d{13}$", pub_time):
            return datetime.fromtimestamp(int(pub_time) / 1000)

    except Exception:
        return None

    return None


def is_within_days(date_str, days=7):
    """检查日期是否在指定天数内"""
    if not date_str:
        return False
    try:
        timestamp = parse_date_to_timestamp(date_str)
        if timestamp == 0:
            return False
        days_ago = (datetime.now() - timedelta(days=days)).timestamp()
        return timestamp >= days_ago
    except Exception as e:  # noqa 841
        return False


def clean_date_text(text):
    """专为日期清理文本，保留日期格式关键字符"""
    if not text:
        return ""
    try:
        if isinstance(text, bytes):
            text = text.decode("utf-8", errors="ignore")
        text = html.unescape(text)
        text = re.sub(
            r"^(发表于|更新时间|发布时间|创建时间|Posted on|Published on|Date):\s*",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()
        text = "".join(char for char in text if unicodedata.category(char)[0] != "C")
        # 保留单个空格，避免破坏中文日期格式
        text = re.sub(r"\s+", " ", text).strip()
        return text
    except Exception:
        return ""


def clean_text(text):
    """清理乱码文本，更少地过滤有效字符"""
    if not text:
        return ""
    try:
        # 如果是字节串，尝试解码
        if isinstance(text, bytes):
            text = text.decode("utf-8", errors="ignore")

        # 处理常见的 Unicode 转义序列，这可能表示乱码文本
        # 例如，字符串中可能出现 "\\xef\\xbb\\xbf" 这样的内容
        try:
            if "\\x" in text:
                # 尝试解码常见的有问题字节序列
                text = (
                    text.encode("utf-8")
                    .decode("unicode_escape")
                    .encode("latin1")
                    .decode("utf-8", errors="ignore")  # 添加 errors='ignore'
                )
        except Exception:
            pass  # 如果解码失败，保留原始文本

        # 移除 Unicode 分类为 'C' (Other) 的字符，这通常包括控制字符、格式字符、未分配字符和私用字符。
        # 这种方式对于移除真正不可打印/不可见的字符来说通常是安全的。
        # 同时排除行分隔符 (Zl) 和段落分隔符 (Zp)
        text = "".join(
            char for char in text if unicodedata.category(char)[0] not in ["C", "Zl", "Zp"]
        )

        # 可选：移除未被解析的 HTML 实体，例如 "&#x200B;" 或其他具名实体
        text = re.sub(r"&#x[0-9a-fA-F]+;", "", text)  # 移除 HTML 数字字符引用
        text = re.sub(r"&[a-zA-Z]+;", "", text)  # 移除 HTML 具名字符引用

        # 将多个空格替换为单个空格，并移除首尾空格
        text = re.sub(r"\s+", " ", text).strip()

        return text.strip()
    except Exception:
        return ""


def get_common_headers():
    """获取通用请求头"""
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",  # noqa 501
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


def parse_date_to_timestamp(date_str):
    """将日期字符串转换为时间戳用于排序，增加更多日期格式识别"""
    if not date_str:
        return 0

    # 预处理常见的非标准字符和修饰语
    # 移除括号及其内容，例如 "(发布时间)"
    date_str = re.sub(r"\(.*?\)", "", date_str).strip()
    date_str = date_str.replace("年", "-").replace("月", "-").replace("日", "").replace("/", "-")
    # 移除常见的日期前缀或无关文本，但保留日期本身
    date_str = re.sub(
        r"^(发表于|更新时间|发布时间|创建时间|Posted on|Published on|Date):\s*",
        "",
        date_str,
        flags=re.IGNORECASE,
    ).strip()
    date_str = re.sub(
        r"[^\d\s\-:]", "", date_str
    )  # 移除多余的非日期字符，但保留数字、空格、连字符、冒号
    date_str = date_str.split("T")[
        0
    ]  # 通常时间戳格式的'T'后面是时间，我们只取日期部分，但确保不会切掉只有日期部分的时间

    # 尝试匹配更广泛的日期时间格式
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%Y%m%d",  # 例如 20240530
        "%m-%d-%Y",  # 例如 05-30-2024
        "%B %d, %Y",  # 例如 May 30, 2024 (如果文本是英文)
        "%d %B %Y",  # 例如 30 May 2024 (如果文本是英文)
        "%Y.%m.%d",  # 例如 2024.05.30
        "%y-%m-%d",  # 例如 24-05-30
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.timestamp()
        except ValueError:
            continue

    return 0


def extract_page_content(url, headers=None):
    """从 URL 提取页面内容和发布日期"""
    try:
        time.sleep(1)
        response = requests.get(url, headers=headers or {}, timeout=30)
        response.encoding = response.apparent_encoding or "utf-8"
        content = response.text

        page_soup = BeautifulSoup(content, "html.parser")

        pub_time = None

        # Meta 标签
        meta_selectors = [
            "meta[property='article:published_time']",
            "meta[itemprop='datePublished']",
            "meta[name='publishdate']",
            "meta[name='pubdate']",
            "meta[name='original-publish-date']",
            "meta[name='weibo:article:create_at']",
            "meta[name='baidu_ssp:publishdate']",
        ]
        for selector in meta_selectors:
            meta_tag = page_soup.select_one(selector)
            if meta_tag:
                pub_time = clean_date_text(meta_tag.get("content"))
                if pub_time and is_valid_date(pub_time):
                    meta_date = calculate_actual_date(pub_time, time.time())
                    if meta_date:
                        pub_time = meta_date.strftime("%Y-%m-%d")
                        break

        # Time 标签
        if not pub_time:
            time_tags = page_soup.select("time")
            for time_tag in time_tags:
                pub_time = clean_date_text(time_tag.get("datetime") or time_tag.get_text())
                if pub_time and is_valid_date(pub_time):
                    time_date = calculate_actual_date(pub_time, time.time())
                    if time_date:
                        pub_time = time_date.strftime("%Y-%m-%d")
                        break

        # HTML 元素
        date_selectors = [
            "[class*='date']",
            "[class*='time']",
            "[class*='publish']",
            "[class*='post-date']",
            "[id*='date']",
            "[id*='time']",
            ".byline",
            ".info",
            ".article-meta",
            ".source",
            ".entry-date",
            "div.date",
            "p.date",
            "p.time",
        ]
        if not pub_time:
            for selector in date_selectors:
                elements = page_soup.select(selector)
                for elem in elements:
                    text = clean_date_text(elem.get_text())
                    if text and is_valid_date(text):
                        elem_date = calculate_actual_date(text, time.time())
                        if elem_date:
                            pub_time = elem_date.strftime("%Y-%m-%d")
                            break
                if pub_time:
                    break

        # 兜底：全文搜索（增强正则）
        if not pub_time:
            text = clean_date_text(page_soup.get_text())
            for pattern in [
                r"\d{4}\s*[-/年\.]?\s*\d{1,2}\s*[-/月\.]?\s*\d{1,2}\s*(?:日)?(?:\s+\d{1,2}:\d{1,2}(?::\d{1,2})?)?",  # noqa 501
                r"\d{1,2}[-/]\d{1,2}[-/]\d{4}",
                r"\d{1,2}\s*[月]\s*\d{1,2}\s*[日]?",
                r"(?:\d+\s*(?:秒|分钟|分|小时|个小时|天|日|周|星期|个月|月|年)前|刚刚|今天|昨天|前天|上周|上星期|上个月|上月|去年)",
                r"\d{4}年\d{1,2}月\d{1,2}日",
            ]:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    pub_time = match.group(0)
                    if is_valid_date(pub_time):
                        pub_time_date = calculate_actual_date(pub_time, time.time())
                        if pub_time_date:
                            pub_time = pub_time_date.strftime("%Y-%m-%d")
                            break

        return page_soup, pub_time, content

    except Exception:
        return None, None, None


def enhance_abstract(abstract, page_soup):
    """
    增强摘要内容。
    如果原始摘要过短，尝试从页面内容中提取前几段作为补充。
    """
    # 定义一个最小摘要长度，例如MIN_ABSTRACT_LENGTH个字符，如果摘要小于这个长度则尝试增强
    MIN_ABSTRACT_LENGTH = 300
    MAX_ABSTRACT_LENGTH = 500

    # 检查原始摘要是否过短或不存在，并且 page_soup 存在
    if (not abstract or len(abstract.strip()) < MIN_ABSTRACT_LENGTH) and page_soup:
        content_parts = []
        # 查找所有段落标签，例如 <p>
        paragraphs = page_soup.find_all("p")

        # 遍历前几段，尝试提取有意义的文本
        # 限制遍历的段落数量，避免处理整个页面导致效率低下
        for p in paragraphs[:5]:  # 尝试前5个段落
            text = clean_text(p.get_text().strip())
            # 确保提取的文本有足够的长度，避免加入过短或无意义的段落
            if len(text) > 30:  # 过滤掉长度小于30的段落
                content_parts.append(text)
            # 可以在这里添加一个条件，如果已经提取了足够的文本，就停止
            # 尝试凑够MAX_ABSTRACT_LENGTH字符，考虑到原始摘要可能已经占据一部分长度
            if sum(len(part) for part in content_parts) >= (
                MAX_ABSTRACT_LENGTH - len(abstract.strip())
            ):
                break

        if content_parts:
            # 将提取到的内容拼接起来，并限制总长度
            # 将原始摘要放在前面，然后追加增强内容
            enhanced_text = abstract.strip() + " " + " ".join(content_parts)
            return enhanced_text[
                :MAX_ABSTRACT_LENGTH
            ].strip()  # 限制总长度为MAX_ABSTRACT_LENGTH字符，并移除首尾空白

    return abstract  # 如果不满足增强条件，返回原始摘要


def sort_and_filter_results(results):
    if not results:
        return results

    recent_results = [result for result in results if is_within_days(result.get("pub_time"), 7)]
    recent_results.sort(key=lambda x: parse_date_to_timestamp(x.get("pub_time", "")), reverse=True)

    return recent_results


def _search_template(topic, max_results, engine_config):
    """通用搜索模板"""
    try:
        results = []
        headers = get_common_headers()
        search_url = engine_config["url"].format(topic=quote(topic), max_results=max_results)

        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # 查找结果容器
        search_results = []
        for selector in engine_config["result_selectors"]:
            search_results = soup.select(selector)
            if search_results:
                break

        if not search_results:
            return {
                "timestamp": time.time(),
                "topic": topic,
                "results": [],
                "success": False,
                "error": "未找到搜索结果容器",
            }

        # 收集结果和需要抓取的URL
        tasks = []
        parsed_results = []
        for result in search_results[:max_results]:
            try:
                # 提取标题
                title_elem = None
                for selector in engine_config["title_selectors"]:
                    title_elem = result.select_one(selector)
                    if title_elem:
                        break
                if not title_elem:
                    continue

                link_elem = (
                    title_elem
                    if title_elem.name == "a"
                    else title_elem.find("a") or result.select_one("a[href]")
                )
                if not link_elem:
                    continue

                title = clean_text(title_elem.get_text().strip()) or "无标题"
                url = link_elem.get("href", "")

                # 处理重定向链接
                if (
                    engine_config.get("redirect_pattern")
                    and engine_config["redirect_pattern"] in url
                ):
                    try:
                        response = requests.head(
                            url, headers=headers, allow_redirects=True, timeout=5
                        )
                        response.raise_for_status()
                        url = response.url
                    except requests.exceptions.RequestException:
                        url = ""

                # 提取摘要
                abstract = ""
                for selector in engine_config["abstract_selectors"]:
                    abstract_elem = result.select_one(selector)
                    if abstract_elem:
                        abstract = clean_text(abstract_elem.get_text().strip())
                        if len(abstract) > 20:
                            break
                if not abstract and engine_config.get("fallback_abstract"):
                    abstract_elem = result.find(text=True, recursive=True)
                    abstract = clean_text(abstract_elem.strip())[:200] if abstract_elem else ""

                parsed_results.append({"title": title, "url": url, "abstract": abstract})
                if url and url.startswith("http"):
                    tasks.append((url, headers))

            except Exception:
                continue

        # 并行获取页面内容
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(max_results, 5)) as executor:
            future_to_url = {
                executor.submit(extract_page_content, url, headers): url for url, headers in tasks
            }
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    page_soup, pub_time, _ = future.result()
                    for res in parsed_results:
                        if res["url"] == url:
                            res["pub_time"] = pub_time
                            res["abstract"] = (
                                enhance_abstract(res["abstract"], page_soup) or res["abstract"]
                            )
                            break
                except Exception:
                    pass

        # 构建最终结果
        results = [
            {
                "title": res["title"],
                "url": res["url"],
                "abstract": res["abstract"] or "",
                "pub_time": res.get("pub_time", None),
            }
            for res in parsed_results
            if res["title"] and res["url"]
        ]
        results = sort_and_filter_results(results)

        return {
            "timestamp": time.time(),
            "topic": topic,
            "results": results,
            "success": bool(results),
            "error": None if results else "未生成有效结果",
        }

    except Exception as e:
        return {
            "timestamp": time.time(),
            "topic": topic,
            "results": [],
            "success": False,
            "error": str(e),
        }


# 搜索引擎配置
ENGINE_CONFIGS = {
    "baidu": {
        "url": "https://www.baidu.com/s?wd={topic}&rn={max_results}",
        "redirect_pattern": "baidu.com/link?url=",
        "result_selectors": [
            "div.result",
            "div.c-container",
            "div[class*='result']",
            "div[tpl]",
            ".c-result",
            "div[mu]",
            ".c-result-content",
            "[data-log]",
            "div.c-row",
            ".c-border",
            "div[data-click]",
            ".result-op",
            "[class*='search']",
            "[class*='item']",
            "article",
            "section",
            "div#content_left div",
            "div.result-c",
            "div.c-abstract",
            "div.result-classic",
            "div.result-new",
            "[data-tuiguang]",
            "div.c-container-new",
            "div.result-item",
            "div.c-frame",
            "div.c-gap",
        ],
        "title_selectors": [
            "h3",
            "h3 a",
            ".t",
            ".c-title",
            "[class*='title']",
            "h3.t",
            ".c-title-text",
            "h3[class*='title']",
            ".result-title",
            "a[class*='title']",
            ".c-link",
            "h1",
            "h2",
            "h4",
            "h5",
            "h6",
            "a[href]",
            ".link",
            ".url",
            ".c-title a",
            ".c-title-new",
            "[data-title]",
            ".c-showurl",
            "div.title a",
        ],
        "abstract_selectors": [
            "span.content-right_8Zs40",
            "div.c-abstract",
            ".c-span9",
            "[class*='abstract']",
            ".c-span-last",
            ".c-summary",
            "div.c-row .c-span-last",
            ".result-desc",
            "[class*='desc']",
            ".c-font-normal",
            "p",
            "div",
            "span",
            ".text",
            ".content",
            "[class*='text']",
            "[class*='content']",
            "[class*='summary']",
            "[class*='excerpt']",
            ".c-abstract-new",
            ".c-abstract-content",
            "div.c-gap-bottom",
            "div.c-span18",
        ],
        "fallback_abstract": False,
    },
    "bing": {
        "url": "https://www.bing.com/search?q={topic}&count={max_results}",
        "result_selectors": [
            "li.b_algo",
            "div.b_algo",
            "li[class*='algo']",
            ".b_searchResult",
            "[class*='result']",
            ".b_ans",
            ".b_algoheader",
            "li.b_ad",
            ".b_entityTP",
            ".b_rich",
            "[data-bm]",
            ".b_caption",
            "[class*='search']",
            "[class*='item']",
            "article",
            "section",
            "div.b_pag",
            ".b_algoSlug",
            ".b_vList li",
            ".b_resultCard",
            ".b_focusList",
            ".b_answer",
        ],
        "title_selectors": [
            "h2",
            "h3",
            "h2 a",
            "h3 a",
            ".b_title",
            "[class*='title']",
            "h2.b_topTitle",
            ".b_algo h2",
            ".b_entityTitle",
            "a h2",
            ".b_adlabel + h2",
            ".b_promoteText h2",
            "h1",
            "h4",
            "h5",
            "h6",
            "a[href]",
            ".link",
            ".url",
            ".b_title a",
            ".b_caption h2",
            "[data-title]",
            ".b_focusTitle",
        ],
        "abstract_selectors": [
            "p.b_lineclamp4",
            "div.b_caption",
            ".b_snippet",
            "[class*='caption']",
            "[class*='snippet']",
            ".b_paractl",
            ".b_dList",
            ".b_factrow",
            ".b_rich .b_caption",
            ".b_entitySubTypes",
            "p",
            "div",
            "span",
            ".text",
            ".content",
            "[class*='text']",
            "[class*='content']",
            "[class*='summary']",
            "[class*='excerpt']",
            ".b_vPanel",
            ".b_algoSlug",
            ".b_attribution",
        ],
        "fallback_abstract": False,
    },
    "360": {
        "url": "https://www.so.com/s?q={topic}&pn=1&rn={max_results}",
        "result_selectors": [
            "li.res-list",
            "div.result",
            "li[class*='res']",
            ".res-item",
            "[class*='result']",
            ".res",
            "li.res-top",
            ".res-gap-right",
            "[data-res]",
            ".result-item",
            ".res-rich",
            ".res-video",
            "[class*='search']",
            "[class*='item']",
            "article",
            "section",
            ".res-news",
            ".res-article",
            ".res-block",
            "div.g",
            ".res-container",
        ],
        "title_selectors": [
            "h3.res-title",
            "h3",
            "h3 a",
            ".res-title",
            "[class*='title']",
            "a[class*='title']",
            ".res-title a",
            "h4.res-title",
            ".title",
            ".res-meta .title",
            ".res-rich-title",
            "h1",
            "h2",
            "h4",
            "h5",
            "h6",
            "a[href]",
            ".link",
            ".url",
            ".res-news-title",
            ".res-block-title",
        ],
        "abstract_selectors": [
            "p.res-desc",
            "div.res-desc",
            ".res-summary",
            "[class*='desc']",
            "[class*='summary']",
            ".res-rich-desc",
            ".res-meta",
            ".res-info",
            ".res-rich .res-desc",
            ".res-gap-right p",
            "p",
            "div",
            "span",
            ".text",
            ".content",
            "[class*='text']",
            "[class*='content']",
            "[class*='summary']",
            "[class*='excerpt']",
            ".res-news-desc",
            ".res-block-desc",
        ],
        "fallback_abstract": False,
    },
    "sogou": {
        "url": "https://www.sogou.com/web?query={topic}",
        "redirect_pattern": "/link?url=",
        "result_selectors": [
            "div.vrwrap",
            "div.results",
            "div.result",
            "[class*='vrwrap']",
            "[class*='result']",
            ".rb",
            ".vrwrap-new",
            ".results-wrapper",
            "[data-md5]",
            ".result-item",
            ".vrwrap-content",
            ".sogou-results",
            "[class*='search']",
            "[class*='item']",
            "article",
            "section",
            ".results-div",
            ".vrwrap-item",
            "div.results > div",
            ".result-wrap",
        ],
        "title_selectors": [
            "h3.vr-title",
            "h3.vrTitle",
            "a.title",
            "h3",
            "a",
            "[class*='title']",
            "[class*='vr-title']",
            "[class*='vrTitle']",
            ".vr-title a",
            ".vrTitle a",
            "h4.vr-title",
            "h4.vrTitle",
            ".result-title",
            ".vrwrap h3",
            ".rb h3",
            ".title-link",
            "h1",
            "h2",
            "h4",
            "h5",
            "h6",
            "a[href]",
            ".link",
            ".url",
            ".vr-title",
        ],
        "abstract_selectors": [
            "div.str-info",
            "div.str_info",
            "p.str-info",
            "p.str_info",
            "div.ft",
            "[class*='str-info']",
            "[class*='str_info']",
            "[class*='abstract']",
            "[class*='desc']",
            ".rb .ft",
            ".vrwrap .ft",
            ".result-desc",
            ".content-info",
            "p",
            "div",
            "span",
            ".text",
            ".content",
            "[class*='text']",
            "[class*='content']",
            "[class*='summary']",
            "[class*='excerpt']",
            ".vr-desc",
        ],
        "fallback_abstract": True,
    },
}


# 搜索引擎特定函数
def template_baidu_specific(topic, max_results=10):
    return _search_template(topic, max_results, ENGINE_CONFIGS["baidu"])


def template_bing_specific(topic, max_results=10):
    return _search_template(topic, max_results, ENGINE_CONFIGS["bing"])


def template_360_specific(topic, max_results=10):
    return _search_template(topic, max_results, ENGINE_CONFIGS["360"])


def template_sougou_specific(topic, max_results=10):
    return _search_template(topic, max_results, ENGINE_CONFIGS["sogou"])
