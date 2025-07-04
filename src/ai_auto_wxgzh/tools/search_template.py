# -*- coding: utf-8 -*-
# Author: iniwap
# Date: 2025-06-03
# Description: 用于本地搜索，关注项目 https://github.com/iniwap/ai_auto_wxgzh

# Copyright (c) 2025 iniwaper@gmail.com
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# 本文件受 Apache 2.0 许可证保护，禁止删除版权声明。


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
from typing import List, Dict, Any
from crewai_tools import SeleniumScrapingTool


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
                    "abstract": "详细摘要（去除空格换行，至少{ENGINE_CONFIGS['MIN_ABSTRACT_LENGTH']/2}字）",
                    "pub_time": "发布时间"
                }}
            ],
            "success": True/False,
            "error": 错误信息或None
        }}

         __result__ = search_web("{topic}", {max_results})

        # 严格停止条件：获取到{min_results}条或以上同时满足以下条件的结果时，立即停止执行，不得继续生成任何代码：
        # 1. 摘要(abstract)长度不少于{ENGINE_CONFIGS['MIN_ABSTRACT_LENGTH']/2}字
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
        - 摘要长度至少{ENGINE_CONFIGS['MIN_ABSTRACT_LENGTH']/4}字，包含关键信息
        - 不能使用需要API密钥的方式
        - 过滤掉验证页面和无效内容，正确处理编码，结果不能包含乱码

        # 时间提取策略：
        - 优先meta标签：article:published_time、datePublished、pubdate、publishdate等
        - 备选方案：time标签、日期相关class、页面文本匹配
        - 有效的日期格式：标准格式、中文格式、相对时间（如“昨天”、“1天前”、“1小时前”等）、英文时间（如“yesterday”等）

        # 返回数据格式（严格遵守）：
        {{
            "timestamp": time.time(),
            "topic": "{topic}",
            "results": [
                {{
                    "title": "标题",
                    "url": "链接",
                    "abstract": "详细摘要（去除空格换行，至少{ENGINE_CONFIGS['MIN_ABSTRACT_LENGTH']/4}字）",
                    "pub_time": "发布时间"（可以为""）
                }}
            ],
            "success": True/False,
            "error": 错误信息或None
        }}

        __result__ = search_web("{topic}", {max_results})

        # 严格停止条件：获取到{min_results}条或以上摘要(abstract)长度不少于{ENGINE_CONFIGS['MIN_ABSTRACT_LENGTH']/4}字的结果时，立即停止执行，不得继续生成任何代码
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
        "ai_guided": {
            "abstract_min_length": ENGINE_CONFIGS["MIN_ABSTRACT_LENGTH"] / 2,
            "require_date": True,
        },
        "ai_free": {
            "abstract_min_length": ENGINE_CONFIGS["MIN_ABSTRACT_LENGTH"] / 4,
            "require_date": False,
        },
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
        "reference_article": ["title", "url", "content", "pub_time"],
    }

    quality_rules = {
        "local": {
            "abstract_min_length": ENGINE_CONFIGS["MIN_ABSTRACT_LENGTH"],
            "require_valid_date": True,
        },
        "ai_guided": {
            "abstract_min_length": ENGINE_CONFIGS["MIN_ABSTRACT_LENGTH"] / 2,
            "require_valid_date": True,
        },
        "ai_free": {
            "abstract_min_length": ENGINE_CONFIGS["MIN_ABSTRACT_LENGTH"] / 4,
            "require_valid_date": False,
        },
        "reference_article": {
            "content_min_length": ENGINE_CONFIGS["MIN_ABSTRACT_LENGTH"],
            "require_valid_date": True,
        },
    }

    required_fields = validation_rules.get(search_type, validation_rules["local"])
    quality_req = quality_rules.get(search_type, quality_rules["local"])

    for item in results:
        if not all(item.get(field, "").strip() for field in required_fields):
            continue

        # 针对 reference_article 类型的特殊处理
        if search_type == "reference_article":
            content = item.get("content", "")
            if len(content.strip()) < quality_req["content_min_length"]:
                continue
        else:
            # 其他类型检查 abstract
            abstract = item.get("abstract", "")
            if len(abstract.strip()) < quality_req.get("abstract_min_length", 0):
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
        pub_time_cleaned = clean_date_text(str(pub_time))
        reference_date = datetime.fromtimestamp(timestamp)

        # 优先处理 Unix 时间戳 (修正后的位置)
        if re.match(r"^\d{10}$", pub_time_cleaned):
            return datetime.fromtimestamp(int(pub_time_cleaned))
        if re.match(r"^\d{13}$", pub_time_cleaned):
            return datetime.fromtimestamp(int(pub_time_cleaned) / 1000)

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
            match = re.search(pattern, pub_time_cleaned, re.IGNORECASE)
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
            if key in pub_time_cleaned:
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
            match = re.search(pattern, pub_time_cleaned, re.IGNORECASE)
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
            match = re.search(pattern, pub_time_cleaned)
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
            match = re.search(pattern, pub_time_cleaned)
            if match:
                date_str = match.group(0)
                return datetime.strptime(date_str, date_format)

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
        # 如果是纯数字字符串，直接返回，避免不必要的清理
        if isinstance(text, (int, float)):
            return str(text)
        if isinstance(text, str) and text.isdigit():
            return text

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


