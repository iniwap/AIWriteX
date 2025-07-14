#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
配图管理界面，负责文章配图的设置和管理
"""

import os
import glob
import shutil
import PySimpleGUI as sg
from PIL import Image
import io
import subprocess
import tempfile


from src.ai_write_x.utils import utils
from src.ai_write_x.config.config import Config


__author__ = "iniwaper@gmail.com"
__copyright__ = "Copyright (C) 2025 iniwap"
__date__ = "2025/07/10"


class ImageConfigWindow:
    def __init__(self, article):
        """初始化配图配置窗口"""
        self.article = article
        self.window = None
        self.modified_content = None
        self.image_dir = utils.get_current_dir("image")
        self.right_clicked_item = None  # 存储右键点击的项目
        self.current_preview_file = None  # 当前预览的文件路径
        self.current_preview_filename = None  # 当前预览的文件名
        self.current_cover_filename = None  # 当前封面文件名

        # 确保图片目录存在
        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir)

        # 读取文章内容
        try:
            with open(self.article["path"], "r", encoding="utf-8") as f:
                self.modified_content = f.read()
        except Exception:
            self.modified_content = ""

        self.original_image_urls = self._get_article_image_urls()  # 保存初始URL列表
        self.replacement_mapping = {}  # 跟踪每个位置的替换情况

        sg.theme("systemdefault")

    def _reset_preview_to_default(self):
        """重置预览图片为默认白色背景，带文字提示"""
        try:
            # 创建白色背景图片
            img = Image.new("RGB", (400, 200), (255, 255, 255))

            # 添加文字提示
            from PIL import ImageDraw, ImageFont

            draw = ImageDraw.Draw(img)

            text = "选中图片以预览"

            # 尝试使用系统字体，如果失败则使用默认字体
            try:
                # Windows 系统字体
                font = ImageFont.truetype("msyh.ttc", 16)  # 微软雅黑
            except Exception:
                try:
                    font = ImageFont.truetype("arial.ttf", 16)
                except Exception:
                    font = ImageFont.load_default()

            # 获取文字尺寸并居中
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (400 - text_width) // 2
            y = (200 - text_height) // 2

            # 绘制文字
            draw.text((x, y), text, fill=(128, 128, 128), font=font)

            bio = io.BytesIO()
            img.save(bio, format="PNG")
            return bio.getvalue()
        except Exception:
            # 如果出错，返回纯白色背景
            img = Image.new("RGB", (400, 200), (255, 255, 255))
            bio = io.BytesIO()
            img.save(bio, format="PNG")
            return bio.getvalue()

    def _rename_image(self, old_filename, new_filename):
        """重命名图片文件"""
        old_path = os.path.join(self.image_dir, old_filename)
        new_path = os.path.join(self.image_dir, new_filename)

        try:
            os.rename(old_path, new_path)
            return True
        except Exception:
            return False

    def _delete_images(self, filenames):
        """批量删除图片文件，如果删除的是封面则清空封面设置"""
        deleted_count = 0
        cover_deleted = False

        for filename in filenames:
            file_path = os.path.join(self.image_dir, filename)
            try:
                # 检查是否删除的是当前封面
                if filename == self.current_cover_filename:
                    cover_deleted = True

                os.remove(file_path)
                deleted_count += 1
            except Exception:
                continue

        # 如果删除了封面文件，清空封面设置
        if cover_deleted:
            self._clear_cover_setting()

        return deleted_count

    def _clear_cover_setting(self):
        """清空封面设置"""
        self.current_cover_filename = None
        Config.get_instance().current_preview_cover = ""
        if self.window and "-CURRENT_COVER_DISPLAY-" in self.window.AllKeysDict:
            self.window["-CURRENT_COVER_DISPLAY-"].update("未设置")
            self.window["-PREVIEW_COVER-"].update(disabled=True)
            self.window["-CLEAR_COVER-"].update(disabled=True)

    def _open_image(self, filename):
        """打开图片文件"""
        file_path = os.path.join(self.image_dir, filename)
        try:
            os.startfile(file_path)
            return True
        except Exception:
            return False

    def _get_image_files(self):
        """获取图片目录中的所有图片文件"""
        image_files = []
        for ext in ["*.jpg", "*.jpeg", "*.png"]:
            image_files.extend(glob.glob(os.path.join(self.image_dir, ext)))
        return [os.path.basename(f) for f in image_files]

    def _get_article_image_urls(self):
        """获取文章中的图片URLs"""
        try:
            return utils.extract_image_urls(self.modified_content, False)
        except Exception:
            return []

    def _get_display_image_urls(self):
        urls = self._get_article_image_urls()
        display_urls = []

        normalized_image_dir = self.image_dir.replace("\\", "/")

        for url in urls:
            normalized_url = url.replace("\\", "/")

            if os.path.isabs(normalized_url) and normalized_url.startswith(normalized_image_dir):
                display_name = os.path.basename(url)
                display_urls.append(display_name)
            else:
                display_urls.append(url)

        return display_urls

    def _replace_image_at_position(self, position_index, new_image_path):
        """在指定位置替换图片"""
        try:
            current_urls = utils.extract_image_urls(self.modified_content, no_repeate=False)

            if position_index >= len(current_urls):
                return False

            # 找到所有URL在文档中的位置
            url_positions = []
            content = self.modified_content
            search_start = 0

            for i, url in enumerate(current_urls):
                pos = content.find(url, search_start)
                if pos == -1:
                    return False
                url_positions.append((pos, pos + len(url), url, i))
                search_start = pos + len(url)

            # 按位置排序
            url_positions.sort(key=lambda x: x[0])

            # 找到目标位置并替换
            if position_index < len(url_positions):
                start_pos, end_pos, _, _ = url_positions[position_index]
                self.modified_content = (
                    self.modified_content[:start_pos]
                    + new_image_path
                    + self.modified_content[end_pos:]
                )
                return True

            return False

        except Exception:
            return False

    def _update_display_based_on_mapping(self):
        """基于替换映射更新显示列表"""
        display_list = []

        # 始终使用格式化后的显示URL，确保一致性
        current_display_urls = self._get_display_image_urls()

        for i in range(len(self.original_image_urls)):
            if i in self.replacement_mapping:
                # 已替换的显示文件名
                replaced_path = self.replacement_mapping[i]
                display_name = os.path.basename(replaced_path)
                display_list.append(f"{i+1}. {display_name}")
            else:
                # 未替换的使用当前格式化后的显示URL
                if i < len(current_display_urls):
                    display_list.append(f"{i+1}. {current_display_urls[i]}")
                else:
                    # 备用方案：强制使用文件名格式
                    original_url = self.original_image_urls[i]
                    display_name = (
                        os.path.basename(original_url)
                        if os.path.isabs(original_url)
                        else original_url
                    )
                    display_list.append(f"{i+1}. {display_name}")

        self.window["-ARTICLE_IMAGES-"].update(values=display_list)

    def _convert_to_bytes(self, file_path, resize=None):
        """转换图片为字节数据用于显示，等比例缩放填充锁定区域"""
        try:
            img = Image.open(file_path)
            if resize:
                # 等比例缩放并居中填充
                new_width, new_height = resize
                scale = min(new_height / img.height, new_width / img.width)
                scaled_size = (int(img.width * scale), int(img.height * scale))
                img = img.resize(scaled_size, Image.Resampling.LANCZOS)

                # 创建固定大小的背景并居中粘贴
                background = Image.new("RGB", resize, (255, 255, 255))
                paste_x = (new_width - scaled_size[0]) // 2
                paste_y = (new_height - scaled_size[1]) // 2
                background.paste(img, (paste_x, paste_y))
                img = background

            bio = io.BytesIO()
            img.save(bio, format="PNG")
            return bio.getvalue()
        except Exception:
            return None

    def _add_images_to_library(self, source_files):
        """批量添加图片到图片库，处理重名和格式验证"""
        if not source_files:
            return 0, []

        added_count = 0
        skipped_files = []
        supported_formats = [".jpg", ".jpeg", ".png", ".gif", ".bmp"]

        for source_file in source_files:
            if not os.path.exists(source_file):
                continue

            # 检查文件格式
            file_ext = os.path.splitext(source_file)[1].lower()
            if file_ext not in supported_formats:
                skipped_files.append(f"{os.path.basename(source_file)} (不支持的格式)")
                continue

            original_filename = os.path.basename(source_file)
            dest_path = os.path.join(self.image_dir, original_filename)

            # 处理重名文件
            if os.path.exists(dest_path):
                # 自动重命名：在文件名后添加数字后缀
                name, ext = os.path.splitext(original_filename)
                counter = 1
                while os.path.exists(dest_path):
                    new_filename = f"{name}_{counter}{ext}"
                    dest_path = os.path.join(self.image_dir, new_filename)
                    counter += 1

                skipped_files.append(
                    f"{original_filename} → {os.path.basename(dest_path)} (重命名)"
                )

            try:
                shutil.copy2(source_file, dest_path)
                added_count += 1
            except Exception as e:
                skipped_files.append(f"{original_filename} (复制失败: {str(e)})")

        return added_count, skipped_files

    def _create_layout(self):
        """创建配图配置窗口布局"""
        image_filenames = self._get_image_files()
        image_urls = self._get_display_image_urls()

        # 左侧图片库列表
        left_col = [
            [sg.Text("本地图片库", font=("Microsoft YaHei", 12, "bold"))],
            [
                sg.Listbox(
                    values=image_filenames,
                    key="-IMAGE_LIST-",
                    size=(30, 33),
                    enable_events=True,
                    select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                    right_click_menu=[[], ["打开", "重命名", "删除"]],
                    tooltip="1. 右键选择操作 \n2. 单击选中 / Ctrl+单击或 Shift+单击多选",
                )
            ],
            [
                sg.Button("添加", key="-ADD_IMAGES-", size=(6, 1)),
                sg.Button("刷新", key="-REFRESH_IMAGES-", size=(6, 1)),
                sg.Button(
                    "批量删除",
                    key="-BATCH_DELETE-",
                    size=(10, 1),
                    button_color=("white", "firebrick3"),
                ),
            ],
        ]

        # 右侧预览和配置区域
        right_col = [
            [sg.Text("图片预览", font=("Microsoft YaHei", 12, "bold"))],
            [sg.Image(key="-PREVIEW-", size=(400, 200), background_color="white")],
            # 预览操作按钮组
            [
                sg.Button(
                    "预览图→封面",
                    key="-SET_AS_COVER-",
                    size=(12, 1),
                    disabled=True,
                    tooltip="将当前预览的图片设置为文章封面",
                ),
                sg.Button(
                    "预览图→替换链接",
                    key="-REPLACE_WITH_PREVIEW-",
                    size=(15, 1),
                    disabled=True,
                    tooltip="使用当前预览的图片替换选中的文章链接图片",
                ),
            ],
            [sg.HorizontalSeparator()],
            # 文章配图管理区域
            [sg.Text("文章配图管理", font=("Microsoft YaHei", 12, "bold"))],
            [
                sg.Frame(
                    "封面图片设置",
                    [
                        # 当前封面状态显示
                        [sg.Text("当前封面：", size=(10, 1))],
                        [
                            sg.Text(
                                "未设置",
                                key="-CURRENT_COVER_DISPLAY-",
                                size=(24, 1),
                                relief=sg.RELIEF_SUNKEN,
                                background_color="white",
                            ),
                            sg.Button(
                                "预览封面", key="-PREVIEW_COVER-", size=(10, 1), disabled=True
                            ),
                            sg.Button("清除封面", key="-CLEAR_COVER-", size=(10, 1), disabled=True),
                        ],
                    ],
                    size=(450, 100),
                    pad=(5, 5),
                )
            ],
            [
                sg.Frame(
                    "文章中的图片链接",
                    [
                        [
                            sg.Listbox(
                                values=[f"{i+1}. {url}" for i, url in enumerate(image_urls)],
                                key="-ARTICLE_IMAGES-",
                                size=(53, 8),
                                enable_events=True,
                                tooltip="选择要替换的图片链接",
                            )
                        ]
                    ],
                    size=(450, 170),
                )
            ],
            [sg.HorizontalSeparator()],
            [
                sg.Button("保存设置", key="-SAVE_CONFIG-", size=(10, 1)),
                sg.Button("恢复默认", key="-RESTORE_DEFAULT-", size=(10, 1)),
                sg.Button("预览页面", key="-PREVIEW_ARTICLE-", size=(10, 1)),
                sg.Button("编辑页面", key="-EDIT_ARTICLE-", size=(10, 1)),
            ],
        ]
        layout = [
            [
                sg.Column(left_col, vertical_alignment="top", size=(250, 660)),  # 固定左列大小
                sg.VerticalSeparator(),
                sg.Column(right_col, vertical_alignment="top", size=(500, 660)),  # 固定右列大小
            ],
        ]

        return layout

    def run(self):
        """显示配图管理窗口"""
        layout = self._create_layout()

        self.window = sg.Window(
            f'AIWriteX - 配图管理 - {self.article["title"]}',
            layout,
            size=(700, 660),
            finalize=True,
            resizable=False,
            icon=self._get_icon(),
        )
        self.window["-PREVIEW-"].update(data=self._reset_preview_to_default())
        self.window["-IMAGE_LIST-"].bind("<Button-3>", "+RIGHT_CLICK+")

        while True:
            event, values = self.window.read()

            if event in (sg.WIN_CLOSED, "-CLOSE-"):
                break

            elif event == "-REFRESH_IMAGES-":
                # 刷新图片列表
                image_filenames = self._get_image_files()
                self.window["-IMAGE_LIST-"].update(values=image_filenames)

            elif event == "-PREVIEW_ARTICLE-":
                # 获取原文件扩展名
                original_ext = os.path.splitext(self.article["path"])[1]

                try:
                    # 使用tempfile创建临时文件，保持原扩展名
                    with tempfile.NamedTemporaryFile(
                        mode="w",
                        encoding="utf-8",
                        suffix=original_ext,
                        prefix="preview_",
                        delete=False,
                    ) as temp_f:
                        temp_f.write(self.modified_content)
                        temp_file = temp_f.name

                    # 存储临时文件路径用于后续清理
                    if not hasattr(self, "temp_files"):
                        self.temp_files = []
                    self.temp_files.append(temp_file)

                    if utils.open_url(temp_file):
                        sg.popup_error("无法打开预览", title="系统提示", icon=self._get_icon())

                except Exception as e:
                    sg.popup_error(f"预览失败: {str(e)}", title="系统提示", icon=self._get_icon())

            elif event == "-SAVE_CONFIG-":
                # 保存配图配置到原文件
                try:
                    with open(self.article["path"], "w", encoding="utf-8") as f:
                        f.write(self.modified_content)
                    sg.popup("配图设置已保存到文章文件", title="系统提示", icon=self._get_icon())
                except Exception as e:
                    sg.popup_error(f"保存失败: {str(e)}", title="系统提示", icon=self._get_icon())
            elif event == "-EDIT_ARTICLE-":
                # 使用系统默认编辑器打开文章文件
                try:
                    editors = [
                        "cursor",  # Cursor AI 代码编辑器
                        "trae",  # Trae AI 代码编辑器
                        "windsurf",  # Windsurf AI 代码编辑器
                        "zed",  # Zed Editor
                        "tabby",  # TabbyML
                        "code",  # Visual Studio Code
                        "subl",  # Sublime Text
                        "notepad++",  # Notepad++
                        "webstorm",  # WebStorm
                        "phpstorm",  # PhpStorm
                        "pycharm",  # PyCharm
                        "idea",  # IntelliJ IDEA
                        "brackets",  # Brackets
                        "gvim",  # Vim（图形界面）
                        "emacs",  # Emacs
                        "notepad",  # Windows 记事本
                    ]

                    for editor_cmd in editors:
                        try:
                            subprocess.run(
                                f'{editor_cmd} "{self.article["path"]}"',
                                shell=True,
                                check=True,
                                stderr=subprocess.DEVNULL,
                            )

                            return
                        except (subprocess.CalledProcessError, FileNotFoundError):
                            continue
                except Exception as e:
                    sg.popup_error(
                        f"打开编辑器失败: {str(e)}", title="系统提示", icon=self._get_icon()
                    )

            elif event == "-RESTORE_DEFAULT-":
                if (
                    sg.popup_yes_no(
                        "确定要恢复到默认设置吗？所有未保存的更改将丢失。",
                        title="系统提示",
                        icon=self._get_icon(),
                    )
                    == "Yes"
                ):
                    try:
                        with open(self.article["path"], "r", encoding="utf-8") as f:
                            self.modified_content = f.read()

                        # 重置替换映射和原始URL列表
                        self.replacement_mapping = {}
                        self.original_image_urls = self._get_article_image_urls()

                        # 清空封面设置
                        self._clear_cover_setting()

                        # 使用显示方法获取格式化的URL列表
                        display_urls = self._get_display_image_urls()
                        self.window["-ARTICLE_IMAGES-"].update(
                            values=[f"{i+1}. {url}" for i, url in enumerate(display_urls)]
                        )

                        sg.popup("已恢复到默认设置", title="系统提示", icon=self._get_icon())
                    except Exception as e:
                        sg.popup_error(
                            f"恢复失败: {str(e)}", title="系统提示", icon=self._get_icon()
                        )
            # 添加右键菜单事件处理
            elif event == "重命名":
                selected_files = values["-IMAGE_LIST-"]
                if len(selected_files) == 1:
                    old_filename = selected_files[0]
                    new_filename = sg.popup_get_text(
                        "请输入新的文件名:",
                        default_text=old_filename,
                        title="系统提示",
                        icon=self._get_icon(),
                    )
                    if new_filename and new_filename != old_filename:
                        if self._rename_image(old_filename, new_filename):
                            # 检查是否重命名了当前预览的图片
                            if old_filename == self.current_preview_filename:
                                self.current_preview_filename = new_filename
                                self.current_preview_file = os.path.join(
                                    self.image_dir, new_filename
                                )

                            # 检查是否重命名了当前封面图片
                            if old_filename == self.current_cover_filename:
                                self.current_cover_filename = new_filename
                                # 更新封面显示
                                if (
                                    self.window
                                    and "-CURRENT_COVER_DISPLAY-" in self.window.AllKeysDict
                                ):
                                    self.window["-CURRENT_COVER_DISPLAY-"].update(new_filename)
                                # 更新配置
                                Config.get_instance().current_preview_cover = os.path.join(
                                    utils.get_current_dir("image"), new_filename
                                )

                            sg.popup(
                                f"重命名成功: {new_filename}",
                                title="系统提示",
                                icon=self._get_icon(),
                            )
                            # 刷新图片列表
                            image_filenames = self._get_image_files()
                            self.window["-IMAGE_LIST-"].update(values=image_filenames)
                        else:
                            sg.popup_error("重命名失败", title="系统提示", icon=self._get_icon())
                else:
                    sg.popup_error(
                        "请选择单个文件进行重命名", title="系统提示", icon=self._get_icon()
                    )

            elif event == "-IMAGE_LIST-" and values["-IMAGE_LIST-"]:
                # 统一处理图片选择事件（单选和多选）
                selected_files = values["-IMAGE_LIST-"]
                if selected_files:
                    # 获取最后选中的图片进行预览（兼容单选和多选）
                    last_selected = selected_files[-1]
                    file_path = os.path.join(self.image_dir, last_selected)
                    image_data = self._convert_to_bytes(file_path, (400, 200))
                    if image_data:
                        self.window["-PREVIEW-"].update(data=image_data)
                        # 启用操作按钮
                        self.window["-SET_AS_COVER-"].update(disabled=False)
                        self.window["-REPLACE_WITH_PREVIEW-"].update(disabled=False)
                        # 存储当前预览的文件信息，用于后续操作
                        self.current_preview_file = file_path
                        self.current_preview_filename = last_selected
                else:
                    # 没有选中图片时禁用按钮
                    self.window["-SET_AS_COVER-"].update(disabled=True)
                    self.window["-REPLACE_WITH_PREVIEW-"].update(disabled=True)
            elif event == "-IMAGE_LIST-+RIGHT_CLICK+":
                # 获取右键点击时的鼠标位置对应的列表项
                try:
                    listbox = self.window["-IMAGE_LIST-"].Widget
                    index = listbox.nearest(
                        self.window["-IMAGE_LIST-"].Widget.winfo_pointery()
                        - self.window["-IMAGE_LIST-"].Widget.winfo_rooty()
                    )
                    if index >= 0:
                        image_filenames = self._get_image_files()
                        if index < len(image_filenames):
                            self.right_clicked_item = image_filenames[index]
                except Exception:
                    self.right_clicked_item = None

            elif event == "删除":
                # 只删除右键点击的单个文件
                if self.right_clicked_item:
                    # 检查是否要删除封面文件
                    warning_msg = f"确定要删除文件 '{self.right_clicked_item}' 吗？"
                    if self.right_clicked_item == self.current_cover_filename:
                        warning_msg += "\n\n注意：此文件是当前封面，删除后封面设置将被清空。"

                    if (
                        sg.popup_yes_no(warning_msg, title="系统提示", icon=self._get_icon())
                        == "Yes"
                    ):
                        deleted_count = self._delete_images([self.right_clicked_item])
                        if deleted_count > 0:
                            sg.popup(
                                f"成功删除文件: {self.right_clicked_item}",
                                title="系统提示",
                                icon=self._get_icon(),
                            )
                            # 刷新图片列表
                            image_filenames = self._get_image_files()
                            self.window["-IMAGE_LIST-"].update(values=image_filenames)
                            # 清空预览
                            self.window["-PREVIEW-"].update(data=self._reset_preview_to_default())

                            if self.right_clicked_item == self.current_preview_filename:
                                self.current_preview_file = None
                                self.current_preview_filename = None
                                self.window["-SET_AS_COVER-"].update(disabled=True)
                                self.window["-REPLACE_WITH_PREVIEW-"].update(disabled=True)

                            self.right_clicked_item = None
                        else:
                            sg.popup_error("删除失败", title="系统提示", icon=self._get_icon())
                else:
                    sg.popup_error(
                        "请先右键点击要删除的文件", title="系统提示", icon=self._get_icon()
                    )

            elif event == "打开":
                selected_files = values["-IMAGE_LIST-"]
                if len(selected_files) == 1:
                    filename = selected_files[0]
                    if not self._open_image(filename):
                        sg.popup_error("无法打开文件", title="系统提示", icon=self._get_icon())
                elif len(selected_files) > 1:
                    sg.popup_error(
                        "请选择单个文件进行打开", title="系统提示", icon=self._get_icon()
                    )
                else:
                    sg.popup_error("请先选择要打开的文件", title="系统提示", icon=self._get_icon())

            elif event == "-BATCH_DELETE-":
                selected_files = values["-IMAGE_LIST-"]
                if selected_files:
                    # 检查是否包含封面文件
                    cover_in_selection = self.current_cover_filename in selected_files

                    # 检查是否包含当前预览的文件
                    preview_in_selection = self.current_preview_filename in selected_files

                    confirm_message = (
                        f"确认删除以下 {len(selected_files)} 个图片？\n"
                        + "\n".join(f"- {filename}" for filename in selected_files[:5])
                        + ("..." if len(selected_files) > 5 else "")
                    )

                    # 如果包含封面，添加特别提示
                    if cover_in_selection:
                        confirm_message += f"\n\n⚠️ 注意：选中的文件包含当前封面图片 '{self.current_cover_filename}'，删除后封面设置将被清空。"  # noqa 501

                    if (
                        sg.popup_yes_no(confirm_message, title="系统提示", icon=self._get_icon())
                        == "Yes"
                    ):
                        deleted_count = self._delete_images(selected_files)
                        if deleted_count > 0:
                            # 如果删除了当前预览的图片，重置预览状态
                            if preview_in_selection:
                                self.current_preview_file = None
                                self.current_preview_filename = None
                                self.window["-SET_AS_COVER-"].update(disabled=True)
                                self.window["-REPLACE_WITH_PREVIEW-"].update(disabled=True)

                            sg.popup(
                                f"成功删除 {deleted_count} 个文件",
                                title="系统提示",
                                icon=self._get_icon(),
                            )

                            # 刷新图片列表
                            image_filenames = self._get_image_files()
                            self.window["-IMAGE_LIST-"].update(values=image_filenames)

                            # 清空预览
                            self.window["-PREVIEW-"].update(data=self._reset_preview_to_default())
                        else:
                            sg.popup_error("删除失败", title="系统提示", icon=self._get_icon())
                else:
                    sg.popup_error("请先选择要删除的文件", title="系统提示", icon=self._get_icon())

            elif event == "-SET_AS_COVER-":
                self.current_cover_filename = self.current_preview_filename
                self.window["-CURRENT_COVER_DISPLAY-"].update(self.current_cover_filename)
                self.window["-PREVIEW_COVER-"].update(disabled=False)
                self.window["-CLEAR_COVER-"].update(disabled=False)
                Config.get_instance().current_preview_cover = os.path.join(
                    utils.get_current_dir("image"), self.current_cover_filename
                )
            elif event == "-PREVIEW_COVER-":
                if self.current_cover_filename:
                    file_path = os.path.join(self.image_dir, self.current_cover_filename)
                    image_data = self._convert_to_bytes(file_path, (400, 200))
                    if image_data:
                        self.window["-PREVIEW-"].update(data=image_data)
                        # 同步左侧列表选中状态
                        image_filenames = self._get_image_files()
                        if self.current_cover_filename in image_filenames:
                            # 设置左侧列表选中封面图片
                            self.window["-IMAGE_LIST-"].update(
                                set_to_index=[image_filenames.index(self.current_cover_filename)]
                            )
                            # 更新当前预览文件信息
                            self.current_preview_file = file_path
                            self.current_preview_filename = self.current_cover_filename
            # 清除封面设置
            elif event == "-CLEAR_COVER-":
                self.current_cover_filename = None
                self.window["-CURRENT_COVER_DISPLAY-"].update("未设置")
                self.window["-PREVIEW_COVER-"].update(disabled=True)
                self.window["-CLEAR_COVER-"].update(disabled=True)
                Config.get_instance().current_preview_cover = ""
            elif event == "-REPLACE_WITH_PREVIEW-":
                if not values["-ARTICLE_IMAGES-"]:
                    sg.popup_error(
                        "请先选择要替换的图片链接", title="系统提示", icon=self._get_icon()
                    )
                elif not self.current_preview_filename:
                    sg.popup_error(
                        "请先选择要用于替换的图片", title="系统提示", icon=self._get_icon()
                    )
                else:
                    selected_item = values["-ARTICLE_IMAGES-"][0]
                    selected_index = int(selected_item.split(". ")[0]) - 1

                    if selected_index < len(self.original_image_urls):
                        # 生成新的完整路径
                        full_image_path = os.path.join(
                            self.image_dir, self.current_preview_filename
                        )
                        html_image_path = full_image_path.replace("\\", "/")

                        # 使用精确的位置替换
                        if self._replace_image_at_position(selected_index, html_image_path):
                            # 更新替换映射
                            self.replacement_mapping[selected_index] = html_image_path

                            # 更新显示
                            self._update_display_based_on_mapping()
                        else:
                            sg.popup_error("替换失败", title="系统提示", icon=self._get_icon())
            elif event == "-ADD_IMAGES-":
                # 使用FilesBrowse的多选功能
                files = sg.popup_get_file(
                    "选择要添加的图片文件",
                    multiple_files=True,
                    file_types=(
                        ("图片文件", "*.png *.jpg *.jpeg *.gif *.bmp"),
                        ("PNG文件", "*.png"),
                        ("JPEG文件", "*.jpg *.jpeg"),
                        ("所有文件", "*.*"),
                    ),
                    title="添加图片到图库",
                )

                if files:
                    # files是分号分隔的字符串，需要分割
                    file_list = files.split(";") if ";" in files else [files]
                    added_count, skipped_files = self._add_images_to_library(file_list)

                    # 显示结果
                    if added_count > 0:
                        message = f"成功添加 {added_count} 个图片文件"
                        if skipped_files:
                            message += "\n\n处理的文件：\n" + "\n".join(skipped_files)
                        sg.popup(message, title="添加完成", icon=self._get_icon())

                        # 刷新图片列表
                        image_filenames = self._get_image_files()
                        self.window["-IMAGE_LIST-"].update(values=image_filenames)
                    else:
                        message = "没有添加任何文件"
                        if skipped_files:
                            message += "\n\n跳过的文件：\n" + "\n".join(skipped_files)
                        sg.popup_error(message, title="添加失败", icon=self._get_icon())
        self.window.close()
        # 清理临时文件
        if hasattr(self, "temp_files"):
            for temp_file in self.temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception:
                    pass

    def _get_icon(self):
        """获取窗口图标"""
        try:
            return utils.get_res_path("UI\\icon.ico", os.path.dirname(__file__))
        except Exception:
            return None


def gui_start(article):
    ImageConfigWindow(article).run()


if __name__ == "__main__":
    # 测试用的示例文章数据
    test_article = {"title": "测试文章", "path": "test_article.html"}
    gui_start(test_article)
