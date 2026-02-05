"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { tradingAPI } from "@/lib/api-client";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/hooks/use-toast";
import {
  ArrowLeft,
  Brain,
  TrendingUp,
  TrendingDown,
  Play,
  Pause,
  Square,
  Plus,
  Trash2,
  Clock,
  DollarSign,
  Target,
  BarChart3,
} from "lucide-react";

type SimulationStatus = "pending" | "running" | "paused" | "completed" | "stopped" | "failed";

interface Trade {
  id: string;
  trade_date: string;
  action: string;
  symbol: string;
  quantity: string;
  price: string;
  total_amount: string;
  realized_pnl: string | null;
  llm_reasoning: string;
  confidence_score: string | null;
}

interface Simulation {
  id: string;
  symbol: string;
  market: string;
  agent_name: string;
  status: SimulationStatus;
  initial_balance: string;
  current_balance: string;
  current_shares: string;
  total_profit_loss: string;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  created_at: string;
  start_date: string;
  end_date: string;
}

interface SimulationDetail extends Simulation {
  trades: Trade[];
  llm_model: string;
  average_cost: string | null;
  max_drawdown: string | null;
  sharpe_ratio: string | null;
  total_tokens_used: number;
  summary: string | null;
}

const STATUS_CONFIG: Record<SimulationStatus, { label: string; color: string }> = {
  pending: { label: "等待开始", color: "bg-gray-100 text-gray-700" },
  running: { label: "运行中", color: "bg-green-100 text-green-700" },
  paused: { label: "已暂停", color: "bg-yellow-100 text-yellow-700" },
  completed: { label: "已完成", color: "bg-blue-100 text-blue-700" },
  stopped: { label: "已停止", color: "bg-red-100 text-red-700" },
  failed: { label: "失败", color: "bg-red-100 text-red-700" },
};

const AGENT_NAMES: Record<string, string> = {
  deepseek: "DeepSeek",
  minimax: "MiniMax",
  claude: "Claude",
  openai: "GPT-4o",
};

