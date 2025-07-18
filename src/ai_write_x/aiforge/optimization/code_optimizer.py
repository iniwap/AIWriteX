import re
import ast
import keyword


class CodeOptimizer:
    """代码压缩和混淆器"""

    def __init__(self):
        self.var_mapping = {}
        self.func_mapping = {}
        self.short_names = self._generate_short_names()
        self.reserved_words = set(keyword.kwlist) | {
            "__result__",
            "requests",
            "json",
            "time",
            "os",
            "sys",
        }

    def _generate_short_names(self) -> list:
        """生成短变量名序列"""
        names = []
        # 单字符变量名
        for c in "abcdefghijklmnopqrstuvwxyz":
            if c not in keyword.kwlist:
                names.append(c)
        # 双字符变量名
        for c1 in "abcdefghijklmnopqrstuvwxyz":
            for c2 in "abcdefghijklmnopqrstuvwxyz":
                name = c1 + c2
                if name not in keyword.kwlist:
                    names.append(name)
        return names

    def optimize_code(self, code: str, aggressive=True) -> str:
        """优化代码以减少token消耗"""
        try:
            # 1. 移除注释和空行
            code = self._remove_comments_and_empty_lines(code)

            # 2. 变量名混淆
            if aggressive:
                code = self._obfuscate_variables(code)

            # 3. 压缩空白字符
            code = self._compress_whitespace(code)

            # 4. 简化字符串
            code = self._optimize_strings(code)

            return code
        except Exception:
            # 如果优化失败，返回原代码
            return code

    def _remove_comments_and_empty_lines(self, code: str) -> str:
        """移除注释和空行"""
        lines = []
        for line in code.split("\n"):
            # 移除行注释
            if "#" in line:
                # 简单处理，不在字符串内的#
                in_string = False
                quote_char = None
                for i, char in enumerate(line):
                    if char in ['"', "'"] and (i == 0 or line[i - 1] != "\\"):
                        if not in_string:
                            in_string = True
                            quote_char = char
                        elif char == quote_char:
                            in_string = False
                    elif char == "#" and not in_string:
                        line = line[:i].rstrip()
                        break

            # 保留非空行
            if line.strip():
                lines.append(line)

        return "\n".join(lines)

    def _obfuscate_variables(self, code: str) -> str:
        """变量名混淆"""
        try:
            tree = ast.parse(code)

            # 收集所有变量名
            variables = set()
            functions = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    if node.id not in self.reserved_words:
                        variables.add(node.id)
                elif isinstance(node, ast.FunctionDef):
                    if node.name not in self.reserved_words:
                        functions.add(node.name)

            # 创建映射
            name_idx = 0
            for var in sorted(variables):
                if var not in self.var_mapping and name_idx < len(self.short_names):
                    self.var_mapping[var] = self.short_names[name_idx]
                    name_idx += 1

            for func in sorted(functions):
                if func not in self.func_mapping and name_idx < len(self.short_names):
                    self.func_mapping[func] = self.short_names[name_idx]
                    name_idx += 1

            # 应用映射
            for old_name, new_name in {**self.var_mapping, **self.func_mapping}.items():
                # 使用正则表达式替换，确保只替换完整的标识符
                pattern = r"\b" + re.escape(old_name) + r"\b"
                code = re.sub(pattern, new_name, code)

            return code
        except Exception:
            return code

    def _compress_whitespace(self, code: str) -> str:
        """压缩空白字符"""
        lines = []
        for line in code.split("\n"):
            # 保持必要的缩进，但移除多余空格
            stripped = line.lstrip()
            if stripped:
                indent_level = len(line) - len(stripped)
                # 将缩进标准化为最小空格数
                indent = " " * (indent_level // 4 * 4) if indent_level > 0 else ""
                # 压缩行内空格
                compressed = re.sub(r"\s+", " ", stripped)
                lines.append(indent + compressed)

        return "\n".join(lines)

    def _optimize_strings(self, code: str) -> str:
        """优化字符串字面量"""
        # 将长字符串替换为变量
        string_vars = {}
        string_counter = 0

        def replace_long_strings(match):
            nonlocal string_counter
            string_content = match.group(0)
            if len(string_content) > 20:  # 只替换长字符串
                var_name = f"s{string_counter}"
                string_vars[var_name] = string_content
                string_counter += 1
                return var_name
            return string_content

        # 匹配字符串字面量
        code = re.sub(r'["\'][^"\']*["\']', replace_long_strings, code)

        # 在代码开头添加字符串变量定义
        if string_vars:
            var_definitions = "\n".join([f"{var}={value}" for var, value in string_vars.items()])
            code = var_definitions + "\n" + code

        return code
