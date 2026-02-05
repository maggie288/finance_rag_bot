export interface User {
  id: string;
  email: string;
  display_name: string | null;
  credits_balance: number;
  preferred_llm: string;
  language: string;
  created_at: string;
}

export interface StockQuote {
  symbol: string;
  name: string | null;
  market: string;
  price: number;
  change: number | null;
  change_percent: number | null;
  volume: number | null;
  high: number | null;
  low: number | null;
  open: number | null;
  prev_close: number | null;
  timestamp: string | null;
}

export interface KlinePoint {
  datetime: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number | null;
}

export interface FundamentalData {
  symbol: string;
  market: string;
  pe_ratio: number | null;
  pb_ratio: number | null;
  roe: number | null;
  debt_ratio: number | null;
  revenue_growth: number | null;
  net_profit_margin: number | null;
  market_cap: number | null;
  dividend_yield: number | null;
  eps: number | null;
  revenue: number | null;
  net_income: number | null;
  total_debt: number | null;
  total_cash: number | null;
  operating_cash_flow: number | null;
  free_cash_flow: number | null;
  // 估算标记和技术指标
  is_estimated?: boolean;
  estimation_note?: string | null;
  price_ma20?: number | null;
  price_ma60?: number | null;
  volatility?: number | null;
  return_60d?: number | null;
}

export interface PredictionResult {
  id: string;
  symbol: string;
  market: string;
  prediction_type: string;
  current_price: number;
  current_state: string;
  state_labels: string[];
  transition_matrix: number[][];
  predicted_state_probs: Record<string, number>;
  predicted_range: { low: number; mid: number; high: number };
  confidence: number;
  computation_steps: ComputationStep[];
  created_at: string;
}

export interface ComputationStep {
  step: number;
  title: string;
  description: string;
  data: Record<string, unknown> | null;
}

export interface CreditTransaction {
  id: string;
  type: string;
  amount: number;
  balance_after: number;
  description: string | null;
  reference_type: string | null;
  created_at: string;
}

export interface NewsArticle {
  id: string;
  source: string;
  title: string | null;
  content: string | null;
  url: string | null;
  author: string | null;
  symbols: string[];
  sentiment_score: number | null;
  sentiment_label: string | null;
  published_at: string | null;
}

export interface WatchlistItem {
  id: string;
  symbol: string;
  market: string;
  name: string | null;
  sort_order: number;
}

export type MarketType = "us" | "hk" | "cn" | "commodity";
export type LLMModel = "deepseek" | "minimax" | "claude" | "openai";

export interface ExecutionLog {
  timestamp: string;
  level: string;
  message: string;
}

export interface TradingSimulation {
  id: string;
  symbol: string;
  market: string;
  agent_name: string;
  llm_model: string;
  initial_balance: number;
  current_balance: number;
  currency: string;
  start_date: string;
  end_date: string;
  status: string;
  current_shares: number;
  average_cost: number | null;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  total_profit_loss: number;
  max_drawdown: number | null;
  sharpe_ratio: number | null;
  config: Record<string, unknown> | null;
  total_tokens_used: number;
  total_llm_cost: number;
  summary: string | null;
  error_message: string | null;
  execution_logs: { logs: ExecutionLog[] } | null;
  created_at: string;
  updated_at: string;
}

export interface TradeMarketData {
  price: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number | null;
}

export interface Trade {
  id: string;
  trade_date: string;
  action: string;
  symbol: string;
  quantity: number;
  price: number;
  total_amount: number;
  commission: number;
  shares_before: number;
  shares_after: number;
  cash_before: number;
  cash_after: number;
  realized_pnl: number | null;
  llm_reasoning: string;
  confidence_score: number | null;
  market_data: TradeMarketData | null;
  tokens_used: number;
  llm_cost: number;
}

export interface AgentInfo {
  name: string;
  display_name: string;
  description: string;
  model_name: string;
  available: boolean;
}
