"""通用工具函数"""
import json


def sse(event_type: str, data: dict) -> str:
    """构造 SSE (Server-Sent Events) 消息字符串"""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
