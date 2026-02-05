"use client";

import { useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { tradingAPI } from "@/lib/api-client";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  ArrowLeft,
  TrendingDown,
  Brain,
  BarChart3,
  Terminal,
  Info,
  ChevronDown,
  ChevronUp,
  Wallet,
  Activity,
} from "lucide-react";
import { TradingSimulation, Trade } from "@/types";

export default function SimulationDetailPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const symbol = decodeURIComponent(params.symbol as string);
  const simId = params.simId as string;
  const market = searchParams.get("market") || "us";

  const [showDrawdownInfo, setShowDrawdownInfo] = useState(false);
  const [expandedTrades, setExpandedTrades] = useState<Set<string>>(new Set());

  // Fetch simulation details
  const { data: simulation } = useQuery({
    queryKey: ["simulation", simId],
    queryFn: async () => {
      const res = await tradingAPI.getSimulation(simId);
      console.log("[SimulationDetailPage] API Response:", JSON.stringify(res.data, null, 2));
      return res.data as TradingSimulation & { trades: Trade[] };
    },
  });

  const toggleTradeExpand = (tradeId: string) => {
    setExpandedTrades((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(tradeId)) {
        newSet.delete(tradeId);
      } else {
        newSet.add(tradeId);
      }
      return newSet;
    });
  };

  if (!simulation) {
    return (
      <div>
        <Header title="加载中..." />
        <div className="flex h-[50vh] items-center justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      </div>
    );
  }

  // Convert all numeric fields to ensure they are numbers (API may return strings)
  const totalProfitLoss = Number(simulation.total_profit_loss) || 0;
  const initialBalance = Number(simulation.initial_balance) || 0;
  const currentBalance = Number(simulation.current_balance) || 0;
  const currentShares = Number(simulation.current_shares) || 0;
  const totalLlmCost = Number(simulation.total_llm_cost) || 0;
  const totalTokensUsed = Number(simulation.total_tokens_used) || 0;
  const totalTrades = Number(simulation.total_trades) || 0;
  const winningTrades = Number(simulation.winning_trades) || 0;
  const losingTrades = Number(simulation.losing_trades) || 0;
  const maxDrawdown = simulation.max_drawdown != null ? Number(simulation.max_drawdown) : null;
  const averageCost = simulation.average_cost != null ? Number(simulation.average_cost) : null;
  const sharpeRatio = simulation.sharpe_ratio != null ? Number(simulation.sharpe_ratio) : null;

  const isProfitable = totalProfitLoss > 0;
  const roi = initialBalance > 0 ? (totalProfitLoss / initialBalance * 100) : 0;
  const winRate = totalTrades > 0 ? (winningTrades / totalTrades * 100) : 0;

  return (
    <div>
      <Header title="模拟交易详情" />
      <div className="mx-auto max-w-lg space-y-4 p-4">
        {/* Back button */}
        <Link href={`/market/${encodeURIComponent(symbol)}/ai-trading?market=${market}`} className="inline-flex items-center gap-1 text-sm text-muted-foreground">
          <ArrowLeft className="h-4 w-4" /> 返回AI交易
        </Link>

        {/* Performance Summary */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">交易表现</CardTitle>
              <Badge variant={simulation.status === "completed" ? "default" : "secondary"}>
                {simulation.status === "completed" && "已完成"}
                {simulation.status === "running" && "运行中"}
                {simulation.status === "failed" && "失败"}
                {simulation.status === "pending" && "待执行"}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-muted-foreground">总收益率</p>
                <p className={`text-2xl font-bold ${isProfitable ? "text-green-500" : "text-red-500"}`}>
                  {isProfitable ? "+" : ""}{roi.toFixed(2)}%
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">总盈亏</p>
                <p className={`text-2xl font-bold ${isProfitable ? "text-green-500" : "text-red-500"}`}>
                  {isProfitable ? "+" : ""}{totalProfitLoss.toFixed(2)} {simulation.currency}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3 text-sm">
              <div className="flex flex-col gap-1">
                <span className="text-muted-foreground">总交易</span>
                <span className="font-semibold">{totalTrades}</span>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-muted-foreground">盈/亏</span>
                <span className="font-semibold">
                  <span className="text-green-500">{winningTrades}</span>
                  <span className="text-muted-foreground"> / </span>
                  <span className="text-red-500">{losingTrades}</span>
                </span>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-muted-foreground">胜率</span>
                <span className="font-semibold text-green-500">{winRate.toFixed(1)}%</span>
              </div>
            </div>

            {/* Max Drawdown with explanation */}
            <div className="border rounded-lg p-3 bg-muted/30">
              <div
                className="flex items-center justify-between cursor-pointer"
                onClick={() => setShowDrawdownInfo(!showDrawdownInfo)}
              >
                <div className="flex items-center gap-2">
                  <TrendingDown className="h-4 w-4 text-red-500" />
                  <span className="text-sm font-medium">最大回撤</span>
                  <Info className="h-3 w-3 text-muted-foreground" />
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-red-500">
                    {maxDrawdown != null ? `${(maxDrawdown * 100).toFixed(2)}%` : "N/A"}
                  </span>
                  {showDrawdownInfo ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </div>
              </div>
              {showDrawdownInfo && (
                <div className="mt-3 pt-3 border-t text-xs text-muted-foreground space-y-2">
                  <p><strong>指标说明：</strong></p>
                  <p>最大回撤 (Maximum Drawdown, MDD) 是衡量投资组合风险的重要指标，表示从历史最高点到最低点的最大跌幅。</p>
                  <p><strong>计算公式：</strong></p>
                  <p className="font-mono bg-slate-900 p-2 rounded">
                    MDD = (峰值 - 谷值) / 峰值 × 100%
                  </p>
                  <p><strong>计算逻辑：</strong></p>
                  <ol className="list-decimal list-inside space-y-1">
                    <li>记录每次交易后的组合总价值</li>
                    <li>持续追踪历史最高价值（峰值）</li>
                    <li>计算当前价值与峰值的差距比例</li>
                    <li>取所有回撤中的最大值</li>
                  </ol>
                  <p className="mt-2 text-yellow-500">⚠️ 最大回撤越小，说明投资策略的风险控制能力越强。一般认为最大回撤应控制在20%以内。</p>
                </div>
              )}
            </div>

            {/* Sharpe Ratio */}
            {sharpeRatio != null && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">夏普比率</span>
                <span className={`font-semibold ${sharpeRatio > 1 ? "text-green-500" : sharpeRatio > 0 ? "text-yellow-500" : "text-red-500"}`}>
                  {sharpeRatio.toFixed(4)}
                </span>
              </div>
            )}

            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="flex flex-col gap-1">
                <span className="text-muted-foreground">初始资金</span>
                <span className="font-semibold">{initialBalance.toFixed(2)} {simulation.currency}</span>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-muted-foreground">当前现金</span>
                <span className="font-semibold">{currentBalance.toFixed(2)} {simulation.currency}</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="flex flex-col gap-1">
                <span className="text-muted-foreground">持仓股数</span>
                <span className="font-semibold">{currentShares.toFixed(4)}</span>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-muted-foreground">平均成本</span>
                <span className="font-semibold">
                  {averageCost != null ? `${averageCost.toFixed(2)} ${simulation.currency}` : "N/A"}
                </span>
              </div>
            </div>

            <div className="border-t pt-3 text-xs text-muted-foreground">
              <p>AI Agent: {(simulation.agent_name || "").toUpperCase()} ({simulation.llm_model})</p>
              <p>LLM成本: ${totalLlmCost.toFixed(4)}</p>
              <p>Token使用: {totalTokensUsed.toLocaleString()}</p>
            </div>
          </CardContent>
        </Card>

        {/* Trade History - Enhanced */}
        {simulation.trades && simulation.trades.length > 0 && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4" />
                <CardTitle className="text-base">交易明细</CardTitle>
                <Badge variant="outline" className="ml-auto">{simulation.trades.length} 笔</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {simulation.trades.map((trade, idx) => {
                const isBuy = trade.action === "buy";
                const quantity = Number(trade.quantity) || 0;
                const price = Number(trade.price) || 0;
                const totalAmount = Number(trade.total_amount) || 0;
                const commission = Number(trade.commission) || 0;
                const profitLoss = Number(trade.realized_pnl) || 0;
                const isProfit = profitLoss > 0;
                const confidenceScore = Number(trade.confidence_score) || 0;
                const sharesBefore = Number(trade.shares_before) || 0;
                const sharesAfter = Number(trade.shares_after) || 0;
                const cashBefore = Number(trade.cash_before) || 0;
                const cashAfter = Number(trade.cash_after) || 0;
                const tokensUsed = Number(trade.tokens_used) || 0;
                const llmCost = Number(trade.llm_cost) || 0;
                const isExpanded = expandedTrades.has(trade.id);

                return (
                  <div key={trade.id} className="border rounded-lg overflow-hidden">
                    {/* Trade Header */}
                    <div
                      className={`p-3 cursor-pointer ${isBuy ? "bg-green-500/10" : "bg-red-500/10"}`}
                      onClick={() => toggleTradeExpand(trade.id)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <Badge variant={isBuy ? "default" : "secondary"} className={isBuy ? "bg-green-500" : "bg-red-500"}>
                              {isBuy ? "买入" : "卖出"}
                            </Badge>
                            <span className="text-sm font-bold">
                              #{idx + 1}
                            </span>
                            <span className="text-sm font-medium">
                              {quantity.toFixed(2)} 股
                            </span>
                            <span className="text-sm text-muted-foreground">
                              @ {price.toFixed(2)}
                            </span>
                          </div>
                          <p className="text-xs text-muted-foreground mt-1">
                            {trade.trade_date ? new Date(trade.trade_date).toLocaleDateString("zh-CN", {
                              year: "numeric", month: "2-digit", day: "2-digit", weekday: "short"
                            }) : "N/A"}
                          </p>
                        </div>
                        <div className="text-right flex items-center gap-2">
                          <div>
                            <p className="text-sm font-semibold">
                              {isBuy ? "-" : "+"}{totalAmount.toFixed(2)}
                            </p>
                            {!isBuy && trade.realized_pnl != null && (
                              <p className={`text-xs font-semibold ${isProfit ? "text-green-500" : "text-red-500"}`}>
                                {isProfit ? "盈利 +" : "亏损 "}{profitLoss.toFixed(2)}
                              </p>
                            )}
                          </div>
                          {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                        </div>
                      </div>
                    </div>

                    {/* Expanded Details */}
                    {isExpanded && (
                      <div className="p-3 border-t space-y-4 bg-background">
                        {/* Market Data at Trade Time */}
                        {trade.market_data && (
                          <div className="space-y-2">
                            <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                              <BarChart3 className="h-3 w-3" />
                              交易时市场数据
                            </div>
                            <div className="grid grid-cols-4 gap-2 text-xs">
                              <div className="bg-muted/50 p-2 rounded">
                                <p className="text-muted-foreground">开盘</p>
                                <p className="font-mono font-semibold">{Number(trade.market_data.open).toFixed(2)}</p>
                              </div>
                              <div className="bg-muted/50 p-2 rounded">
                                <p className="text-muted-foreground">最高</p>
                                <p className="font-mono font-semibold text-green-500">{Number(trade.market_data.high).toFixed(2)}</p>
                              </div>
                              <div className="bg-muted/50 p-2 rounded">
                                <p className="text-muted-foreground">最低</p>
                                <p className="font-mono font-semibold text-red-500">{Number(trade.market_data.low).toFixed(2)}</p>
                              </div>
                              <div className="bg-muted/50 p-2 rounded">
                                <p className="text-muted-foreground">收盘</p>
                                <p className="font-mono font-semibold">{Number(trade.market_data.close).toFixed(2)}</p>
                              </div>
                            </div>
                            {trade.market_data.volume && (
                              <p className="text-xs text-muted-foreground">
                                成交量: {Number(trade.market_data.volume).toLocaleString()}
                              </p>
                            )}
                          </div>
                        )}

                        {/* Position Change */}
                        <div className="space-y-2">
                          <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                            <Wallet className="h-3 w-3" />
                            持仓变化
                          </div>
                          <div className="grid grid-cols-2 gap-3 text-xs">
                            <div className="space-y-1">
                              <p className="text-muted-foreground">股数变化</p>
                              <p className="font-mono">
                                {sharesBefore.toFixed(2)} → {sharesAfter.toFixed(2)}
                                <span className={`ml-2 ${isBuy ? "text-green-500" : "text-red-500"}`}>
                                  ({isBuy ? "+" : "-"}{quantity.toFixed(2)})
                                </span>
                              </p>
                            </div>
                            <div className="space-y-1">
                              <p className="text-muted-foreground">现金变化</p>
                              <p className="font-mono">
                                {cashBefore.toFixed(2)} → {cashAfter.toFixed(2)}
                                <span className={`ml-2 ${isBuy ? "text-red-500" : "text-green-500"}`}>
                                  ({isBuy ? "-" : "+"}{totalAmount.toFixed(2)})
                                </span>
                              </p>
                            </div>
                          </div>
                          <p className="text-xs text-muted-foreground">
                            手续费: {commission.toFixed(2)} {simulation.currency}
                          </p>
                        </div>

                        {/* AI Decision */}
                        <div className="space-y-2">
                          <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                            <Brain className="h-3 w-3" />
                            AI决策分析
                          </div>
                          <div className="flex items-center gap-4 text-xs">
                            <div className="flex items-center gap-1">
                              <span className="text-muted-foreground">置信度:</span>
                              <div className="w-20 h-2 bg-muted rounded-full overflow-hidden">
                                <div
                                  className={`h-full ${confidenceScore >= 0.7 ? "bg-green-500" : confidenceScore >= 0.5 ? "bg-yellow-500" : "bg-red-500"}`}
                                  style={{ width: `${confidenceScore * 100}%` }}
                                />
                              </div>
                              <span className="font-semibold">{(confidenceScore * 100).toFixed(0)}%</span>
                            </div>
                            <span className="text-muted-foreground">|</span>
                            <span className="text-muted-foreground">Token: {tokensUsed.toLocaleString()}</span>
                            <span className="text-muted-foreground">|</span>
                            <span className="text-muted-foreground">成本: ${llmCost.toFixed(4)}</span>
                          </div>
                          {trade.llm_reasoning && (
                            <div className="bg-slate-900 rounded-lg p-3 text-xs">
                              <p className="text-blue-400 font-medium mb-1">AI思考过程：</p>
                              <p className="text-gray-300 whitespace-pre-wrap leading-relaxed">
                                {trade.llm_reasoning}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </CardContent>
          </Card>
        )}

        {/* Execution Logs */}
        {simulation.execution_logs && simulation.execution_logs.logs && simulation.execution_logs.logs.length > 0 && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Terminal className="h-4 w-4" />
                <CardTitle className="text-base">执行日志</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="max-h-[500px] overflow-y-auto space-y-1 bg-slate-950 rounded-lg p-3 font-mono text-xs">
                {simulation.execution_logs.logs.map((log, idx) => {
                  const levelColors = {
                    info: "text-blue-400",
                    success: "text-green-400",
                    warning: "text-yellow-400",
                    error: "text-red-400",
                  };
                  const levelColor = levelColors[log.level as keyof typeof levelColors] || "text-gray-400";

                  return (
                    <div key={idx} className="flex gap-2">
                      <span className="text-gray-500 shrink-0">
                        {new Date(log.timestamp).toLocaleTimeString("zh-CN")}
                      </span>
                      <span className={`${levelColor} whitespace-pre-wrap break-all`}>
                        {log.message}
                      </span>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Summary */}
        {simulation.summary && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">模拟总结</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="text-xs text-muted-foreground whitespace-pre-wrap font-mono">
                {simulation.summary}
              </pre>
            </CardContent>
          </Card>
        )}

        {/* Error Message */}
        {simulation.error_message && (
          <Card className="border-red-500/50 bg-red-500/5">
            <CardHeader>
              <CardTitle className="text-base text-red-500">错误信息</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-red-500">{simulation.error_message}</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
