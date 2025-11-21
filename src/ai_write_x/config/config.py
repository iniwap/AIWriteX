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
    """
    配置管理类 - 统一版本管理策略

    版本管理最佳实践:
    1. 使用智能合并策略处理配置兼容性，替代复杂的版本迁移逻辑
    2. 总是以最新默认配置为基准，保留用户有效配置值
    3. 版本号主要用于用户界面显示，不影响核心功能
    """

    _instance = None
    # _lock = threading.Lock()
    _lock = threading.RLock()  # 可重入锁

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self.config: Dict[Any, Any] = {}
        self.aiforge_config: Dict[Any, Any] = {}
        self.error_message = None
        self.config_path = self.__get_config_path()
        self.config_aiforge_path = self.__get_config_path("aiforge.toml")
        self.config_dimensional_path = self.__get_config_path("dimensional_creative_config.yaml")

        # 加载维度化创意配置
        self.dimensional_creative_options = {}

        # 默认配置
        self.default_config = {
            "platforms": [
                {"name": "微博", "weight": 0.3, "enabled": True},
                {"name": "抖音", "weight": 0.2, "enabled": True},
                {"name": "小红书", "weight": 0.12, "enabled": True},
                {"name": "今日头条", "weight": 0.1, "enabled": True},
                {"name": "百度热点", "weight": 0.08, "enabled": True},
                {"name": "哔哩哔哩", "weight": 0.06, "enabled": True},
                {"name": "快手", "weight": 0.05, "enabled": True},
                {"name": "虎扑", "weight": 0.05, "enabled": True},
                {"name": "豆瓣小组", "weight": 0.02, "enabled": True},
                {"name": "澎湃新闻", "weight": 0.01, "enabled": True},
                {"name": "知乎热榜", "weight": 0.01, "enabled": True},
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
                ]
            },
            "api": {
                "api_type": "OpenRouter",
                "OpenRouter": {
                    "key": "OPENROUTER_API_KEY",
                    "key_index": 0,
                    "api_key": [],
                    "model_index": 0,
                    "model": [
                        "openrouter/deepseek/deepseek-chat-v3-0324:free",
                        "openrouter/deepseek/deepseek-r1-0528:free",
                        "openrouter/deepseek/deepseek-prover-v2:free",
                        "openrouter/deepseek/deepseek-r1:free",
                        "openrouter/deepseek/deepseek-chat:free",
                        "openrouter/qwen/qwen3-32b:free",
                        "openrouter/qwen/qwq-32b:free",
                        "openrouter/google/gemini-2.0-flash-lite-preview-02-05:free",
                        "openrouter/google/gemini-2.0-flash-thinking-exp:free",
                    ],
                    "api_base": "https://openrouter.ai/api/v1",
                },
                "Deepseek": {
                    "key": "DEEPSEEK_API_KEY",
                    "key_index": 0,
                    "api_key": [],
                    "model_index": 0,
                    "model": ["deepseek/deepseek-chat", "deepseek/deepseek-reasoner"],
                    "api_base": "https://api.deepseek.com/v1",
                },
                "Grok": {
                    "key": "XAI_API_KEY",
                    "key_index": 0,
                    "api_key": [],
                    "model_index": 0,
                    "model": ["xai/grok-3"],
                    "api_base": "https://api.x.ai/v1/chat/completions",
                },
                "Qwen": {
                    "key": "OPENAI_API_KEY",
                    "key_index": 0,
                    "api_key": [],
                    "model_index": 0,
                    "model": ["openai/qwen-plus"],
                    "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                },
                "Gemini": {
                    "key": "GEMINI_API_KEY",
                    "key_index": 0,
                    "api_key": [],
                    "model_index": 0,
                    "model": [
                        "gemini/gemini-1.5-flash",
                        "gemini/gemini-1.5-pro",
                        "gemini/gemini-2.0-flash",
                    ],
                    "api_base": "https://generativelanguage.googleapis.com/v1beta/openai/",
                },
                "Ollama": {
                    "key": "OPENAI_API_KEY",
                    "model_index": 0,
                    "key_index": 0,
                    "api_key": [],
                    "model": ["ollama/deepseek-r1:14b", "ollama/deepseek-r1:7b"],
                    "api_base": "http://localhost:11434",
                },
                "SiliconFlow": {
                    "key": "OPENAI_API_KEY",
                    "key_index": 0,
                    "api_key": [],
                    "model_index": 0,
                    "model": [
                        "openai/deepseek-ai/DeepSeek-V3",
                        "openai/deepseek-ai/DeepSeek-R1",
                        "openai/Qwen/QwQ-32B",
                        "openai/Qwen/Qwen3-32B",
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
            "auto_publish": False,
            "article_format": "html",
            "format_publish": True,
            # 维度化创意配置
            "dimensional_creative": {
                "enabled": True,
                "creative_intensity": 1.0,
                "preserve_core_info": True,
                "allow_experimental": False,
                "auto_dimension_selection": True,
                "selected_dimensions": [],
                "priority_categories": ["emotion", "audience", "style", "theme"],
                "max_dimensions": 5,
                "compatibility_threshold": 0.6,
                "available_categories": [
                    "style",  # 文体风格
                    "culture",  # 文化视角
                    "time",  # 时空背景
                    "personality",  # 人格角色
                    "emotion",  # 情感调性
                    "format",  # 表达格式
                    "scene",  # 场景环境
                    "audience",  # 目标受众
                    "theme",  # 主题内容
                    "technique",  # 表现技法
                    "language",  # 语言风格
                    "tone",  # 语调语气
                    "perspective",  # 叙述视角
                    "structure",  # 文章结构
                    "rhythm",  # 节奏韵律
                ],
                # 默认不启用任何维度
                "enabled_dimensions": {
                    "style": False,
                    "culture": False,
                    "time": False,
                    "personality": False,
                    "emotion": False,
                    "format": False,
                    "scene": False,
                    "audience": False,
                    "theme": False,
                    "technique": False,
                    "language": False,
                    "tone": False,
                    "perspective": False,
                    "structure": False,
                    "rhythm": False,
                },
                "dimension_options": {
                    "style": {
                        "name": "文体风格",
                        "allow_custom": True,
                        "selected_option": "",
                        "custom_input": "",
                        "preset_options": [
                            {
                                "name": "poetry",
                                "value": "诗歌",
                                "weight": 1.0,
                                "description": "韵律优美，意境深远",
                            },
                            {
                                "name": "prose",
                                "value": "散文",
                                "weight": 1.0,
                                "description": "形散神聚，情感真挚",
                            },
                            {
                                "name": "novel",
                                "value": "小说",
                                "weight": 1.0,
                                "description": "情节丰富，人物鲜明",
                            },
                            {
                                "name": "essay",
                                "value": "议论文",
                                "weight": 1.0,
                                "description": "观点明确，论证严密",
                            },
                            {
                                "name": "narrative",
                                "value": "叙事文",
                                "weight": 1.0,
                                "description": "故事性强，引人入胜",
                            },
                            {
                                "name": "expository",
                                "value": "说明文",
                                "weight": 1.0,
                                "description": "条理清晰，解释详尽",
                            },
                            {
                                "name": "academic",
                                "value": "学术论文",
                                "weight": 1.0,
                                "description": "严谨规范，逻辑清晰",
                            },
                            {
                                "name": "news",
                                "value": "新闻报道",
                                "weight": 1.0,
                                "description": "客观真实，时效性强",
                            },
                            {
                                "name": "children",
                                "value": "儿童文学",
                                "weight": 1.0,
                                "description": "天真烂漫，寓教于乐",
                            },
                            {
                                "name": "fantasy",
                                "value": "奇幻文学",
                                "weight": 1.0,
                                "description": "想象丰富，魔幻色彩",
                            },
                        ],
                    },
                    "culture": {
                        "name": "文化视角",
                        "allow_custom": True,
                        "selected_option": "",
                        "custom_input": "",
                        "preset_options": [
                            {
                                "name": "eastern_philosophy",
                                "value": "东方哲学",
                                "weight": 1.0,
                                "description": "道家思想，禅宗智慧",
                            },
                            {
                                "name": "western_logic",
                                "value": "西方思辨",
                                "weight": 1.0,
                                "description": "理性分析，逻辑严密",
                            },
                            {
                                "name": "japanese_mono",
                                "value": "日式物哀",
                                "weight": 1.0,
                                "description": "瞬间美学，淡淡哀愁",
                            },
                            {
                                "name": "french_romance",
                                "value": "法式浪漫",
                                "weight": 1.0,
                                "description": "优雅情调，艺术气息",
                            },
                            {
                                "name": "american_freedom",
                                "value": "美式自由",
                                "weight": 1.0,
                                "description": "个人主义，追求自由",
                            },
                            {
                                "name": "chinese_tradition",
                                "value": "中华传统",
                                "weight": 1.0,
                                "description": "儒家文化，礼仪之邦",
                            },
                            {
                                "name": "european_classical",
                                "value": "欧洲古典",
                                "weight": 1.0,
                                "description": "文艺复兴，古典艺术",
                            },
                            {
                                "name": "latin_american",
                                "value": "拉美风情",
                                "weight": 1.0,
                                "description": "热情奔放，魔幻现实",
                            },
                            {
                                "name": "african_tribal",
                                "value": "非洲部落",
                                "weight": 1.0,
                                "description": "原始力量，图腾崇拜",
                            },
                            {
                                "name": "middle_eastern",
                                "value": "中东神秘",
                                "weight": 1.0,
                                "description": "沙漠文明，宗教色彩",
                            },
                        ],
                    },
                    "time": {
                        "name": "时空背景",
                        "allow_custom": True,
                        "selected_option": "",
                        "custom_input": "",
                        "preset_options": [
                            {
                                "name": "ancient_china",
                                "value": "春秋战国",
                                "weight": 1.0,
                                "description": "礼崩乐坏，百家争鸣",
                            },
                            {
                                "name": "tang_song",
                                "value": "唐宋盛世",
                                "weight": 1.0,
                                "description": "文化繁荣，诗词鼎盛",
                            },
                            {
                                "name": "republic",
                                "value": "民国风云",
                                "weight": 1.0,
                                "description": "新旧交替，风起云涌",
                            },
                            {
                                "name": "eighties",
                                "value": "80年代",
                                "weight": 1.0,
                                "description": "改革开放，青春热血",
                            },
                            {
                                "name": "cyberpunk",
                                "value": "赛博朋克2077",
                                "weight": 1.0,
                                "description": "科技未来，霓虹反乌托邦",
                            },
                            {
                                "name": "medieval",
                                "value": "中世纪",
                                "weight": 1.0,
                                "description": "骑士精神，神秘主义",
                            },
                            {
                                "name": "prehistoric",
                                "value": "史前时代",
                                "weight": 1.0,
                                "description": "原始社会，洪荒之力",
                            },
                            {
                                "name": "space_age",
                                "value": "太空纪元",
                                "weight": 1.0,
                                "description": "星际旅行，宇宙探索",
                            },
                            {
                                "name": "victorian",
                                "value": "维多利亚时代",
                                "weight": 1.0,
                                "description": "工业革命，社会变革",
                            },
                            {
                                "name": "renaissance",
                                "value": "文艺复兴",
                                "weight": 1.0,
                                "description": "人文主义，艺术复兴",
                            },
                        ],
                    },
                    "personality": {
                        "name": "人格角色",
                        "allow_custom": True,
                        "selected_option": "",
                        "custom_input": "",
                        "preset_options": [
                            {
                                "name": "libai",
                                "value": "李白",
                                "weight": 1.0,
                                "description": "浪漫主义诗人，豪放不羁",
                            },
                            {
                                "name": "luxun",
                                "value": "鲁迅",
                                "weight": 1.0,
                                "description": "现代文学家，深刻批判",
                            },
                            {
                                "name": "confucius",
                                "value": "孔子",
                                "weight": 1.0,
                                "description": "思想家，仁爱之道",
                            },
                            {
                                "name": "dreamer_poet",
                                "value": "梦境诗人",
                                "weight": 1.0,
                                "description": "善于将现实与梦境交织",
                            },
                            {
                                "name": "data_philosopher",
                                "value": "数据哲学家",
                                "weight": 1.0,
                                "description": "用数据思维解读人文",
                            },
                            {
                                "name": "time_traveler",
                                "value": "时空旅者",
                                "weight": 1.0,
                                "description": "穿梭时代，独特视角",
                            },
                            {
                                "name": "emotion_healer",
                                "value": "情感治愈师",
                                "weight": 1.0,
                                "description": "温暖人心，抚慰心灵",
                            },
                            {
                                "name": "mystery_detective",
                                "value": "悬疑侦探",
                                "weight": 1.0,
                                "description": "逻辑推理，揭秘真相",
                            },
                            {
                                "name": "innovator",
                                "value": "创新先锋",
                                "weight": 1.0,
                                "description": "勇于探索，突破传统",
                            },
                            {
                                "name": "storyteller",
                                "value": "故事大王",
                                "weight": 1.0,
                                "description": "生动叙述，引人入胜",
                            },
                            {
                                "name": "scientist",
                                "value": "科学家",
                                "weight": 1.0,
                                "description": "理性严谨，探索真理",
                            },
                            {
                                "name": "artist",
                                "value": "艺术家",
                                "weight": 1.0,
                                "description": "感性创造，美学追求",
                            },
                        ],
                    },
                    "emotion": {
                        "name": "情感调性",
                        "allow_custom": True,
                        "selected_option": "",
                        "custom_input": "",
                        "preset_options": [
                            {
                                "name": "healing",
                                "value": "治愈系",
                                "weight": 1.0,
                                "description": "温暖人心，抚慰心灵",
                            },
                            {
                                "name": "suspense",
                                "value": "悬疑惊悚",
                                "weight": 1.0,
                                "description": "紧张刺激，扣人心弦",
                            },
                            {
                                "name": "inspiring",
                                "value": "热血励志",
                                "weight": 1.0,
                                "description": "激情澎湃，正能量满满",
                            },
                            {
                                "name": "philosophical",
                                "value": "深度哲思",
                                "weight": 1.0,
                                "description": "思辨深刻，启发智慧",
                            },
                            {
                                "name": "humorous",
                                "value": "幽默诙谐",
                                "weight": 1.0,
                                "description": "轻松愉快，妙趣横生",
                            },
                            {
                                "name": "melancholy",
                                "value": "忧郁怀旧",
                                "weight": 1.0,
                                "description": "淡淡忧伤，回忆如潮",
                            },
                            {
                                "name": "romantic",
                                "value": "浪漫爱情",
                                "weight": 1.0,
                                "description": "甜蜜温馨，情意绵绵",
                            },
                            {
                                "name": "mysterious",
                                "value": "神秘莫测",
                                "weight": 1.0,
                                "description": "扑朔迷离，引人遐想",
                            },
                            {
                                "name": "tragic",
                                "value": "悲剧色彩",
                                "weight": 1.0,
                                "description": "悲壮深沉，命运抗争",
                            },
                            {
                                "name": "epic",
                                "value": "史诗气概",
                                "weight": 1.0,
                                "description": "宏大叙事，英雄传奇",
                            },
                        ],
                    },
                    "format": {
                        "name": "表达格式",
                        "allow_custom": True,
                        "selected_option": "",
                        "custom_input": "",
                        "preset_options": [
                            {
                                "name": "diary",
                                "value": "日记体",
                                "weight": 1.0,
                                "description": "私密真实，情感流露",
                            },
                            {
                                "name": "dialogue",
                                "value": "对话体",
                                "weight": 1.0,
                                "description": "生动活泼，互动性强",
                            },
                            {
                                "name": "poetry",
                                "value": "诗歌散文",
                                "weight": 1.0,
                                "description": "韵律优美，意境深远",
                            },
                            {
                                "name": "script",
                                "value": "剧本形式",
                                "weight": 1.0,
                                "description": "戏剧冲突，画面感强",
                            },
                            {
                                "name": "letter",
                                "value": "书信体",
                                "weight": 1.0,
                                "description": "情真意切，时光穿越",
                            },
                            {
                                "name": "interview",
                                "value": "访谈录",
                                "weight": 1.0,
                                "description": "问答互动，真实自然",
                            },
                            {
                                "name": "report",
                                "value": "调查报告",
                                "weight": 1.0,
                                "description": "数据支撑，客观分析",
                            },
                            {
                                "name": "fable",
                                "value": "寓言故事",
                                "weight": 1.0,
                                "description": "寓意深刻，启发思考",
                            },
                            {
                                "name": "essay",
                                "value": "随笔杂谈",
                                "weight": 1.0,
                                "description": "自由灵活，见解独特",
                            },
                            {
                                "name": "manual",
                                "value": "操作手册",
                                "weight": 1.0,
                                "description": "步骤清晰，实用指导",
                            },
                        ],
                    },
                    "scene": {
                        "name": "场景环境",
                        "allow_custom": True,
                        "selected_option": "",
                        "custom_input": "",
                        "preset_options": [
                            {
                                "name": "coffee_shop",
                                "value": "咖啡馆",
                                "weight": 1.0,
                                "description": "温馨惬意，都市情调",
                            },
                            {
                                "name": "midnight_subway",
                                "value": "深夜地铁",
                                "weight": 1.0,
                                "description": "孤独思考，城市夜色",
                            },
                            {
                                "name": "rainy_bookstore",
                                "value": "雨夜书店",
                                "weight": 1.0,
                                "description": "文艺浪漫，知识殿堂",
                            },
                            {
                                "name": "seaside_cabin",
                                "value": "海边小屋",
                                "weight": 1.0,
                                "description": "自然宁静，心灵栖息",
                            },
                            {
                                "name": "bustling_city",
                                "value": "繁华都市",
                                "weight": 1.0,
                                "description": "节奏快速，机遇挑战",
                            },
                            {
                                "name": "mountain_temple",
                                "value": "山中古寺",
                                "weight": 1.0,
                                "description": "清幽宁静，禅意深远",
                            },
                            {
                                "name": "university_campus",
                                "value": "大学校园",
                                "weight": 1.0,
                                "description": "青春洋溢，求知氛围",
                            },
                            {
                                "name": "futuristic_city",
                                "value": "未来都市",
                                "weight": 1.0,
                                "description": "科技感强，超现实",
                            },
                            {
                                "name": "forest",
                                "value": "神秘森林",
                                "weight": 1.0,
                                "description": "原始自然，探险奇遇",
                            },
                            {
                                "name": "library",
                                "value": "古老图书馆",
                                "weight": 1.0,
                                "description": "知识海洋，智慧殿堂",
                            },
                        ],
                    },
                    "audience": {
                        "name": "目标受众",
                        "allow_custom": True,
                        "selected_option": "",
                        "custom_input": "",
                        "preset_options": [
                            {
                                "name": "gen_z",
                                "value": "Z世代",
                                "weight": 1.0,
                                "description": "年轻时尚，网络原生",
                            },
                            {
                                "name": "professionals",
                                "value": "职场精英",
                                "weight": 1.0,
                                "description": "理性务实，效率导向",
                            },
                            {
                                "name": "seniors",
                                "value": "银发族",
                                "weight": 1.0,
                                "description": "阅历丰富，情感细腻",
                            },
                            {
                                "name": "students",
                                "value": "学生党",
                                "weight": 1.0,
                                "description": "青春活力，求知欲强",
                            },
                            {
                                "name": "parents",
                                "value": "宝妈群体",
                                "weight": 1.0,
                                "description": "关爱家庭，实用贴心",
                            },
                            {
                                "name": "entrepreneurs",
                                "value": "创业者",
                                "weight": 1.0,
                                "description": "冒险精神，创新意识",
                            },
                            {
                                "name": "tech_workers",
                                "value": "技术人员",
                                "weight": 1.0,
                                "description": "逻辑思维，追求效率",
                            },
                            {
                                "name": "artists",
                                "value": "文艺青年",
                                "weight": 1.0,
                                "description": "审美独特，情感丰富",
                            },
                            {
                                "name": "retirees",
                                "value": "退休人员",
                                "weight": 1.0,
                                "description": "闲暇时光，生活感悟",
                            },
                            {
                                "name": "travelers",
                                "value": "旅行爱好者",
                                "weight": 1.0,
                                "description": "探索世界，体验丰富",
                            },
                        ],
                    },
                    "theme": {
                        "name": "主题内容",
                        "allow_custom": True,
                        "selected_option": "",
                        "custom_input": "",
                        "preset_options": [
                            {
                                "name": "growth",
                                "value": "成长蜕变",
                                "weight": 1.0,
                                "description": "青春成长，自我发现",
                            },
                            {
                                "name": "time_healing",
                                "value": "时间治愈",
                                "weight": 1.0,
                                "description": "岁月如歌，伤痛愈合",
                            },
                            {
                                "name": "dream_pursuit",
                                "value": "梦想追寻",
                                "weight": 1.0,
                                "description": "理想主义，不懈奋斗",
                            },
                            {
                                "name": "human_nature",
                                "value": "人性探索",
                                "weight": 1.0,
                                "description": "心理深度，道德思辨",
                            },
                            {
                                "name": "tech_reflection",
                                "value": "科技反思",
                                "weight": 1.0,
                                "description": "技术进步，人文关怀",
                            },
                            {
                                "name": "environmental",
                                "value": "环保理念",
                                "weight": 1.0,
                                "description": "绿色生态，可持续发展",
                            },
                            {
                                "name": "social_justice",
                                "value": "社会公正",
                                "weight": 1.0,
                                "description": "公平正义，社会责任",
                            },
                            {
                                "name": "cultural_heritage",
                                "value": "文化传承",
                                "weight": 1.0,
                                "description": "传统延续，文化保护",
                            },
                            {
                                "name": "love",
                                "value": "爱情故事",
                                "weight": 1.0,
                                "description": "情感纠葛，心灵共鸣",
                            },
                            {
                                "name": "adventure",
                                "value": "冒险历程",
                                "weight": 1.0,
                                "description": "挑战极限，勇往直前",
                            },
                        ],
                    },
                    "technique": {
                        "name": "表现技法",
                        "allow_custom": True,
                        "selected_option": "",
                        "custom_input": "",
                        "preset_options": [
                            {
                                "name": "first_person",
                                "value": "第一人称",
                                "weight": 1.0,
                                "description": "亲身体验，情感直接",
                            },
                            {
                                "name": "omniscient",
                                "value": "全知视角",
                                "weight": 1.0,
                                "description": "上帝视角，洞察全局",
                            },
                            {
                                "name": "multiple",
                                "value": "多重叙述",
                                "weight": 1.0,
                                "description": "多角度展现，复杂立体",
                            },
                            {
                                "name": "stream",
                                "value": "意识流",
                                "weight": 1.0,
                                "description": "内心独白，思维跳跃",
                            },
                            {
                                "name": "flashback",
                                "value": "倒叙",
                                "weight": 1.0,
                                "description": "时空交错，悬念重生",
                            },
                            {
                                "name": "montage",
                                "value": "蒙太奇",
                                "weight": 1.0,
                                "description": "画面拼接，时空压缩",
                            },
                            {
                                "name": "symbolism",
                                "value": "象征主义",
                                "weight": 1.0,
                                "description": "寓意深刻，含蓄表达",
                            },
                            {
                                "name": "satire",
                                "value": "讽刺手法",
                                "weight": 1.0,
                                "description": "幽默批判，辛辣讽刺",
                            },
                            {
                                "name": "metaphor",
                                "value": "隐喻象征",
                                "weight": 1.0,
                                "description": "比喻暗示，意味深长",
                            },
                            {
                                "name": "contrast",
                                "value": "对比反衬",
                                "weight": 1.0,
                                "description": "鲜明对照，突出主题",
                            },
                        ],
                    },
                    "language": {
                        "name": "语言风格",
                        "allow_custom": True,
                        "selected_option": "",
                        "custom_input": "",
                        "preset_options": [
                            {
                                "name": "classical",
                                "value": "古典雅致",
                                "weight": 1.0,
                                "description": "文言韵味，典雅庄重",
                            },
                            {
                                "name": "modern",
                                "value": "现代白话",
                                "weight": 1.0,
                                "description": "通俗易懂，贴近生活",
                            },
                            {
                                "name": "vernacular",
                                "value": "方言土语",
                                "weight": 1.0,
                                "description": "地域特色，生动亲切",
                            },
                            {
                                "name": "foreign",
                                "value": "外语混杂",
                                "weight": 1.0,
                                "description": "多语融合，国际范儿",
                            },
                            {
                                "name": "technical",
                                "value": "专业术语",
                                "weight": 1.0,
                                "description": "行业词汇，精准表达",
                            },
                            {
                                "name": "slang",
                                "value": "网络流行",
                                "weight": 1.0,
                                "description": "潮流用语，年轻时尚",
                            },
                            {
                                "name": "poetic",
                                "value": "诗意语言",
                                "weight": 1.0,
                                "description": "韵律优美，意境深远",
                            },
                            {
                                "name": "plain",
                                "value": "朴素平实",
                                "weight": 1.0,
                                "description": "简洁明了，朴实无华",
                            },
                        ],
                    },
                    "tone": {
                        "name": "语调语气",
                        "allow_custom": True,
                        "selected_option": "",
                        "custom_input": "",
                        "preset_options": [
                            {
                                "name": "serious",
                                "value": "严肃庄重",
                                "weight": 1.0,
                                "description": "郑重其事，不容置疑",
                            },
                            {
                                "name": "casual",
                                "value": "轻松随意",
                                "weight": 1.0,
                                "description": "自然亲切，不拘一格",
                            },
                            {
                                "name": "sarcastic",
                                "value": "讽刺挖苦",
                                "weight": 1.0,
                                "description": "反语讥讽，辛辣犀利",
                            },
                            {
                                "name": "enthusiastic",
                                "value": "热情洋溢",
                                "weight": 1.0,
                                "description": "激情澎湃，感染力强",
                            },
                            {
                                "name": "calm",
                                "value": "平静温和",
                                "weight": 1.0,
                                "description": "心平气和，娓娓道来",
                            },
                            {
                                "name": "urgent",
                                "value": "急切紧迫",
                                "weight": 1.0,
                                "description": "迫在眉睫，刻不容缓",
                            },
                            {
                                "name": "mysterious",
                                "value": "神秘莫测",
                                "weight": 1.0,
                                "description": "扑朔迷离，引人入胜",
                            },
                            {
                                "name": "humorous",
                                "value": "幽默诙谐",
                                "weight": 1.0,
                                "description": "妙趣横生，令人发笑",
                            },
                        ],
                    },
                    "perspective": {
                        "name": "叙述视角",
                        "allow_custom": True,
                        "selected_option": "",
                        "custom_input": "",
                        "preset_options": [
                            {
                                "name": "first_person",
                                "value": "第一人称",
                                "weight": 1.0,
                                "description": "以我为主，亲身经历",
                            },
                            {
                                "name": "second_person",
                                "value": "第二人称",
                                "weight": 1.0,
                                "description": "直接对话，身临其境",
                            },
                            {
                                "name": "third_person_limited",
                                "value": "第三人称有限",
                                "weight": 1.0,
                                "description": "聚焦主角，深入内心",
                            },
                            {
                                "name": "third_person_omniscient",
                                "value": "第三人称全知",
                                "weight": 1.0,
                                "description": "全知全能，洞察一切",
                            },
                            {
                                "name": "multiple_pov",
                                "value": "多视角切换",
                                "weight": 1.0,
                                "description": "不同人物，不同视角",
                            },
                            {
                                "name": "observer",
                                "value": "旁观者视角",
                                "weight": 1.0,
                                "description": "客观记录，冷眼旁观",
                            },
                            {
                                "name": "participant",
                                "value": "参与者视角",
                                "weight": 1.0,
                                "description": "身在其中，主观感受",
                            },
                        ],
                    },
                    "structure": {
                        "name": "文章结构",
                        "allow_custom": True,
                        "selected_option": "",
                        "custom_input": "",
                        "preset_options": [
                            {
                                "name": "chronological",
                                "value": "时间顺序",
                                "weight": 1.0,
                                "description": "按时间发展，脉络清晰",
                            },
                            {
                                "name": "spatial",
                                "value": "空间顺序",
                                "weight": 1.0,
                                "description": "按空间位置，层次分明",
                            },
                            {
                                "name": "thematic",
                                "value": "主题分类",
                                "weight": 1.0,
                                "description": "按主题划分，逻辑严密",
                            },
                            {
                                "name": "problem_solution",
                                "value": "问题解决",
                                "weight": 1.0,
                                "description": "提出问题，分析解决",
                            },
                            {
                                "name": "cause_effect",
                                "value": "因果关系",
                                "weight": 1.0,
                                "description": "分析原因，探讨结果",
                            },
                            {
                                "name": "compare_contrast",
                                "value": "对比对照",
                                "weight": 1.0,
                                "description": "比较异同，突出特点",
                            },
                            {
                                "name": "circular",
                                "value": "首尾呼应",
                                "weight": 1.0,
                                "description": "开头结尾，遥相呼应",
                            },
                            {
                                "name": "layered",
                                "value": "层层递进",
                                "weight": 1.0,
                                "description": "由浅入深，逐步深入",
                            },
                        ],
                    },
                    "rhythm": {
                        "name": "节奏韵律",
                        "allow_custom": True,
                        "selected_option": "",
                        "custom_input": "",
                        "preset_options": [
                            {
                                "name": "fast",
                                "value": "快节奏",
                                "weight": 1.0,
                                "description": "紧凑激烈，扣人心弦",
                            },
                            {
                                "name": "slow",
                                "value": "慢节奏",
                                "weight": 1.0,
                                "description": "舒缓悠扬，娓娓道来",
                            },
                            {
                                "name": "variable",
                                "value": "变化多端",
                                "weight": 1.0,
                                "description": "张弛有度，起伏跌宕",
                            },
                            {
                                "name": "steady",
                                "value": "平稳均匀",
                                "weight": 1.0,
                                "description": "节奏一致，稳定推进",
                            },
                            {
                                "name": "accelerating",
                                "value": "逐渐加快",
                                "weight": 1.0,
                                "description": "层层推进，越来越快",
                            },
                            {
                                "name": "decelerating",
                                "value": "逐渐放缓",
                                "weight": 1.0,
                                "description": "渐入佳境，慢慢回味",
                            },
                            {
                                "name": "syncopated",
                                "value": "切分节奏",
                                "weight": 1.0,
                                "description": "错落有致，富有变化",
                            },
                        ],
                    },
                },  # 维度选项配置
            },
            # 页面设计配置 - 默认不启用,使用原始HTML样式
            "page_design": {
                "use_original_styles": True,  # 默认true,不应用全局样式覆盖
                "container": {
                    "max_width": 750,
                    "margin_horizontal": 10,
                    "background_color": "#f8f9fa",
                },
                "card": {
                    "border_radius": 12,
                    "box_shadow": "0 4px 16px rgba(0,0,0,0.06)",
                    "padding": 24,
                    "background_color": "#ffffff",
                },
                "typography": {
                    "base_font_size": 16,
                    "line_height": 1.6,
                    "heading_scale": 1.5,
                    "text_color": "#333333",
                    "heading_color": "#333333",
                },
                "spacing": {"section_margin": 24, "element_margin": 16},
                "accent": {
                    "primary_color": "#3a7bd5",
                    "secondary_color": "#00b09b",
                    "highlight_bg": "#f0f7ff",
                },
            },
        }

        self.default_aiforge_config = {
            "locale": "zh",
            "max_rounds": 2,
            "max_tokens": 4096,
            "max_optimization_attempts": 3,
            "default_llm_provider": "openrouter",
            "llm": {
                "openrouter": {
                    "type": "openai",
                    "model": "deepseek/deepseek-chat-v3-0324:free",
                    "api_key": "",
                    "base_url": "https://openrouter.ai/api/v1",
                    "timeout": 60,
                    "max_tokens": 8192,
                },
                "grok": {
                    "type": "grok",
                    "model": "xai/grok-3",
                    "api_key": "",
                    "base_url": "https://api.x.ai/v1/",
                    "timeout": 60,
                    "max_tokens": 8192,
                },
                "qwen": {
                    "type": "openai",
                    "model": "qwen-plus",
                    "api_key": "",
                    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                    "timeout": 60,
                    "max_tokens": 8192,
                },
                "gemini": {
                    "type": "gemini",
                    "model": "gemini/gemini-2.5-flash",
                    "api_key": "",
                    "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
                    "timeout": 60,
                    "max_tokens": 8192,
                },
                "ollama": {
                    "type": "ollama",
                    "model": "llama3",
                    "api_key": "",
                    "base_url": "http://localhost:11434",
                    "timeout": 60,
                    "max_tokens": 8192,
                },
                "deepseek": {
                    "type": "deepseek",
                    "model": "deepseek-chat",
                    "api_key": "",
                    "base_url": "https://api.deepseek.com",
                    "timeout": 60,
                    "max_tokens": 8192,
                },
                "claude": {
                    "type": "claude",
                    "model": "claude-4-sonnet",
                    "api_key": "",
                    "base_url": "https://api.anthropic.com/v1",
                    "timeout": 60,
                    "max_tokens": 4096,
                },
                "cohere": {
                    "type": "cohere",
                    "model": "command-r-plus",
                    "api_key": "",
                    "base_url": "https://api.cohere.ai/v1",
                    "timeout": 60,
                    "max_tokens": 4096,
                },
                "mistral": {
                    "type": "mistral",
                    "model": "mistral-large-latest",
                    "api_key": "",
                    "base_url": "https://api.mistral.ai/v1",
                    "timeout": 60,
                    "max_tokens": 4096,
                },
            },
            "cache": {
                "code": {
                    "enabled": True,
                    "max_modules": 20,
                    "failure_threshold": 0.8,
                    "max_age_days": 30,
                    "cleanup_interval": 10,
                    "semantic_threshold": 0.6,
                    "enable_semantic_matching": True,
                    "use_lightweight_semantic": False,
                    "enable_action_clustering": True,
                    "action_cluster_threshold": 0.75,
                },
            },
            "optimization": {
                "enabled": False,
                "aggressive_minify": True,
                "max_feedback_length": 200,
                "obfuscate_variables": True,
            },
            "security": {
                "execution_timeout": 60,
                "memory_limit_mb": 512,
                "cpu_time_limit": 60,
                "file_descriptor_limit": 64,
                "max_file_size_mb": 100,
                "max_processes": 10,
                "file_access": {
                    "user_specified_paths": True,
                    "default_allowed_paths": ["./data", "./output"],
                    "require_explicit_permission": True,
                    "max_allowed_paths": 10,
                },
                "network": {
                    "policy": "unrestricted",
                    "max_requests_per_minute": 60,
                    "max_concurrent_connections": 10,
                    "request_timeout": 30,
                    "allowed_protocols": ["http", "https"],
                    "allowed_ports": [80, 443, 8080, 8443],
                    "blocked_ports": [22, 23, 3389, 5432, 3306],
                    "generated_code": {
                        "force_block_modules": False,
                        "force_block_access": False,
                    },
                    "domain_filtering": {
                        "enabled": True,
                        "whitelist": [
                            "api.openai.com",
                            "api.deepseek.com",
                            "openrouter.ai",
                            "baidu.com",
                            "bing.com",
                            "so.com",
                            "sogou.com",
                            "api.x.ai",
                            "dashscope.aliyuncs.com",
                            "generativelanguage.googleapis.com",
                        ],
                        "blacklist": ["malicious-site.com"],
                        "task_overrides": {
                            "data_fetch": {
                                "mode": "extended",
                                "additional_domains": [
                                    "sina.com.cn",
                                    "163.com",
                                    "qq.com",
                                    "sohu.com",
                                    "xinhuanet.com",
                                    "people.com.cn",
                                    "chinanews.com",
                                    "thepaper.cn",
                                    "36kr.com",
                                    "ifeng.com",
                                    "cnbeta.com",
                                    "zol.com.cn",
                                    "csdn.net",
                                    "jianshu.com",
                                    "zhihu.com",
                                    "weibo.com",
                                    "douban.com",
                                    "bilibili.com",
                                    "youku.com",
                                    "iqiyi.com",
                                    "tencent.com",
                                    "alibaba.com",
                                    "jd.com",
                                    "tmall.com",
                                    "taobao.com",
                                ],
                            },
                        },
                    },
                },
            },
            "extensions": {
                "enabled": True,
                "auto_load": True,
                "extension_dir": "extensions",
                "registered": [
                    {
                        "name": "custom_executor",
                        "type": "executor",
                        "config": {},
                    },
                    {
                        "name": "custom_data_processor",
                        "type": "executor",
                        "module_path": "my_plugins.data_processor",
                        "class_name": "CustomDataProcessor",
                        "priority": 1,
                    },
                    {
                        "name": "domain_specific_executor",
                        "type": "executor",
                        "config_file": "plugins/domain_executor.toml",
                    },
                ],
            },
        }
        # 自定义话题和文章参考链接，根据是否为空判断是否自定义
        self.custom_topic = ""  # 自定义话题（字符串）
        self.urls = []  # 参考链接（列表）
        self.reference_ratio = 0.0  # 文章借鉴比例[0-1]
        self.custom_template_category = ""  # 自定义话题时，模板分类
        self.custom_template = ""  # 自定义话题时，模板

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @property
    def platforms(self):
        with self._lock:
            if not self.config:
                raise ValueError("配置未加载")
            return self.config["platforms"]

    @property
    def wechat_credentials(self):
        with self._lock:
            if not self.config:
                raise ValueError("配置未加载")
            return self.config["wechat"]["credentials"]

    @property
    def api_type(self):
        with self._lock:
            if not self.config:
                raise ValueError("配置未加载")
            return self.config["api"]["api_type"]

    @property
    def api_key_name(self):
        with self._lock:
            if not self.config:
                raise ValueError("配置未加载")
            return self.config["api"][self.config["api"]["api_type"]]["key"]

    @property
    def api_key(self):
        with self._lock:
            if not self.config:
                raise ValueError("配置未加载")
            api_key = self.config["api"][self.config["api"]["api_type"]]["api_key"]
            key_index = self.config["api"][self.config["api"]["api_type"]]["key_index"]
            return api_key[key_index]

    @property
    def api_model(self):
        with self._lock:
            if not self.config:
                raise ValueError("配置未加载")
            model = self.config["api"][self.config["api"]["api_type"]]["model"]
            model_index = self.config["api"][self.config["api"]["api_type"]]["model_index"]
            return model[model_index]

    @property
    def api_apibase(self):
        with self._lock:
            if not self.config:
                raise ValueError("配置未加载")
            return self.config["api"][self.config["api"]["api_type"]]["api_base"]

    @property
    def img_api_type(self):
        with self._lock:
            if not self.config:
                raise ValueError("配置未加载")
            return self.config["img_api"]["api_type"]

    @property
    def img_api_key(self):
        with self._lock:
            if not self.config:
                raise ValueError("配置未加载")
            return self.config["img_api"][self.config["img_api"]["api_type"]]["api_key"]

    @property
    def img_api_model(self):
        with self._lock:
            if not self.config:
                raise ValueError("配置未加载")
            return self.config["img_api"][self.config["img_api"]["api_type"]]["model"]

    @property
    def use_template(self):
        with self._lock:
            if not self.config:
                raise ValueError("配置未加载")
            return self.config["use_template"]

    @property
    def template_category(self):
        with self._lock:
            if not self.config:
                raise ValueError("配置未加载")
            return self.config["template_category"]

    @property
    def template(self):
        with self._lock:
            if not self.config:
                raise ValueError("配置未加载")
            return self.config["template"]

    @property
    def use_compress(self):
        with self._lock:
            if not self.config:
                raise ValueError("配置未加载")
            return self.config["use_compress"]

    @property
    def aiforge_search_max_results(self):
        with self._lock:
            if not self.config:
                raise ValueError("配置未加载")
            return self.config["aiforge_search_max_results"]

    @property
    def aiforge_search_min_results(self):
        with self._lock:
            if not self.config:
                raise ValueError("配置未加载")
            return self.config["aiforge_search_min_results"]

    @property
    def min_article_len(self):
        with self._lock:
            if not self.config:
                raise ValueError("配置未加载")
            return self.config["min_article_len"]

    @property
    def max_article_len(self):
        with self._lock:
            if not self.config:
                raise ValueError("配置未加载")
            return self.config["max_article_len"]

    @property
    def article_format(self):
        with self._lock:
            if not self.config:
                raise ValueError("配置未加载")
            return self.config["article_format"]

    @property
    def auto_publish(self):
        with self._lock:
            if not self.config:
                raise ValueError("配置未加载")
            return self.config["auto_publish"]

    @property
    def format_publish(self):
        with self._lock:
            if not self.config:
                raise ValueError("配置未加载")
            return self.config["format_publish"]

    @property
    def publish_platform(self):
        with self._lock:
            if not self.config:
                raise ValueError("配置未加载")
            return self.config["publish_platform"]

    @property
    def creative_config(self):
        """获取维度化创意配置"""
        with self._lock:
            if not self.config:
                raise ValueError("配置未加载")
            return self.config.get("dimensional_creative", {})

    @property
    def dimensional_creative_config(self):
        """维度化创意配置"""
        with self._lock:
            return self.creative_config

    @property
    def smart_recommendation_config(self):
        """智能推荐配置"""
        with self._lock:
            return self.creative_config.get("smart_recommendation", {})

    @property
    def api_list(self):
        with self._lock:
            if not self.config:
                raise ValueError("配置未加载")

            api_keys_list = list(self.config["api"].keys())
            if "api_type" in api_keys_list:
                api_keys_list.remove("api_type")

            return api_keys_list

    @property
    def api_list_display(self):
        """返回用于界面显示的API类型列表"""
        with self._lock:
            if not self.config:
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
            if not self.aiforge_config:
                raise ValueError("配置未加载")
            return self.aiforge_config["default_llm_provider"]

    @property
    def aiforge_api_key(self):
        with self._lock:
            if not self.aiforge_config:
                raise ValueError("配置未加载")
            return self.aiforge_config["llm"][self.aiforge_config["default_llm_provider"]][
                "api_key"
            ]

    @property
    def license(self):
        """授权配置"""
        with self._lock:
            if not self.config:
                raise ValueError("配置未加载")
            return self.config.get("license", {})

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
                        if not self.config:
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
                        if not self.aiforge_config:
                            self.aiforge_config = self.default_aiforge_config
                except Exception as e:
                    self.error_message = f"加载 aiforge.toml 失败: {e}"
                    log.print_log(self.error_message, "error")
                    self.aiforge_config = self.default_aiforge_config
                    ret = False
            else:
                self.aiforge_config = self.default_aiforge_config

            return ret

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

    def save_dimensional_creative_config(self, dimensional_config):
        """保存维度化创意配置到单独的文件"""
        with self._lock:
            ret = True
            try:
                # 创建包含维度选项的完整配置
                full_config = {"dimension_options": dimensional_config}

                with open(self.config_dimensional_path, "w", encoding="utf-8") as f:
                    yaml.dump(
                        full_config,
                        f,
                        Dumper=IndentedDumper,
                        allow_unicode=True,
                        sort_keys=False,
                        default_flow_style=False,
                        indent=2,
                    )
            except Exception as e:
                self.error_message = f"保存 dimensional_creative_config.yaml 失败: {e}"
                log.print_log(self.error_message, "error")
                ret = False

            return ret

    def get_config(self):
        """获取配置，不验证"""
        with self._lock:
            if not self.config:
                raise ValueError("配置未加载")
            return self.config

    def validate_config(self):
        """验证配置,仅在 CrewAI 执行时调用"""
        try:
            # 获取 API 配置
            api_type = self.api_type
            api_config = self.config["api"][api_type]

            # 检查 api_key 列表
            api_keys = api_config.get("api_key", [])
            if not api_keys or not any(api_keys):
                self.error_message = f"未配置API KEY，请打开配置填写{api_type}的api_key"
                return False

            # 检查 key_index 是否有效
            key_index = api_config.get("key_index", 0)
            if key_index >= len(api_keys):
                self.error_message = f"{api_type}的key_index({key_index})超出范围，api_key列表只有{len(api_keys)}个元素"  # noqa 501
                return False

            # 检查选中的 api_key 是否为空
            if not api_keys[key_index]:
                self.error_message = f"未配置API KEY，请打开配置填写{api_type}的api_key"
                return False

            # 检查 model 列表
            models = api_config.get("model", [])
            if not models:
                self.error_message = f"未配置Model，请打开配置填写{api_type}的model"
                return False

            # 检查 model_index 是否有效
            model_index = api_config.get("model_index", 0)
            if model_index >= len(models):
                self.error_message = f"{api_type}的model_index({model_index})超出范围，model列表只有{len(models)}个元素"  # noqa 501
                return False

            # 检查选中的 model 是否为空
            if not models[model_index]:
                self.error_message = f"未配置Model，请打开配置填写{api_type}的model"
                return False

            # 检查图片生成配置
            if self.img_api_type != "picsum":
                img_api_config = self.config["img_api"][self.img_api_type]
                img_api_keys = img_api_config.get("api_key", [])
                img_key_index = img_api_config.get("key_index", 0)

                if (
                    not img_api_keys
                    or img_key_index >= len(img_api_keys)
                    or not img_api_keys[img_key_index]
                ):
                    self.error_message = (
                        f"未配置图片生成模型的API KEY，请打开配置填写{self.img_api_type}的api_key"
                    )
                    return False

                img_models = img_api_config.get("model", [])
                img_model_index = img_api_config.get("model_index", 0)

                if (
                    not img_models
                    or img_model_index >= len(img_models)
                    or not img_models[img_model_index]
                ):
                    self.error_message = (
                        f"未配置图片生成的模型，请打开配置填写{self.img_api_type}的model"
                    )
                    return False

            # 检查自动发布配置
            if self.auto_publish:
                valid_cred = any(
                    cred["appid"] and cred["appsecret"] for cred in self.wechat_credentials
                )
                if not valid_cred:
                    self.error_message = "【自动发布】时，需配置微信公众号appid和appsecret"
                    return False

            # 检查 AIForge 配置
            if not self.aiforge_api_key:
                log.print_log("AIForge未配置有效的llm提供商的api_key，将不使用搜索功能")

            return True

        except Exception as e:
            self.error_message = f"配置验证失败: {e}"
            return False

    def reload_config(self):
        """重新加载配置文件"""
        with self._lock:
            log.print_log("重新加载配置文件...", "info")
            return self.load_config()

    def merge_with_user_config(self, user_config: dict) -> dict:
        """
        智能合并用户配置：以默认配置为基础，保留用户已配置的有效值
        这是配置处理的核心逻辑，替代复杂的版本迁移
        """
        import copy

        # 以默认配置为基础
        merged_config = copy.deepcopy(self.default_config)

        if not user_config:
            return merged_config

        preserved_count = 0

        # 递归合并函数
        def merge_dict(default_dict: dict, user_dict: dict, path: str = "") -> int:
            nonlocal preserved_count
            count = 0

            for key, user_value in user_dict.items():
                current_path = f"{path}.{key}" if path else key

                # 如果默认配置中不存在该键，跳过（废弃的配置）
                if key not in default_dict:
                    continue

                default_value = default_dict[key]

                # 对于字典类型，递归合并
                if isinstance(default_value, dict) and isinstance(user_value, dict):
                    count += merge_dict(default_value, user_value, current_path)

                # 对于非空的有意义值，保留用户配置
                elif self._is_meaningful_value(user_value, default_value):
                    default_dict[key] = user_value
                    count += 1

            return count

        preserved_count = merge_dict(merged_config, user_config)

        return merged_config

    def _is_meaningful_value(self, user_value, default_value) -> bool:
        """判断用户值是否有意义（值得保留）"""
        # 对于字符串，不保留空字符串
        if isinstance(user_value, str):
            return user_value.strip() != ""

        # 对于列表，不保留空列表或只有空字符串的列表
        if isinstance(user_value, list):
            if not user_value:
                return False
            # 检查是否所有元素都是空字符串
            if all(isinstance(item, str) and item.strip() == "" for item in user_value):
                return False
            return True

        # 对于布尔值，只有与默认值不同时才保留
        if isinstance(user_value, bool):
            return user_value != default_value

        # 对于数字，只有与默认值不同时才保留
        if isinstance(user_value, (int, float)):
            return user_value != default_value

        # 其他类型，默认保留
        return True

    def smart_update_config(self):
        """
        智能更新配置：替代复杂的版本迁移逻辑
        使用最新默认配置 + 保留用户配置值的方式
        """
        with self._lock:
            try:
                user_config = None

                # 读取用户配置（如果存在）
                if os.path.exists(self.config_path):
                    try:
                        with open(self.config_path, "r", encoding="utf-8") as f:
                            user_config = yaml.safe_load(f)
                    except Exception as e:
                        log.print_log(f"读取用户配置失败: {e}", "warning")
                        user_config = None

                # 合并配置（版本号自动更新为最新）
                merged_config = self.merge_with_user_config(user_config or {})

                # 保存合并后的配置
                with open(self.config_path, "w", encoding="utf-8") as f:
                    yaml.dump(
                        merged_config,
                        f,
                        Dumper=IndentedDumper,
                        allow_unicode=True,
                        sort_keys=False,
                        default_flow_style=False,
                        indent=2,
                    )

                # 更新内存中的配置
                self.config = merged_config

                log.print_log("配置数据加载成功", "success")
                return True

            except Exception as e:
                log.print_log(f"配置数据加载失败: {e}", "error")
                return False

    def migrate_config_if_needed(self):
        """
        智能配置更新：替代复杂的版本迁移逻辑
        总是使用最新默认配置 + 保留用户配置值
        """
        try:
            return self.smart_update_config()
        except Exception:
            # 失败时使用默认配置
            try:
                # 直接使用默认配置重写（版本号已是最新）
                config_path = str(PathManager.get_config_path("config.yaml"))
                with open(config_path, "w", encoding="utf-8") as f:
                    yaml.dump(
                        self.default_config,
                        f,
                        allow_unicode=True,
                        sort_keys=False,
                        default_flow_style=False,
                        indent=2,
                    )

                self.config = self.default_config.copy()
                return True

            except Exception:
                return False
