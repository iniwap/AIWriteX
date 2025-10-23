from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
from typing import List, Optional
import json
from datetime import datetime

from ...config.config import Config
from ...utils.path_manager import PathManager
from ...tools.wx_publisher import pub2wx

router = APIRouter(prefix="/api/articles", tags=["articles"])


class PublishRequest(BaseModel):
    article_paths: List[str]
    account_indices: List[int]
    platform: str = "wechat"


@router.get("/")
async def list_articles():
    """获取文章列表"""
    try:
        articles_dir = PathManager.get_article_dir()
        articles = []

        patterns = ["*.html", "*.md", "*.txt"]
        article_files = []

        for pattern in patterns:
            article_files.extend(articles_dir.glob(pattern))

        for file_path in article_files:
            stat = file_path.stat()
            title = file_path.stem.replace("_", "|")
            status = get_publish_status(title)

            articles.append(
                {
                    "path": str(file_path),
                    "title": title,
                    "format": file_path.suffix[1:].upper(),
                    "size": format_size(stat.st_size),
                    "create_time": datetime.fromtimestamp(stat.st_mtime).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "status": status,
                }
            )

        articles.sort(key=lambda x: x["create_time"], reverse=True)
        return articles
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/content")
async def get_article_content(path: str):
    """获取文章内容"""
    try:
        file_path = Path(path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文章不存在")

        content = file_path.read_text(encoding="utf-8")
        return content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{path:path}")
async def delete_article(path: str):
    """删除文章"""
    try:
        file_path = Path(path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文章不存在")

        file_path.unlink()
        return {"status": "success", "message": "文章已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/publish")
async def publish_articles(request: PublishRequest):
    """发布文章到平台"""
    try:
        config = Config.get_instance()
        credentials = config.wechat_credentials

        if not credentials:
            raise HTTPException(status_code=400, detail="未配置微信账号")

        success_count = 0
        fail_count = 0

        for article_path in request.article_paths:
            file_path = Path(article_path)
            if not file_path.exists():
                fail_count += 1
                continue

            content = file_path.read_text(encoding="utf-8")
            title = file_path.stem

            for account_index in request.account_indices:
                if account_index >= len(credentials):
                    continue

                cred = credentials[account_index]
                try:
                    result = pub2wx(
                        title=title,
                        content=content,
                        appid=cred["appid"],
                        appsecret=cred["appsecret"],
                        author=cred.get("author_name", ""),
                    )

                    if result.get("success"):
                        success_count += 1
                        save_publish_record(article_path, cred, True, None)
                    else:
                        fail_count += 1
                        save_publish_record(article_path, cred, False, result.get("error"))

                except Exception as e:
                    fail_count += 1
                    save_publish_record(article_path, cred, False, str(e))

        return {"status": "success", "success_count": success_count, "fail_count": fail_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_publish_status(title: str) -> str:
    """获取文章发布状态"""
    records_file = PathManager.get_article_dir() / "publish_records.json"
    if not records_file.exists():
        return "unpublished"

    try:
        records = json.loads(records_file.read_text(encoding="utf-8"))
        article_records = records.get(title, [])

        if not article_records:
            return "unpublished"

        latest = max(article_records, key=lambda x: x.get("publish_time", ""))
        return "published" if latest.get("success") else "failed"
    except Exception:
        return "unpublished"


def save_publish_record(article_path: str, credential: dict, success: bool, error: Optional[str]):
    """保存发布记录"""
    records_file = PathManager.get_data_dir() / "publish_records.json"

    records = {}
    if records_file.exists():
        try:
            records = json.loads(records_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    if article_path not in records:
        records[article_path] = []

    records[article_path].append(
        {
            "timestamp": datetime.now().isoformat(),
            "account": credential.get("author_name", ""),
            "appid": credential["appid"][-4:],
            "success": success,
            "error": error,
        }
    )

    records_file.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def format_size(size: int) -> str:
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"