export default function TradingAgentsPage() {
  const [selectedSimulation, setSelectedSimulation] = useState<SimulationDetail | null>(null);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: simulationsData, isLoading } = useQuery({
    queryKey: ["trading-simulations"],
    queryFn: async () => {
      const res = await tradingAPI.getSimulations({ page: 1, page_size: 50 });
      return res.data;
    },
  });

  const simulations = simulationsData?.items || [];

  const startMutation = useMutation({
    mutationFn: (id: string) => tradingAPI.startSimulation(id),
    onSuccess: () => {
      toast({ title: "成功", description: "交易代理已启动" });
      queryClient.invalidateQueries({ queryKey: ["trading-simulations"] });
    },
    onError: () => {
      toast({ title: "失败", description: "无法启动交易代理", variant: "destructive" });
    },
  });

  const pauseMutation = useMutation({
    mutationFn: (id: string) => tradingAPI.pauseSimulation(id),
    onSuccess: () => {
      toast({ title: "成功", description: "交易代理已暂停" });
      queryClient.invalidateQueries({ queryKey: ["trading-simulations"] });
    },
    onError: () => {
      toast({ title: "失败", description: "无法暂停交易代理", variant: "destructive" });
    },
  });

  const resumeMutation = useMutation({
    mutationFn: (id: string) => tradingAPI.resumeSimulation(id),
    onSuccess: () => {
      toast({ title: "成功", description: "交易代理已恢复" });
      queryClient.invalidateQueries({ queryKey: ["trading-simulations"] });
    },
    onError: () => {
      toast({ title: "失败", description: "无法恢复交易代理", variant: "destructive" });
    },
  });

  const stopMutation = useMutation({
    mutationFn: (id: string) => tradingAPI.stopSimulation(id),
    onSuccess: () => {
      toast({ title: "成功", description: "交易代理已停止" });
      queryClient.invalidateQueries({ queryKey: ["trading-simulations"] });
    },
    onError: () => {
      toast({ title: "失败", description: "无法停止交易代理", variant: "destructive" });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => tradingAPI.deleteSimulation(id),
    onSuccess: () => {
      toast({ title: "成功", description: "交易记录已删除" });
      queryClient.invalidateQueries({ queryKey: ["trading-simulations"] });
      setSelectedSimulation(null);
    },
    onError: () => {
      toast({ title: "失败", description: "无法删除交易记录", variant: "destructive" });
    },
  });

  const fetchSimulationDetail = async (id: string) => {
    const res = await tradingAPI.getSimulation(id);
    setSelectedSimulation(res.data);
  };

  const handleAction = async (action: string, id: string) => {
    switch (action) {
      case "start":
        startMutation.mutate(id);
        break;
      case "pause":
        pauseMutation.mutate(id);
        break;
      case "resume":
        resumeMutation.mutate(id);
        break;
      case "stop":
        stopMutation.mutate(id);
        break;
    }
  };

  return (
    <div>
      <Header title="AI 交易代理" showCredits={false} />
      <div className="mx-auto max-w-lg space-y-4 p-4">
        <Link href="/profile" className="inline-flex items-center gap-1 text-sm text-muted-foreground">
          <ArrowLeft className="h-4 w-4" /> 返回
        </Link>

        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold">我的交易代理</h1>
          <Link href="/market">
            <Button size="sm">
              <Plus className="mr-1 h-4 w-4" />
              新建代理
            </Button>
          </Link>
        </div>

        {isLoading ? (
          <div className="py-8 text-center text-muted-foreground">加载中...</div>
        ) : simulations.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center">
              <Brain className="mx-auto h-12 w-12 text-muted-foreground/50" />
              <p className="mt-4 text-muted-foreground">暂无交易代理</p>
              <p className="mt-1 text-sm text-muted-foreground">在行情页选择股票创建AI交易代理</p>
              <Link href="/market">
                <Button className="mt-4" variant="outline">
                  前往行情页
                </Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {simulations.map((sim: Simulation) => {
              const status = STATUS_CONFIG[sim.status as SimulationStatus];
              const profitLoss = parseFloat(sim.total_profit_loss || "0");
              const isProfit = profitLoss >= 0;

              return (
                <Card key={sim.id} className="cursor-pointer transition-shadow hover:shadow-md">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold">{sim.symbol}</span>
                          <Badge variant="secondary" className="text-xs">
                            {AGENT_NAMES[sim.agent_name] || sim.agent_name}
                          </Badge>
                          <span className={`rounded px-2 py-0.5 text-xs ${status.color}`}>
                            {status.label}
                          </span>
                        </div>
                        <div className="mt-2 flex items-center gap-4 text-sm text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <DollarSign className="h-3.5 w-3.5" />
                            {parseFloat(sim.current_balance).toFixed(2)}
                          </span>
                          <span className="flex items-center gap-1">
                            <Target className="h-3.5 w-3.5" />
                            {sim.total_trades} 笔交易
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock className="h-3.5 w-3.5" />
                            {new Date(sim.created_at).toLocaleDateString("zh-CN")}
                          </span>
                        </div>
                      </div>
                      <div className={`text-right font-medium ${isProfit ? "text-green-500" : "text-red-500"}`}>
                        <div className="flex items-center justify-end gap-1">
                          {isProfit ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                          {isProfit ? "+" : ""}{profitLoss.toFixed(2)}
                        </div>
                        <p className="text-xs text-muted-foreground">盈亏</p>
                      </div>
                    </div>

                    <Separator className="my-3" />

                    <div className="flex items-center justify-between">
                      <div className="flex gap-1">
                        {sim.status === "pending" && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleAction("start", sim.id);
                            }}
                          >
                            <Play className="mr-1 h-3.5 w-3.5" />
                            启动
                          </Button>
                        )}
                        {sim.status === "running" && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleAction("pause", sim.id);
                            }}
                          >
                            <Pause className="mr-1 h-3.5 w-3.5" />
                            暂停
                          </Button>
                        )}
                        {sim.status === "paused" && (
                          <>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleAction("resume", sim.id);
                              }}
                            >
                              <Play className="mr-1 h-3.5 w-3.5" />
                              恢复
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleAction("stop", sim.id);
                              }}
                            >
                              <Square className="mr-1 h-3.5 w-3.5" />
                              停止
                            </Button>
                          </>
                        )}
                        {(sim.status === "completed" || sim.status === "stopped" || sim.status === "failed") && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={(e) => {
                              e.stopPropagation();
                              deleteMutation.mutate(sim.id);
                            }}
                          >
                            <Trash2 className="mr-1 h-3.5 w-3.5" />
                            删除
                          </Button>
                        )}
                      </div>
                      <Button
                        size="sm"
                        variant="link"
                        onClick={() => fetchSimulationDetail(sim.id)}
                      >
                        查看详情
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}

        {selectedSimulation && (
          <SimulationDetailModal
            simulation={selectedSimulation}
            onClose={() => setSelectedSimulation(null)}
          />
        )}
      </div>
    </div>
  );
}

