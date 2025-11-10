#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional
import asyncio
import time
import queue

from src.ai_write_x.config.config import Config
from src.ai_write_x.crew_main import ai_write_x_main
from src.ai_write_x.tools import hotnews
from src.ai_write_x.utils import utils, log

router = APIRouter(prefix="/api", tags=["generate"])

# 全局任务管理
_current_process = None
_current_log_queue = None
_task_status = {"status": "idle", "error": None}


class ReferenceConfig(BaseModel):
    """借鉴模式配置"""

    template_category: Optional[str] = None
    template_name: Optional[str] = None
    reference_urls: Optional[str] = None
    reference_ratio: Optional[int] = 30


class GenerateRequest(BaseModel):
    """内容生成请求"""

    topic: str
    reference: Optional[ReferenceConfig] = None


@router.get("/config/validate")
async def validate_config():
    """
    验证系统配置

    返回友好的错误消息,前端可以直接显示给用户
    """
    try:
        config = Config.get_instance()

        if not config.validate_config():
            # 根据错误类型返回不同的消息
            error_msg = config.error_message

            # 检查是否是 API KEY 相关错误
            if "API KEY" in error_msg or "api_key" in error_msg:
                detail = f"{error_msg}\n\n请前往【系统设置 → 大模型API】配置您的 API 密钥。"
            elif "Model" in error_msg or "model" in error_msg:
                detail = f"{error_msg}\n\n请前往【系统设置 → 大模型API】配置模型参数。"
            elif "微信公众号" in error_msg or "appid" in error_msg:
                detail = f"{error_msg}\n\n请前往【系统设置 → 微信公众号】配置账号信息。"
            else:
                detail = f"配置错误: {error_msg}"

            raise HTTPException(status_code=400, detail=detail)

        return {"status": "success", "message": "配置验证通过"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"配置验证失败: {str(e)}")


@router.post("/generate")
async def generate_content(request: GenerateRequest):
    global _current_process, _current_log_queue, _task_status

    if _current_process and _current_process.is_alive():
        raise HTTPException(status_code=409, detail="任务正在运行中,请先停止当前任务")

    try:
        config = Config.get_instance()

        # 系统配置校验
        if not config.validate_config():
            raise HTTPException(status_code=400, detail=f"配置错误: {config.error_message}")

        config.custom_topic = ""
        config.urls = []
        config.reference_ratio = 0.0
        config.custom_template_category = ""
        config.custom_template = ""

        # 准备配置数据
        config_data = {
            "custom_topic": "",
            "urls": [],
            "reference_ratio": 0.0,
            "custom_template_category": "",
            "custom_template": "",
        }

        # 如果启用借鉴模式,覆盖默认值
        if request.reference:
            config_data["custom_topic"] = request.topic
            config_data["custom_template_category"] = request.reference.template_category or ""
            config_data["custom_template"] = request.reference.template_name or ""

            if request.reference.reference_urls:
                urls = [
                    url.strip()
                    for url in request.reference.reference_urls.split("|")
                    if url.strip()
                ]
                valid_urls = [url for url in urls if utils.is_valid_url(url)]
                if len(valid_urls) != len(urls):
                    raise HTTPException(status_code=400, detail="存在无效的URL")
                config_data["urls"] = valid_urls

            config_data["reference_ratio"] = float(request.reference.reference_ratio or 30) / 100

        # 启动任务
        result = ai_write_x_main(config_data)

        if result and result[0] and result[1]:
            _current_process, _current_log_queue = result
            _task_status = {"status": "running", "error": None}
            _current_process.start()

            return {
                "status": "success",
                "message": "正在生成内容，请耐心等待...",
                "mode": "reference" if request.reference else "hot_search",
                "topic": request.topic,
            }
        else:
            raise HTTPException(status_code=500, detail="执行启动失败,请检查配置")

    except HTTPException:
        raise
    except Exception as e:

        log.print_log(f"生成启动失败: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/stop")
