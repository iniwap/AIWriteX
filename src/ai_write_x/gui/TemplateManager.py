#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
模板管理界面，独立窗口，负责HTML模板的显示、编辑、预览、删除、移动分类、添加、复制和重命名
支持新增分类，默认分类文件夹不可删除，缺失时自动创建
采用树状结构 + 详情面板的UI设计
"""

import os
import glob
import time
import PySimpleGUI as sg
import subprocess
import shutil

from src.ai_write_x.utils import utils
from src.ai_write_x.config.config import DEFAULT_TEMPLATE_CATEGORIES


__author__ = "iniwaper@gmail.com"
__copyright__ = "Copyright (C) 2025 iniwap"
__date__ = "2025/06/25"


class TemplateManager:
    def __init__(self):
        """初始化模板管理窗口"""
        self._current_category = None
        self._window = None
        self._templates = []  # 模板列表
        self._categories = []  # 可用分类
        self._current_template = None  # 当前选中的模板
        sg.theme("systemdefault")
        self._ensure_default_categories()  # 确保默认分类文件夹存在
        self._refresh_data()  # 加载数据

    def _ensure_default_categories(self):
        """确保默认分类文件夹存在，缺失时创建"""
        template_dir = utils.get_template_dir()
        # 使用中文名称作为文件夹名
        for chinese_name in DEFAULT_TEMPLATE_CATEGORIES.values():
            category_path = os.path.join(template_dir, chinese_name)
            if not os.path.exists(category_path):
                os.makedirs(category_path)
                print(f"创建缺失的默认分类文件夹：{chinese_name}")

    def _is_default_category(self, category_name):
        """检查是否为默认分类（不可删除）"""
        return category_name in DEFAULT_TEMPLATE_CATEGORIES.values()

    def _get_templates(self):
        """获取所有模板列表"""
        template_dir = utils.get_template_dir()
        templates = []

        for category in self._categories:
            category_path = os.path.join(template_dir, category)
            if not os.path.exists(category_path):
                continue

            template_files = glob.glob(os.path.join(category_path, "*.html"))
            for file_path in template_files:
                basename = os.path.basename(file_path)
                name = os.path.splitext(basename)[0]
                stats = os.stat(file_path)
                create_time = time.strftime("%Y-%m-%d", time.localtime(stats.st_ctime))
                size = f"{stats.st_size / 1024:.2f} KB"
                templates.append(
                    {
                        "name": name,
                        "path": file_path,
                        "category": category,
                        "create_time": create_time,
                        "size": size,
                    }
                )

        return sorted(templates, key=lambda x: x["create_time"], reverse=True)

    def _refresh_data(self):
        """刷新分类和模板数据"""
        self._categories = utils.get_all_categories(DEFAULT_TEMPLATE_CATEGORIES)
        self._templates = self._get_templates()

    def _build_tree_data(self):
        """构建树状数据结构"""
        treedata = sg.TreeData()

        for category in self._categories:
            # 添加分类节点，使用文件夹前缀
            category_templates = [t for t in self._templates if t["category"] == category]
            template_count = len(category_templates)
            # category_display = f"📁 {category} ({template_count})"
            category_display = f"{category} ({template_count})"
            treedata.Insert("", category, category_display, values=[])

            # 添加该分类下的模板，使用文件前缀
            for template in category_templates:
                # template_display = f"📄 {template['name']}"
                template_display = f"{template['name']}"
                treedata.Insert(
                    category,
                    template["path"],
                    template_display,
                    values=[template["size"], template["create_time"]],
                )

        return treedata

    def _update_detail_panel(self, template=None):
        """更新右侧详情面板"""
        if not self._window:
            return

        if template:
            self._window["-DETAIL_NAME-"].update(template["name"])
            self._window["-DETAIL_CATEGORY-"].update(template["category"])
            self._window["-DETAIL_SIZE-"].update(template["size"])
            self._window["-DETAIL_TIME-"].update(template["create_time"])
            self._window["-DETAIL_PATH-"].update(
                os.path.normpath(template["path"]).replace("/", "\\")
            )

            # 自动加载并显示完整HTML内容
            self._load_template_preview(template)

            # 启用操作按钮
            for key in ["-EDIT-", "-PREVIEW-", "-COPY-", "-RENAME-", "-DELETE-", "-MOVE-"]:
                self._window[key].update(disabled=False)
        else:
            # 清空详情和预览内容
            for key in [
                "-DETAIL_NAME-",
                "-DETAIL_CATEGORY-",
                "-DETAIL_SIZE-",
                "-DETAIL_TIME-",
                "-DETAIL_PATH-",
            ]:
                self._window[key].update("")

            # 清空预览内容
            self._window["-PREVIEW_CONTENT-"].update("")

            # 禁用操作按钮
            for key in ["-EDIT-", "-PREVIEW-", "-COPY-", "-RENAME-", "-DELETE-", "-MOVE-"]:
                self._window[key].update(disabled=True)

    def _create_layout(self):
        """创建窗口布局"""
        # 左侧树状结构
        left_col = sg.Column(
            [
                [sg.Text("模板分类", font=("Arial", 12, "bold"))],
                [
                    sg.Text("搜索:", size=(4, 1), font=("Arial", 10)),
                    sg.Input(
                        "",
                        key="-SEARCH-",
                        size=(25, 1),
                        tooltip="搜索分类或模板名称",
                        enable_events=True,
                    ),
                    sg.Text("🔍", font=("Microsoft YaHei", 12)),
                ],
                [
                    sg.Tree(
                        data=self._build_tree_data(),
                        headings=["大小", "创建时间"],
                        auto_size_columns=True,
                        num_rows=25,
                        col0_width=25,
                        col0_heading="模板",
                        key="-TREE-",
                        show_expanded=False,
                        enable_events=True,
                        expand_x=True,
                        expand_y=True,
                        font=("Arial", 10),
                        row_height=20,
                        right_click_menu=["", ["编辑分类", "删除分类"]],
                    )
                ],
                [
                    sg.Button("添加模板", key="-ADD_TEMPLATE-", size=(10, 1)),
                    sg.Button("添加分类", key="-ADD_CATEGORY-", size=(10, 1)),
                    sg.Button("刷新", key="-REFRESH-", size=(8, 1)),
                ],
            ],
            expand_x=True,
            expand_y=True,
            size=(450, 600),
        )

        # 右侧详情面板
        right_col = sg.Column(
            [
                [
                    sg.Frame(
                        "📄 模板详情",
                        [
                            [
                                sg.Text("名称:", size=(8, 1)),
                                sg.Text("", key="-DETAIL_NAME-", size=(30, 1)),
                            ],
                            [
                                sg.Text("分类:", size=(8, 1)),
                                sg.Text("", key="-DETAIL_CATEGORY-", size=(30, 1)),
                            ],
                            [
                                sg.Text("大小:", size=(8, 1)),
                                sg.Text("", key="-DETAIL_SIZE-", size=(30, 1)),
                            ],
                            [
                                sg.Text("创建时间:", size=(8, 1)),
                                sg.Text("", key="-DETAIL_TIME-", size=(30, 1)),
                            ],
                            [sg.Text("路径:", size=(8, 1))],
                            [sg.Multiline("", key="-DETAIL_PATH-", size=(40, 3), disabled=True)],
                        ],
                        expand_x=True,
                    )
                ],
                [
                    sg.Frame(
                        "📄 模板操作",
                        [
                            [
                                sg.Button("编辑", key="-EDIT-", size=(8, 1), disabled=True),
                                sg.Button("预览", key="-PREVIEW-", size=(8, 1), disabled=True),
                                sg.Button("复制", key="-COPY-", size=(8, 1), disabled=True),
                                sg.Button("重命名", key="-RENAME-", size=(8, 1), disabled=True),
                            ],
                            [
                                sg.Button("移动", key="-MOVE-", size=(8, 1), disabled=True),
                                sg.Button(
                                    "删除",
                                    key="-DELETE-",
                                    size=(8, 1),
                                    disabled=True,
                                    button_color=("white", "red"),
                                ),
                            ],
                        ],
                        expand_x=True,
                    )
                ],
                [
                    sg.Frame(
                        "📄 模板预览",
                        [
                            [sg.Text("选择模板查看预览信息")],
                            [
                                sg.Multiline(
                                    "", key="-PREVIEW_CONTENT-", size=(40, 15), disabled=True
                                )
                            ],
                        ],
                        expand_x=True,
                        expand_y=True,
                    )
                ],
            ],
            expand_x=True,
            expand_y=True,
            size=(450, 600),
        )

        return [[left_col, sg.VSep(), right_col]]

    def _get_template_by_path(self, path):
        """根据路径获取模板对象"""
        for template in self._templates:
            if template["path"] == path:
                return template
        return None

    def _edit_template(self, template):
        """编辑模板文件"""
        path = template["path"]
        name = template["name"]

        if not os.path.exists(path):
            sg.popup_error(f"模板文件不存在：{name}", title="系统提示", icon=self.__get_icon())
            return
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
        for editor in editors:
            try:
                subprocess.run(
                    f'{editor} "{path}"',
                    shell=True,
                    check=True,
                    stderr=subprocess.DEVNULL,
                )
                return
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        sg.popup_error("未找到可用的编辑器", title="系统提示", icon=self.__get_icon())

    def _load_template_preview(self, template):
        """加载模板预览内容"""
        path = template["path"]

        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()  # 读取全部内容，不截断
                    self._window["-PREVIEW_CONTENT-"].update(content)
            except Exception:
                self._window["-PREVIEW_CONTENT-"].update("无法读取文件内容")
        else:
            self._window["-PREVIEW_CONTENT-"].update("文件不存在")

    def _view_template(self, template):
        """在浏览器中预览模板"""
        path = template["path"]
        name = template["name"]

        if os.path.exists(path):
            utils.open_url(path)
        else:
            sg.popup_error(f"模板文件不存在：{name}", title="系统提示", icon=self.__get_icon())

    def _delete_template(self, template):
        """删除模板文件"""
        path = template["path"]
        name = template["name"]

        if os.path.exists(path):
            try:
                os.remove(path)
                sg.popup(
                    f"模板已删除：{name}",
                    non_blocking=True,
                    title="系统提示",
                    icon=self.__get_icon(),
                )
                self._refresh_data()
                self._update_tree()
                self._update_detail_panel()  # 清空详情面板
            except Exception:
                sg.popup_error(f"无法删除模板：{name}", title="系统提示", icon=self.__get_icon())
        else:
            sg.popup_error(f"模板文件不存在：{name}", title="系统提示", icon=self.__get_icon())

    def _move_template(self, template):
        """移动模板到其他分类"""
        layout = [
            [sg.Text("选择目标分类:")],
            [
                sg.Combo(
                    self._categories,
                    key="-TARGET_CATEGORY-",
                    default_value=template["category"],
                    size=(30, 1),
                )
            ],
            [sg.Button("移动", key="-MOVE_CONFIRM-"), sg.Button("取消")],
        ]
        window = sg.Window("系统提示", layout, modal=True, icon=self.__get_icon())

        while True:
            event, values = window.read()
            if event in (sg.WIN_CLOSED, "取消"):
                break
            elif event == "-MOVE_CONFIRM-" and values["-TARGET_CATEGORY-"]:
                new_category = values["-TARGET_CATEGORY-"]
                if new_category != template["category"]:
                    old_path = template["path"]
                    template_dir = utils.get_template_dir()
                    new_path = os.path.join(template_dir, new_category, os.path.basename(old_path))

                    if not os.path.exists(os.path.dirname(new_path)):
                        os.makedirs(os.path.dirname(new_path))

                    try:
                        shutil.move(old_path, new_path)
                        sg.popup(
                            f"模板已移动到 {new_category}",
                            non_blocking=True,
                            title="系统提示",
                            icon=self.__get_icon(),
                        )
                        self._refresh_data()
                        self._update_tree()
                        self._update_detail_panel()
                    except Exception as e:
                        sg.popup_error(
                            f"移动模板失败：{str(e)}", title="系统提示", icon=self.__get_icon()
                        )
                break

        window.close()

    def _copy_template(self, template):
        """复制模板"""
        new_name = sg.popup_get_text(
            "输入新模板名称:",
            default_text=template["name"] + "_copy",
            title="系统提示",
            size=(30, 1),
            icon=self.__get_icon(),
        )
        if not new_name:
            return

        old_path = template["path"]
        new_path = os.path.join(os.path.dirname(old_path), f"{new_name}.html")

        if os.path.exists(new_path):
            sg.popup_error(f"模板名称 {new_name} 已存在", title="系统提示", icon=self.__get_icon())
            return

        try:
            shutil.copy(old_path, new_path)
            sg.popup(
                f"模板已复制为 {new_name}",
                non_blocking=True,
                title="系统提示",
                icon=self.__get_icon(),
            )
            self._refresh_data()
            self._update_tree()
        except Exception as e:
            sg.popup_error(f"复制模板失败：{str(e)}", title="系统提示", icon=self.__get_icon())

    def _rename_template(self, template):
        """重命名模板"""
        new_name = sg.popup_get_text(
            "输入新模板名称:",
            default_text=template["name"],
            title="系统提示",
            size=(30, 1),
            icon=self.__get_icon(),
        )
        if not new_name:
            return

        old_path = template["path"]
        new_path = os.path.join(os.path.dirname(old_path), f"{new_name}.html")

        if os.path.exists(new_path):
            sg.popup_error(f"模板名称 {new_name} 已存在", title="系统提示", icon=self.__get_icon())
            return

        try:
            shutil.move(old_path, new_path)
            sg.popup(
                f"模板已重命名为 {new_name}",
                non_blocking=True,
                title="系统提示",
                icon=self.__get_icon(),
            )
            self._refresh_data()
            self._update_tree()
            self._update_detail_panel()
        except Exception as e:
            sg.popup_error(f"重命名模板失败：{str(e)}", title="系统提示", icon=self.__get_icon())

    def _add_template(self):
        """添加新模板 - 支持创建和导入两种方式"""
        # 使用对齐的布局设计
        layout = [
            [sg.Text("添加模板", font=("Arial", 14, "bold"), justification="center")],
            [sg.HSeparator()],
            [sg.Text("选择添加方式:", font=("Arial", 10))],
            [
                sg.Radio(
                    "创建新模板",
                    "ADD_TYPE",
                    key="-CREATE-",
                    default=True,
                    font=("Arial", 10),
                    enable_events=True,
                )
            ],
            [
                sg.Radio(
                    "导入已有文件",
                    "ADD_TYPE",
                    key="-IMPORT-",
                    font=("Arial", 10),
                    enable_events=True,
                )
            ],
            # [sg.HSeparator()],
            # 模板信息输入区域 - 注意对齐
            [
                sg.Text("模板名称:", size=(8, 1), justification="left"),
                sg.Input("", key="-NEW_NAME-", size=(23, 1)),
            ],
            [
                sg.Text("选择分类:", size=(8, 1), justification="left"),
                sg.Combo(self._categories, key="-NEW_CATEGORY-", size=(23, 1)),
            ],
            # 文件选择区域（仅导入时显示）
            [
                sg.pin(
                    sg.Column(
                        [
                            [
                                sg.Text(
                                    "选择文件:",
                                    size=(8, 1),
                                    justification="left",
                                    key="-FILE_LABEL-",
                                ),
                                sg.Input("", key="-FILE_PATH-", size=(20, 1), enable_events=True),
                                sg.FileBrowse(
                                    "浏览",
                                    target="-FILE_PATH-",
                                    file_types=(("HTML Files", "*.html"), ("All Files", "*.*")),
                                    size=(5, 1),
                                ),
                            ]
                        ],
                        key="-FILE_SECTION-",
                        visible=False,
                        element_justification="left",
                        pad=(0, 0),
                    )
                )
            ],
            [sg.HSeparator()],
            # 按钮区域 - 居中对齐
            [
                sg.Column(
                    [
                        [
                            sg.Button("确定", key="-CONFIRM-", size=(8, 1)),
                            sg.Button("取消", key="-CANCEL-", size=(8, 1)),
                        ]
                    ],
                    justification="center",
                )
            ],
        ]

        window = sg.Window(
            "系统提示",
            layout,
            modal=True,
            icon=self.__get_icon(),
            element_justification="left",
            finalize=True,
        )

        while True:
            event, values = window.read()

            if event in (sg.WIN_CLOSED, "-CANCEL-"):
                break

            elif event in ["-CREATE-", "-IMPORT-"]:
                show_file_controls = values["-IMPORT-"]
                window["-FILE_SECTION-"].update(visible=show_file_controls)

            elif event == "-CONFIRM-":
                if not values["-NEW_NAME-"] or not values["-NEW_CATEGORY-"]:
                    sg.popup_error("请填写完整信息", title="系统提示", icon=self.__get_icon())
                    continue

                name = values["-NEW_NAME-"]
                category = values["-NEW_CATEGORY-"]

                if values["-CREATE-"]:
                    self._create_new_template(name, category)
                else:
                    if not values["-FILE_PATH-"]:
                        sg.popup_error(
                            "请选择要导入的文件", title="系统提示", icon=self.__get_icon()
                        )
                        continue
                    self._import_existing_file(name, category, values["-FILE_PATH-"])
                break

            elif event == "-FILE_PATH-":
                # 当文件路径改变时，自动填充模板名称（如果为空）
                if values["-FILE_PATH-"] and not values["-NEW_NAME-"]:
                    filename = os.path.basename(values["-FILE_PATH-"])
                    name_without_ext = os.path.splitext(filename)[0]
                    window["-NEW_NAME-"].update(name_without_ext)

        window.close()

    def _create_new_template(self, name, category):
        """创建新模板"""
        template_dir = utils.get_template_dir()
        category_path = os.path.join(template_dir, category)
        if not os.path.exists(category_path):
            os.makedirs(category_path)

        file_path = os.path.join(category_path, f"{name}.html")
        if os.path.exists(file_path):
            # 提供覆盖选项而不是直接失败
            choice = sg.popup_yes_no(
                f"模板名称 {name} 已存在",
                "是否覆盖现有模板？",
                title="系统提示",
                icon=self.__get_icon(),
            )
            if choice != "Yes":
                return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("")

            template = {
                "name": name,
                "path": file_path,
                "category": category,
                "create_time": time.strftime("%Y-%m-%d"),
                "size": "0.1 KB",
            }
            self._edit_template(template)
            self._refresh_data()
            self._update_tree()
        except Exception as e:
            sg.popup_error(f"创建模板失败：{str(e)}", title="系统提示", icon=self.__get_icon())

    def _import_existing_file(self, name, category, source_path):
        """导入已有文件"""
        if not os.path.exists(source_path):
            sg.popup_error("源文件不存在", title="系统提示", icon=self.__get_icon())
            return

        template_dir = utils.get_template_dir()
        category_path = os.path.join(template_dir, category)
        if not os.path.exists(category_path):
            os.makedirs(category_path)

        target_path = os.path.join(category_path, f"{name}.html")
        if os.path.exists(target_path):
            # 提供覆盖选项而不是直接失败
            choice = sg.popup_yes_no(
                f"模板名称 {name} 已存在",
                "是否覆盖现有模板？",
                title="系统提示",
                icon=self.__get_icon(),
            )
            if choice != "Yes":
                return

        try:
            shutil.copy2(source_path, target_path)
            sg.popup(f"模板 {name} 导入成功", title="系统提示", icon=self.__get_icon())
            self._refresh_data()
            self._update_tree()
        except Exception as e:
            sg.popup_error(f"导入模板失败：{str(e)}", title="系统提示", icon=self.__get_icon())

    def _add_category(self):
        """添加新分类"""
        category_name = sg.popup_get_text(
            "输入新分类名称:", size=(30, 1), title="系统提示", icon=self.__get_icon()
        )
        if not category_name or category_name in self._categories:
            if category_name:
                sg.popup_error("分类名称已存在", title="系统提示", icon=self.__get_icon())
            return

        template_dir = utils.get_template_dir()
        category_path = os.path.join(template_dir, category_name)

        try:
            os.makedirs(category_path, exist_ok=True)
            self._refresh_data()
            self._update_tree()
            sg.popup(
                f"分类 {category_name} 已添加",
                non_blocking=True,
                title="系统提示",
                icon=self.__get_icon(),
            )
        except Exception as e:
            sg.popup_error(f"创建分类失败：{str(e)}", title="系统提示", icon=self.__get_icon())

    def _update_tree(self):
        """更新树状结构"""
        if self._window:
            self._window["-TREE-"].update(values=self._build_tree_data())

    def _search_templates(self, search_term):
        """实时搜索模板和分类"""
        if not search_term:
            self._update_tree()
            return

        treedata = sg.TreeData()
        search_term = search_term.lower()

        for category in self._categories:
            # 检查分类名是否匹配
            category_matches = search_term in category.lower()

            # 获取该分类下匹配的模板
            category_templates = [
                t
                for t in self._templates
                if t["category"] == category and search_term in t["name"].lower()
            ]

            # 如果分类名匹配，显示该分类下的所有模板
            if category_matches:
                category_templates = [t for t in self._templates if t["category"] == category]

            # 只显示有匹配内容的分类
            if category_templates or category_matches:
                template_count = len(category_templates)
                # category_display = f"📁 {category} ({template_count})"
                category_display = f"{category} ({template_count})"
                treedata.Insert("", category, category_display, values=[])

                for template in category_templates:
                    # template_display = f"📄 {template['name']}"
                    template_display = f"{template['name']}"
                    treedata.Insert(
                        category,
                        template["path"],
                        template_display,
                        values=[template["size"], template["create_time"]],
                    )

        self._window["-TREE-"].update(values=treedata)

    def _edit_category(self, old_category_name):
        """编辑分类称"""
        if self._is_default_category(old_category_name):
            sg.popup_error("默认分类不能重命名", title="系统提示", icon=self.__get_icon())
            return

        new_name = sg.popup_get_text(
            "输入新分类名称:",
            default_text=old_category_name,
            title="系统提示",
            icon=self.__get_icon(),
            size=(30, 1),
        )

        if not new_name or new_name == old_category_name:
            return

        if new_name in self._categories:
            sg.popup_error("分类名称已存在", title="系统提示", icon=self.__get_icon())
            return

        template_dir = utils.get_template_dir()
        old_path = os.path.join(template_dir, old_category_name)
        new_path = os.path.join(template_dir, new_name)

        try:
            os.rename(old_path, new_path)
            sg.popup(f"分类已重命名为 {new_name}", title="系统提示", icon=self.__get_icon())
            self._refresh_data()
            self._update_tree()
        except Exception as e:
            sg.popup_error(f"重命名分类失败：{str(e)}", title="系统提示", icon=self.__get_icon())

    def _delete_category(self, category_name):
        """删除分类及其所有文件"""
        if self._is_default_category(category_name):
            sg.popup_error("默认分类不能删除", title="系统提示", icon=self.__get_icon())
            return

        # 获取分类下的模板数量
        category_templates = [t for t in self._templates if t["category"] == category_name]
        template_count = len(category_templates)

        # 确认删除
        if template_count > 0:
            confirm_msg = f"确认删除分类 '{category_name}' 及其包含的 {template_count} 个模板？\n\n====此操作不可撤销！===="  # noqa 541
        else:
            confirm_msg = f"确认删除空分类 '{category_name}'？"

        choice = sg.popup_yes_no(confirm_msg, title="系统提示", icon=self.__get_icon())
        if choice != "Yes":
            return

        template_dir = utils.get_template_dir()
        category_path = os.path.join(template_dir, category_name)

        try:
            # 删除整个分类文件夹及其内容
            shutil.rmtree(category_path)
            sg.popup(f"分类 '{category_name}' 已删除", title="系统提示", icon=self.__get_icon())
            self._refresh_data()
            self._update_tree()
            self._update_detail_panel()  # 清空详情面板
        except Exception as e:
            sg.popup_error(f"删除分类失败：{str(e)}", title="系统提示", icon=self.__get_icon())

    def run(self):
        """运行模板管理窗口"""
        self._window = sg.Window(
            "AIWriteX - 模板管理",
            self._create_layout(),
            size=(850, 640),
            resizable=False,
            icon=self.__get_icon(),
            finalize=True,
        )

        self._current_category = None
        # 初始化详情面板为禁用状态
        self._update_detail_panel()

        while True:
            event, values = self._window.read()

            if event == sg.WIN_CLOSED:
                break

            elif event == "-TREE-":
                if values["-TREE-"]:
                    selected_key = values["-TREE-"][0]
                    template = self._get_template_by_path(selected_key)

                    if template:
                        self._current_template = template
                        self._current_category = template["category"]
                        self._update_detail_panel(template)
                    else:
                        self._current_template = None
                        self._current_category = selected_key
                        self._update_detail_panel()

            elif event == "-SEARCH-":
                search_term = values["-SEARCH-"].strip()
                self._search_templates(search_term)

            elif event == "-REFRESH-":
                self._ensure_default_categories()
                self._refresh_data()
                self._update_tree()
                self._update_detail_panel()

            elif event == "-ADD_TEMPLATE-":
                self._add_template()

            elif event == "-ADD_CATEGORY-":
                self._add_category()

            elif event == "-EDIT-" and self._current_template:
                self._edit_template(self._current_template)

            elif event == "-PREVIEW-" and self._current_template:
                self._view_template(self._current_template)

            elif event == "-COPY-" and self._current_template:
                self._copy_template(self._current_template)

            elif event == "-RENAME-" and self._current_template:
                self._rename_template(self._current_template)

            elif event == "-MOVE-" and self._current_template:
                self._move_template(self._current_template)

            elif event == "-DELETE-" and self._current_template:
                if (
                    sg.popup_yes_no(
                        f"是否确认删除模板：{self._current_template['name']}？",
                        title="系统提示",
                        icon=self.__get_icon(),
                    )
                    == "Yes"
                ):
                    self._delete_template(self._current_template)

            elif event == "编辑分类":
                # 检查是否有有效的分类可以操作
                if self._current_category and self._current_category in self._categories:
                    if self._is_default_category(self._current_category):
                        sg.popup(
                            "系统默认分类，不可编辑 :(",
                            title="系统提示",
                            icon=self.__get_icon(),
                        )
                    else:
                        self._edit_category(self._current_category)

            elif event == "删除分类":
                # 检查是否有有效的分类可以操作
                if self._current_category and self._current_category in self._categories:
                    if self._is_default_category(self._current_category):
                        sg.popup(
                            "系统默认分类，不可删除 :(",
                            title="系统提示",
                            icon=self.__get_icon(),
                        )
                    else:
                        self._delete_category(self._current_category)

        self._window.close()

    def __get_icon(self):
        """获取窗口图标"""
        return utils.get_res_path("UI\\icon.ico", os.path.dirname(__file__))


def gui_start():
    """启动模板管理界面"""
    TemplateManager().run()


if __name__ == "__main__":
    gui_start()