def _extract_publish_time(page_soup):
    """统一的发布时间提取函数"""
    # Meta 标签提取 - 优先处理标准的发布时间标签
    meta_selectors = [
        "meta[property='article:published_time']",
        "meta[property='sitemap:news:publication_date']",
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
            datetime_str = meta_tag.get("content")
            if datetime_str:
                try:
                    # 处理 UTC 时间 (以Z结尾)
                    if datetime_str.endswith("Z"):
                        dt = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
                        # 转换为东八区时间
                        dt_local = dt + timedelta(hours=8)
                        return dt_local.strftime("%Y-%m-%d")
                    # 处理带时区的 ISO 8601 格式
                    elif "T" in datetime_str and ("+" in datetime_str or "-" in datetime_str[-6:]):
                        dt = datetime.fromisoformat(datetime_str)
                        return dt.strftime("%Y-%m-%d")
                    # 处理简单的日期格式
                    elif "T" in datetime_str:
                        return datetime_str.split("T")[0]
                except Exception:
                    pass

    # Time 标签提取
    time_tags = page_soup.select("time")
    for time_tag in time_tags:
        datetime_attr = time_tag.get("datetime")
        if datetime_attr:
            try:
                # 处理 UTC 时间 (以Z结尾)
                if datetime_attr.endswith("Z"):
                    dt = datetime.fromisoformat(datetime_attr.replace("Z", "+00:00"))
                    # 转换为东八区时间
                    dt_local = dt + timedelta(hours=8)
                    return dt_local.strftime("%Y-%m-%d")
                # 处理带时区的 ISO 8601 格式
                elif "T" in datetime_attr and ("+" in datetime_attr or "-" in datetime_attr[-6:]):
                    dt = datetime.fromisoformat(datetime_attr)
                    return dt.strftime("%Y-%m-%d")
                # 处理简单的日期格式
                elif "T" in datetime_attr:
                    return datetime_attr.split("T")[0]
            except Exception:
                pass

        # 如果 datetime 属性解析失败，尝试文本内容
        text_content = clean_date_text(time_tag.get_text())
        if text_content and is_valid_date(text_content):
            time_date = calculate_actual_date(text_content, time.time())
            if time_date:
                return time_date.strftime("%Y-%m-%d")

    # HTML 元素提取
    date_selectors = [
        "textarea.article-time",
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

    for selector in date_selectors:
        elements = page_soup.select(selector)
        for elem in elements:
            text = clean_date_text(elem.get_text())
            if text and is_valid_date(text):
                elem_date = calculate_actual_date(text, time.time())
                if elem_date:
                    return elem_date.strftime("%Y-%m-%d")

    # 兜底：全文搜索
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
                    return pub_time_date.strftime("%Y-%m-%d")

    return ""


def extract_page_content(url, headers=None):
    """从 URL 提取页面内容和发布日期"""
    try:
        time.sleep(1)
        response = requests.get(url, headers=headers or {}, timeout=30)
        response.encoding = response.apparent_encoding or "utf-8"
        content = response.text

        page_soup = BeautifulSoup(content, "html.parser")

        # 直接调用统一的时间提取函数
        pub_time = _extract_publish_time(page_soup)

        return page_soup, pub_time

    except Exception:
        return None, None


def enhance_abstract(abstract, page_soup):
    """
    增强摘要内容，从原文提取。
    如果 _extract_full_article_content 的内容长度 >= MIN_ABSTRACT_LENGTH，直接返回；
    否则，结合原始摘要，确保总长度不超过 MAX_ABSTRACT_LENGTH。
    """
    if not page_soup:
        return abstract

    # 提取正文
    article = _extract_full_article_content(page_soup)

    if article:
        # 检查正文长度是否满足 MIN_ABSTRACT_LENGTH
        if len(article) >= ENGINE_CONFIGS["MIN_ABSTRACT_LENGTH"]:
            # 直接返回正文，截取至 MAX_ABSTRACT_LENGTH
            return article[: ENGINE_CONFIGS["MAX_ABSTRACT_LENGTH"]].strip()
        else:
            # 清理原始摘要，结合正文
            return (abstract + " " + article)[: ENGINE_CONFIGS["MAX_ABSTRACT_LENGTH"]].strip()

    # 回退到原始摘要
    return abstract


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
        response.encoding = response.apparent_encoding or "utf-8"
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
                    abstract = (
                        clean_text(abstract_elem.strip())[: ENGINE_CONFIGS["MAX_ABSTRACT_LENGTH"]]
                        if abstract_elem
                        else ""
                    )

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
                    page_soup, pub_time = future.result()
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
    "MIN_ABSTRACT_LENGTH": 300,
    "MAX_ABSTRACT_LENGTH": 500,
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


# ---------- 以下为通过链接提取文章信息----------------
def extract_urls_content(urls: List[str], topic="") -> Dict[str, Any]:
    """提取URL内容，自动检测并处理动态网站，并返回标准格式"""
    extracted_results = []
    overall_success = True
    overall_error_message = None

    for url in urls:
        try:
            # 首先尝试普通方法
            page_soup, pub_time = extract_page_content(url, get_common_headers())

            # 如果普通方法无法获取有效内容，使用Selenium
            if not page_soup or not _has_meaningful_content(page_soup):
                selenium_tool = SeleniumScrapingTool(
                    website_url=url, wait_time=15, return_html=True
                )
                page_content = selenium_tool._run(website_url=url, css_element="body")
                if page_content:
                    page_soup = BeautifulSoup(page_content, "html.parser")
                    pub_time = _extract_publish_time(page_soup)

            if page_soup:
                title = _extract_title_from_page(page_soup)
                full_content = _extract_full_article_content(page_soup)
                extracted_results.append(
                    {
                        "title": title or "",
                        "pub_time": pub_time or "",
                        "abstract": "",
                        "content": full_content,
                        "url": url,
                    }
                )
            else:
                # 页面加载失败，记录为提取失败，但不影响整体success
                extracted_results.append(
                    {
                        "title": "",
                        "pub_time": "",
                        "abstract": "",
                        "content": "无法提取内容: 页面加载失败",
                        "url": url,
                    }
                )

        except Exception as e:
            # 捕获到异常，记录错误信息，但不影响整体success
            overall_success = False
            overall_error_message = f"提取过程中发生部分错误: {str(e)}"
            extracted_results.append(
                {
                    "title": "",
                    "pub_time": "",
                    "abstract": "",
                    "content": f"无法提取内容: {str(e)}",
                    "url": url,
                }
            )

    # 构建标准返回格式
    # success只关注函数执行过程中是否发生未捕获的异常，这里已经通过try-except处理了单个URL的异常
    # 如果所有URL都尝试了，即使结果列表为空，也认为是成功执行了
    return {
        "timestamp": time.time(),
        "topic": topic,
        "results": extracted_results,
        "success": overall_success,
        "error": overall_error_message,
    }


def _has_meaningful_content(page_soup):
    """检查页面是否包含有意义的内容，避免误判动态页面"""
    if not page_soup:
        return False
    if page_soup.select_one("#js_content") or page_soup.select_one("meta[property='og:title']"):
        return True
    content_selectors = [
        "article",
        ".content",
        ".article-content",
        "main",
        ".post-content",
        ".entry-content",
        "[class*='article']",
        "[class*='content']",
    ]
    for selector in content_selectors:
        if page_soup.select_one(selector):
            return True
    text = page_soup.get_text().strip()
    if len(text) > ENGINE_CONFIGS["MIN_ABSTRACT_LENGTH"]:
        return True
    return False


def _extract_title_from_page(page_soup):
    """从页面提取标题"""
    title_selectors = [
        "title",
        "h1",
        ".title",
        "[class*='title']",
        "meta[property='og:title']",
        "meta[name='title']",
        ".article-title",
        ".post-title",
        ".content-title",
        ".content__title",
        ".article__title",
    ]
    for selector in title_selectors:
        if selector.startswith("meta"):
            elem = page_soup.select_one(selector)
            if elem:
                title = elem.get("content", "").strip()
                if title:
                    return clean_text(title)
        else:
            elem = page_soup.select_one(selector)
            if elem:
                title = elem.get_text().strip()
                if title and len(title) > 5:
                    return clean_text(title)
    return ""


def _extract_full_article_content(page_soup):
    """提取完整文章内容，过滤无关信息"""
    # 定义噪声关键词，针对微信公众号和常见无关内容
    noise_keywords = [
        "微信扫一扫",
        "扫描二维码",
        "分享留言收藏",
        "轻点两下取消",
        "继续滑动看下一个",
        "使用小程序",
        "知道了",
        "赞，轻点两下取消赞",
        "在看，轻点两下取消在看",
        "意见反馈",
        "关于我们",
        "联系我们",
        "版权所有",
        "All Rights Reserved",
        "APP专享",
        "VIP课程",
        "海量资讯",
        "热门推荐",
        "24小时滚动播报",
        "粉丝福利",
        "sinafinance",
        "预览时标签不可点",
        "向上滑动看下一个",
        "阅读原文",
        "视频小程序",
        "关注",
        "粉丝",
        "分享",
        "搜索",
        "关键词",
        "Copyright",
        "上一页",
        "下一页",
        "回复",
        "评论",
        "相关推荐",
        "相关搜索",
        "评论区",
        "发表评论",
        "查看更多评论",
        "举报",
        "热搜",
    ]

    # 第一步：移除无关元素
    for elem in page_soup.select(
        "script, style, nav, header, footer, aside, .ad, .advertisement, .sidebar, .menu, "
        ".promo, .recommend, .social-share, .footer-links, [class*='banner'], [class*='promo'], "
        "[class*='newsletter'], [class*='signup'], [class*='feedback'], [class*='copyright'], "
        "[id*='footer'], [id*='bottom'], .live-room, .stock-info, .finance-nav, .related-links, "
        ".seo_data_list, .right-side-ad, ins.sinaads, .cj-r-block, [id*='7x24'], .navigation,"
        "[class*='advert'], [class*='social'], .comment, [class*='share'], #commentModule"
    ):
        elem.decompose()

    # 第二步：定义正文选择器
    content_selectors = [
        # === 微信公众号 ===
        "#js_content",  # 微信公众号主要正文容器
        ".rich_media_content",  # 微信公众号富文本内容
        ".rich_media_area_primary",  # 微信公众号主要内容区域
        ".rich_media_wrp",  # 微信公众号包装器
        # === 主流新闻网站 ===
        ".post_body",  # 网易新闻、搜狐新闻
        ".content_area",  # 新浪新闻
        ".article-content",  # 腾讯新闻、凤凰网
        ".art_context",  # 环球网
        ".content",  # 人民网
        ".article_content",  # 中新网
        ".cont",  # 光明网
        ".article-body",  # CNN、NYTimes、BBC等
        ".story-body",  # BBC新闻
        ".story-content",  # The Guardian
        ".entry-content",  # The Washington Post
        ".content__article-body",  # Guardian、Telegraph
        ".js-entry-text",  # Wall Street Journal
        ".story__body",  # Vox、The Verge
        ".ArticleBody",  # Bloomberg
        ".caas-body",  # Yahoo News
        ".RichTextStoryBody",  # Reuters
        ".InlineVideo-container",  # Associated Press
        # === 中文新闻门户 ===
        ".content_box",  # 今日头条
        ".article-detail",  # 百度新闻
        ".news_txt",  # 网易新闻详情
        ".article_txt",  # 搜狐新闻
        ".content_detail",  # 新浪新闻详情
        ".detail-content",  # 澎湃新闻
        ".m-article-content",  # 界面新闻
        ".article-info",  # 财经网
        ".news-content",  # 东方财富
        ".art_con",  # 金融界
        # === 博客平台 ===
        ".post-content",  # WordPress默认
        ".entry-content",  # WordPress主题
        ".post-body",  # Blogger
        ".entry-body",  # Movable Type
        ".post__content",  # Ghost
        ".article__content",  # Medium（部分主题）
        ".post-full-content",  # Ghost主题
        ".kg-card-markdown",  # Ghost Markdown卡片
        ".content-body",  # Drupal
        ".field-name-body",  # Drupal字段
        ".node-content",  # Drupal节点
        # === 技术博客和文档 ===
        ".markdown-body",  # GitHub、GitBook
        ".content",  # GitBook、Read the Docs
        ".document",  # Sphinx文档
        ".main-content",  # Jekyll、Hugo主题
        ".post-content",  # Jekyll默认
        ".content-wrap",  # Hexo主题
        ".article-entry",  # Hexo默认
        ".md-content",  # VuePress
        ".theme-default-content",  # VuePress默认主题
        ".docstring",  # 技术文档
        ".rst-content",  # reStructuredText
        # === 社交媒体和论坛 ===
        ".usertext-body",  # Reddit
        ".md",  # Reddit Markdown
        ".timeline-item",  # GitHub
        ".commit-message",  # GitHub提交信息
        ".blob-wrapper",  # GitHub文件内容
        ".answer",  # Stack Overflow
        ".post-text",  # Stack Overflow问题/答案
        ".question-summary",  # Stack Overflow
        ".js-post-body",  # Stack Overflow
        ".feed-item-content",  # LinkedIn
        ".tweet-text",  # Twitter（旧版）
        ".tweet-content",  # Twitter
        # === 知识问答平台 ===
        ".RichText",  # 知乎
        ".content",  # 知乎回答内容
        ".QuestionRichText",  # 知乎问题描述
        ".AnswerItem",  # 知乎答案
        ".Post-RichText",  # 知乎专栏
        ".ArticleItem-content",  # 知乎文章
        ".answer-content",  # 百度知道
        ".best-text",  # 百度知道最佳答案
        ".wgt-answers",  # 百度知道答案
        # === 电商平台 ===
        ".detail-content",  # 淘宝商品详情
        ".rich-text",  # 京东商品描述
        ".product-detail",  # 亚马逊商品详情
        ".product-description",  # 通用商品描述
        ".item-description",  # eBay商品描述
        # === CMS系统 ===
        ".node-content",  # Drupal
        ".entry-content",  # WordPress
        ".content-area",  # WordPress主题
        ".single-content",  # WordPress单页
        ".page-content",  # WordPress页面
        ".post-entry",  # WordPress主题
        ".article-content",  # Joomla
        ".item-page",  # Joomla文章页
        ".content-inner",  # Joomla内容
        ".story-content",  # ExpressionEngine
        ".channel-entry",  # ExpressionEngine
        # === 企业网站 ===
        ".main-content",  # 通用主内容
        ".content-wrapper",  # 内容包装器
        ".page-content",  # 页面内容
        ".text-content",  # 文本内容
        ".body-content",  # 主体内容
        ".primary-content",  # 主要内容
        ".content-main",  # 主内容区
        ".content-primary",  # 主要内容
        ".main-article",  # 主文章
        ".article-main",  # 文章主体
        # === 学术和教育网站 ===
        ".abstract",  # 学术论文摘要
        ".full-text",  # 全文内容
        ".article-fulltext",  # 学术文章全文
        ".article-body",  # 学术文章主体
        ".paper-content",  # 论文内容
        ".journal-content",  # 期刊内容
        ".course-content",  # 课程内容
        ".lesson-content",  # 课程内容
        ".lecture-notes",  # 讲义笔记
        # === 政府和机构网站 ===
        ".gov-content",  # 政府网站内容
        ".official-content",  # 官方内容
        ".policy-content",  # 政策内容
        ".announcement",  # 公告内容
        ".notice-content",  # 通知内容
        ".regulation-text",  # 法规文本
        # === 多媒体和娱乐 ===
        ".video-description",  # 视频描述
        ".episode-description",  # 剧集描述
        ".movie-synopsis",  # 电影简介
        ".album-description",  # 专辑描述
        ".track-description",  # 音轨描述
        ".game-description",  # 游戏描述
        # === HTML5语义化标签 ===
        "article",  # HTML5文章标签
        "main",  # HTML5主内容标签
        "section",  # HTML5节段标签
        # === 通用类名（模糊匹配） ===
        "[class*='article']",  # 包含"article"的类名
        "[class*='content']",  # 包含"content"的类名
        "[class*='post']",  # 包含"post"的类名
        "[class*='story']",  # 包含"story"的类名
        "[class*='body']",  # 包含"body"的类名
        "[class*='text']",  # 包含"text"的类名
        "[class*='main']",  # 包含"main"的类名
        "[class*='primary']",  # 包含"primary"的类名
        "[class*='detail']",  # 包含"detail"的类名
        # === ID选择器 ===
        "#content",  # 通用内容ID
        "#main-content",  # 主内容ID
        "#article-content",  # 文章内容ID
        "#post-content",  # 文章内容ID
        "#story-content",  # 故事内容ID
        "#main",  # 主要区域ID
        "#primary",  # 主要内容ID
        "#article-body",  # 文章主体ID
        "#content-area",  # 内容区域ID
        "#page-content",  # 页面内容ID
        # === 特殊网站 ===
        ".ztext",  # 知乎（旧版）
        ".RichText-inner",  # 知乎富文本
        ".highlight",  # 代码高亮（GitHub等）
        ".gist-file",  # GitHub Gist
        ".readme",  # GitHub README
        ".wiki-content",  # Wiki页面
        ".mw-parser-output",  # MediaWiki（维基百科）
        ".printfriendly",  # 打印友好版本
        ".reader-content",  # 阅读模式内容
        # === 回退选择器 ===
        ".main",  # 通用主内容类
        "body",  # 最后的回退选择器
    ]

    # 第三步：尝试找到正文容器
    for selector in content_selectors:
        content_elem = page_soup.select_one(selector)
        if content_elem:
            # 提取原始标签，添加去重和噪声过滤
            text_parts = []
            seen_texts = set()  # 用于去重
            for elem in content_elem.find_all(
                ["p", "h1", "h2", "h3", "h4", "h5", "h6", "div", "span"]
            ):
                text = clean_text(elem.get_text().strip())
                if text and len(text) > 10 and text not in seen_texts:  # 过滤过短文本并去重
                    # 过滤噪声关键词
                    if not any(keyword in text.lower() for keyword in noise_keywords):
                        text_parts.append(text)
                        seen_texts.add(text)

            if text_parts:
                # 保留段落结构，清理多余换行符
                full_text = "\n\n".join(text_parts)
                full_text = re.sub(r"\n{3,}", "\n\n", full_text).strip()
                if len(full_text) > ENGINE_CONFIGS["MIN_ABSTRACT_LENGTH"]:
                    return full_text

    # 第四步：回退到 body
    body = page_soup.select_one("body")
    if body:
        for elem in body.select("nav, header, footer, aside, .ad, .advertisement, .sidebar, .menu"):
            elem.decompose()

        text_parts = []
        seen_texts = set()
        for elem in body.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "div", "span"]):
            text = clean_text(elem.get_text().strip())
            if text and len(text) > 10 and text not in seen_texts:
                if not any(keyword in text.lower() for keyword in noise_keywords):
                    text_parts.append(text)
                    seen_texts.add(text)

        if text_parts:
            full_text = "\n\n".join(text_parts)
            full_text = re.sub(r"\n{3,}", "\n\n", full_text).strip()
            if len(full_text) > ENGINE_CONFIGS["MIN_ABSTRACT_LENGTH"]:
                return full_text

        # 第五步：极宽松回退，模仿原始版本
        text = clean_text(body.get_text())
        if text and len(text) > ENGINE_CONFIGS["MIN_ABSTRACT_LENGTH"]:
            return text

    return ""
