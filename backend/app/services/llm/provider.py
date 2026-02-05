from __future__ import annotations

import logging
import traceback
from typing import AsyncGenerator, List
import litellm
from app.config import settings

logger = logging.getLogger(__name__)


MODEL_CONFIGS = {
    "deepseek": {
        "model": "deepseek/deepseek-chat",
        "api_key": lambda: settings.deepseek_api_key,
        "cost_per_1k_input": 0.0001,
        "cost_per_1k_output": 0.0002,
    },
    "minimax": {
        "model": "openai/MiniMax-Text-01",
        "api_key": lambda: settings.minimax_api_key,
        "api_base": "https://api.minimax.chat/v1",
        "cost_per_1k_input": 0.0005,
        "cost_per_1k_output": 0.001,
    },
    "claude": {
        "model": "anthropic/claude-sonnet-4-20250514",
        "api_key": lambda: settings.anthropic_api_key,
        "cost_per_1k_input": 0.003,
        "cost_per_1k_output": 0.015,
    },
    "openai": {
        "model": "gpt-4o",
        "api_key": lambda: settings.openai_api_key,
        "cost_per_1k_input": 0.0025,
        "cost_per_1k_output": 0.01,
    },
}


class LLMProvider:
    def get_available_models(self) -> List[dict]:
        return [
            {"key": key, "model": config["model"], "available": bool(config["api_key"]())}
            for key, config in MODEL_CONFIGS.items()
        ]

    async def chat(
        self,
        model_key: str,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> dict:
        config = MODEL_CONFIGS.get(model_key)
        if not config:
            logger.error(f"[LLM] 未知模型: {model_key}, 可用模型: {list(MODEL_CONFIGS.keys())}")
            raise ValueError(f"Unknown model: {model_key}")

        api_key = config["api_key"]()
        if not api_key:
            logger.error(f"[LLM] 模型 {model_key} 的API密钥未配置")
            raise ValueError(f"API key not configured for model: {model_key}")

        logger.info(f"[LLM] 调用模型={model_key}, 实际模型={config['model']}, messages数量={len(messages)}")
        logger.debug(f"[LLM] 请求参数: temperature={temperature}, max_tokens={max_tokens}")

        kwargs = {
            "model": config["model"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "api_key": api_key,
        }
        if "api_base" in config:
            kwargs["api_base"] = config["api_base"]
            logger.debug(f"[LLM] 使用自定义API地址: {config['api_base']}")

        try:
            response = await litellm.acompletion(**kwargs)
        except Exception as e:
            logger.error(f"[LLM] 调用失败 模型={model_key}: {str(e)}\n{traceback.format_exc()}")
            raise

        usage = response.usage
        content = response.choices[0].message.content

        input_cost = (usage.prompt_tokens / 1000) * config["cost_per_1k_input"]
        output_cost = (usage.completion_tokens / 1000) * config["cost_per_1k_output"]

        logger.info(f"[LLM] 调用成功 模型={model_key}, prompt_tokens={usage.prompt_tokens}, "
                   f"completion_tokens={usage.completion_tokens}, cost=${input_cost + output_cost:.6f}")

        return {
            "content": content,
            "model": model_key,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "cost_usd": input_cost + output_cost,
        }

    async def chat_stream(
        self,
        model_key: str,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        config = MODEL_CONFIGS.get(model_key)
        if not config:
            logger.error(f"[LLM Stream] 未知模型: {model_key}")
            raise ValueError(f"Unknown model: {model_key}")

        api_key = config["api_key"]()
        if not api_key:
            logger.error(f"[LLM Stream] 模型 {model_key} 的API密钥未配置")
            raise ValueError(f"API key not configured for model: {model_key}")

        logger.info(f"[LLM Stream] 开始流式调用 模型={model_key}, 实际模型={config['model']}")

        kwargs = {
            "model": config["model"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "api_key": api_key,
            "stream": True,
        }
        if "api_base" in config:
            kwargs["api_base"] = config["api_base"]

        try:
            response = await litellm.acompletion(**kwargs)
        except Exception as e:
            logger.error(f"[LLM Stream] 流式调用初始化失败 模型={model_key}: {str(e)}\n{traceback.format_exc()}")
            raise

        chunk_count = 0
        try:
            async for chunk in response:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    chunk_count += 1
                    yield delta.content
            logger.info(f"[LLM Stream] 流式调用完成 模型={model_key}, chunks={chunk_count}")
        except Exception as e:
            logger.error(f"[LLM Stream] 流式响应处理失败 (已接收 {chunk_count} chunks): {str(e)}\n{traceback.format_exc()}")
            raise


# Singleton
llm_provider = LLMProvider()
