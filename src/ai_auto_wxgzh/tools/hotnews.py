import requests
from typing import Optional, List, Dict

from src.ai_auto_wxgzh.utils import log


def get_hotnews() -> Optional[List[Dict]]:
    """
    获取各大平台热点数据
    返回格式: {"success": true, "data": 数组数据}
    """
    api_url = "https://api.vvhan.com/api/hotlist/all"

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        data = response.json()
        if data.get("success") and isinstance(data.get("data"), list):
            return data["data"]

        return None

    except requests.exceptions.RequestException as e:
        log.print_log(f"请求异常: {str(e)}")
        return None
    except ValueError as e:
        log.print_log(f"JSON解析异常: {str(e)}")
        return None


def get_platform_news(platform, cnt=1):
    platform_news = []
    hotnews = get_hotnews()
    if hotnews:
        result = {}

        for pf in hotnews:
            result[pf["name"]] = [item["title"] for item in pf["data"]]
        platform_news.extend(result[platform][:cnt])

    return platform_news


if __name__ == "__main__":
    hotnews = get_hotnews()
    if hotnews:
        result = {}

        for platform in hotnews:
            result[platform["name"]] = [item["title"] for item in platform["data"]]
        log.print_log(result.keys())
    else:
        log.print_log("未能获取热点数据")
