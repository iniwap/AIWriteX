import requests
import random
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


def get_platform_news(platform, cnt=10):
    hotnews = get_hotnews()
    if not hotnews:
        return []

    platform_data = next((pf["data"] for pf in hotnews if pf["name"] == platform), [])
    return [item["title"] for item in platform_data[:cnt]]


def select_platform_topic(platform, cnt=10):
    """
    获取指定平台的新闻话题，并按排名加权随机选择一个话题。
    若无话题，返回默认话题。
    """
    topics = get_platform_news(platform, cnt)
    if not topics:
        topics = ["DeepSeek AI 提效秘籍"]
        log.print_log("无法获取到热榜，接口暂时不可用，将使用默认话题。")

    # 加权随机选择：排名靠前的话题权重更高
    weights = [
        1 / (i + 1) ** 2 for i in range(len(topics))
    ]  # 权重递减，如 [68.30%,17.08%,7.59%,4.27%,2.73%,...]
    selected_topic = random.choices(topics, weights=weights, k=1)[0]

    return selected_topic


if __name__ == "__main__":
    hotnews = get_hotnews()
    if hotnews:
        result = {}

        for platform in hotnews:
            result[platform["name"]] = [item["title"] for item in platform["data"]]
        log.print_log(result.keys())
    else:
        log.print_log("未能获取热点数据")
