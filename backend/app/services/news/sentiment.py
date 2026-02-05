"""新闻情感分析服务"""
from __future__ import annotations

import logging
import json
from typing import Optional
from app.services.llm.provider import llm_provider

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """新闻情感分析器 - 使用LLM分析新闻情感"""

    def __init__(self, model_name: str = "deepseek"):
        self.model_name = model_name

    async def analyze_sentiment(
        self, title: str, content: Optional[str] = None
    ) -> dict:
        """
        分析新闻情感

        Returns:
            {
                "score": float,  # -1.0 到 1.0，负数=看跌，正数=看涨
                "label": str,  # "positive", "negative", "neutral"
                "confidence": float,  # 0.0 到 1.0
                "reasoning": str  # 分析理由
            }
        """
        try:

            text = f"{title}"
            if content:
                text += f"\n\n{content[:500]}"  # 限制长度

            prompt = f"""分析以下财经新闻的市场情感倾向：

新闻内容：
{text}

请以JSON格式返回分析结果：
{{
    "score": <-1.0到1.0的数值，负数表示看跌/利空，正数表示看涨/利好>,
    "label": "<positive/negative/neutral>",
    "confidence": <0.0到1.0的置信度>,
    "reasoning": "<简短的分析理由>"
}}

注意：
- 仅分析市场情感，不做投资建议
- score应反映新闻对市场的影响方向和强度
- 考虑新闻的时效性和可靠性"""

            response = await llm_provider.chat(
                model_key=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500,
            )

            result_text = response["content"].strip()

            # 尝试解析JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            result = json.loads(result_text)

            # 验证结果
            if "score" not in result or "label" not in result:
                raise ValueError("Invalid sentiment result format")

            # 标准化label
            score = float(result["score"])
            if score > 0.2:
                result["label"] = "positive"
            elif score < -0.2:
                result["label"] = "negative"
            else:
                result["label"] = "neutral"

            return result

        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            # 返回中性结果
            return {
                "score": 0.0,
                "label": "neutral",
                "confidence": 0.0,
                "reasoning": f"分析失败: {str(e)}"
            }

    async def batch_analyze(
        self, articles: list[dict]
    ) -> list[dict]:
        """
        批量分析多篇新闻

        Args:
            articles: [{"title": str, "content": str}, ...]

        Returns:
            list of sentiment results
        """
        results = []
        for article in articles:
            result = await self.analyze_sentiment(
                article.get("title", ""),
                article.get("content")
            )
            results.append(result)

        return results
