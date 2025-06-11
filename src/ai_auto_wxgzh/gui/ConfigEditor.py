import PySimpleGUI as sg
import re
import os
import copy  # noqa 841
import glob

from src.ai_auto_wxgzh.config.config import Config
from src.ai_auto_wxgzh.utils import utils


class ConfigEditor:
    def __init__(self):
        """初始化配置编辑器，使用单例配置"""
        sg.theme("systemdefault")
        self.config = Config.get_instance()
        self.platform_count = len(self.config.platforms)
        self.wechat_count = len(self.config.wechat_credentials)
        self.window = None
        self.window = sg.Window(
            "配置管理",
            self.create_layout(),
            size=(500, 600),
            resizable=False,
            finalize=True,
            icon=self.__get_icon(),
        )

        # 设置默认选中的API类型的TAB
        self.__default_select_api_tab()

    def __get_icon(self):
        return utils.get_res_path("UI\\icon.ico", os.path.dirname(__file__))

    def __get_templates(self):
        try:
            template_files_abs = glob.glob(
                os.path.join(
                    utils.get_res_path(
                        "templates",
                        os.path.join(utils.get_current_dir("knowledge", False)),
                    ),
                    "*.html",
                )
            )

            if not template_files_abs:
                return []

            # 提取文件名（不含路径），限制数量
            template_filenames = sorted(
                [os.path.splitext(os.path.basename(path))[0] for path in template_files_abs]
            )

            return template_filenames
        except Exception as e:  # noqa 841
            return []

    def create_platforms_tab(self):
        """创建平台 TAB 布局"""
        # 确保使用最新的 self.config.platforms 数据
        self.platform_count = len(self.config.platforms)
        platform_rows = [
            [
                sg.InputText(
                    platform["name"], key=f"-PLATFORM_NAME_{i}-", size=(20, 1), disabled=True
                ),
                sg.Text("权重:", size=(6, 1)),
                sg.InputText(platform["weight"], key=f"-PLATFORM_WEIGHT_{i}-", size=(50, 1)),
            ]
            for i, platform in enumerate(self.config.platforms)
        ]
        layout = [
            [sg.Text("热搜平台列表")],
            *platform_rows,
            [
                sg.Text(
                    "Tips：\n"
                    "1、根据权重随机一个平台，获取其当前的最热门话题；\n"
                    "2、权重总和超过1，默认选取微博作为热搜话题。\n",
                    size=(70, 3),
                    text_color="gray",
                ),
            ],
            [
                sg.Button("保存配置", key="-SAVE_PLATFORMS-"),
                sg.Button("恢复默认", key="-RESET_PLATFORMS-"),
            ],
        ]
        # 使用 sg.Column 包裹布局，设置 pad=(0, 0) 确保顶部无额外边距
        return [[sg.Column(layout, scrollable=False, vertical_scroll_only=False, pad=(0, 0))]]

    def create_wechat_tab(self):
        """创建微信 TAB 布局 (垂直排列，标签固定宽度对齐，支持滚动)"""
        credentials = self.config.wechat_credentials
        self.wechat_count = len(credentials)
        label_width = 12
        wechat_rows = []
        for i, cred in enumerate(credentials):
            wechat_rows.append(
                [sg.Text(f"凭证 {i+1}:", size=(label_width, 1), key=f"-WECHAT_TITLE_{i}-")]
            )
            wechat_rows.append(
                [
                    sg.Text("AppID*:", size=(label_width, 1)),
                    sg.InputText(cred["appid"], key=f"-WECHAT_APPID_{i}-", size=(45, 1)),
                ]
            )
            wechat_rows.append(
                [
                    sg.Text("AppSecret*:", size=(label_width, 1)),
                    sg.InputText(cred["appsecret"], key=f"-WECHAT_SECRET_{i}-", size=(45, 1)),
                ]
            )
            wechat_rows.append(
                [
                    sg.Text("作者:", size=(label_width, 1)),
                    sg.InputText(cred["author"], key=f"-WECHAT_AUTHOR_{i}-", size=(45, 1)),
                ]
            )
            wechat_rows.append([sg.Button("删除", key=f"-DELETE_WECHAT_{i}-", disabled=i == 0)])
            wechat_rows.append([sg.HorizontalSeparator()])

        layout = [
            [sg.Text("微信公众号凭证")],
            [
                sg.Column(
                    wechat_rows,
                    key="-WECHAT_CREDENTIALS_COLUMN-",
                    scrollable=True,
                    vertical_scroll_only=True,
                    size=(480, 400),
                    expand_y=True,
                )
            ],
            [
                sg.Text(
                    "Tips：添加凭证、填写后，请先保存再继续添加（至少填写一个）。",
                    size=(70, 1),
                    text_color="gray",
                ),
            ],
            [sg.Button("添加凭证", key="-ADD_WECHAT-")],
            [
                sg.Button("保存配置", key="-SAVE_WECHAT-"),
                sg.Button("恢复默认", key="-RESET_WECHAT-"),
            ],
        ]
        return [[sg.Column(layout, scrollable=False, vertical_scroll_only=False, pad=(0, 0))]]

    def create_api_sub_tab(self, api_name, api_data):
        """创建 API 子 TAB 布局"""
        layout = [
            [sg.Text(f"{api_name.upper()} 配置")],
            [
                sg.Text("KEY名称:", size=(15, 1)),
                sg.InputText(api_data["key"], key=f"-{api_name}_KEY-", disabled=True),
            ],
            [
                sg.Text("API BASE:", size=(15, 1)),
                sg.InputText(api_data["api_base"], key=f"-{api_name}_API_BASE-", disabled=True),
            ],
            [
                sg.Text("KEY索引*:", size=(15, 1)),
                sg.InputText(api_data["key_index"], key=f"-{api_name}_KEY_INDEX-"),
            ],
            [
                sg.Text("API KEY*:", size=(15, 1)),
                sg.InputText(", ".join(api_data["api_key"]), key=f"-{api_name}_API_KEYS-"),
            ],
            [
                sg.Text("模型索引*:", size=(15, 1)),
                sg.InputText(api_data["model_index"], key=f"-{api_name}_MODEL_INDEX-"),
            ],
            [
                sg.Text("模型*:", size=(15, 1)),
                sg.InputText(", ".join(api_data["model"]), key=f"-{api_name}_MODEL-"),
            ],
            [
                sg.Text(
                    "Tips：\n"
                    "1、API KEY和模型都是列表，如果有多个用逗号分隔；\n"
                    "2、索引即使用哪个API KEY、模型（从0开始）；\n"
                    "3、默认已提供较多模型，原则上只需要填写API KEY；\n"
                    "4、只需要填写选中的API类型相应的参数。",
                    size=(70, 5),
                    text_color="gray",
                ),
            ],
        ]
        return layout

    def __default_select_api_tab(self):
        # 设置 API TabGroup 的默认选中子 TAB
        api_data = self.config.get_config()["api"]
        tab_group = self.window["-API_TAB_GROUP-"]
        for tab in tab_group.Widget.tabs():
            tab_text = tab_group.Widget.tab(tab, "text")
            if tab_text == api_data["api_type"]:
                tab_group.Widget.select(tab)
                break
        self.window.refresh()

    def create_api_tab(self):
        """创建 API TAB 布局"""
        api_data = self.config.get_config()["api"]
        layout = [
            [
                sg.Text("API 类型"),
                sg.Combo(
                    self.config.api_list,
                    default_value=api_data["api_type"],
                    key="-API_TYPE-",
                    enable_events=True,
                ),
            ],
            [
                sg.TabGroup(
                    [
                        [sg.Tab("Grok", self.create_api_sub_tab("Grok", api_data["Grok"]))],
                        [sg.Tab("Qwen", self.create_api_sub_tab("Qwen", api_data["Qwen"]))],
                        [sg.Tab("Gemini", self.create_api_sub_tab("Gemini", api_data["Gemini"]))],
                        [
                            sg.Tab(
                                "OpenRouter",
                                self.create_api_sub_tab("OpenRouter", api_data["OpenRouter"]),
                            )
                        ],
                        [sg.Tab("Ollama", self.create_api_sub_tab("Ollama", api_data["Ollama"]))],
                        [
                            sg.Tab(
                                "Deepseek",
                                self.create_api_sub_tab("Deepseek", api_data["Deepseek"]),
                            )
                        ],
                    ],
                    key="-API_TAB_GROUP-",
                )
            ],
            [
                sg.Button("保存配置", key="-SAVE_API-"),
                sg.Button("恢复默认", key="-RESET_API-"),
            ],
        ]
        # 使用 sg.Column 包裹布局，设置 pad=(0, 0) 确保顶部无额外边距
        return [[sg.Column(layout, scrollable=False, vertical_scroll_only=False, pad=(0, 0))]]

    def create_img_api_tab(self):
        """创建图像 API TAB 布局"""
        img_api = self.config.get_config()["img_api"]
        layout = [
            [
                sg.Text("API 类型"),
                sg.Combo(
                    ["picsum", "ali"], default_value=img_api["api_type"], key="-IMG_API_TYPE-"
                ),
            ],
            [sg.Text("阿里 API 配置")],
            [
                sg.Text("API KEY:", size=(15, 1)),
                sg.InputText(img_api["ali"]["api_key"], key="-ALI_API_KEY-"),
            ],
            [
                sg.Text("模型:", size=(15, 1)),
                sg.InputText(img_api["ali"]["model"], key="-ALI_MODEL-"),
            ],
            [sg.Text("Picsum API 配置")],
            [
                sg.Text("API KEY:", size=(15, 1)),
                sg.InputText(img_api["picsum"]["api_key"], key="-PICSUM_API_KEY-", disabled=True),
            ],
            [
                sg.Text("模型:", size=(15, 1)),
                sg.InputText(img_api["picsum"]["model"], key="-PICSUM_MODEL-", disabled=True),
            ],
            [
                sg.Text(
                    "Tips：\n"
                    "1、选择picsum时，无需填写KEY和模型；\n"
                    "2、选择阿里时，均为必填项，API KEY跟QWen相同。",
                    size=(70, 3),
                    text_color="gray",
                ),
            ],
            [
                sg.Button("保存配置", key="-SAVE_IMG_API-"),
                sg.Button("恢复默认", key="-RESET_IMG_API-"),
            ],
        ]
        # 使用 sg.Column 包裹布局，设置 pad=(0, 0) 确保顶部无额外边距
        return [[sg.Column(layout, scrollable=False, vertical_scroll_only=False, pad=(0, 0))]]

    def create_other_tab(self):
        """创建其他 TAB 布局"""
        # 获取模板文件列表（仅文件名，不含扩展名）
        template_files = self.__get_templates()
        template_options = ["随机模板"] + template_files
        # 获取当前配置中的 template 值
        current_template = self.config.template if self.config.template else "随机模板"
        # 检查模板列表是否为空
        is_template_empty = len(template_files) == 0
        layout = [
            [
                sg.Checkbox(
                    "使用模板",
                    default=self.config.use_template
                    and not is_template_empty,  # 仅当模板非空且配置启用时默认选中
                    key="-USE_TEMPLATE-",
                    enable_events=True,
                    disabled=is_template_empty,  # 模板为空时禁用
                )
            ],
            [
                sg.Text("模板:", size=(15, 1)),
                sg.Combo(
                    template_options,
                    default_value=current_template,
                    key="-TEMPLATE-",
                    size=(30, 1),
                    disabled=not self.config.use_template
                    or is_template_empty,  # 模板为空或未启用时禁用
                    readonly=True,
                ),
            ],
            [sg.Checkbox("需要审核者", default=self.config.need_auditor, key="-NEED_AUDITOR-")],
            [sg.Checkbox("压缩模板", default=self.config.use_compress, key="-USE_COMPRESS-")],
            [
                sg.Checkbox(
                    "AIPy搜索缓存",
                    default=self.config.use_search_service,
                    key="-USE_SEARCH_SERVICE-",
                )
            ],
            [
                sg.Text("最大搜索数量:", size=(15, 1)),
                sg.InputText(self.config.aipy_search_max_results, key="-AIPY_SEARCH_MAX_RESULTS-"),
            ],
            [
                sg.Text("最小搜索数量:", size=(15, 1)),
                sg.InputText(self.config.aipy_search_min_results, key="-AIPY_SEARCH_MIN_RESULTS-"),
            ],
            [
                sg.Text(
                    "Tips：\n"
                    "1、使用模板：\n"
                    "    - 使用：\n"
                    "           随机模板：程序随机选取一个并将生成的文章填充到模板里\n"
                    "           选定模板：使用指定的模板\n"
                    "    - 不使用：AI根据要求生成模板，并填充文章\n"
                    "2、需要审核者：\n"
                    "    - 需要：生成文章后执行审核，文章可能更好，但token消耗更高\n"
                    "    - 不需要：生成文章后直接填充模板，消耗低，文章可能略差\n"
                    "3、压缩模板：\n"
                    "    - 压缩：读取模板后压缩，降低token消耗，可能影响AI解析模板\n"
                    "    - 不压缩：token消耗，AI可能理解更精确\n"
                    "4、AIPy搜索缓存：\n"
                    "    - 使用：优先使用本地缓存，降低后续执行搜索任务的token消耗\n"
                    "    - 不使用：可能更精准，但token消耗较高，总体执行成功率降低\n"
                    "5、最大搜索数量：返回的最大搜索结果数量（1 ~ 20）\n"
                    "6、最小搜索数量：返回的最小搜索结果数量（1 ~ 10），越大失败率越高",
                    size=(70, 17),
                    text_color="gray",
                ),
            ],
            [sg.Button("保存配置", key="-SAVE_OTHER-"), sg.Button("恢复默认", key="-RESET_OTHER-")],
        ]
        # 使用 sg.Column 包裹布局，设置 pad=(0, 0) 确保顶部无额外边距
        return [[sg.Column(layout, scrollable=False, vertical_scroll_only=False, pad=(0, 0))]]

    def create_aipy_tab(self):
        """创建 AIPy 配置 TAB 布局，显示选中的 LLM 提供商的所有参数"""
        aipy_config = self.config.aipy_config
        llm_providers = list(aipy_config["llm"].keys())
        default_provider = aipy_config["default_llm_provider"]

        # 获取当前提供商的配置，防止键不存在
        provider_config = aipy_config["llm"].get(default_provider, {})

        layout = [
            [
                sg.Text("工作目录:", size=(15, 1)),
                sg.InputText(aipy_config["workdir"], key="-AIPY_WORKDIR-", size=(45, 1)),
            ],
            [
                sg.Checkbox(
                    "记录控制台输出",
                    default=aipy_config["record"],
                    key="-AIPY_RECORD-",
                ),
            ],
            [
                sg.Text("模型提供商*:", size=(15, 1)),
                sg.Combo(
                    llm_providers,
                    default_value=default_provider,
                    key="-AIPY_DEFAULT_LLM_PROVIDER-",
                    size=(15, 1),
                    readonly=True,
                    enable_events=True,  # 启用事件以动态更新
                ),
            ],
            [
                sg.Text("类型:", size=(15, 1)),
                sg.InputText(
                    provider_config.get("type", ""),
                    key="-AIPY_TYPE-",
                    size=(45, 1),
                    disabled=True,  # 类型通常不可编辑
                ),
            ],
            [
                sg.Text("模型*:", size=(15, 1)),
                sg.InputText(
                    provider_config.get("model", ""),
                    key="-AIPY_MODEL-",
                    size=(45, 1),
                ),
            ],
            [
                sg.Text("API KEY*:", size=(15, 1)),
                sg.InputText(
                    provider_config.get("api_key", ""),
                    key="-AIPY_API_KEY-",
                    size=(45, 1),
                ),
            ],
            [
                sg.Text("Base URL*:", size=(15, 1)),
                sg.InputText(
                    provider_config.get("base_url", ""),
                    key="-AIPY_BASE_URL-",
                    size=(45, 1),
                ),
            ],
            [
                sg.Checkbox(
                    "启用",
                    default=provider_config.get("enable", True),
                    key="-AIPY_ENABLE-",
                ),
            ],
            [
                sg.Checkbox(
                    "默认提供商",
                    default=provider_config.get("default", False),
                    key="-AIPY_DEFAULT-",
                ),
            ],
            [
                sg.Text("超时时间 (秒):", size=(15, 1)),
                sg.InputText(
                    provider_config.get("timeout", 30),
                    key="-AIPY_TIMEOUT-",
                    size=(45, 1),
                ),
            ],
            [
                sg.Text("最大 Tokens:", size=(15, 1)),
                sg.InputText(
                    provider_config.get("max_tokens", 8192),
                    key="-AIPY_MAX_TOKENS-",
                    size=(45, 1),
                ),
            ],
            [
                sg.Text(
                    "Tips：\n"
                    "1、工作目录：AIPy的工作输出目录；\n"
                    "2、记录控制台输出：用于控制流式响应的记录；\n"
                    "3、模型提供商：AIPy使用的LLM 提供商；\n"
                    "4、模型：使用的具体模型名称；\n"
                    "5、API KEY：模型提供商的API KEY（必填）；\n"
                    "6、基础URL：API的基础地址；\n"
                    "7、启用：是否启用该提供商；\n"
                    "8、默认提供商：是否为默认选择的提供商；\n"
                    "9、超时时间：API请求的超时时间（秒）；\n"
                    "10、最大 Tokens：控制生成内容的长度，建议根据模型支持范围设置。",
                    size=(70, 11),
                    text_color="gray",
                ),
            ],
            [
                sg.Button("保存配置", key="-SAVE_AIPY-"),
                sg.Button("恢复默认", key="-RESET_AIPY-"),
            ],
        ]
        return [
            [
                sg.Column(
                    layout,
                    scrollable=False,
                    vertical_scroll_only=False,
                    size=(480, 520),
                    pad=(0, 0),
                )
            ]
        ]

    def create_layout(self):
        """创建主布局"""
        return [
            [
                sg.TabGroup(
                    [
                        [sg.Tab("热搜平台", self.create_platforms_tab(), key="-TAB_PLATFORM-")],
                        [sg.Tab("微信公众号*", self.create_wechat_tab(), key="-TAB_WECHAT-")],
                        [sg.Tab("大模型API*", self.create_api_tab(), key="-TAB_API-")],
                        [sg.Tab("图片生成API", self.create_img_api_tab(), key="-TAB_IMG_API-")],
                        [sg.Tab("其他", self.create_other_tab(), key="-TAB_OTHER-")],
                        [sg.Tab("AIPy*", self.create_aipy_tab(), key="-TAB_AIPY-")],
                    ],
                    key="-TAB_GROUP-",
                )
            ],
        ]

    def clear_tab(self, tab):
        """清空指定 tab 的内容，并清理相关的 key，但不清理 Tab 本身的 key"""
        tab_widget = tab.Widget
        tab_key = tab.Key  # 获取 Tab 本身的 key，例如 "-TAB_PLATFORM-"
        # 收集 tab 内的所有 key，但排除 Tab 本身的 key
        keys_to_remove = []
        # 遍历 window 的 key_dict，检查哪些 key 属于当前 tab
        for key, element in list(self.window.key_dict.items()):  # 使用 list 避免运行时修改字典
            if key == tab_key:  # 跳过 Tab 本身的 key
                continue
            if hasattr(element, "Widget") and element.Widget:
                try:
                    # 获取元素所在的父容器
                    parent = element.Widget
                    # 向上遍历父容器，直到找到顶层容器
                    while parent:
                        if parent == tab_widget:
                            keys_to_remove.append(key)
                            break
                        parent = parent.master  # 继续向上查找父容器
                except Exception as e:  # noqa 841
                    continue

        # 从 window 的 key_dict 中移除这些 key
        for key in keys_to_remove:
            if key in self.window.key_dict:
                del self.window.key_dict[key]

        # 清空 tab 的内容
        for widget in tab_widget.winfo_children():
            widget.destroy()

    def update_tab(self, tab_key, new_layout):
        """更新指定 tab 的内容"""
        # 清空现有内容
        tab = self.window[tab_key]
        self.clear_tab(tab)
        # 直接使用 new_layout（已经是 [[sg.Column(...)]]
        self.window.extend_layout(self.window[tab_key], new_layout)
        # 强制刷新布局，确保内容正确渲染
        self.window.refresh()

    def run(self):
        while True:
            event, values = self.window.read()
            if event in (sg.WIN_CLOSED, "-EXIT-"):
                break

            # 动态启用/禁用 template 下拉列表
            elif event == "-USE_TEMPLATE-":
                self.window["-TEMPLATE-"].update(disabled=not values["-USE_TEMPLATE-"])
                self.window.refresh()

            # 切换API TAB
            elif event == "-API_TYPE-":
                tab_group = self.window["-API_TAB_GROUP-"]
                # 遍历 TabGroup 的子 TAB，找到匹配的标题
                for tab in tab_group.Widget.tabs():
                    tab_text = tab_group.Widget.tab(tab, "text")  # 直接在 Notebook 上调用 tab()
                    if tab_text == values["-API_TYPE-"]:
                        tab_group.Widget.select(tab)
                        break
                self.window.refresh()

            # 添加微信凭证
            elif event == "-ADD_WECHAT-":
                credentials = self.config.wechat_credentials  # 直接使用内存中的 credentials
                credentials.append({"appid": "", "appsecret": "", "author": ""})
                self.wechat_count = len(credentials)
                try:
                    self.update_tab("-TAB_WECHAT-", self.create_wechat_tab())
                    self.window["-WECHAT_CREDENTIALS_COLUMN-"].contents_changed()
                    self.window["-WECHAT_CREDENTIALS_COLUMN-"].Widget.canvas.yview_moveto(1.0)
                    self.window.TKroot.update_idletasks()
                    self.window.TKroot.update()
                    self.window.refresh()
                    self.window["-TAB_WECHAT-"].Widget.update()
                    self.window["-WECHAT_CREDENTIALS_COLUMN-"].Widget.update()
                except Exception as e:
                    sg.popup_error(f"添加凭证失败: {e}", icon=self.__get_icon())
            # 删除微信凭证
            elif event.startswith("-DELETE_WECHAT_"):
                match = re.search(r"-DELETE_WECHAT_(\d+)", event)
                if match:
                    index = int(match.group(1))
                    credentials = self.config.wechat_credentials  # 直接使用内存中的 credentials
                    if 0 <= index < len(credentials):
                        try:
                            credentials.pop(index)
                            self.wechat_count = len(credentials)
                            self.update_tab("-TAB_WECHAT-", self.create_wechat_tab())
                            self.window.TKroot.update_idletasks()
                            self.window.TKroot.update()
                            self.window.refresh()
                            self.window["-TAB_WECHAT-"].Widget.update()
                            self.window["-WECHAT_CREDENTIALS_COLUMN-"].Widget.update()
                        except Exception as e:
                            sg.popup_error(f"删除凭证失败: {e}", icon=self.__get_icon())
                    else:
                        sg.popup_error(f"无效的凭证索引: {index}", icon=self.__get_icon())

            # 保存平台配置
            elif event.startswith("-SAVE_PLATFORMS-"):
                config = self.config.get_config().copy()
                platforms = []
                total_weight = 0.0
                # 动态检测界面上实际的平台数量
                i = 0
                while f"-PLATFORM_NAME_{i}-" in values:
                    try:
                        weight = float(values[f"-PLATFORM_WEIGHT_{i}-"])
                        # 限定weight范围
                        if weight < 0:
                            weight = 0
                            sg.popup_error(
                                f"平台 {values[f'-PLATFORM_NAME_{i}-']} 权重小于0，将被设为0",
                                icon=self.__get_icon(),
                            )
                            # 更新界面上的权重值
                            self.window[f"-PLATFORM_WEIGHT_{i}-"].update(value=str(weight))
                        elif weight > 1:
                            weight = 1
                            sg.popup_error(
                                f"平台 {values[f'-PLATFORM_NAME_{i}-']} 权重大于1，将被设为1",
                                icon=self.__get_icon(),
                            )
                            # 更新界面上的权重值
                            self.window[f"-PLATFORM_WEIGHT_{i}-"].update(value=str(weight))

                        total_weight += weight
                        platforms.append({"name": values[f"-PLATFORM_NAME_{i}-"], "weight": weight})
                    except ValueError:
                        sg.popup_error(
                            f"平台 {values[f'-PLATFORM_NAME_{i}-']} 权重必须是数字",
                            icon=self.__get_icon(),
                        )
                        break
                    i += 1
                else:
                    if total_weight > 1.0:
                        sg.popup(
                            "平台权重之和超过1，将默认选取微博热搜。",
                            icon=self.__get_icon(),
                        )
                    config["platforms"] = platforms
                    if self.config.save_config(config):
                        self.platform_count = len(platforms)  # 同步更新计数器
                        sg.popup(
                            "平台配置已保存",
                            icon=self.__get_icon(),
                        )
                    else:
                        sg.popup_error(
                            self.config.error_message,
                            icon=self.__get_icon(),
                        )

            # 保存微信配置
            elif event.startswith("-SAVE_WECHAT-"):
                config = self.config.get_config().copy()
                credentials = []
                # 遍历窗口中所有可能的微信凭证键
                max_index = -1
                for key in self.window.AllKeysDict:
                    if isinstance(key, str) and key.startswith("-WECHAT_APPID_"):  # 添加类型检查
                        try:
                            # 提取索引，移除尾部连字符
                            index = int(key.split("_")[-1].rstrip("-"))
                            max_index = max(max_index, index)
                        except ValueError:
                            continue  # 跳过无效键
                max_index = max_index + 1 if max_index >= 0 else 0
                i = 0
                while i <= max_index:
                    appid_key = f"-WECHAT_APPID_{i}-"
                    secret_key = f"-WECHAT_SECRET_{i}-"
                    author_key = f"-WECHAT_AUTHOR_{i}-"
                    # 检查键是否存在且元素可见
                    if (
                        appid_key in self.window.AllKeysDict
                        and secret_key in self.window.AllKeysDict
                        and author_key in self.window.AllKeysDict
                        and self.window[appid_key].visible
                    ):
                        credentials.append(
                            {
                                "appid": values.get(appid_key, ""),
                                "appsecret": values.get(secret_key, ""),
                                "author": values.get(author_key, ""),
                            }
                        )
                    i += 1
                config["wechat"]["credentials"] = credentials
                if self.config.save_config(config):
                    self.wechat_count = len(credentials)  # 同步更新计数器
                    # 刷新界面以确保一致
                    self.update_tab("-TAB_WECHAT-", self.create_wechat_tab())
                    self.window.TKroot.update_idletasks()
                    self.window.TKroot.update()
                    self.window.refresh()
                    self.window["-TAB_WECHAT-"].Widget.update()
                    self.window["-WECHAT_CREDENTIALS_COLUMN-"].Widget.update()
                    sg.popup("微信配置已保存", icon=self.__get_icon())
                else:
                    sg.popup_error(self.config.error_message, icon=self.__get_icon())

            # 保存 API 配置
            elif event.startswith("-SAVE_API-"):
                config = self.config.get_config().copy()
                config["api"]["api_type"] = values["-API_TYPE-"]
                for api_name in self.config.api_list:
                    try:
                        model_index = int(values[f"-{api_name}_MODEL_INDEX-"])
                        key_index = int(values[f"-{api_name}_KEY_INDEX-"])
                        models = [
                            m.strip()
                            for m in re.split(r",|，", values[f"-{api_name}_MODEL-"])
                            if m.strip()
                        ]
                        api_keys = [
                            k.strip()
                            for k in re.split(r",|，", values[f"-{api_name}_API_KEYS-"])
                            if k.strip()
                        ]
                        if not api_keys:
                            api_keys = [""]  # 确保至少有一个空密钥
                        if key_index >= len(api_keys):
                            raise ValueError(f"{api_name} API KEY 索引超出范围")
                        if model_index >= len(models):
                            raise ValueError(f"{api_name} 模型索引超出范围")
                        api_data = {
                            "key": values[f"-{api_name}_KEY-"],
                            "key_index": key_index,
                            "api_key": api_keys,
                            "model_index": model_index,
                            "api_base": values[f"-{api_name}_API_BASE-"],
                            "model": models,
                        }
                        config["api"][api_name].update(api_data)
                    except ValueError as e:
                        sg.popup_error(
                            f"{api_name} 配置错误: {e}",
                            icon=self.__get_icon(),
                        )
                        break
                else:
                    if self.config.save_config(config):
                        sg.popup(
                            "API 配置已保存",
                            icon=self.__get_icon(),
                        )
                    else:
                        sg.popup_error(
                            self.config.error_message,
                            icon=self.__get_icon(),
                        )

            # 保存图像 API 配置
            elif event.startswith("-SAVE_IMG_API-"):
                config = self.config.get_config().copy()
                config["img_api"]["api_type"] = values["-IMG_API_TYPE-"]
                config["img_api"]["ali"].update(
                    {"api_key": values["-ALI_API_KEY-"], "model": values["-ALI_MODEL-"]}
                )
                config["img_api"]["picsum"].update(
                    {"api_key": values["-PICSUM_API_KEY-"], "model": values["-PICSUM_MODEL-"]}
                )
                if self.config.save_config(config):
                    sg.popup(
                        "图像 API 配置已保存",
                        icon=self.__get_icon(),
                    )
                else:
                    sg.popup_error(
                        self.config.error_message,
                        icon=self.__get_icon(),
                    )

            # 保存其他配置
            elif event.startswith("-SAVE_OTHER-"):
                config = self.config.get_config().copy()
                config["use_template"] = values["-USE_TEMPLATE-"]
                config["need_auditor"] = values["-NEED_AUDITOR-"]
                config["use_compress"] = values["-USE_COMPRESS-"]
                config["use_search_service"] = values["-USE_SEARCH_SERVICE-"]
                if str(values["-AIPY_SEARCH_MAX_RESULTS-"]).isdigit():
                    input_value = int(values["-AIPY_SEARCH_MAX_RESULTS-"])
                    config["aipy_search_max_results"] = (
                        input_value
                        if 1 < input_value <= 20
                        else self.config.default_config["aipy_search_max_results"]
                    )
                    if not (1 < input_value <= 20):
                        self.window["-AIPY_SEARCH_MAX_RESULTS-"].update(
                            value=self.config.default_config["aipy_search_max_results"]
                        )
                else:
                    config["aipy_search_max_results"] = self.config.default_config[
                        "aipy_search_max_results"
                    ]
                    self.window["-AIPY_SEARCH_MAX_RESULTS-"].update(
                        value=self.config.default_config["aipy_search_max_results"]
                    )

                if str(values["-AIPY_SEARCH_MIN_RESULTS-"]).isdigit():
                    input_value = int(values["-AIPY_SEARCH_MIN_RESULTS-"])
                    config["aipy_search_min_results"] = (
                        input_value
                        if 1 < input_value <= self.config.default_config["aipy_search_max_results"]
                        and input_value
                        < config["aipy_search_max_results"]  # 最大为10且不能比最大值大
                        else self.config.default_config["aipy_search_min_results"]
                    )
                    if not (
                        1 < input_value <= self.config.default_config["aipy_search_max_results"]
                    ):
                        self.window["-AIPY_SEARCH_MIN_RESULTS-"].update(
                            value=self.config.default_config["aipy_search_min_results"]
                        )
                else:
                    config["aipy_search_min_results"] = self.config.default_config[
                        "aipy_search_min_results"
                    ]
                    self.window["-AIPY_SEARCH_MIN_RESULTS-"].update(
                        value=self.config.default_config["aipy_search_min_results"]
                    )
                # 处理 template 保存逻辑
                template_value = values["-TEMPLATE-"]
                config["template"] = "" if template_value == "随机模板" else template_value
                if self.config.save_config(config):
                    sg.popup(
                        "其他配置已保存",
                        icon=self.__get_icon(),
                    )
                else:
                    sg.popup_error(
                        self.config.error_message,
                        icon=self.__get_icon(),
                    )

            # 恢复默认配置 - 平台
            elif event.startswith("-RESET_PLATFORMS-"):
                config = self.config.get_config().copy()
                config["platforms"] = copy.deepcopy(self.config.default_config["platforms"])
                if self.config.save_config(config):
                    self.platform_count = len(config["platforms"])
                    # 清空并重建平台 tab
                    self.update_tab("-TAB_PLATFORM-", self.create_platforms_tab())
                    sg.popup(
                        "已恢复默认平台配置",
                        icon=self.__get_icon(),
                    )
                else:
                    sg.popup_error(
                        self.config.error_message,
                        icon=self.__get_icon(),
                    )

            # 恢复默认配置 - 微信
            elif event.startswith("-RESET_WECHAT-"):
                config = self.config.get_config().copy()
                config["wechat"]["credentials"] = copy.deepcopy(
                    self.config.default_config["wechat"]["credentials"]
                )
                if self.config.save_config(config):
                    self.wechat_count = len(config["wechat"]["credentials"])
                    # 清空并重建微信 tab
                    self.update_tab("-TAB_WECHAT-", self.create_wechat_tab())
                    sg.popup(
                        "已恢复默认微信配置",
                        icon=self.__get_icon(),
                    )
                else:
                    sg.popup_error(
                        self.config.error_message,
                        icon=self.__get_icon(),
                    )

            # 恢复默认配置 - API
            elif event.startswith("-RESET_API-"):
                config = self.config.get_config().copy()
                config["api"] = copy.deepcopy(self.config.default_config["api"])
                if self.config.save_config(config):
                    # 清空并重建 API tab
                    self.update_tab("-TAB_API-", self.create_api_tab())
                    self.__default_select_api_tab()
                    sg.popup(
                        "已恢复默认API配置",
                        icon=self.__get_icon(),
                    )
                else:
                    sg.popup_error(
                        self.config.error_message,
                        icon=self.__get_icon(),
                    )

            # 恢复默认配置 - 图像 API
            elif event.startswith("-RESET_IMG_API-"):
                config = self.config.get_config().copy()
                config["img_api"] = copy.deepcopy(self.config.default_config["img_api"])
                if self.config.save_config(config):
                    # 清空并重建图像 API tab
                    self.update_tab("-TAB_IMG_API-", self.create_img_api_tab())
                    sg.popup(
                        "已恢复默认图像API配置",
                        icon=self.__get_icon(),
                    )
                else:
                    sg.popup_error(
                        self.config.error_message,
                        icon=self.__get_icon(),
                    )

            # 恢复默认配置 - 其他
            elif event.startswith("-RESET_OTHER-"):
                config = self.config.get_config().copy()
                config["use_template"] = self.config.default_config["use_template"]
                config["need_auditor"] = self.config.default_config["need_auditor"]
                config["use_compress"] = self.config.default_config["use_compress"]
                config["use_search_service"] = self.config.default_config["use_search_service"]
                config["aipy_search_max_results"] = self.config.default_config[
                    "aipy_search_max_results"
                ]
                config["aipy_search_min_results"] = self.config.default_config[
                    "aipy_search_min_results"
                ]
                config["template"] = self.config.default_config["template"]
                if self.config.save_config(config):
                    self.update_tab("-TAB_OTHER-", self.create_other_tab())
                    sg.popup(
                        "已恢复默认其他配置",
                        icon=self.__get_icon(),
                    )
                else:
                    sg.popup_error(
                        self.config.error_message,
                        icon=self.__get_icon(),
                    )

            # 动态更新 AIPy 提供商的所有参数
            elif event == "-AIPY_DEFAULT_LLM_PROVIDER-":
                try:
                    selected_provider = values["-AIPY_DEFAULT_LLM_PROVIDER-"]
                    # 获取新选中的提供商的配置
                    provider_config = self.config.aipy_config["llm"].get(selected_provider, {})
                    # 更新所有参数的输入框
                    self.window["-AIPY_TYPE-"].update(value=provider_config.get("type", ""))
                    self.window["-AIPY_MODEL-"].update(value=provider_config.get("model", ""))
                    self.window["-AIPY_API_KEY-"].update(value=provider_config.get("api_key", ""))
                    self.window["-AIPY_BASE_URL-"].update(value=provider_config.get("base_url", ""))
                    self.window["-AIPY_ENABLE-"].update(value=provider_config.get("enable", True))
                    self.window["-AIPY_DEFAULT-"].update(
                        value=provider_config.get("default", False)
                    )
                    self.window["-AIPY_TIMEOUT-"].update(value=provider_config.get("timeout", 30))
                    self.window["-AIPY_MAX_TOKENS-"].update(
                        value=provider_config.get("max_tokens", 8192)
                    )
                    self.window.refresh()
                except Exception as e:
                    sg.popup_error(f"更新 AIPy 提供商配置失败: {e}", icon=self.__get_icon())

            # 保存 AIPy 配置
            elif event.startswith("-SAVE_AIPY-"):
                aipy_config = self.config.aipy_config.copy()
                try:
                    selected_provider = values["-AIPY_DEFAULT_LLM_PROVIDER-"]
                    aipy_config["default_llm_provider"] = selected_provider
                    aipy_config["workdir"] = values["-AIPY_WORKDIR-"]
                    aipy_config["record"] = values["-AIPY_RECORD-"]

                    # 更新选中的提供商的所有参数
                    aipy_config["llm"][selected_provider]["type"] = values.get("-AIPY_TYPE-", "")
                    aipy_config["llm"][selected_provider]["model"] = values.get("-AIPY_MODEL-", "")
                    aipy_config["llm"][selected_provider]["api_key"] = values.get(
                        "-AIPY_API_KEY-", ""
                    )
                    aipy_config["llm"][selected_provider]["base_url"] = values.get(
                        "-AIPY_BASE_URL-", ""
                    )
                    aipy_config["llm"][selected_provider]["enable"] = values.get(
                        "-AIPY_ENABLE-", True
                    )
                    aipy_config["llm"][selected_provider]["default"] = values.get(
                        "-AIPY_DEFAULT-", False
                    )
                    aipy_config["llm"][selected_provider]["timeout"] = int(
                        values.get("-AIPY_TIMEOUT-", 30)
                    )
                    aipy_config["llm"][selected_provider]["max_tokens"] = int(
                        values.get("-AIPY_MAX_TOKENS-", 8192)
                    )

                    if self.config.save_config(self.config.get_config(), aipy_config):
                        sg.popup("AIPy 配置已保存", icon=self.__get_icon())
                    else:
                        sg.popup_error(self.config.error_message, icon=self.__get_icon())
                except ValueError:
                    sg.popup_error("超时时间或最大 Tokens 必须是整数", icon=self.__get_icon())

            # 恢复默认 AIPy 配置
            elif event.startswith("-RESET_AIPY-"):
                aipy_config = copy.deepcopy(self.config.default_aipy_config)
                if self.config.save_config(self.config.get_config(), aipy_config):
                    self.update_tab("-TAB_AIPY-", self.create_aipy_tab())
                    sg.popup("已恢复默认 AIPy 配置", icon=self.__get_icon())
                else:
                    sg.popup_error(self.config.error_message, icon=self.__get_icon())

        self.window.close()


def gui_start():
    ConfigEditor().run()
