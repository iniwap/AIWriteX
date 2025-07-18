import hashlib
import time
import json
from pathlib import Path
from typing import Any, Optional, List
from peewee import Case
from .code_cache import AiForgeCodeCache


class EnhancedAiForgeCodeCache(AiForgeCodeCache):
    """增强的AIForge代码缓存管理器 - 支持多种缓存策略"""

    def __init__(self, cache_dir: Path, config: dict = None):
        super().__init__(cache_dir, config)

        # 任务类型关键词映射
        self.task_keywords = {
            "web_search": ["搜索", "search", "查找", "爬取", "crawl", "scrape", "抓取"],
            "data_processing": ["分析", "analyze", "处理", "process", "计算", "calculate", "统计"],
            "file_operation": ["文件", "file", "读取", "read", "写入", "write", "保存", "save"],
            "api_call": ["api", "接口", "request", "请求", "http", "get", "post"],
            "web_request": ["网页", "webpage", "url", "html", "http", "requests"],
        }

    def _generate_cache_key(
        self,
        instruction: str,
        executor_type: str = None,
        task_category: str = None,
        use_semantic: bool = True,
    ) -> str:
        """生成基于执行器类型和任务分类的缓存键"""

        # 策略1: 优先使用明确的执行器类型和任务分类
        if executor_type and task_category:
            key_base = f"{executor_type}_{task_category}"
            return hashlib.md5(key_base.encode()).hexdigest()

        # 策略2: 基于执行器类型推断
        if executor_type:
            inferred_category = self._infer_category_from_executor(executor_type)
            if inferred_category:
                key_base = f"{executor_type}_{inferred_category}"
                return hashlib.md5(key_base.encode()).hexdigest()

        # 策略3: 基于指令内容分析任务类型
        if use_semantic:
            analyzed_type = self._analyze_task_type(instruction)
            key_base = f"semantic_{analyzed_type}"
            return hashlib.md5(key_base.encode()).hexdigest()

        # 策略4: 回退到原始指令哈希
        return self._generate_instruction_hash(instruction)

    def _analyze_task_type(self, instruction: str) -> str:
        """智能分析任务类型"""
        instruction_lower = instruction.lower()

        # 计算每种任务类型的匹配分数
        type_scores = {}
        for task_type, keywords in self.task_keywords.items():
            score = sum(1 for keyword in keywords if keyword in instruction_lower)
            if score > 0:
                type_scores[task_type] = score

        # 返回得分最高的任务类型
        if type_scores:
            return max(type_scores.items(), key=lambda x: x[1])[0]

        return "general"

    def _infer_category_from_executor(self, executor_type: str) -> str:
        """从执行器类型推断任务分类"""
        executor_mapping = {
            "DefaultModuleExecutor": "general",
            "FunctionBasedExecutor": "function_based",
            "DataProcessingExecutor": "data_processing",
            "WebRequestExecutor": "web_request",
            "FileOperationExecutor": "file_operation",
            "APICallExecutor": "api_call",
        }
        return executor_mapping.get(executor_type, "general")

    def get_cached_modules_enhanced(self, instruction: str, executor_type: str = None) -> List[Any]:
        """获取缓存模块 - 支持多种匹配策略"""

        results = []

        # 策略1: 精确匹配（基于执行器类型）
        if executor_type:
            exact_key = self._generate_cache_key(
                instruction, executor_type, self._infer_category_from_executor(executor_type)
            )
            exact_matches = self._get_modules_by_key(exact_key)
            results.extend([(m, "exact") for m in exact_matches])

        # 策略2: 语义匹配（基于任务类型）
        semantic_key = self._generate_cache_key(instruction, use_semantic=True)
        semantic_matches = self._get_modules_by_key(semantic_key)
        results.extend([(m, "semantic") for m in semantic_matches])

        # 策略3: 原始指令匹配（回退策略）
        original_key = self._generate_instruction_hash(instruction)
        original_matches = self._get_modules_by_key(original_key)
        results.extend([(m, "original") for m in original_matches])

        # 按匹配策略优先级和成功率排序
        return self._rank_and_deduplicate_results(results)

    def _get_modules_by_key(self, cache_key: str) -> List[Any]:
        """根据缓存键获取模块"""
        with self._lock:
            try:
                modules = (
                    self.CodeModule.select()
                    .where(self.CodeModule.instruction_hash == cache_key)
                    .order_by(
                        Case(
                            None,
                            [
                                (
                                    (self.CodeModule.success_count + self.CodeModule.failure_count)
                                    == 0,
                                    0.5,
                                )
                            ],
                            self.CodeModule.success_count
                            / (self.CodeModule.success_count + self.CodeModule.failure_count),
                        ).desc()
                    )
                )
                return [
                    (m.module_id, m.file_path, m.success_count, m.failure_count) for m in modules
                ]
            except Exception:
                return []

    def _rank_and_deduplicate_results(self, results: List[tuple]) -> List[Any]:
        """对结果进行排序和去重"""
        # 按策略优先级排序: exact > semantic > original
        strategy_priority = {"exact": 3, "semantic": 2, "original": 1}

        # 去重（基于module_id）
        seen_modules = set()
        ranked_results = []

        for (module_id, file_path, success_count, failure_count), strategy in results:
            if module_id not in seen_modules:
                seen_modules.add(module_id)
                # 计算综合分数：策略优先级 + 成功率
                total_attempts = success_count + failure_count
                success_rate = success_count / total_attempts if total_attempts > 0 else 0.5
                score = strategy_priority[strategy] + success_rate

                ranked_results.append((module_id, file_path, success_count, failure_count, score))

        # 按综合分数排序
        ranked_results.sort(key=lambda x: x[4], reverse=True)

        # 返回原格式
        return [(m[0], m[1], m[2], m[3]) for m in ranked_results]

    def save_enhanced_module(
        self, instruction: str, code: str, executor_type: str = None, metadata: dict = None
    ) -> Optional[str]:
        """保存增强代码模块"""

        if not self._validate_code(code):
            return None

        # 生成基于执行器类型的缓存键
        cache_key = self._generate_cache_key(
            instruction, executor_type, self._infer_category_from_executor(executor_type)
        )

        module_id = f"module_{cache_key}_{int(time.time())}"
        file_path = self.modules_dir / f"{module_id}.py"

        try:
            # 保存代码文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)

            # 扩展元数据
            extended_metadata = {
                "executor_type": executor_type,
                "task_category": (
                    self._infer_category_from_executor(executor_type) if executor_type else None
                ),
                "original_instruction": instruction,
                **(metadata or {}),
            }

            # 保存到数据库
            current_time = time.time()
            with self._lock:
                self.CodeModule.create(
                    module_id=module_id,
                    instruction_hash=cache_key,  # 使用新的缓存键
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
