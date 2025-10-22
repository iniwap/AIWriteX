#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import webview
import threading
import time
import uvicorn
import asyncio
import platform
from pathlib import Path
import signal
import sys
import os

from src.ai_write_x.web.app import app
from src.ai_write_x.utils import log
from src.ai_write_x.config.config import Config
from src.ai_write_x.utils.tray_manager import TrayManager
from src.ai_write_x.utils.icon_manager import WindowIconManager


class WebViewGUI:
    def __init__(self):
        self.server_thread = None
        self.window = None
        self.server_port = 8000
        self.tray_manager = TrayManager("AIWriteX")
        self.tray_thread = None

        # 设置托盘管理器的窗口管理器引用
        self.tray_manager.set_window_manager(self)
        self.icon_manager = WindowIconManager()

        self.is_shutting_down = False

        # 设置Windows应用用户模型ID
        if sys.platform == "win32":
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.iniwap.AIWriteX")

    def signal_handler(self, signum, frame):
        """处理系统信号"""
        print(f"接收到信号 {signum}，开始退出...")
        self.quit_application()
        sys.exit(0)

    def setup_signal_handlers(self):
        """设置信号处理器"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        if platform.system() == "Windows":
            signal.signal(signal.SIGBREAK, self.signal_handler)

    def quit_application(self):
        """完整的退出流程"""
        if self.is_shutting_down:
            return

        self.is_shutting_down = True

        try:
            # 1. 停止托盘
            if self.tray_manager:
                self.tray_manager.stop_tray()

            # 2. 停止后端服务器
            if hasattr(self, "server_thread") and self.server_thread:
                # 这里需要添加服务器停止逻辑
                pass

            # 3. 关闭WebView窗口
            if self.window:
                try:
                    self.window.destroy()
                except Exception:
                    pass

        except Exception as e:
            print(f"退出时出错: {e}")
        finally:
            # 强制退出
            os._exit(0)

    def start_server(self):
        """启动FastAPI服务器"""
        try:
            # 配置uvicorn服务器
            config = uvicorn.Config(
                app, host="127.0.0.1", port=self.server_port, log_level="warning", access_log=False
            )
            server = uvicorn.Server(config)

            # 在新的事件循环中运行服务器
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(server.serve())

        except Exception as e:
            log.print_log(f"服务器启动失败: {str(e)}", "error")

    def check_server_ready(self, max_attempts=30):
        """检查服务器是否就绪"""
        import requests

        for attempt in range(max_attempts):
            try:
                response = requests.get(f"http://127.0.0.1:{self.server_port}/health", timeout=1)
                if response.status_code == 200:
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        return False

    def show_window(self):
        """显示主窗口"""
        try:
            if self.window:
                # 如果窗口存在，显示它
                self.window.show()
                # 更新托盘提示
                if self.tray_manager:
                    self.tray_manager.update_tooltip("运行中")
        except Exception as e:
            log.print_log(f"显示窗口时出错: {e}", "error")

    def hide_window(self):
        """隐藏窗口到托盘"""
        if self.is_shutting_down:
            return  # 退出过程中不显示通知

        if self.window:
            try:
                self.window.minimize()
            except Exception:
                pass

        # 通知用户已最小化到托盘
        if self.tray_manager:
            self.tray_manager.show_notification("AIWriteX", "已最小化到系统托盘")

    def on_window_closing(self):
        """窗口关闭事件处理"""
        # 如果有托盘，隐藏到托盘而不是退出
        if self.tray_manager and self.tray_manager.tray:
            self.hide_window()
            return False  # 阻止窗口关闭
        else:
            # 没有托盘时直接退出
            self.quit_application()
            return True

    def start(self):
        """启动WebView应用"""
        try:
            # 设置信号处理器
            self.setup_signal_handlers()

            # 初始化配置
            config = Config.get_instance()
            if not config.load_config():
                log.print_log("配置加载失败，使用默认配置", "warning")

            # 启动后端服务器
            self.server_thread = threading.Thread(target=self.start_server, daemon=True)
            self.server_thread.start()

            # 等待服务器启动
            log.print_log("正在启动Web服务器...", "info")
            if not self.check_server_ready():
                raise Exception("Web服务器启动超时")

            log.print_log("Web服务器启动成功", "info")

            # 读取窗口模式设置（首次启动时使用默认值）
            window_config = self.get_window_config()

            # 创建WebView窗口时设置图标
            window_kwargs = {
                "title": "AIWriteX - 智能内容创作平台",
                "url": f"http://127.0.0.1:{self.server_port}",
                "width": window_config["width"],
                "height": window_config["height"],
                "min_size": (1000, 700),
                "resizable": True,
                "maximized": window_config["maximized"],
                "fullscreen": False,  # 可选：如果需要真正全屏
            }

            # 创建WebView窗口
            # Linux 平台直接设置图标
            if platform.system() == "Linux" and Path(self.icon_manager.icon_path).exists():
                window_kwargs["icon"] = str(self.icon_manager.icon_path)

            self.window = webview.create_window(**window_kwargs)

            # Windows 平台异步设置图标
            if webview.windows:
                window = webview.windows[0]

                # 监听窗口加载完成事件
                def on_loaded():
                    time.sleep(0.05)
                    try:
                        # 可保证启动在最前面显示，但这样会有个缩放动画，非全屏
                        """
                        import win32gui
                        import win32con

                        hwnd = win32gui.FindWindow(None, "AIWriteX - 智能内容创作平台")
                        if hwnd:
                            win32gui.SetForegroundWindow(hwnd)
                            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                            win32gui.SetWindowPos(
                                hwnd,
                                win32con.HWND_TOPMOST,
                                0,
                                0,
                                0,
                                0,
                                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE,
                            )
                            win32gui.SetWindowPos(
                                hwnd,
                                win32con.HWND_NOTOPMOST,
                                0,
                                0,
                                0,
                                0,
                                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE,
                            )
                        """
                        # 触发自定义就绪事件
                        window.evaluate_js("document.dispatchEvent(new Event('pywebviewready'))")
                        # Windows 图标设置
                        self.icon_manager.set_window_icon_windows()
                    except Exception:
                        pass

                window.events.loaded += on_loaded

            # 设置窗口关闭事件
            if hasattr(self.window, "events"):
                self.window.events.closing += self.on_window_closing

            # 延迟创建托盘图标
            def delayed_tray_creation():
                time.sleep(2.0)  # 等待窗口完全显示
                if self.tray_manager.create_tray_icon():
                    self.tray_thread = threading.Thread(
                        target=self.tray_manager.tray.run, daemon=True
                    )
                    self.tray_thread.start()

                    # 设置初始状态
                    self.tray_manager.update_tooltip("运行中")

            # 启动延迟托盘创建线程
            threading.Thread(target=delayed_tray_creation, daemon=True).start()

            # 启动WebView
            log.print_log("正在启动用户界面...", "info")
            webview.start(debug=False)
        except KeyboardInterrupt:
            self.quit_application()
        except Exception as e:
            log.print_log(f"GUI启动失败: {str(e)}", "error")
            raise
        finally:
            # 确保清理资源
            self.quit_application()

    def on_task_start(self):
        """任务开始时的托盘状态更新"""
        if self.tray_manager:
            self.tray_manager.set_icon_status("working")
            self.tray_manager.update_tooltip("正在生成内容...")

    def on_task_complete(self):
        """任务完成时的托盘状态更新"""
        if self.tray_manager:
            self.tray_manager.set_icon_status("normal")
            self.tray_manager.update_tooltip("运行中")
            self.tray_manager.show_notification("AIWriteX", "内容生成完成")

    def on_task_error(self, error_msg):
        """任务出错时的托盘状态更新"""
        if self.tray_manager:
            self.tray_manager.set_icon_status("error")
            self.tray_manager.update_tooltip("任务执行出错")
            self.tray_manager.show_notification("AIWriteX", f"任务执行出错: {error_msg}")

    def get_window_mode_from_js(self):
        """从前端 localStorage 读取窗口模式设置"""
        try:
            if self.window:
                # 执行 JavaScript 代码读取 localStorage
                mode = self.window.evaluate_js(
                    """
                    try {
                        return localStorage.getItem('aiwritex_window_mode') || 'STANDARD';
                    } catch (e) {
                        return 'STANDARD';
                    }
                """
                )
                return mode
        except Exception:
            return "STANDARD"

    def get_window_config(self):
        """获取窗口配置"""
        try:
            from src.ai_write_x.utils.path_manager import PathManager
            import json

            ui_config_file = PathManager.get_config_dir() / "ui_config.json"
            if ui_config_file.exists():
                config = json.loads(ui_config_file.read_text(encoding="utf-8"))
                mode = config.get("windowMode", "STANDARD")

                if mode == "MAXIMIZED":
                    return {"width": 1400, "height": 900, "maximized": True}
                else:
                    return {"width": 1400, "height": 900, "maximized": False}
        except Exception as e:
            log.print_log(f"读取 UI 配置失败: {e}", "warning")

        return {"width": 1400, "height": 900, "maximized": False}


def gui_start():
    """启动WebView GUI的入口函数"""
    try:
        gui = WebViewGUI()
        gui.start()
    except KeyboardInterrupt:
        log.print_log("用户中断程序", "info")
    except Exception as e:
        log.print_log(f"GUI启动失败: {str(e)}", "error")
        # 如果WebView启动失败，可以回退到原有GUI
        try:
            log.print_log("尝试启动传统GUI界面...", "warning")
            import src.ai_write_x.gui.MainGUI as MainGUI

            MainGUI.gui_start()
        except Exception:
            log.print_log("传统GUI启动也失败", "error")


if __name__ == "__main__":
    gui_start()
