#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import pystray
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import threading
from src.ai_write_x.utils import utils


class TrayManager:
    """系统托盘管理器"""

    def __init__(self, app_name="AIWriteX"):
        self.app_name = app_name
        self.tray = None
        self.icon_path = self._get_icon_path()
        self.window_manager = None
        self.tray_thread = None
        self.is_stopping = False

    def _get_icon_path(self):
        """获取图标文件路径"""
        try:
            # 复用现有的图标获取逻辑
            icon_path = utils.get_gui_icon()
            if isinstance(icon_path, str) and Path(icon_path).exists():
                return Path(icon_path)
        except Exception:
            pass

        # 回退到默认路径
        gui_dir = Path(__file__).parent.parent / "assets"
        default_icon = utils.get_res_path("UI/icon.ico", str(gui_dir))
        return Path(default_icon) if Path(default_icon).exists() else None

    def set_window_manager(self, window_manager):
        """设置窗口管理器引用"""
        self.window_manager = window_manager

    def create_tray_icon(self):
        """创建系统托盘图标"""
        try:
            # 加载图标
            if self.icon_path and self.icon_path.exists():
                try:
                    image = Image.open(self.icon_path)
                    # 确保图标尺寸适合托盘
                    image = image.resize((64, 64), Image.Resampling.LANCZOS)
                except Exception:
                    image = self._create_default_icon()
            else:
                image = self._create_default_icon()

            # 创建托盘菜单
            menu = pystray.Menu(
                pystray.MenuItem(f"显示 {self.app_name}", self._show_window),
                pystray.MenuItem("隐藏窗口", self._hide_window),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("创意工坊", self._open_creative_workshop),
                pystray.MenuItem("文章管理", self._open_article_manager),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("关于", self._show_about),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("退出", self._quit_application),
            )

            # 创建托盘图标
            self.tray = pystray.Icon(
                self.app_name, image, f"{self.app_name} - 智能内容创作平台", menu
            )

            return True
        except Exception as e:
            print(f"创建托盘图标失败: {e}")
            return False

    def _create_default_icon(self):
        """创建默认图标"""
        # 创建简单的默认图标
        image = Image.new("RGBA", (64, 64), (37, 99, 235, 255))
        # 添加简单的文字标识
        try:
            draw = ImageDraw.Draw(image)
            # 尝试使用默认字体
            try:
                font = ImageFont.load_default()
            except Exception:
                font = None
            draw.text((16, 24), "AX", fill=(255, 255, 255, 255), font=font)
        except ImportError:
            pass
        return image

    def _show_window(self, icon=None, item=None):
        """显示主窗口"""
        if self.window_manager:
            self.window_manager.show_window()

    def _hide_window(self, icon=None, item=None):
        """隐藏主窗口"""
        if self.window_manager:
            self.window_manager.hide_window()
            # 只有隐藏到托盘时才显示此通知
            self.show_notification("AIWriteX", "已最小化到系统托盘")

    def _open_creative_workshop(self, icon=None, item=None):
        """打开创意工坊"""
        if self.window_manager:
            self.window_manager.show_window()
            # 可以添加切换到创意工坊视图的逻辑

    def _open_article_manager(self, icon=None, item=None):
        """打开文章管理"""
        if self.window_manager:
            self.window_manager.show_window()
            # 可以添加切换到文章管理视图的逻辑

    def _show_about(self, icon=None, item=None):
        """显示关于信息"""
        # 这里可以实现一个简单的关于对话框
        print(f"关于 {self.app_name}")
        print("智能内容创作平台")
        print("版本: 2.3.0")
        print("基于 CrewAI 和 AIForge 构建")

    def _quit_application(self, icon=None, item=None):
        """退出应用程序"""
        if self.window_manager:
            self.window_manager.quit_application()
        else:
            # 如果没有窗口管理器，直接退出
            os._exit(0)

    def run_tray(self):
        """运行托盘（在单独线程中）"""
        if self.tray:

            def run_tray_thread():
                try:
                    self.tray.run()
                except Exception as e:
                    print(f"托盘运行错误: {e}")

            self.tray_thread = threading.Thread(target=run_tray_thread, daemon=True)
            self.tray_thread.start()
            return self.tray_thread
        return None

    def stop_tray(self):
        """停止托盘"""
        if self.is_stopping:
            return

        self.is_stopping = True

        if self.tray:
            try:
                self.tray.stop()
            except Exception as e:
                print(f"停止托盘时出错: {e}")

        # 等待托盘线程结束
        if self.tray_thread and self.tray_thread.is_alive():
            self.tray_thread.join(timeout=2.0)

    def update_tooltip(self, message):
        """更新托盘图标提示信息"""
        if self.tray:
            self.tray.title = f"{self.app_name} - {message}"

    def show_notification(self, title, message, timeout=3):
        """显示系统通知"""
        if self.tray:
            try:
                self.tray.notify(message, title)
            except Exception:
                pass

    def set_icon_status(self, status="normal"):
        """设置图标状态（可以用不同颜色表示状态）"""
        try:
            if status == "working":
                # 创建工作状态图标（例如添加小点）
                image = self._create_status_icon("working")
            elif status == "error":
                # 创建错误状态图标
                image = self._create_status_icon("error")
            else:
                # 正常状态
                image = self._load_normal_icon()

            if self.tray and image:
                self.tray.icon = image
        except Exception as e:
            print(f"设置图标状态失败: {e}")

    def _create_status_icon(self, status):
        """创建状态图标"""
        base_image = self._load_normal_icon()
        if not base_image:
            return None

        # 在基础图标上添加状态指示
        draw = ImageDraw.Draw(base_image)

        if status == "working":
            # 添加绿色圆点
            draw.ellipse([50, 50, 64, 64], fill=(0, 255, 0, 255))
        elif status == "error":
            # 添加红色圆点
            draw.ellipse([50, 50, 64, 64], fill=(255, 0, 0, 255))

        return base_image

    def _load_normal_icon(self):
        """加载正常状态图标"""
        if self.icon_path and self.icon_path.exists():
            try:
                image = Image.open(self.icon_path)
                return image.resize((64, 64), Image.Resampling.LANCZOS)
            except Exception:
                pass
        return self._create_default_icon()
