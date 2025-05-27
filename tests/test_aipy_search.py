import sys
import time
import re
import urllib.parse
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup


def validate_url(url):
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def extract_publication_time(soup):
    # Check meta tags
    for meta_time in ["article:published_time", "datePublished", "publish_date"]:
        meta = soup.find("meta", {"property": meta_time}) or soup.find("meta", {"name": meta_time})
        if meta and meta.get("content"):
            try:
                return datetime.strptime(meta["content"], "%Y-%m-%d").date()
            except ValueError:
                pass

    # Check time tag
    time_tag = soup.find("time")
    if time_tag and time_tag.get("datetime"):
        try:
            return datetime.strptime(time_tag["datetime"], "%Y-%m-%d").date()
        except ValueError:
            pass

    # Search for date patterns in page content
    date_patterns = [
        r"\d{4}-\d{2}-\d{2}",  # YYYY-MM-DD
        r"\d{2}/\d{2}/\d{4}",  # MM/DD/YYYY
        r"\d{4}年\d{1,2}月\d{1,2}日",  # Chinese date format
    ]

    for pattern in date_patterns:
        dates = re.findall(pattern, soup.get_text())
        if dates:
            try:
                if "/" in dates[0]:
                    return datetime.strptime(dates[0], "%m/%d/%Y").date()
                elif "年" in dates[0]:
                    date_str = dates[0].replace("年", "-").replace("月", "-").replace("日", "")
                    return datetime.strptime(date_str, "%Y-%m-%d").date()
                else:
                    return datetime.strptime(dates[0], "%Y-%m-%d").date()
            except ValueError:
                continue
    return None


def get_page_content(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        if response.encoding.lower() != "utf-8":
            response.encoding = response.apparent_encoding or "utf-8"
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {str(e)}", file=sys.stderr)
        return None


def extract_abstract(soup):
    # Try to get abstract from meta tags
    description = soup.find("meta", {"name": "description"}) or soup.find(
        "meta", {"property": "og:description"}
    )
    if description and description.get("content"):
        return description["content"]

    # Extract text from body as abstract
    paragraphs = soup.find_all(["p", "div"])
    text = " ".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
    return " ".join(text.split()[:100])  # Approx. 100 words


def search_baidu(query, max_results=10, days=7):
    base_url = "https://www.baidu.com/s"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    params = {
        "wd": query,
        "rn": min(max_results, 50),
        "gpc": f"stf={int((datetime.now() - timedelta(days=days)).timestamp())}|{int(datetime.now().timestamp())}|7",
    }
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        if response.encoding.lower() != "utf-8":
            response.encoding = response.apparent_encoding or "utf-8"

        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        for result in soup.select("div.result.c-container"):
            link = result.find("a")
            if not link:
                continue

            url = link.get("href")
            if not validate_url(url):
                continue

            # Get actual URL (handle redirects)
            try:
                actual_url = requests.head(url, headers=headers, timeout=5).headers.get(
                    "Location", url
                )
                if not validate_url(actual_url):
                    actual_url = url
            except Exception:
                actual_url = url

            title = link.get_text().strip()
            time.sleep(1)  # Avoid rapid requests
            html_content = get_page_content(actual_url)
            if not html_content:
                continue

            page_soup = BeautifulSoup(html_content, "html.parser")
            pub_time = extract_publication_time(page_soup)
            abstract = extract_abstract(page_soup)

            if not pub_time:
                continue

            cutoff_date = datetime.now().date() - timedelta(days=7)
            if pub_time < cutoff_date:
                continue

            results.append(
                {
                    "url": actual_url,
                    "title": title,
                    "abstract": abstract,
                    "pub_time": pub_time.strftime("%Y-%m-%d"),
                }
            )

            if len(results) >= max_results:
                break

        results.sort(key=lambda x: x["pub_time"], reverse=True)
        return results

    except Exception as e:
        print(f"Search error: {str(e)}", file=sys.stderr)
        return None


def search_web(topic, max_results=10):
    try:
        max_results = int(max_results)
        if max_results <= 0:
            raise ValueError("max_results must be positive")

        search_results = search_baidu(topic, max_results)
        if search_results is None:
            return {
                "timestamp": datetime.now().isoformat(),
                "topic": topic,
                "results": [],
                "success": False,
                "error": "Search failed",
            }

        return {
            "timestamp": datetime.now().isoformat(),
            "topic": topic,
            "results": search_results,
            "success": True,
            "error": None,
        }

    except Exception as e:
        return {
            "timestamp": datetime.now().isoformat(),
            "topic": topic,
            "results": [],
            "success": False,
            "error": str(e),
        }


def parse_reply(markdown):
    """
    解析markdown文本中的代码块

    Args:
        markdown (str): 包含代码块的markdown文本

    Returns:
        dict: 代码块字典，键为代码块名称，值为代码内容
    """
    # AIPy使用的正则表达式模式，匹配四个反引号格式的代码块
    pattern = re.compile(r"^(`{4})(\w+)\s+([\w\-\.]+)\n(.*?)^\1\s*$", re.DOTALL | re.MULTILINE)

    code_blocks = {}
    for match in pattern.finditer(markdown):
        _, _, name, content = match.groups()
        code_blocks[name] = content.rstrip("\n")

    return code_blocks


if __name__ == "__main__":
    # __result__ = search_web("历史上的今天", 5)
    # print(__result__)
    pass