async def stop_generation():
    """
    停止当前生成任务

    参考 PySimpleGUI 的进程终止逻辑:
    src/ai_write_x/gui/MainGUI.py:853-931
    """
    global _current_process, _current_log_queue, _task_status

    if not _current_process or not _current_process.is_alive():
        return {"status": "info", "message": "没有正在运行的任务"}

    try:
        log.print_log("正在停止任务...", "info")

        # 首先尝试优雅终止
        _current_process.terminate()
        _current_process.join(timeout=2.0)

        # 检查是否真正终止
        if _current_process.is_alive():
            log.print_log("执行未响应,强制终止", "warning")
            _current_process.kill()
            _current_process.join(timeout=1.0)

            if _current_process.is_alive():
                log.print_log("警告:执行可能未完全终止", "warning")
            else:
                log.print_log("任务执行已强制终止", "info")
        else:
            log.print_log("任务执行已停止", "info")

        # 清理队列中的剩余消息
        if _current_log_queue:
            try:
                while True:
                    _current_log_queue.get_nowait()
            except queue.Empty:
                pass

        # 重置状态
        _current_process = None
        _current_log_queue = None
        _task_status = {"status": "stopped", "error": None}

        return {"status": "success", "message": "任务已停止"}

    except Exception as e:
        log.print_log(f"终止执行时出错: {str(e)}", "error")

        # 即使出错也要重置状态
        _current_process = None
        _current_log_queue = None
        _task_status = {"status": "error", "error": str(e)}

        raise HTTPException(status_code=500, detail=str(e))


@router.get("/generate/status")
async def get_generation_status():
    global _current_process, _task_status, _current_log_queue

    # 检查进程状态
    if _current_process:
        if _current_process.is_alive():
            return {"status": "running", "error": None}
        else:
            # 进程已结束,检查退出码
            exit_code = _current_process.exitcode
            if exit_code == 0:
                status = {"status": "completed", "error": None}
            else:
                status = {"status": "failed", "error": f"退出码: {exit_code}"}

            # 清理资源
            _current_process = None
            _current_log_queue = None
            _task_status = {"status": "idle", "error": None}

            return status

    return _task_status


@router.websocket("/ws/generate/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()

    global _current_log_queue, _current_process

    # 初始化文件日志处理器
    from datetime import datetime
    from src.ai_write_x.utils.path_manager import PathManager

    log_file = PathManager.get_log_dir() / f"WEB_{datetime.now().strftime('%Y-%m-%d')}.log"
    log.LogManager.get_instance().set_file_handler(log_file)
    file_handler = log.LogManager.get_instance().get_file_handler()

    try:
        while True:
            # 检查进程状态
            if _current_process and not _current_process.is_alive():
                exit_code = _current_process.exitcode
                if exit_code != 0:
                    # 进程异常退出,发送失败消息
                    await websocket.send_json(
                        {
                            "type": "failed",
                            "message": f"任务执行失败,退出码: {exit_code}",
                            "error": f"进程异常退出(exitcode={exit_code})",
                        }
                    )
                    break

            if _current_log_queue:
                try:
                    msg = _current_log_queue.get_nowait()

                    # 发送到前端
                    await websocket.send_json(
                        {
                            "type": msg.get("type", "info"),
                            "message": msg.get("message", ""),
                            "timestamp": msg.get("timestamp", time.time()),
                        }
                    )

                    # 保存到文件
                    if file_handler:
                        file_handler.write_log(msg)

                    # 检查任务完成
                    if msg.get("type") == "internal":
                        if "任务执行完成" in msg.get("message", ""):
                            await websocket.send_json(
                                {
                                    "type": "completed",
                                    "message": "任务执行完成",
                                    "timestamp": time.time(),
                                }
                            )
                            break
                        elif "任务执行失败" in msg.get("message", ""):
                            await websocket.send_json(
                                {
                                    "type": "failed",
                                    "message": "任务执行失败",
                                    "error": msg.get("error", "未知错误"),
                                    "timestamp": time.time(),
                                }
                            )
                            break

                except queue.Empty:
                    pass

            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        log.print_log("WebSocket 连接断开", "info")
    except Exception as e:
        log.print_log(f"WebSocket 错误: {str(e)}", "error")
    finally:
        if websocket.client_state.name != "DISCONNECTED":
            try:
                await websocket.close()
            except RuntimeError:
                pass


@router.get("/hot-topics")
async def get_hot_topics():
    """
    获取热搜话题

    参考 PySimpleGUI 版本的热搜获取逻辑:
    src/ai_write_x/crew_main.py:133-136
    src/ai_write_x/tools/hotnews.py:168-189
    """
    try:
        config = Config.get_instance()

        # 获取随机平台
        platform = utils.get_random_platform(config.platforms)

        # 选择平台话题 - 前5个热门话题根据权重选一个
        topic = hotnews.select_platform_topic(platform, 5)

        log.print_log(f"获取热搜话题: 平台={platform}, 话题={topic}", "info")

        return {"status": "success", "platform": platform, "topic": topic}

    except Exception as e:
        log.print_log(f"获取热搜失败: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=str(e))