function SimulationDetailModal({
  simulation,
  onClose,
}: {
  simulation: SimulationDetail;
  onClose: () => void;
}) {
  const profitLoss = parseFloat(simulation.total_profit_loss || "0");
  const isProfit = profitLoss >= 0;
  const winRate = simulation.total_trades > 0
    ? ((simulation.winning_trades / simulation.total_trades) * 100).toFixed(1)
    : "0";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-lg bg-background">
        <div className="sticky top-0 border-b bg-background p-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">交易详情</h2>
            <Button size="sm" variant="ghost" onClick={onClose}>
              ✕
            </Button>
          </div>
        </div>

        <div className="p-4 space-y-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                收益概览
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-muted-foreground">当前资产</p>
                  <p className="text-xl font-bold">{parseFloat(simulation.current_balance).toFixed(2)}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-muted-foreground">总盈亏</p>
                  <p className={`text-xl font-bold ${isProfit ? "text-green-500" : "text-red-500"}`}>
                    {isProfit ? "+" : ""}{profitLoss.toFixed(2)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">收益率</p>
                  <p className="text-lg font-medium">
                    {((profitLoss / parseFloat(simulation.initial_balance)) * 100).toFixed(2)}%
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-muted-foreground">胜率</p>
                  <p className="text-lg font-medium">{winRate}%</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">交易记录</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {simulation.trades.length === 0 ? (
                <div className="py-6 text-center text-sm text-muted-foreground">
                  暂无交易记录
                </div>
              ) : (
                <div className="divide-y max-h-64 overflow-y-auto">
                  {simulation.trades.map((trade: Trade) => {
                    const isBuy = trade.action === "buy";
                    const pnl = trade.realized_pnl ? parseFloat(trade.realized_pnl) : null;
                    
                    return (
                      <div key={trade.id} className="p-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Badge variant={isBuy ? "default" : "destructive"} className="text-xs">
                              {isBuy ? "买入" : "卖出"}
                            </Badge>
                            <span className="text-sm font-medium">{trade.symbol}</span>
                          </div>
                          <span className="text-xs text-muted-foreground">
                            {new Date(trade.trade_date).toLocaleDateString("zh-CN")}
                          </span>
                        </div>
                        <div className="mt-1 flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">
                            {parseFloat(trade.quantity).toFixed(4)} @ {parseFloat(trade.price).toFixed(2)}
                          </span>
                          {pnl !== null && (
                            <span className={pnl >= 0 ? "text-green-500" : "text-red-500"}>
                              {pnl >= 0 ? "+" : ""}{pnl.toFixed(2)}
                            </span>
                          )}
                        </div>
                        <details className="mt-2">
                          <summary className="cursor-pointer text-xs text-muted-foreground">
                            AI 决策理由
                          </summary>
                          <p className="mt-1 text-xs text-muted-foreground">
                            {trade.llm_reasoning}
                          </p>
                        </details>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>

          {simulation.summary && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">执行总结</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{simulation.summary}</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
