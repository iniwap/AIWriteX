from typing import Any, Dict
import os
import yaml
import threading
import tomlkit

from src.ai_write_x.utils import log
from src.ai_write_x.utils import utils
from src.ai_write_x.utils.path_manager import PathManager

# 默认分类配置
DEFAULT_TEMPLATE_CATEGORIES = {
    "TechDigital": "科技数码",
    "FinanceInvestment": "财经投资",
    "EducationLearning": "教育学习",
    "HealthWellness": "健康养生",
    "FoodTravel": "美食旅行",
    "FashionLifestyle": "时尚生活",
    "CareerDevelopment": "职场发展",
    "EmotionPsychology": "情感心理",
    "EntertainmentGossip": "娱乐八卦",
    "NewsCurrentAffairs": "新闻时事",
    "Others": "其他",
}


# 自定义 Dumper，仅调整数组子元素缩进
class IndentedDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        # 强制数组子元素（-）缩进 2 个空格
        return super().increase_indent(flow, False)


class Config:
    _instance = None
    _lock = threading.Lock()
    # _lock = threading.RLock()  # 可重入锁

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self.config: Dict[Any, Any] = {}
        self.aiforge_config = None
        self.error_message = None
        self.config_path = self.__get_config_path()
        self.config_aiforge_path = self.__get_config_path("aiforge.toml")
        self.default_config = {
            "platforms": [
                {"name": "微博", "weight": 0.3},
                {"name": "抖音", "weight": 0.20},
                {"name": "小红书", "weight": 0.12},
                {"name": "今日头条", "weight": 0.1},
                {"name": "百度热点", "weight": 0.08},
                {"name": "哔哩哔哩", "weight": 0.06},
                {"name": "快手", "weight": 0.05},
                {"name": "虎扑", "weight": 0.05},
                {"name": "豆瓣小组", "weight": 0.02},
                {"name": "澎湃新闻", "weight": 0.01},
                {"name": "知乎热榜", "weight": 0.01},
            ],
            "publish_platform": "wechat",
            "wechat": {
                "credentials": [
                    {
                        "appid": "",
                        "appsecret": "",
                        "author": "",
                        "call_sendall": False,
                        "sendall": True,
                        "tag_id": 0,
                    },
                    {
                        "appid": "",
                        "appsecret": "",
                        "author": "",
                        "call_sendall": False,
                        "sendall": True,
                        "tag_id": 0,
                    },
                    {
                        "appid": "",
                        "appsecret": "",
                        "author": "",
                        "call_sendall": False,
                        "sendall": True,
                        "tag_id": 0,
                    },
                ]
            },
            "api": {
                "api_type": "OpenRouter",
                "Grok": {
                    "key": "XAI_API_KEY",
                    "key_index": 0,
                    "api_key": ["", ""],
                    "model_index": 0,
                    "model": ["xai/grok-3"],
                    "api_base": "https://api.x.ai/v1/chat/completions",
                },
                "Qwen": {
                    "key": "OPENAI_API_KEY",
                    "key_index": 0,
                    "api_key": ["", ""],
                    "model_index": 0,
                    "model": ["openai/qwen-plus"],
                    "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                },
                "Gemini": {
                    "key": "GEMINI_API_KEY",
                    "key_index": 0,
                    "api_key": ["", ""],
                    "model_index": 0,
                    "model": [
                        "gemini/gemini-1.5-flash",
                        "gemini/gemini-1.5-pro",
                        "gemini/gemini-2.0-flash",
                    ],
                    "api_base": "https://generativelanguage.googleapis.com/v1beta/openai/",
                },
                "OpenRouter": {
                    "key": "OPENROUTER_API_KEY",
                    "model_index": 0,
                    "key_index": 0,
                    "api_key": ["", ""],
                    "model": [
                        "openrouter/deepseek/deepseek-chat-v3-0324:free",
                        "openrouter/deepseek/deepseek-r1:free",
                        "openrouter/deepseek/deepseek-chat:free",
                        "openrouter/qwen/qwq-32b:free",
                        "openrouter/google/gemini-2.0-flash-lite-preview-02-05:free",
                        "openrouter/google/gemini-2.0-flash-thinking-exp:free",
                    ],
                    "api_base": "https://openrouter.ai/api/v1",
                },
                "Ollama": {
                    "key": "OPENAI_API_KEY",
                    "model_index": 0,
                    "key_index": 0,
                    "api_key": ["tmp-key", ""],
                    "model": ["ollama/deepseek-r1:14b", "ollama/deepseek-r1:7b"],
                    "api_base": "http://localhost:11434",
                },
                "Deepseek": {
                    "key": "DEEPSEEK_API_KEY",
                    "key_index": 0,
                    "api_key": [""],
                    "model_index": 0,
                    "model": [
                        "deepseek/deepseek-chat",
                        "deepseek/deepseek-reasoner",
                    ],
                    "api_base": "https://api.deepseek.com/v1",
                },
                "SiliconFlow": {
                    "key": "SILICONFLOW_API_KEY",
                    "key_index": 0,
                    "api_key": ["", ""],
                    "model_index": 0,
                    "model": [
                        "siliconflow/deepseek-chat",
                        "siliconflow/qwen-turbo",
                        "siliconflow/glm-4-chat",
                        "siliconflow/yi-lightning",
                    ],
                    "api_base": "https://api.siliconflow.cn/v1",
                },
            },
            "img_api": {
                "api_type": "picsum",
                "ali": {"api_key": "", "model": "wanx2.0-t2i-turbo"},
                "picsum": {"api_key": "", "model": ""},
            },
            "use_template": True,
            "template_category": "",
            "template": "",
            "use_compress": True,
            "aiforge_search_max_results": 10,
            "aiforge_search_min_results": 1,
            "min_article_len": 1000,
            "max_article_len": 2000,
            "auto_publish": True,
            "article_format": "html",
            "format_publish": True,
            "creative_mode": "",
            "creative_config": {
                "style_transform": {
                    "enabled": False,
                    "style_target": "shakespeare",
                    "available_styles": [
                        "shakespeare",
                        "detective",
                        "scifi",
                        "classical_poetry",
                        "modern_poetry",
                        "academic",
                        "news",
                    ],
                },
                "time_travel": {
                    "enabled": False,
                    "time_perspective": "ancient",
                    "available_perspectives": ["ancient", "modern", "future"],
                },
                "role_play": {
                    "enabled": False,
                    "role_character": "libai",
                    "available_roles": [
                        # 古典诗词
                        "libai",
                        "dufu",
                        "sushi",
                        "liqingzhao",
                        # 古典小说
                        "caoxueqin",
                        "shinaian",
                        "wuchengen",
                        "pusonglin",
                        # 现代文学
                        "luxun",
                        "laoshe",
                        "bajin",
                        "qianjunru",
                        # 武侠小说
                        "jinyong",
                        "gulongxia",
                        # 新闻主播/评论员
                        "baiyansong",
                        "cuiyongyuan",
                        "yanglan",
                        "luyu",
                        # 音乐人
                        "zhoujielun",
                        "denglijun",
                        "lironghao",
                        # 相声曲艺
                        "guodegang",
                        "zhaobenshang",
                        # 自定义
                        "custom",
                    ],
                    "custom_character": "",
                },
                "combination_mode": False,
            },
        }
        self.default_aiforge_config = {
            "locale": "zh",
            "max_rounds": 5,
            "max_tokens": 4096,
            "default_llm_provider": "openrouter",
            "llm": {
                "openrouter": {
                    "type": "openai",
                    "model": "deepseek/deepseek-chat-v3-0324:free",
                    "api_key": "",
                    "base_url": "https://openrouter.ai/api/v1",
                    "timeout": 30,
                    "max_tokens": 8192,
                },
                "grok": {
                    "type": "grok",
                    "model": "xai/grok-3",
                    "api_key": "",
                    "base_url": "https://api.x.ai/v1/chat/completions",
                    "timeout": 30,
                    "max_tokens": 8192,
                },
                "qwen": {
                    "type": "openai",
                    "model": "openai/qwen-plus",
                    "api_key": "",
                    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                    "timeout": 30,
                    "max_tokens": 8192,
                },
                "gemini": {
                    "type": "gemini",
                    "model": "gemini-2.5-pro-exp-03-25",
                    "api_key": "",
                    "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
                    "timeout": 30,
                    "max_tokens": 8192,
                },
                "ollama": {
                    "type": "ollama",
                    "model": "ollama/deepseek-r1:14b",
                    "api_key": "",
                    "base_url": "http://localhost:11434",
                    "timeout": 30,
                    "max_tokens": 8192,
                },
                "deepseek": {
                    "type": "deepseek",
                    "model": "deepseek-chat",
                    "api_key": "",
                    "base_url": "https://api.deepseek.com",
                    "timeout": 30,
                    "max_tokens": 8192,
                },
            },
            "cache": {
                "code": {
                    "enabled": True,
                    "max_modules": 20,
                    "failure_threshold": 0.8,
                    "max_age_days": 30,
                    "cleanup_interval": 10,
                },
            },
        }

        # 全局变量
        self._ui_mode = False

        # 自定义话题和文章参考链接，根据是否为空判断是否自定义
        self.custom_topic = ""  # 自定义话题（字符串）
        self.urls = []  # 参考链接（列表）
        self.reference_ratio = 0  # 文章借鉴比例[0-1]
        self.custom_template_category = ""  # 自定义话题时，模板分类
        self.custom_template = ""  # 自定义话题时，模板
        self.current_preview_cover = ""  # 当前设置的封面

        self._process_log_queue = None

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @property
    def ui_mode(self):  # Getter
        return self._ui_mode

    @ui_mode.setter
    def ui_mode(self, value):  # Setter with validation
        if not isinstance(value, bool):
            raise ValueError("ui_mode must be a boolean")
        self._ui_mode = value

    @property
    def platforms(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            return self.config["platforms"]

    @property
    def wechat_credentials(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            return self.config["wechat"]["credentials"]

    @property
    def api_type(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            return self.config["api"]["api_type"]

    @property
    def api_key_name(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            return self.config["api"][self.config["api"]["api_type"]]["key"]

    @property
    def api_key(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            api_key = self.config["api"][self.config["api"]["api_type"]]["api_key"]
            key_index = self.config["api"][self.config["api"]["api_type"]]["key_index"]
            return api_key[key_index]

    @property
    def api_model(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            model = self.config["api"][self.config["api"]["api_type"]]["model"]
            model_index = self.config["api"][self.config["api"]["api_type"]]["model_index"]
            return model[model_index]

    @property
    def api_apibase(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            return self.config["api"][self.config["api"]["api_type"]]["api_base"]

    @property
    def img_api_type(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            return self.config["img_api"]["api_type"]

    @property
    def img_api_key(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            return self.config["img_api"][self.config["img_api"]["api_type"]]["api_key"]

    @property
    def img_api_model(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            return self.config["img_api"][self.config["img_api"]["api_type"]]["model"]

    @property
    def use_template(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            return self.config["use_template"]

    @property
    def template_category(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            return self.config["template_category"]

    @property
    def template(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            return self.config["template"]

    @property
    def use_compress(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            return self.config["use_compress"]

    @property
    def aiforge_search_max_results(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            return self.config["aiforge_search_max_results"]

    @property
    def aiforge_search_min_results(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            return self.config["aiforge_search_min_results"]

    @property
    def min_article_len(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            return self.config["min_article_len"]

    @property
    def max_article_len(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            return self.config["max_article_len"]

    @property
    def article_format(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            return self.config["article_format"]

    @property
    def auto_publish(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            return self.config["auto_publish"]

    @property
    def format_publish(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            return self.config["format_publish"]

    @property
    def publish_platform(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            return self.config["publish_platform"]

    @property
    def creative_mode(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            return self.config["creative_mode"]

    @property
    def api_list(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")

            api_keys_list = list(self.config["api"].keys())
            if "api_type" in api_keys_list:
                api_keys_list.remove("api_type")

            return api_keys_list

    @property
    def api_list_display(self):
        """返回用于界面显示的API类型列表"""
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")

            api_keys_list = list(self.config["api"].keys())
            if "api_type" in api_keys_list:
                api_keys_list.remove("api_type")

            # 转换为显示名称
            display_list = []
            for api_type in api_keys_list:
                if api_type == "SiliconFlow":
                    display_list.append("硅基流动")
                else:
                    display_list.append(api_type)

            return display_list

    # aiforge 配置
    @property
    def aiforge_default_llm_provider(self):
        with self._lock:
            if self.aiforge_config is None:
                raise ValueError("配置未加载")
            return self.aiforge_config["default_llm_provider"]

    @property
    def aiforge_api_key(self):
        with self._lock:
            if self.aiforge_config is None:
                raise ValueError("配置未加载")
            return self.aiforge_config["llm"][self.aiforge_config["default_llm_provider"]][
                "api_key"
            ]

    def __get_config_path(self, file_name="config.yaml"):
        """获取配置文件路径并确保文件存在"""

        config_path = str(PathManager.get_config_path(file_name))

        if utils.get_is_release_ver():
            # 发布模式：使用PathManager获取跨平台可写路径
            # 将资源文件复制到配置目录下（保留原有逻辑）
            res_config_path = utils.get_res_path(f"config/{file_name}")
            if os.path.exists(res_config_path):
                utils.copy_file(res_config_path, config_path)

        return config_path

    def get_sendall_by_appid(self, target_appid):
        for cred in self.config["wechat"]["credentials"]:
            if cred["appid"] == target_appid:
                return cred["sendall"]
        return False

    def get_call_sendall_by_appid(self, target_appid):
        for cred in self.config["wechat"]["credentials"]:
            if cred["appid"] == target_appid:
                return cred["call_sendall"]
        return False

    def get_tagid_by_appid(self, target_appid):
        for cred in self.config["wechat"]["credentials"]:
            if cred["appid"] == target_appid:
                return cred["tag_id"]
        return False

    def load_config(self):
        """加载配置，从 config.yaml 或默认配置，不验证"""
        with self._lock:
            ret = True
            if os.path.exists(self.config_path):
                try:
                    with open(self.config_path, "r", encoding="utf-8") as f:
                        self.config = yaml.safe_load(f)
                        if self.config is None:
                            self.config = self.default_config
                except Exception as e:
                    self.error_message = f"加载 config.yaml 失败: {e}"
                    log.print_log(self.error_message, "error")
                    self.config = self.default_config
                    ret = False
            else:
                self.config = self.default_config

            if os.path.exists(self.config_aiforge_path):
                try:
                    with open(self.config_aiforge_path, "r", encoding="utf-8") as f:
                        self.aiforge_config = tomlkit.parse(f.read())
                        if self.aiforge_config is None:
                            self.aiforge_config = self.default_aiforge_config
                except Exception as e:
                    self.error_message = f"加载 aiforge.toml 失败: {e}"
                    log.print_log(self.error_message, "error")
                    self.aiforge_config = self.default_aiforge_config
                    ret = False
            else:
                self.aiforge_config = self.default_aiforge_config

            return ret

    def validate_config(self):
        """验证配置，仅在 CrewAI 执行时调用"""
        try:
            if self.api_key == "":
                self.error_message = f"未配置API KEY，请打开配置填写{self.api_type}的api_key"
                return False

            if self.api_model == "":
                self.error_message = f"未配置Model，请打开配置填写{self.api_type}的model"
                return False

            if self.img_api_type != "picsum":
                if self.img_api_key == "":
                    self.error_message = (
                        f"未配置图片生成模型的API KEY，请打开配置填写{self.img_api_type}的api_key"
                    )
                    return False
                elif self.img_api_model == "":
                    self.error_message = (
                        f"未配置图片生成的模型，请打开配置填写{self.img_api_type}的model"
                    )
                    return False

            # 只有自动发布才需要检验公众号配置
            if self.auto_publish:
                valid_cred = any(
                    cred["appid"] and cred["appsecret"] for cred in self.wechat_credentials
                )
                if not valid_cred:
                    self.error_message = "【自动发布】时，需配置微信公众号appid和appsecret"
                    return False

            # 检查是否配置了aiforge api_key
            if not self.aiforge_api_key:
                log.print_log("AIForge未配置有效的llm提供商的api_key，将不使用搜索功能")

            total_weight = sum(platform["weight"] for platform in self.platforms)
            if abs(total_weight - 1.0) > 0.01:
                self.error_message = f"平台权重之和 {total_weight} 不等于 1"
                return True  # 这里可以不失败，会默认使用微博

            return True

        except Exception as e:
            self.error_message = f"配置验证失败: {e}"
            return False

    def get_config(self):
        """获取配置，不验证"""
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            return self.config

    def save_config(self, config, aiforge_config=None):
        """保存配置到 config.yaml，不验证"""
        with self._lock:
            ret = True
            self.config = config
            try:
                with open(self.config_path, "w", encoding="utf-8") as f:
                    yaml.dump(
                        config,
                        f,
                        Dumper=IndentedDumper,
                        allow_unicode=True,
                        sort_keys=False,
                        default_flow_style=False,
                        indent=2,
                    )
            except Exception as e:
                self.error_message = f"保存 config.yaml 失败: {e}"
                log.print_log(self.error_message, "error")
                ret = False

            # 如果传递了
            if aiforge_config is not None:
                self.aiforge_config = aiforge_config
                try:
                    with open(self.config_aiforge_path, "w", encoding="utf-8") as f:
                        f.write(tomlkit.dumps(self.aiforge_config))

                except Exception as e:
                    self.error_message = f"保存 aiforge.toml 失败: {e}"
                    log.print_log(self.error_message, "error")
                    ret = False

            return ret
