#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import asyncio
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.ai_write_x.crew_main import ai_write_x_main
from src.ai_write_x.utils import log
from ..state import get_app_state

router = APIRouter(prefix="/api/content", tags=["content"])


class ContentRequest(BaseModel):
    topic: str = ""
    platform: str = ""
    urls: List[str] = []
    reference_ratio: float = 0.0
    custom_template_category: str = ""
    custom_template: str = ""


class ContentResponse(BaseModel):
    status: str
    message: str
    task_id: str = ""


@router.post("/generate", response_model=ContentResponse)
async def generate_content(request: ContentRequest):
    """启动内容生成任务"""
    app_state = get_app_state()

    if app_state.is_running:
        raise HTTPException(status_code=400, detail="任务正在运行中")

    try:
        # 准备配置数据
        config_data = {
            "custom_topic": request.topic,
            "urls": request.urls,
            "reference_ratio": request.reference_ratio,
            "custom_template_category": request.custom_template_category,
            "custom_template": request.custom_template,
        }

        # 启动AI写作任务
        result = ai_write_x_main(config_data)
        if result and result[0] and result[1]:
            app_state.current_process, app_state.log_queue = result
            app_state.is_running = True

            # 启动进程
            app_state.current_process.start()

            return ContentResponse(
                status="success", message="任务启动成功", task_id=str(app_state.current_process.pid)
            )
        else:
            raise HTTPException(status_code=500, detail="任务启动失败")

    except Exception as e:
        log.print_log(f"启动错误: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_generation():
    """停止内容生成任务"""
    app_state = get_app_state()

    if not app_state.is_running or not app_state.current_process:
        return {"status": "success", "message": "没有运行中的任务"}

    try:
        app_state.current_process.terminate()
        app_state.current_process.join(timeout=5.0)

        if app_state.current_process.is_alive():
            app_state.current_process.kill()

        app_state.is_running = False
        app_state.current_process = None
        app_state.log_queue = None

        return {"status": "success", "message": "任务已停止"}

    except Exception as e:
        log.print_log(f"停止任务时出错: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """获取任务状态"""
    app_state = get_app_state()

    return {
        "is_running": app_state.is_running,
        "process_id": app_state.current_process.pid if app_state.current_process else None,
        "timestamp": asyncio.get_event_loop().time(),
    }
