"""
LLM 网关

优先调用配置好的真实大模型；没有 API Key 或依赖缺失时，自动降级到本地
演示模型，保证 Sprint1 的注册、上传、RAG 问答、摘要、知识点提取流程可离线跑通。
"""
from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass

from ..core.config import settings


@dataclass
class LLMResponse:
    content: str


def _sentence_split(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text or "").strip()
    if not normalized:
        return []
    parts = re.split(r"(?<=[。！？!?；;])\s*", normalized)
    return [part.strip() for part in parts if part.strip()]


def _extract_between(text: str, start_marker: str, end_marker: str | None = None) -> str:
    start = text.find(start_marker)
    if start < 0:
        return ""
    start += len(start_marker)
    if end_marker is None:
        return text[start:].strip()
    end = text.find(end_marker, start)
    if end < 0:
        return text[start:].strip()
    return text[start:end].strip()


def _extract_source_blocks(context: str) -> list[tuple[str, str]]:
    blocks = []
    for raw in context.split("---"):
        raw = raw.strip()
        if not raw:
            continue
        lines = raw.splitlines()
        label = lines[0].strip() if lines else "来源"
        body = "\n".join(lines[1:]).strip()
        if body:
            blocks.append((label, body))
    return blocks


class LocalDemoLLM:
    """无需网络的演示 LLM，输出稳定、可解释。"""

    def invoke(self, prompt: str) -> LLMResponse:
        if "JSON数组" in prompt and "知识点" in prompt:
            return LLMResponse(self._knowledge_json(prompt))
        if "摘要" in prompt or "总结" in prompt:
            return LLMResponse(self._summary(prompt))
        return LLMResponse(self._answer(prompt))

    async def astream(self, prompt: str):
        content = self._answer(prompt)
        for token in re.findall(r".{1,12}", content, flags=re.S):
            await asyncio.sleep(0.01)
            yield LLMResponse(token)

    def _summary(self, prompt: str) -> str:
        source = _extract_between(prompt, "原文内容：")
        sentences = _sentence_split(source)
        if not sentences:
            return "暂未读取到可摘要的正文内容。"

        core = sentences[:5]
        bullets = "\n".join(f"- {sentence[:120]}" for sentence in core[:4])
        return (
            "### 文档摘要\n"
            f"{core[0][:180]}\n\n"
            "### 核心要点\n"
            f"{bullets}\n\n"
            "### 学习建议\n"
            "建议先通读摘要，再围绕上述要点逐条追问，最后用习题或复述检查掌握情况。"
        )

    def _knowledge_json(self, prompt: str) -> str:
        source = _extract_between(prompt, "原文内容：")
        sentences = _sentence_split(source)
        points = []
        for index, sentence in enumerate(sentences[:6], 1):
            title = re.sub(r"[：:，,。！？!?\s].*$", "", sentence).strip()[:18]
            if len(title) < 4:
                title = f"知识点{index}"
            points.append(
                {
                    "title": title,
                    "description": sentence[:120],
                }
            )
        if not points:
            points = [{"title": "文档主题", "description": "当前文档内容较短，可继续上传更完整资料后再提取。"}]
        return json.dumps(points, ensure_ascii=False)

    def _answer(self, prompt: str) -> str:
        context = _extract_between(prompt, "参考资料：", "用户问题：")
        query = _extract_between(prompt, "用户问题：", "请基于以上参考资料")
        blocks = _extract_source_blocks(context)

        if blocks and "未找到相关知识库内容" not in context:
            evidence = []
            for idx, (label, body) in enumerate(blocks[:3], 1):
                first_sentence = (_sentence_split(body) or [body])[0]
                evidence.append(f"{idx}. {first_sentence[:180]}（{label}）")
            joined = "\n".join(evidence)
            return (
                f"### 回答\n"
                f"围绕你的问题“{query or '当前问题'}”，我从已上传资料中找到了相关片段。"
                "可以先按下面几个要点理解：\n\n"
                f"{joined}\n\n"
                "### 结论\n"
                "这些资料说明，回答问题时应优先抓住材料中的核心概念、关键原因和对应例子。"
                "如果需要，我可以继续把这些内容整理成提纲、表格或练习题。"
            )

        return (
            "### 回答\n"
            f"你问的是“{query or prompt[:80]}”。当前知识库里还没有检索到足够相关的上传资料，"
            "所以我先给出通用学习建议：先补充课程资料或笔记，再围绕主题提问，系统就能基于资料给出带来源的回答。\n\n"
            "### 建议\n"
            "- 上传 PDF、Word、TXT 或 Markdown 学习资料\n"
            "- 针对一个章节或概念提问\n"
            "- 使用“生成摘要”和“知识点提取”快速建立学习框架"
        )


class ChatOpenAIGateway:
    def __init__(self, client):
        self.client = client

    def invoke(self, prompt: str) -> LLMResponse:
        result = self.client.invoke(prompt)
        return LLMResponse(getattr(result, "content", str(result)))

    async def astream(self, prompt: str):
        async for chunk in self.client.astream(prompt):
            yield LLMResponse(getattr(chunk, "content", ""))


def _is_real_key(value: str) -> bool:
    return bool(value and value.strip() and not value.lower().startswith(("your_", "sk-xxx", "change-")))


def get_llm(temperature: float = 0.7):
    """
    获取LLM实例。
    - 配置真实 API Key 时：调用 DeepSeek/硅基流动兼容 OpenAI 接口。
    - 未配置或依赖不可用时：使用 LocalDemoLLM。
    """
    provider = (settings.LLM_PROVIDER or "").lower()
    has_deepseek_key = _is_real_key(settings.DEEPSEEK_API_KEY)
    has_siliconflow_key = _is_real_key(settings.SILICONFLOW_API_KEY)
    needs_real_llm = (provider == "deepseek" and has_deepseek_key) or (
        provider == "siliconflow" and has_siliconflow_key
    )

    try:
        from langchain_openai import ChatOpenAI
    except Exception as exc:
        if needs_real_llm:
            raise RuntimeError("Real LLM is configured, but langchain-openai is not installed. Run: pip install -r requirements.txt") from exc
        return LocalDemoLLM()

    if provider == "deepseek" and has_deepseek_key:
        return ChatOpenAIGateway(
            ChatOpenAI(
                model=settings.DEEPSEEK_MODEL,
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL,
                temperature=temperature,
                streaming=True,
            )
        )

    if provider == "siliconflow" and has_siliconflow_key:
        return ChatOpenAIGateway(
            ChatOpenAI(
                model=settings.SILICONFLOW_MODEL,
                api_key=settings.SILICONFLOW_API_KEY,
                base_url=settings.SILICONFLOW_BASE_URL,
                temperature=temperature,
                streaming=True,
            )
        )

    return LocalDemoLLM()
