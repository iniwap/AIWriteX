from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
from typing import List, Optional
import json

from ...config.config import Config
from ...utils.path_manager import PathManager
from ...tools.wx_publisher import pub2wx

router = APIRouter(prefix="/api/articles", tags=["articles"])


class ArticleContentUpdate(BaseModel):
    content: str


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
                    "name": file_path.stem,
                    "path": str(file_path),
                    "title": title,
                    "format": file_path.suffix[1:].upper(),
                    "size": f"{stat.st_size / 1024:.2f} KB",
                    "create_time": datetime.fromtimestamp(stat.st_ctime).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "status": status,
                }
            )

        articles.sort(key=lambda x: x["create_time"], reverse=True)
        return {"status": "success", "data": articles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/content")
async def get_article_content(path: str):
    """获取文章内容 - 使用查询参数"""
    file_path = Path(path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文章不存在")

    content = file_path.read_text(encoding="utf-8")
    return Response(content=content, media_type="text/plain; charset=utf-8")


@router.put("/content")
async def update_article_content(path: str, update: ArticleContentUpdate):
    """更新文章内容"""
    file_path = Path(path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文章不存在")

    file_path.write_text(update.content, encoding="utf-8")
    return {"status": "success", "message": "文章已保存"}


@router.get("/preview")
async def preview_article(path: str):
    """安全预览文章 - 使用查询参数"""
    file_path = Path(path)
    if not file_path.exists():
        return HTMLResponse("<p>文章不存在</p>")

    content = file_path.read_text(encoding="utf-8")
    return HTMLResponse(
        content, headers={"Content-Security-Policy": "default-src 'self' 'unsafe-inline'"}
    )


@router.delete("/{article_path:path}")
async def delete_article(article_path: str):
    """删除文章"""
    file_path = Path(article_path)
    if file_path.exists():
        file_path.unlink()
        return {"status": "success", "message": "文章已删除"}
    raise HTTPException(status_code=404, detail="文章不存在")


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
                        author=cred.get("author", ""),
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
            "account": credential.get("author", ""),
            "appid": credential["appid"][-4:],
            "success": success,
            "error": error,
        }
    )

    records_file.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


@router.get("/platforms")
async def get_supported_platforms():
    """获取支持的发布平台列表"""
    config = Config.get_instance()

    platforms = []

    # 微信公众号
    wechat_credentials = config.wechat_credentials or []
    if wechat_credentials:
        platforms.append(
            {
                "id": "wechat",
                "name": "微信公众号",
                "icon": "wechat",
                "accounts": [
                    {
                        "index": idx,
                        "author_name": cred.get("author", "未命名"),
                        "appid": cred["appid"][-4:],
                        "full_info": f"{cred.get('author', '未命名')} ({cred['appid'][-4:]})",
                    }
                    for idx, cred in enumerate(wechat_credentials)
                ],
            }
        )

    # 未来可扩展其他平台
    # if config.other_platform_credentials:
    #     platforms.append({...})

    return {"status": "success", "data": platforms}
