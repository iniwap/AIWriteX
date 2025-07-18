import time
import json
import re
from pathlib import Path
from typing import Any, Optional, Dict, List
from .enhanced_cache import EnhancedAiForgeCodeCache


class TemplateBasedCodeCache(EnhancedAiForgeCodeCache):
    """基于模板的代码缓存管理器 - 继承增强缓存功能"""

    def __init__(self, cache_dir: Path, config: dict = None):
        super().__init__(cache_dir, config)

        # 预定义的任务模板模式（扩展父类的任务类型）
        self.task_templates = {
            "web_search": {
                "pattern": r"请生成一个搜索函数.*搜索引擎URL模式.*返回数据格式",
                "key_params": ["topic", "max_results", "min_results"],
                "template_id": "web_search_v1",
            },
            "data_analysis": {
                "pattern": r"分析.*数据.*生成报告",
                "key_params": ["data_source", "analysis_type"],
                "template_id": "data_analysis_v1",
            },
            "file_processing": {
                "pattern": r"处理.*文件.*批量操作",
                "key_params": ["file_pattern", "operation_type"],
                "template_id": "file_processing_v1",
            },
        }

    def _generate_cache_key(
        self,
        instruction: str,
        executor_type: str = None,
        task_category: str = None,
        use_semantic: bool = True,
    ) -> str:
        """重写缓存键生成，优先使用模板匹配"""

        # 策略1: 模板匹配（最高优先级）
        template_info = self._extract_template_info(instruction)
        if template_info["template_id"]:
            return template_info["cache_key"]

        # 策略2-4: 回退到父类的增强缓存策略
        return super()._generate_cache_key(instruction, executor_type, task_category, use_semantic)

    def _extract_template_info(self, instruction: str) -> Dict:
        """从指令中提取模板信息"""
        for template_name, template_config in self.task_templates.items():
            if re.search(template_config["pattern"], instruction, re.DOTALL | re.IGNORECASE):
                # 提取参数值
                params = self._extract_parameters(instruction, template_config["key_params"])
                return {
                    "template_id": template_config["template_id"],
                    "template_name": template_name,
                    "parameters": params,
                    "cache_key": template_config["template_id"],
                }

        # 如果没有匹配的模板，回退到语义分析
        analyzed_type = self._analyze_task_type(instruction)
        return {
            "template_id": None,
            "template_name": "semantic",
            "parameters": {},
            "cache_key": f"semantic_{analyzed_type}",
        }

    def _extract_parameters(self, instruction: str, param_names: List[str]) -> Dict:
        """从指令中提取参数值"""
        params = {}

        # 针对搜索任务的参数提取
        if "topic" in param_names:
            topic_match = re.search(r'search_web\("([^"]+)"', instruction)
            if topic_match:
                params["topic"] = topic_match.group(1)

        if "max_results" in param_names:
            max_results_match = re.search(r'search_web\("[^"]+",\s*(\d+)', instruction)
            if max_results_match:
                params["max_results"] = int(max_results_match.group(1))

        # 针对文件处理任务的参数提取
        if "file_pattern" in param_names:
            pattern_match = re.search(r"文件.*?([*\w\.]+)", instruction)
            if pattern_match:
                params["file_pattern"] = pattern_match.group(1)

        return params

    def get_cached_modules_by_template(self, instruction: str) -> List[Any]:
        """基于模板获取缓存模块 - 结合增强缓存的多策略查询"""
        template_info = self._extract_template_info(instruction)

        # 如果有模板匹配，使用模板缓存逻辑
        if template_info["template_id"]:
            cache_key = template_info["cache_key"]

            with self._lock:
                try:
                    modules = (
                        self.CodeModule.select()
                        .where(self.CodeModule.instruction_hash == cache_key)
                        .order_by(self.CodeModule.success_count.desc())
                    )

                    results = []
                    for module in modules:
                        metadata = json.loads(module.metadata)

                        if self._is_template_compatible(template_info, metadata):
                            results.append(
                                (
                                    module.module_id,
                                    module.file_path,
                                    module.success_count,
                                    module.failure_count,
                                    metadata.get("parameters", {}),
                                )
                            )

                    return results
                except Exception:
                    return []
        else:
            # 没有模板匹配，使用父类的增强缓存策略
            enhanced_results = self.get_cached_modules_enhanced(instruction)
            # 转换格式以匹配模板缓存的返回格式
            return [(r[0], r[1], r[2], r[3], {}) for r in enhanced_results]

    def _is_template_compatible(self, template_info: Dict, metadata: Dict) -> bool:
        """检查模板兼容性"""
        return metadata.get("template_id") == template_info.get("template_id")

    def save_template_module(
        self, instruction: str, code: str, metadata: dict = None
    ) -> Optional[str]:
        """保存模板化代码模块 - 结合增强缓存的保存策略"""
        if not self._validate_code(code):
            return None

        template_info = self._extract_template_info(instruction)
        cache_key = template_info["cache_key"]

        # 根据是否有模板匹配选择不同的保存策略
        if template_info["template_id"]:
            # 模板化保存
            module_id = f"template_{template_info['template_name']}_{int(time.time())}"
            file_path = self.modules_dir / f"{module_id}.py"

            try:
                # 生成参数化代码模板
                template_code = self._parameterize_code(code, template_info["parameters"])

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(template_code)

                # 扩展元数据
                extended_metadata = {
                    "template_id": template_info["template_id"],
                    "template_name": template_info["template_name"],
                    "parameters": template_info["parameters"],
                    "original_instruction": instruction,
                    "is_template": True,
                    **(metadata or {}),
                }

                current_time = time.time()
                with self._lock:
                    self.CodeModule.create(
                        module_id=module_id,
                        instruction_hash=cache_key,
                        file_path=str(file_path),
                        created_at=current_time,
                        last_used=current_time,
                        metadata=json.dumps(extended_metadata),
                    )

                return module_id

            except Exception:
                if file_path.exists():
                    file_path.unlink()
                return None
        else:
            # 回退到增强缓存的保存策略
            return self.save_enhanced_module(instruction, code, metadata=metadata)

    def _parameterize_code(self, code: str, params: Dict) -> str:
        """将代码参数化"""
        parameterized_code = code
        for param_name, param_value in params.items():
            if isinstance(param_value, str) and param_value in code:
                placeholder = f"{{{{ {param_name} }}}}"
                parameterized_code = parameterized_code.replace(param_value, placeholder)
        return parameterized_code

    def execute_template_module(self, module_id: str, current_params: Dict) -> Any:
        """执行模板模块，动态替换参数"""
        module = self.load_module(module_id)
        if not module:
            return None

        try:
            module_record = self.CodeModule.get(self.CodeModule.module_id == module_id)
            metadata = json.loads(module_record.metadata)

            # 如果是模板模块，进行参数替换
            if metadata.get("is_template", False):
                original_params = metadata.get("parameters", {})

                # 动态替换参数执行
                if hasattr(module, "search_web"):

                    def parameterized_search(topic, max_results):
                        return module.search_web(topic, max_results)

                    result = parameterized_search(
                        current_params.get("topic", original_params.get("topic")),
                        current_params.get("max_results", original_params.get("max_results", 10)),
                    )
                    return result

            # 通用执行逻辑
            if hasattr(module, "__result__"):
                return getattr(module, "__result__")

            return None

        except Exception:
            return None
