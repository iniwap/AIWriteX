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


class SearchEngine(Enum):
    BAIDU = "baidu"
    BING = "bing"
    SO_360 = "360"
    SOUGOU = "sougou"
    COMBINED = "combined"


def search_web(topic, max_results=10, module_type: SearchEngine = SearchEngine.COMBINED):
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
                if validate_search_result(search_result):
                    return search_result
            except Exception as e:  # noqa 841
                continue

        # 所有搜索引擎都失败，返回 None
        return None

    elif module_type == SearchEngine.BAIDU:
        result = template_baidu_specific(topic, max_results)
        return result if validate_search_result(result) else None
    elif module_type == SearchEngine.BING:
        result = template_bing_specific(topic, max_results)
        return result if validate_search_result(result) else None
    elif module_type == SearchEngine.SO_360:
        result = template_360_specific(topic, max_results)
        return result if validate_search_result(result) else None
    elif module_type == SearchEngine.SOUGOU:
        result = template_sougou_specific(topic, max_results)
        return result if validate_search_result(result) else None
    else:
        return None


def validate_search_result(result, search_type="local"):
    """验证搜索结果质量，确保至少一条结果满足指定搜索类型的完整性条件"""
    # 验证输入是否为有效字典且 success 为 True
    if not isinstance(result, dict) or not result.get("success", False):
        return False

    # 验证 results 是否为非空列表
    results = result.get("results", [])
    if not results:
        return False

    # 定义各搜索类型的完整性规则
    validation_rules = {
        "local": ["title", "url", "abstract", "pub_time"],
        "ai_guided": ["title", "url", "abstract"],
        "ai_free": ["title", "abstract"],
    }

    # 获取对应搜索类型的规则，默认为 local
    required_fields = validation_rules.get(search_type, validation_rules["local"])

    # 检查是否存在至少一条结果，所有指定字段均非空
    for item in results:
        if all(item.get(field) and str(item.get(field)).strip() for field in required_fields):
            return True

    return False


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


