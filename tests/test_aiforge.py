import os
import sys


# 获取当前文件（b.py）的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 找到项目根目录（即 A 和 B 的父目录）
project_root = os.path.dirname(current_dir)
# 将根目录添加到 Python 搜索路径
sys.path.append(project_root)

from src.ai_write_x.aiforge.task_manager import should_use_detailed_prompt

# 简单指令示例
simple_instructions = ["今天有哪些新闻", "帮我搜索一下天气", "查询股票价格", "获取最新资讯"]

# 详细指令示例
detailed_instructions = [
    "请生成一个搜索函数，使用BeautifulSoup解析HTML，返回JSON格式",
    "按优先级依次尝试百度、Bing搜索引擎，提取meta标签中的发布时间",
    "严格遵守以下数据格式：{'results': [...], 'success': True}",
    "使用concurrent.futures.ThreadPoolExecutor并行处理，过滤掉验证页面",
]

for instruction in simple_instructions:
    print(f"'{instruction}' -> {should_use_detailed_prompt(instruction)}")  # False

for instruction in detailed_instructions:
    print(f"'{instruction}' -> {should_use_detailed_prompt(instruction)}")  # True


import time
import urllib.parse
import requests
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta


def search_web(topic, max_results=10):
    result = {
        "timestamp": time.time(),
        "topic": topic,
        "results": [],
        "success": False,
        "error": None,
    }

    search_engines = [
        {
            "name": "百度",
            "url": f"https://www.baidu.com/s?wd={urllib.parse.quote(topic)}&rn={max_results}",
            "result_container": ["div.result", "div.c-container", "div[class*='result']"],
            "title": ["h3", "h3 a", ".t", ".c-title"],
            "abstract": ["div.c-abstract", ".c-span9", "[class*='abstract']"],
        },
        {
            "name": "Bing",
            "url": f"https://www.bing.com/search?q={urllib.parse.quote(topic)}&count={max_results}",
            "result_container": ["li.b_algo", "div.b_algo", "li[class*='algo']"],
            "title": ["h2", "h3", "h2 a", ".b_title"],
            "abstract": ["p.b_lineclamp4", "div.b_caption", ".b_snippet"],
        },
        {
            "name": "360",
            "url": f"https://www.so.com/s?q={urllib.parse.quote(topic)}&rn={max_results}",
            "result_container": ["li.res-list", "div.result", "li[class*='res']"],
            "title": ["h3.res-title", "h3", ".res-title"],
            "abstract": ["p.res-desc", "div.res-desc", ".res-summary"],
        },
        {
            "name": "搜狗",
            "url": f"https://www.sogou.com/web?query={urllib.parse.quote(topic)}",
            "result_container": ["div.vrwrap", "div.results", "div.result"],
            "title": ["h3.vr-title", "h3.vrTitle", "a.title", "h3"],
            "abstract": ["div.str-info", "div.str_info", "p.str-info"],
        },
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    def fetch_url(url):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            return response.text
        except Exception as e:
            return None

    def parse_date(text):
        # 标准格式
        date_patterns = [
            r"\d{4}-\d{2}-\d{2}",  # YYYY-MM-DD
            r"\d{4}年\d{1,2}月\d{1,2}日",  # 中文日期
            r"\d{1,2}天前",  # 几天前
            r"\d{1,2}小时前",  # 几小时前
            r"昨天",  # 昨天
            r"今天",  # 今天
            r"yesterday",  # 英文昨天
            r"(\d+) days? ago",  # 英文几天前
            r"(\d+) hours? ago",  # 英文几小时前
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None

    def extract_pub_time(html):
        soup = BeautifulSoup(html, "html.parser")

        # 检查meta标签
        meta_tags = [
            {"property": "article:published_time"},
            {"property": "datePublished"},
            {"name": "pubdate"},
            {"name": "publishdate"},
            {"itemprop": "datePublished"},
        ]

        for tag in meta_tags:
            meta = soup.find("meta", tag)
            if meta and meta.get("content"):
                return meta["content"]

        # 检查time标签
        time_tag = soup.find("time")
        if time_tag and (time_tag.get("datetime") or time_tag.text.strip()):
            return time_tag.get("datetime") or time_tag.text.strip()

        # 检查常见日期class
        date_classes = ["date", "time", "pub-date", "publish-date", "timestamp"]
        for cls in date_classes:
            element = soup.find(class_=cls)
            if element and element.text.strip():
                return element.text.strip()

        # 尝试从页面文本中提取
        body_text = soup.get_text()
        date = parse_date(body_text)
        if date:
            return date

        return None

    def process_search_engine(engine):
        html = fetch_url(engine["url"])
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")
        results = []

        for container_selector in engine["result_container"]:
            containers = soup.select(container_selector)
            if containers:
                break

        if not containers:
            return None

        for container in containers[:max_results]:
            title_element = None
            for title_selector in engine["title"]:
                title_element = container.select_one(title_selector)
                if title_element:
                    break

            abstract_element = None
            for abstract_selector in engine["abstract"]:
                abstract_element = container.select_one(abstract_selector)
                if abstract_element:
                    break

            if not title_element or not abstract_element:
                continue

            title = title_element.get_text().strip()
            url = (
                title_element.get("href")
                if title_element.name == "a"
                else title_element.find("a").get("href") if title_element.find("a") else None
            )
            if not url:
                continue

            abstract = abstract_element.get_text().replace("\n", "").replace("\r", "").strip()
            abstract = " ".join(abstract.split())

            # 获取详细页面内容
            page_html = fetch_url(url)
            if page_html:
                pub_time = extract_pub_time(page_html)

                # 检查详细页面中的摘要是否更长
                page_soup = BeautifulSoup(page_html, "html.parser")
                article_text = page_soup.get_text()
                article_text = " ".join(article_text.split())

                if len(article_text) > len(abstract):
                    abstract = article_text
            else:
                pub_time = None

            if len(abstract) < 150 or not pub_time:
                continue

            results.append({"title": title, "url": url, "abstract": abstract, "pub_time": pub_time})

            # 检查停止条件
            if len(abstract) >= 150 and pub_time:
                return results

        return results

    # 按优先级依次尝试搜索引擎
    for engine in search_engines:
        results = process_search_engine(engine)
        if results and len(results) > 0:
            result["results"] = results
            result["success"] = True
            return result

    return result


__result__ = search_web("当妈妈说把头发梳起来大大方方的", 10)
print(__result__)
