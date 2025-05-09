import os
import yaml
import threading
from src.ai_auto_wxgzh.utils import comm
from src.ai_auto_wxgzh.utils import utils


# 自定义 Dumper，仅调整数组子元素缩进
class IndentedDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        # 强制数组子元素（-）缩进 2 个空格
        return super().increase_indent(flow, False)


class Config:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self.config = None
        self.error_message = None
        self._config_path = self.__get_config_path()
        self.default_config = {
            "platforms": [
                {"name": "微博", "weight": 0.3},
                {"name": "抖音", "weight": 0.25},
                {"name": "哔哩哔哩", "weight": 0.12},
                {"name": "知乎热榜", "weight": 0.10},
                {"name": "百度热点", "weight": 0.08},
                {"name": "今日头条", "weight": 0.07},
                {"name": "虎扑", "weight": 0.05},
                {"name": "豆瓣小组", "weight": 0.02},
                {"name": "澎湃新闻", "weight": 0.01},
            ],
            "wechat": {
                "credentials": [
                    {"appid": "", "appsecret": "", "author": "作者01"},
                    {"appid": "", "appsecret": "", "author": "作者02"},
                    {"appid": "", "appsecret": "", "author": "作者03"},
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
            },
            "img_api": {
                "api_type": "picsum",
                "ali": {"api_key": "", "model": "wanx2.0-t2i-turbo"},
                "picsum": {"api_key": "", "model": ""},
            },
            "use_template": True,
            "template": "",
            "need_auditor": False,
        }

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

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
    def api_list(self):
        with self._lock:
            if self.config is None:
                raise ValueError("配置未加载")

            api_keys_list = list(self.config["api"].keys())
            # 移除 "api_type" 这个键，得到您需要的列表
            if "api_type" in api_keys_list:
                api_keys_list.remove("api_type")

            return api_keys_list

    def __get_config_path(self):
        # 配置文件不是资源，所以需要重新创建，也可以从资源先提取再创建，不能直接使用
        config_path = "config/config.yaml"
        if not utils.get_is_release_ver():
            config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        else:
            # 将资源文件复制到config目录下
            res_config_path = utils.get_res_path("config/config.yaml")
            utils.copy_file(res_config_path, config_path)

        return config_path

    def load_config(self):
        """加载配置，从 config.yaml 或默认配置，不验证"""
        with self._lock:
            if os.path.exists(self._config_path):
                try:
                    with open(self._config_path, "r", encoding="utf-8") as f:
                        self.config = yaml.safe_load(f)
                        if self.config is None:
                            self.config = self.default_config
                    return True
                except Exception as e:
                    self.error_message = f"加载 config.yaml 失败: {e}"
                    comm.send_update("error", self.error_message)
                    self.config = self.default_config
                    return False
            else:
                self.config = self.default_config
                return True

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

            valid_cred = any(
                cred["appid"] and cred["appsecret"] for cred in self.wechat_credentials
            )
            if not valid_cred:
                self.error_message = "未配置有效的微信公众号appid和appsecret，请打开配置填写"
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

    def save_config(self, config):
        """保存配置到 config.yaml，不验证"""
        with self._lock:
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
                return True
            except Exception as e:
                self.error_message = f"保存 config.yaml 失败: {e}"
                comm.send_update("error", self.error_message)
                return False

    def get_config_path(self):
        return self._config_path
