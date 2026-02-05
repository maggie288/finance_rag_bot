FUNDAMENTAL_ANALYSIS_PROMPT = """You are a professional financial analyst. Analyze the following financial data for {symbol} and provide a comprehensive fundamental analysis report in Chinese.

Financial Data:
{financial_data}

IMPORTANT: Check if the data contains "is_estimated" field set to true. If so:
- This data is ESTIMATED from market price data and technical indicators
- Focus more on technical analysis aspects (moving averages, volatility, price trends)
- Clearly state that fundamental metrics are estimates and should be used with caution
- Emphasize the market sentiment and price action analysis

Please cover:
1. 数据来源说明 (如果是估算数据，明确说明这一点)
2. 估值分析 (PE, PB ratio interpretation - 如果是估算值，结合技术指标分析)
3. 盈利能力评估 (profit margins, ROE - 如果缺少数据，从市场表现推测)
4. 财务健康度 (debt ratio, cash flow - 如果缺少数据，说明市场风险)
5. 技术指标分析 (如果有：移动平均线、波动率、涨跌幅趋势)
6. 成长性分析 (revenue growth trends - 如果缺少数据，从股价表现推测)
7. 投资建议摘要

Format the report in clear sections with headers."""


SENTIMENT_ANALYSIS_PROMPT = """You are a financial sentiment analyst. Analyze the following news and social media content about {symbol} and provide:

Content:
{content}

1. 整体舆情评分 (-1.0 bearish to 1.0 bullish)
2. 关键信息摘要
3. 市场情绪解读
4. 潜在影响分析
5. 交易信号建议 (买入/卖出/持有)

Respond in Chinese."""


RAG_QUERY_PROMPT = """You are a financial research assistant. Use the following context to answer the user's question accurately.

Context from knowledge base:
{context}

User question: {query}

Instructions:
- Answer in the same language as the question
- Cite specific sources when referencing data
- If the context doesn't contain enough information, say so
- Provide actionable insights where possible"""


MACRO_ANALYSIS_PROMPT = """You are a macroeconomic analyst. Summarize and analyze the following macroeconomic data and news.

Data:
{data}

Please provide:
1. 宏观经济概览
2. 货币政策动向
3. 对市场的潜在影响
4. 关键风险因素
5. 投资策略建议

Respond in Chinese."""


PREDICTION_EXPLANATION_PROMPT = """You are a quantitative analyst. Explain the following Markov chain price prediction results for {symbol} in an accessible way.

Prediction Data:
- Current state: {current_state}
- Transition matrix: {transition_matrix}
- Predicted probabilities: {predicted_probs}
- Price range: {price_range}

Please explain:
1. 预测模型的基本原理
2. 当前市场状态解读
3. 预测结果分析
4. 置信度说明
5. 风险提示

Use simple language. Respond in Chinese."""
