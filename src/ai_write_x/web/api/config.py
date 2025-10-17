#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.ai_write_x.config.config import Config
from src.ai_write_x.utils import log
from src.ai_write_x.utils.path_manager import PathManager
from src.ai_write_x.adapters.platform_adapters import PlatformType


router = APIRouter(prefix="/api/config", tags=["config"])


class ConfigUpdateRequest(BaseModel):
    config_data: Dict[str, Any]


@router.get("/")
async def get_config():
    """获取当前配置"""
    try:
        config = Config.get_instance()
        config_dict = config.config

        config_data = {
            "platforms": config_dict.get("platforms", []),
            "publish_platform": config_dict.get("publish_platform", "wechat"),
            "api": config_dict.get("api", {}),
            "img_api": config_dict.get("img_api", {}),
            "wechat": config_dict.get("wechat", {}),
            "use_template": config_dict.get("use_template", True),
            "template_category": config_dict.get("template_category", ""),
            "template": config_dict.get("template", ""),
            "use_compress": config_dict.get("use_compress", True),
            "aiforge_search_max_results": config_dict.get("aiforge_search_max_results", 10),
            "aiforge_search_min_results": config_dict.get("aiforge_search_min_results", 1),
            "min_article_len": config_dict.get("min_article_len", 1000),
            "max_article_len": config_dict.get("max_article_len", 2000),
            "auto_publish": config_dict.get("auto_publish", False),
            "article_format": config_dict.get("article_format", "html"),
            "format_publish": config_dict.get("format_publish", True),
            "dimensional_creative": config_dict.get("dimensional_creative", {}),
        }

        return {"status": "success", "data": config_data}

    except Exception as e:
        log.print_log(f"获取配置失败: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/")
async def update_config_memory(request: ConfigUpdateRequest):
    """仅更新内存中的配置,不保存到文件"""
    try:
        config = Config.get_instance()
        config_data = request.config_data.get("config_data", request.config_data)

        # 深度合并配置到内存
        def deep_merge(target, source):
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    deep_merge(target[key], value)
                else:
                    target[key] = value

        with config._lock:
            deep_merge(config.config, config_data)
        return {"status": "success", "message": "配置已更新(仅内存)"}
    except Exception as e:
        log.print_log(f"更新内存配置失败: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def save_config_to_file():
    """保存当前内存配置到文件"""
    try:
        config = Config.get_instance()

        # 直接保存当前内存中的配置
        if config.save_config(config.config):
            return {"status": "success", "message": "配置已保存"}
        else:
            raise HTTPException(status_code=500, detail="配置保存失败")
    except Exception as e:
        log.print_log(f"保存配置失败: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/default")
async def get_default_config():
    """获取默认配置"""
    try:
        config = Config.get_instance()
        return {"status": "success", "data": config.default_config}
    except Exception as e:
        log.print_log(f"获取默认配置失败: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=str(e))


def get_ui_config_path():
    """获取 UI 配置文件路径"""
    return PathManager.get_config_dir() / "ui_config.json"


@router.get("/ui-config")
async def get_ui_config():
    """获取 UI 配置"""
    config_file = get_ui_config_path()
    if config_file.exists():
        return json.loads(config_file.read_text(encoding="utf-8"))
    return {"theme": "light", "windowMode": "STANDARD"}


@router.post("/ui-config")
async def save_ui_config(config: dict):
    """保存 UI 配置"""
    config_file = get_ui_config_path()
    config_file.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"success": True}


@router.get("/template-categories")
async def get_template_categories():
    """获取所有模板分类"""
    try:
        from src.ai_write_x.config.config import DEFAULT_TEMPLATE_CATEGORIES

        categories = PathManager.get_all_categories(DEFAULT_TEMPLATE_CATEGORIES)

        return {"status": "success", "data": categories}
    except Exception as e:
        log.print_log(f"获取模板分类失败: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{category}")
async def get_templates_by_category(category: str):
    """获取指定分类下的模板列表"""
    try:
        if category == "随机分类":
            return {"status": "success", "data": []}

        templates = PathManager.get_templates_by_category(category)

        return {"status": "success", "data": templates}
    except Exception as e:
        log.print_log(f"获取模板列表失败: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/platforms")
async def get_platforms():
    """获取所有支持的发布平台"""
    try:
        platforms = [
            {"value": platform_value, "label": PlatformType.get_display_name(platform_value)}
            for platform_value in PlatformType.get_all_platforms()
        ]

        return {"status": "success", "data": platforms}
    except Exception as e:
        log.print_log(f"获取平台列表失败: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=str(e))
