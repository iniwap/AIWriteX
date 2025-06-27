import os
import yaml
import threading
import tomlkit

from aipyapp.aipy.config import ConfigManager
from aipyapp.main import get_default_config

from src.ai_auto_wxgzh.utils import comm
from src.ai_auto_wxgzh.utils import utils

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
        self.config = None
        self.aipy_config = None
        self._aipy_settings = None  # 实际使用
        self.error_message = None
        self._config_path = self.__get_config_path()
        self._config_aipy_path = self.__get_config_path("aipyapp.toml")
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
            "wechat": {
                "credentials": [
                    {"appid": "", "appsecret": "", "author": ""},
                    {"appid": "", "appsecret": "", "author": ""},
                    {"appid": "", "appsecret": "", "author": ""},
                ]
            },
            "api": {
                "api_type": "OpenRouter",
                "Grok": {
                    "key": "XAI_API_KEY",
                    "key_index": 0,
                    "api_key": ["", ""],
                    "model_index": 0,
                    "model": ["xai/grok-2-latest"],
                    "api_base": "https://api.x.ai/v1/chat/completions",
                },
                "Qwen": {
                    "key": "OPENAI_API_KEY",
                    "key_index": 0,
                    "api_key": ["", ""],
                    "model_index": 3,
                    "model": [
                        "openai/deepseek-v3",
                        "openai/deepseek-r1",
                        "qwen-max-latest",
                        "openai/qwen-max",
                        "openai/qwen-vl-plus",
                        "openai/qwen-plus",
                    ],
                    "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                },
                "Gemini": {
                    "key": "GEMINI_API_KEY",
                    "key_index": 0,
                    "api_key": ["", ""],
                    "model_index": 0,
                    "model": [
                        "gemini-1.5-flash",
                        "gemini-1.5-pro",
                        "gemini-2.0-flash-lite-preview-02-05",
                        "gemini-2.0-flash",
                    ],
                    "api_base": "https://generativelanguage.googleapis.com",
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
                    "key": "OPENAI_API_KEY",
                    "key_index": 0,
                    "api_key": ["", ""],
                    "model_index": 0,
                    "model": [
                        "openai/deepseek-v3",
                        "openai/deepseek-r1",
                        "openai/deepseek-chat",
                        "openai/deepseek-v3-0324",
                        "openai/deepseek-chat-v3-0324",
                    ],
                    "api_base": "https://api.deepseek.com/v1",
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
            "need_auditor": False,
            "use_compress": True,
            "use_search_service": False,
            "aipy_search_max_results": 10,
            "aipy_search_min_results": 1,
            "min_article_len": 1000,
            "max_article_len": 2000,
            "auto_publish": True,
        }
        self.default_aipy_config = {
            "workdir": "aipy_work",
            "record": True,
            "max_tokens": 4096,
            "default_llm_provider": "openrouter",
            "llm": {
                "openrouter": {
                    "type": "openai",
                    "model": "deepseek/deepseek-chat-v3-0324:free",
                    "api_key": "",
                    "base_url": "https://openrouter.ai/api/v1",
                    "enable": True,
                    "default": True,
                    "timeout": 30,
                    "max_tokens": 8192,
                },
                "grok": {
                    "type": "openai",
                    "model": "grok-3-mini",
                    "api_key": "",
                    "base_url": "https://api.x.ai/v1/",
                    "enable": True,
                    "default": False,
                    "timeout": 30,
                    "max_tokens": 8192,
                },
                "qwen": {
                    "type": "openai",
                    "model": "openai/qwen-max",
                    "api_key": "",
                    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                    "enable": True,
                    "default": False,
                    "timeout": 30,
                    "max_tokens": 8192,
                },
                "gemini": {
                    "type": "openai",
                    "model": "gemini-2.5-pro-exp-03-25",
                    "api_key": "",
                    "base_url": "https://generativelanguage.googleapis.com/v1beta/",
                    "enable": True,
                    "default": False,
                    "timeout": 30,
                    "max_tokens": 8192,
                },
                "ollama": {
                    "type": "ollama",
                    "model": "llama3",
                    "api_key": "",
                    "base_url": "http://localhost:11434",
                    "enable": True,
                    "default": False,
                    "timeout": 30,
                    "max_tokens": 8192,
                },
                "deepseek": {
                    "type": "openai",
                    "model": "openai/deepseek-chat-v3-0324",
                    "api_key": "",
                    "base_url": "https://api.deepseek.com",
                    "enable": True,
                    "default": False,
                    "timeout": 30,
                    "max_tokens": 8192,
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
    def need_auditor(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            return self.config["need_auditor"]

    @property
    def use_compress(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            return self.config["use_compress"]

    @property
    def use_search_service(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            return self.config["use_search_service"]

    @property
    def aipy_search_max_results(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            return self.config["aipy_search_max_results"]

    @property
    def aipy_search_min_results(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            return self.config["aipy_search_min_results"]

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
    def auto_publish(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")
            return self.config["auto_publish"]

    @property
    def api_list(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")

            api_keys_list = list(self.config["api"].keys())
            # 移除 "api_type" 这个键，得到您需要的列表
            if "api_type" in api_keys_list:
                api_keys_list.remove("api_type")

            return api_keys_list

    # aipy 配置
    @property
    def aipy_default_llm_provider(self):
        with self._lock:
            if self.aipy_config is None:
                raise ValueError("配置未加载")
            return self.aipy_config["default_llm_provider"]

    @property
    def aipy_api_key(self):
        with self._lock:
            if self.aipy_config is None:
                raise ValueError("配置未加载")
            return self.aipy_config["llm"][self.aipy_config["default_llm_provider"]]["api_key"]

    def __get_config_path(self, file_name="config.yaml"):
        # 配置文件不是资源，所以需要重新创建，也可以从资源先提取再创建，不能直接使用
        config_path = f"config/{file_name}"
        if not utils.get_is_release_ver():
            config_path = os.path.join(os.path.dirname(__file__), file_name)
        else:
            # 将资源文件复制到config目录下
            res_config_path = utils.get_res_path(config_path)
            utils.copy_file(res_config_path, config_path)

        return config_path

    def load_config(self):
        """加载配置，从 config.yaml 或默认配置，不验证"""
        with self._lock:
            ret = True
            if os.path.exists(self._config_path):
                try:
                    with open(self._config_path, "r", encoding="utf-8") as f:
                        self.config = yaml.safe_load(f)
                        if self.config is None:
                            self.config = self.default_config
                except Exception as e:
                    self.error_message = f"加载 config.yaml 失败: {e}"
                    comm.send_update("error", self.error_message)
                    self.config = self.default_config
                    ret = False
            else:
                self.config = self.default_config

            if os.path.exists(self._config_aipy_path):
                try:
                    with open(self._config_aipy_path, "r", encoding="utf-8") as f:
                        self.aipy_config = tomlkit.parse(f.read())
                        if self.aipy_config is None:
                            self.aipy_config = self.default_aipy_config
                except Exception as e:
                    self.error_message = f"加载 aipyapp.toml 失败: {e}"
                    comm.send_update("error", self.error_message)
                    self.aipy_config = self.default_aipy_config
                    ret = False
            else:
                self.aipy_config = self.default_aipy_config

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
                    self.error_message = "未配置有效的微信公众号appid和appsecret，请打开配置填写"
                    return False

            # 检查是否配置了aipy api_key
            if not self.aipy_api_key:
                self.error_message = "AIPy未配置有效的llm提供商的api_key"
                return False

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

    def get_aipy_config(self):
        with self._lock:
            if self.aipy_config is None:
                raise ValueError("配置未加载")
            return self.aipy_config

    def __update_aipy_config(self):
        file_abs_path = os.path.abspath(self._config_aipy_path)
        dir_path = os.path.dirname(file_abs_path)
        conf = ConfigManager(get_default_config(), dir_path)
        conf.check_config()
        settings = conf.get_config()

        # 软件模式直接安装
        if utils.get_is_release_ver():
            settings.auto_install = True
        else:
            settings.auto_install = False

        self._aipy_settings = settings

    def get_aipy_settings(self):
        # 如果有变化，需要重新加载，在更新保存的地方加载
        with self._lock:
            if self._aipy_settings is None:
                self.__update_aipy_config()

            return self._aipy_settings

    def save_config(self, config, aipy_config=None):
        """保存配置到 config.yaml，不验证"""
        with self._lock:
            ret = True
            self.config = config
            try:
                with open(self._config_path, "w", encoding="utf-8") as f:
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
                comm.send_update("error", self.error_message)
                ret = False

            # 如果传递了
            if aipy_config is not None:
                self.aipy_config = aipy_config
                try:
                    with open(self._config_aipy_path, "w", encoding="utf-8") as f:
                        f.write(tomlkit.dumps(self.aipy_config))

                    self.__update_aipy_config()  # 更新配置
                except Exception as e:
                    self.error_message = f"保存 aipyapp.toml 失败: {e}"
                    comm.send_update("error", self.error_message)
                    ret = False

            return ret

    def get_config_path(self):
        return self._config_path

    def get_aipy_config_path(self):
        return self._config_aipy_path
