import time
import json
import hashlib
import threading
from pathlib import Path
from typing import Any, Optional, Dict, List
from peewee import CharField, DoubleField, IntegerField, Model, TextField, Case
from playhouse.sqlite_ext import SqliteExtDatabase


class AiForgeCodeCache:
    """基于Peewee ORM的AiForge代码缓存管理器"""

    def __init__(self, cache_dir: Path, config: dict = None):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 缓存配置
        self.config = config or {
            "max_modules": 20,
            "failure_threshold": 0.8,
            "max_age_days": 30,
            "cleanup_interval": 10,
        }

        # 数据库和文件路径
        self.db_path = self.cache_dir / "code_cache.db"
        self.modules_dir = self.cache_dir / "modules"
        self.modules_dir.mkdir(exist_ok=True)

        self._lock = threading.RLock()
        self._search_count = 0

        # 初始化数据库
        self._init_database()

    def _init_database(self):
        """初始化Peewee数据库和模型"""
        # 创建数据库连接
        self.db = SqliteExtDatabase(
            str(self.db_path),
            pragmas={
                "journal_mode": "wal",
                "cache_size": -1024 * 64,  # 64MB
                "foreign_keys": 1,
                "ignore_check_constraints": 0,
                "synchronous": 0,
            },
        )

        # 定义模型
        class BaseModel(Model):
            class Meta:
                database = self.db

        class CodeModule(BaseModel):
            module_id = CharField(primary_key=True)
            instruction_hash = CharField(index=True)
            file_path = CharField()
            created_at = DoubleField(default=time.time)
            last_used = DoubleField(default=time.time)
            success_count = IntegerField(default=0)
            failure_count = IntegerField(default=0)
            metadata = TextField(default="{}")

            @property
            def success_rate(self):
                total = self.success_count + self.failure_count
                return self.success_count / total if total > 0 else 0.5

            @property
            def total_attempts(self):
                return self.success_count + self.failure_count

            class Meta:
                table_name = "code_modules"
                indexes = ((("success_count", "failure_count"), False),)

        self.CodeModule = CodeModule

        # 创建表
        with self.db:
            self.db.create_tables([CodeModule], safe=True)

    def _generate_instruction_hash(self, instruction: str) -> str:
        """生成指令哈希"""
        return hashlib.md5(instruction.encode()).hexdigest()

    def get_cached_modules(self, instruction: str) -> List[Any]:
        """获取缓存的模块，按成功率排序"""
        instruction_hash = self._generate_instruction_hash(instruction)

        with self._lock:
            try:
                modules = (
                    self.CodeModule.select()
                    .where(self.CodeModule.instruction_hash == instruction_hash)
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

    def save_code_module(self, instruction: str, code: str, metadata: dict = None) -> Optional[str]:
        """保存代码模块到缓存"""
        if not self._validate_code(code):
            return None

        instruction_hash = self._generate_instruction_hash(instruction)
        module_id = f"module_{instruction_hash}_{int(time.time())}"
        file_path = self.modules_dir / f"{module_id}.py"

        try:
            # 保存代码文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)

            # 保存到数据库
            current_time = time.time()
            metadata_json = json.dumps(metadata or {})

            with self._lock:
                self.CodeModule.create(
                    module_id=module_id,
                    instruction_hash=instruction_hash,
                    file_path=str(file_path),
                    created_at=current_time,
                    last_used=current_time,
                    metadata=metadata_json,
                )

            return module_id

        except Exception:
            if file_path.exists():
                file_path.unlink()
            return None

    def load_module(self, module_id: str):
        """加载缓存的模块"""
        with self._lock:
            try:
                module_record = self.CodeModule.get(self.CodeModule.module_id == module_id)
            except self.CodeModule.DoesNotExist:
                return None

            file_path = Path(module_record.file_path)
            if not file_path.exists():
                self._remove_module(module_id)
                return None

            try:
                import importlib.util

                spec = importlib.util.spec_from_file_location(module_id, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # 更新最后使用时间
                module_record.last_used = time.time()
                module_record.save()

                return module

            except Exception:
                self._remove_module(module_id)
                return None

    def update_module_stats(self, module_id: str, success: bool):
        """更新模块统计信息"""
        with self._lock:
            try:
                module_record = self.CodeModule.get(self.CodeModule.module_id == module_id)

                if success:
                    module_record.success_count += 1
                else:
                    module_record.failure_count += 1

                module_record.save()

            except self.CodeModule.DoesNotExist:
                pass

    def cleanup(self):
        """清理过期和失败的模块"""
        current_time = time.time()
        max_age_seconds = self.config["max_age_days"] * 24 * 3600

        with self._lock:
            # 清理过期模块
            expired_modules = self.CodeModule.select().where(
                self.CodeModule.created_at < (current_time - max_age_seconds)
            )

            for module in expired_modules:
                self._remove_module_file(module.file_path)

            # 删除过期记录
            (
                self.CodeModule.delete()
                .where(self.CodeModule.created_at < (current_time - max_age_seconds))
                .execute()
            )

            # 清理失败率过高的模块
            failed_modules = self.CodeModule.select().where(
                (self.CodeModule.success_count + self.CodeModule.failure_count) >= 3,
                (
                    self.CodeModule.failure_count
                    / (self.CodeModule.success_count + self.CodeModule.failure_count)
                )
                >= self.config["failure_threshold"],
            )

            for module in failed_modules:
                self._remove_module_file(module.file_path)

            # 删除失败率过高的记录
            (
                self.CodeModule.delete()
                .where(
                    (self.CodeModule.success_count + self.CodeModule.failure_count) >= 3,
                    (
                        self.CodeModule.failure_count
                        / (self.CodeModule.success_count + self.CodeModule.failure_count)
                    )
                    >= self.config["failure_threshold"],
                )
                .execute()
            )

            # 保持模块数量限制
            total_count = self.CodeModule.select().count()

            if total_count > self.config["max_modules"]:
                excess_count = total_count - self.config["max_modules"]

                old_modules = (
                    self.CodeModule.select()
                    .order_by(self.CodeModule.last_used.asc())
                    .limit(excess_count)
                )

                for module in old_modules:
                    self._remove_module_file(module.file_path)

                # 删除最旧的记录
                old_module_ids = [m.module_id for m in old_modules]
                (
                    self.CodeModule.delete()
                    .where(self.CodeModule.module_id.in_(old_module_ids))
                    .execute()
                )

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            total = self.CodeModule.select().count()

            current_time = time.time()
            max_age_seconds = self.config["max_age_days"] * 24 * 3600

            valid = (
                self.CodeModule.select()
                .where(self.CodeModule.created_at >= (current_time - max_age_seconds))
                .count()
            )

            expired = total - valid

            # 成功率统计
            modules_with_attempts = self.CodeModule.select().where(
                (self.CodeModule.success_count + self.CodeModule.failure_count) > 0
            )

            if modules_with_attempts.count() > 0:
                avg_success_rate = (
                    sum(m.success_rate for m in modules_with_attempts)
                    / modules_with_attempts.count()
                )
            else:
                avg_success_rate = 0.0

            return {
                "total": total,
                "valid": valid,
                "expired": expired,
                "average_success_rate": avg_success_rate,
                "cleanup_count": self._search_count,
            }

    def _validate_code(self, code: str) -> bool:
        """验证代码的基本可执行性"""
        try:
            compile(code, "<string>", "exec")
            return True
        except SyntaxError:
            return False

    def _remove_module(self, module_id: str):
        """移除指定模块"""
        with self._lock:
            try:
                module_record = self.CodeModule.get(self.CodeModule.module_id == module_id)
                self._remove_module_file(module_record.file_path)
                module_record.delete_instance()
            except self.CodeModule.DoesNotExist:
                pass

    def _remove_module_file(self, file_path: str):
        """删除模块文件"""
        try:
            Path(file_path).unlink(missing_ok=True)
        except Exception:
            pass

    def should_cleanup(self) -> bool:
        """判断是否需要清理"""
        self._search_count += 1
        return self._search_count % self.config["cleanup_interval"] == 0

    def close(self):
        """关闭数据库连接"""
        if hasattr(self, "db"):
            self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
