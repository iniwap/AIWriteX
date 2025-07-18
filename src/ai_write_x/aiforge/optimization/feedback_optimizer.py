import re


class FeedbackOptimizer:
    """优化发送给LLM的反馈信息"""

    @staticmethod
    def compress_error_feedback(error_msg: str, max_length: int = 200) -> str:
        """压缩错误反馈"""
        if len(error_msg) <= max_length:
            return error_msg

        # 提取关键错误信息
        key_patterns = [
            r"(NameError|TypeError|ValueError|AttributeError|ImportError): (.+)",
            r"line (\d+)",
            r'File "([^"]+)"',
        ]

        compressed_parts = []
        for pattern in key_patterns:
            matches = re.findall(pattern, error_msg)
            if matches:
                compressed_parts.extend([str(m) for m in matches])

        compressed = " | ".join(compressed_parts[:3])  # 只保留前3个关键信息
        return compressed if compressed else error_msg[:max_length]

    @staticmethod
    def compress_success_feedback(result: dict, max_length: int = 100) -> str:
        """压缩成功反馈"""
        if not result:
            return "OK"

        # 只返回结果类型和大小信息
        result_type = type(result).__name__
        if isinstance(result, (list, dict)):
            size_info = f"len={len(result)}"
        else:
            size_info = str(result)[:50]

        return f"{result_type}:{size_info}"
