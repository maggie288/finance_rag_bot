"use client";

import { useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { tradingAPI } from "@/lib/api-client";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  ArrowLeft,
  Play,
  Pause,
  Square,
  TrendingUp,
  TrendingDown,
  Zap,
  Loader2,
  Trash2,
  RotateCcw,
  Plus,
} from "lucide-react";
import { TradingSimulation, AgentInfo } from "@/types";
import { useToast } from "@/components/ui/use-toast";

export default function AITradingPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const { toast } = useToast();
  const symbol = decodeURIComponent(params.symbol as string);
  const market = searchParams.get("market") || "us";

  const [selectedAgent, setSelectedAgent] = useState("deepseek");
  const [creating, setCreating] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Fetch available agents
  const { data: agents } = useQuery({
    queryKey: ["trading-agents"],
    queryFn: async () => {
      const res = await tradingAPI.getAgents();
      return res.data as AgentInfo[];
    },
  });

  // Fetch simulations for this symbol
  const { data: simulations, refetch, isLoading: simulationsLoading } = useQuery({
    queryKey: ["simulations", symbol],
    queryFn: async () => {
      console.log("[AI Trading] Fetching simulations for:", symbol);
      const res = await tradingAPI.getSimulations({ symbol, page: 1, page_size: 10 });
      console.log("[AI Trading] Fetched simulations:", res.data.items?.length || 0);
      return res.data.items as TradingSimulation[];
    },
    refetchInterval: (query) => {
      // Auto-refresh every 3 seconds if there are running simulations
      const data = query.state.data as TradingSimulation[] | undefined;
      const hasRunning = data?.some((s) => s.status === "running");
      return hasRunning ? 3000 : false;
    },
    staleTime: 0, // Always refetch
  });

  // Create a new simulation (pending status)
  const handleCreateSimulation = async () => {
    console.log("[AI Trading] Creating simulation...", { symbol, market, agent: selectedAgent });
    setCreating(true);
    try {
      const response = await tradingAPI.createSimulation({
        symbol,
        market,
        agent_name: selectedAgent,
        config: {
          decision_frequency: "daily",
          max_position_size: 0.5,
          stop_loss_pct: 0.1,
          take_profit_pct: 0.2,
          risk_tolerance: "medium",
        },
      });

      console.log("[AI Trading] Simulation created:", response.data);

      toast({
        title: "模拟已创建",
        description: `${selectedAgent.toUpperCase()} Agent 已就绪，点击"启动"开始交易模拟`,
      });

      // Force refetch and wait for it to complete
      await refetch();
      console.log("[AI Trading] Simulations list refreshed");
    } catch (err: unknown) {
      console.error("[AI Trading] Creation failed:", err);
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      const errorMessage = error?.response?.data?.detail || error?.message || "请检查积分余额或网络连接";
      toast({
        title: "创建失败",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setCreating(false);
    }
  };

  // Start a pending simulation
  const handleStartSimulation = async (simId: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setActionLoading(simId);

    try {
      await tradingAPI.startSimulation(simId);
      toast({
        title: "模拟已启动",
        description: "AI Agent 正在分析市场并执行交易策略...",
      });
      refetch();
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      toast({
        title: "启动失败",
        description: error?.response?.data?.detail || "无法启动模拟",
        variant: "destructive",
      });
    } finally {
      setActionLoading(null);
    }
  };

  // Pause a running simulation
  const handlePauseSimulation = async (simId: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setActionLoading(simId);

    try {
      await tradingAPI.pauseSimulation(simId);
      toast({
        title: "模拟已暂停",
        description: "点击「继续」可恢复交易",
      });
      refetch();
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      toast({
        title: "暂停失败",
        description: error?.response?.data?.detail || "无法暂停模拟",
        variant: "destructive",
      });
    } finally {
      setActionLoading(null);
    }
  };

  // Resume a paused simulation
  const handleResumeSimulation = async (simId: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setActionLoading(simId);

    try {
      await tradingAPI.resumeSimulation(simId);
      toast({
        title: "模拟已恢复",
        description: "AI Agent 继续执行交易策略...",
      });
      refetch();
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      toast({
        title: "恢复失败",
        description: error?.response?.data?.detail || "无法恢复模拟",
        variant: "destructive",
      });
    } finally {
      setActionLoading(null);
    }
  };

  // Stop a simulation permanently
  const handleStopSimulation = async (simId: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setActionLoading(simId);

    try {
      await tradingAPI.stopSimulation(simId);
      toast({
        title: "模拟已停止",
        description: "模拟已永久停止",
      });
      refetch();
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      toast({
        title: "停止失败",
        description: error?.response?.data?.detail || "无法停止模拟",
        variant: "destructive",
      });
    } finally {
      setActionLoading(null);
    }
  };

  // Delete a simulation
  const handleDeleteSimulation = async (simId: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (!confirm("确定要删除这个模拟记录吗？")) {
      return;
    }

    setActionLoading(simId);
    try {
      await tradingAPI.deleteSimulation(simId);
      toast({
        title: "已删除",
        description: "模拟记录已删除",
      });
      refetch();
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      toast({
        title: "删除失败",
        description: error?.response?.data?.detail || "无法删除模拟",
        variant: "destructive",
      });
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, string> = {
      pending: "bg-gray-500/10 text-gray-500",
      running: "bg-blue-500/10 text-blue-500 animate-pulse",
      paused: "bg-yellow-500/10 text-yellow-500",
      completed: "bg-green-500/10 text-green-500",
      failed: "bg-red-500/10 text-red-500",
      stopped: "bg-orange-500/10 text-orange-500",
    };
    const labels: Record<string, string> = {
      pending: "待启动",
      running: "运行中",
      paused: "已暂停",
      completed: "已完成",
      failed: "失败",
      stopped: "已停止",
    };
    return (
      <Badge variant="secondary" className={variants[status] || ""}>
        {labels[status] || status}
      </Badge>
    );
  };

  // Render action buttons based on simulation status
  const renderActionButtons = (sim: TradingSimulation) => {
    const isLoading = actionLoading === sim.id;

    return (
      <div className="flex gap-1">
        {/* Pending: Show Start button */}
        {sim.status === "pending" && (
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0 text-green-500 hover:text-green-600 hover:bg-green-500/10"
            onClick={(e) => handleStartSimulation(sim.id, e)}
            disabled={isLoading}
          >
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
          </Button>
        )}

        {/* Running: Show Pause button */}
        {sim.status === "running" && (
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0 text-yellow-500 hover:text-yellow-600 hover:bg-yellow-500/10"
            onClick={(e) => handlePauseSimulation(sim.id, e)}
            disabled={isLoading}
          >
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Pause className="h-4 w-4" />}
          </Button>
        )}

        {/* Paused: Show Resume button */}
        {sim.status === "paused" && (
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0 text-green-500 hover:text-green-600 hover:bg-green-500/10"
            onClick={(e) => handleResumeSimulation(sim.id, e)}
            disabled={isLoading}
          >
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RotateCcw className="h-4 w-4" />}
          </Button>
        )}

        {/* Running/Paused: Show Stop button */}
        {(sim.status === "running" || sim.status === "paused") && (
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0 text-orange-500 hover:text-orange-600 hover:bg-orange-500/10"
            onClick={(e) => handleStopSimulation(sim.id, e)}
            disabled={isLoading}
          >
            <Square className="h-4 w-4" />
          </Button>
        )}

        {/* All: Show Delete button (except running) */}
        {sim.status !== "running" && (
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0 text-red-500 hover:text-red-600 hover:bg-red-500/10"
            onClick={(e) => handleDeleteSimulation(sim.id, e)}
            disabled={isLoading}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        )}
      </div>
    );
  };

  return (
    <div>
      <Header title="AI交易代理" />
      <div className="mx-auto max-w-lg space-y-4 p-4">
        {/* Back button */}
        <Link href={`/market/${encodeURIComponent(symbol)}?market=${market}`} className="inline-flex items-center gap-1 text-sm text-muted-foreground">
          <ArrowLeft className="h-4 w-4" /> 返回股票详情
        </Link>

        {/* Description */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-500/10">
                <Zap className="h-5 w-5 text-purple-500" />
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-medium">AI Agent 自动交易模拟</h3>
                <p className="text-xs text-muted-foreground mt-1">
                  选择AI模型，模拟股票交易。Agent将根据历史数据自主决策买卖时机，生成详细的交易报告。
                </p>
                <div className="mt-2 flex flex-wrap gap-2 text-[10px] text-muted-foreground">
                  <span>• 初始资金: {market === "cn" ? "¥50,000" : "$50,000"}</span>
                  <span>• 费用: 10积分</span>
                </div>
                <div className="mt-2 p-2 bg-muted/50 rounded text-xs text-muted-foreground">
                  <strong>操作说明：</strong>
                  <p>1. 选择AI Agent → 2. 点击「创建模拟」 → 3. 点击「启动」开始交易</p>
                  <p className="mt-1">Agent会自动分析市场数据，决定何时买入/卖出</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Agent Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">选择AI Agent</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {agents?.map((agent) => (
              <button
                key={agent.name}
                onClick={() => setSelectedAgent(agent.name)}
                className={`w-full rounded-lg border p-3 text-left transition-colors ${
                  selectedAgent === agent.name
                    ? "border-primary bg-primary/5"
                    : "border-border hover:bg-accent/50"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{agent.display_name}</p>
                    <p className="text-xs text-muted-foreground">{agent.description}</p>
                  </div>
                  {selectedAgent === agent.name && (
                    <div className="h-2 w-2 rounded-full bg-primary" />
                  )}
                </div>
              </button>
            ))}
          </CardContent>
        </Card>

        {/* Create Button */}
        <Button
          onClick={handleCreateSimulation}
          disabled={creating}
          className="w-full"
        >
          {creating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              创建中...
            </>
          ) : (
            <>
              <Plus className="mr-2 h-4 w-4" />
              创建模拟
            </>
          )}
        </Button>

        {/* Simulation History */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">交易记录</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {simulationsLoading && (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            )}
            {!simulationsLoading && (!simulations || simulations.length === 0) && (
              <p className="text-sm text-muted-foreground text-center py-4">
                暂无交易记录，点击上方按钮创建模拟
              </p>
            )}
            {simulations && simulations.length > 0 && simulations.map((sim) => {
                const isProfitable = Number(sim.total_profit_loss) > 0;
                const roi = Number(sim.initial_balance) > 0
                  ? (Number(sim.total_profit_loss) / Number(sim.initial_balance) * 100)
                  : 0;

                return (
                  <div key={sim.id} className="relative">
                    <Link
                      href={`/market/${encodeURIComponent(symbol)}/ai-trading/${sim.id}?market=${market}`}
                    >
                      <div className="cursor-pointer rounded-lg border p-3 transition-colors hover:bg-accent/50">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <p className="text-sm font-medium">{sim.agent_name.toUpperCase()} Agent</p>
                              {getStatusBadge(sim.status)}
                            </div>
                            <p className="text-xs text-muted-foreground mt-1">
                              {new Date(sim.created_at).toLocaleDateString("zh-CN", {
                                year: "numeric",
                                month: "2-digit",
                                day: "2-digit",
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </p>
                          </div>
                          {(sim.status === "completed" || sim.status === "stopped") && Number(sim.total_trades) > 0 && (
                            <div className="text-right mr-24">
                              <div className={`flex items-center gap-1 text-sm font-semibold ${isProfitable ? "text-green-500" : "text-red-500"}`}>
                                {isProfitable ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                                {isProfitable ? "+" : ""}{roi.toFixed(2)}%
                              </div>
                              <p className="text-xs text-muted-foreground">
                                {sim.total_trades} 笔交易
                              </p>
                            </div>
                          )}
                          {sim.status === "running" && (
                            <div className="text-right mr-24">
                              <p className="text-xs text-blue-500 animate-pulse">
                                执行中... {sim.total_trades} 笔
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    </Link>
                    {/* Action buttons */}
                    <div className="absolute right-3 top-1/2 -translate-y-1/2">
                      {renderActionButtons(sim)}
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>
      </div>
    </div>
  );
}