def extract_page_content(url, headers):
    """从URL提取页面内容和发布时间，增强时间提取逻辑"""
    try:
        time.sleep(1)  # 请求间隔
        page_response = requests.get(url, headers=headers, timeout=10)

        # 编码处理
        if page_response.encoding and page_response.encoding.lower() in ["iso-8859-1", "ascii"]:
            encodings_to_try = ["utf-8", "gbk", "gb2312", "big5"]
            content = None
            for encoding in encodings_to_try:
                try:
                    content = page_response.content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            if content is None:
                content = page_response.content.decode("utf-8", errors="ignore")
        else:
            content = page_response.text

        page_soup = BeautifulSoup(content, "html.parser")

        pub_time = None

        # 1. 优先尝试常见的meta标签
        meta_selectors = [
            "meta[property='article:published_time']",
            "meta[itemprop='datePublished']",
            "meta[name='publishdate']",
            "meta[name='pubdate']",
            "meta[name='original-publish-date']",
            "meta[name='weibo:article:create_at']",  # 微博文章创建时间
            "meta[name='baidu_ssp:publishdate']",  # 百度SSP发布时间
        ]
        for selector in meta_selectors:
            meta_tag = page_soup.select_one(selector)
            if meta_tag:
                pub_time = meta_tag.get("content")
                if pub_time:
                    break

        # 2. 尝试 <time> 标签
        if not pub_time:
            time_tag = page_soup.select_one("time")
            if time_tag:
                pub_time = time_tag.get("datetime") or clean_text(time_tag.get_text())

        # 3. 尝试其他常见日期/时间相关的 HTML 元素和类名
        if not pub_time:
            # 扩展查找范围，增加常见的日期/时间类名和ID
            date_elements_selectors = [
                "[class*='date']",
                "[class*='time']",
                "[class*='publish']",
                "[class*='post-on']",
                "[class*='meta']",
                "[id*='date']",
                "[id*='time']",
                ".byline",
                ".info",
                ".article-info",
                ".source",
                ".entry-date",
                ".post-date",
                ".col-right",  # 某些网站如新浪可能把时间放在这里面
                "span.source-time",  # 常见于新闻网站
                "div.date",
                "div.time",
                "p.date",
                "p.time",
                ".article-meta",  # 文章元信息
            ]
            for selector in date_elements_selectors:
                date_elements = page_soup.select(selector)
                for elem in date_elements:
                    text = clean_text(elem.get_text())
                    # 更多日期格式的正则表达式
                    # 匹配 YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD
                    # 匹配 YYYY年MM月DD日
                    # 匹配 MM-DD-YYYY, MM/DD/YYYY, MM.DD.YYYY
                    # 可选包含时间 HH:MM:SS
                    date_patterns = [
                        r"\d{4}[-/年\.]\d{1,2}[-/月\.]\d{1,2}(?:日)?(?:\s+\d{1,2}:\d{1,2}(?::\d{1,2})?)?",  # noqa 501
                        r"(\d{1,2}[-/月\.]\d{1,2}[-/年\.]\d{4}(?:\s+\d{1,2}:\d{1,2}(?::\d{1,2})?)?)",
                        r"(\d{4})年(\d{1,2})月(\d{1,2})日(?:(\s+\d{1,2}:\d{1,2}(?::\d{1,2})?)?)",
                        r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})",  # 简化日期 MM/DD/YY or MM/DD/YYYY
                        r"(?:发表于|更新时间|发布时间|创建时间|Posted on|Published on|Date)[:\s]*(\d{4}[-/年\.]\d{1,2}[-/月\.]\d{1,2}(?:日)?(?:\s+\d{1,2}:\d{1,2}(?::\d{1,2})?)?)",  # noqa 501
                    ]
                    for pattern in date_patterns:
                        match = re.search(pattern, text)
                        if match:
                            # 如果正则表达式有捕获组，取第一个捕获组；否则取整个匹配内容
                            pub_time = match.group(1) if len(match.groups()) > 0 else match.group(0)
                            if pub_time:  # 确保提取到的时间字符串有效
                                break
                    if pub_time:
                        break
                if pub_time:
                    break

        # 4. 最后，在整个页面文本中查找日期模式（兜底方案）
        if not pub_time and content:
            # 扩展日期匹配模式，包括中文日期和各种分隔符
            date_patterns_in_content = [
                r"\d{4}[-/年\.]\d{1,2}[-/月\.]\d{1,2}(?:日)?(?:\s+\d{1,2}:\d{1,2}(?::\d{1,2})?)?",
                r"(?:发表于|更新时间|发布时间|创建时间|Posted on|Published on|Date)[:\s]*(\d{4}[-/年\.]\d{1,2}[-/月\.]\d{1,2}(?:日)?(?:\s+\d{1,2}:\d{1,2}(?::\d{1,2})?)?)",  # noqa 501
                r"(\d{1,2}[-/月\.]\d{1,2}[-/年\.]\d{4}(?:\s+\d{1,2}:\d{1,2}(?::\d{1,2})?)?)",
            ]
            for pattern in date_patterns_in_content:
                match = re.search(pattern, content)
                if match:
                    pub_time = match.group(1) if len(match.groups()) > 0 else match.group(0)
                    if pub_time:  # 确保提取到的时间字符串有效
                        break

        # 清理提取到的时间字符串
        if pub_time:
            pub_time = clean_text(pub_time)

        return page_soup, pub_time, content
    except Exception as e:  # noqa 841
        return None, None, None


def enhance_abstract(abstract, page_soup):
    """
    增强摘要内容。
    如果原始摘要过短，尝试从页面内容中提取前几段作为补充。
    """
    # 定义一个最小摘要长度，例如50个字符，如果摘要小于这个长度则尝试增强
    MIN_ABSTRACT_LENGTH = 50

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
            # 尝试凑够200字符，考虑到原始摘要可能已经占据一部分长度
            if sum(len(part) for part in content_parts) >= (200 - len(abstract.strip())):
                break

        if content_parts:
            # 将提取到的内容拼接起来，并限制总长度
            # 将原始摘要放在前面，然后追加增强内容
            enhanced_text = abstract.strip() + " " + " ".join(content_parts)
            return enhanced_text[:200].strip()  # 限制总长度为200字符，并移除首尾空白

    return abstract  # 如果不满足增强条件，返回原始摘要


def sort_and_filter_results(results):
    if not results:
        return results

    recent_results = [result for result in results if is_within_days(result.get("pub_time"), 7)]
    recent_results.sort(key=lambda x: parse_date_to_timestamp(x.get("pub_time", "")), reverse=True)

    return recent_results


def search_template(topic, max_results, engine_config):
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
    return search_template(topic, max_results, ENGINE_CONFIGS["baidu"])


def template_bing_specific(topic, max_results=10):
    return search_template(topic, max_results, ENGINE_CONFIGS["bing"])


def template_360_specific(topic, max_results=10):
    return search_template(topic, max_results, ENGINE_CONFIGS["360"])


def template_sougou_specific(topic, max_results=10):
    return search_template(topic, max_results, ENGINE_CONFIGS["sogou"])
