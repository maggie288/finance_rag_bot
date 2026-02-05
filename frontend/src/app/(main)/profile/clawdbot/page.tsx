"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import Link from "next/link";
import { clawdbotAPI } from "@/lib/api-client";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ArrowLeft, RefreshCw, TrendingUp, Wallet, Settings, Zap, DollarSign, Activity } from "lucide-react";

interface Opportunity {
  id: string;
  market_id: string;
  market_question: string;
  opportunity_type: string;
  confidence: number;
  signal_strength: number;
  entry_price_yes: number;
  entry_price_no: number;
  target_price: number;
  expected_return: number;
  status: string;
  created_at: string;
}

interface Trade {
  id: string;
  market_id: string;
  market_slug: string;
  side: string;
  amount_btc: number;
  amount_usd: number;
  entry_price: number;
  pnl: number;
  pnl_percent: number;
  status: string;
  opened_at: string;
}

interface Wallet {
  id: string;
  wallet_type: string;
  wallet_name: string;
  address: string;
  balance_btc: number;
  balance_usd: number;
  is_active: boolean;
}

function OpportunityCard({ opportunity }: { opportunity: Opportunity }) {
  const typeColors: Record<string, string> = {
    arbitrage: "bg-purple-500",
    momentum: "bg-green-500",
    mean_reversion: "bg-blue-500",
  };

  return (
    <Card className="cursor-pointer transition-all hover:shadow-md hover:border-primary/30">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="space-y-1 flex-1">
            <div className="flex items-center gap-2">
              <Badge className={`${typeColors[opportunity.opportunity_type] || "bg-gray-500"} text-white`}>
                {opportunity.opportunity_type === "mean_reversion" ? "均值回归" : opportunity.opportunity_type}
              </Badge>
              <Badge variant="outline">
                置信度: {(opportunity.confidence * 100).toFixed(0)}%
              </Badge>
            </div>
            <p className="text-sm font-medium line-clamp-2">{opportunity.market_question}</p>
          </div>
        </div>

        <div className="mt-3 grid grid-cols-4 gap-2 text-center">
          <div className="rounded bg-muted/50 p-2">
            <p className="text-xs text-muted-foreground">Yes</p>
            <p className="font-bold">${opportunity.entry_price_yes.toFixed(2)}</p>
          </div>
          <div className="rounded bg-muted/50 p-2">
            <p className="text-xs text-muted-foreground">No</p>
            <p className="font-bold">${opportunity.entry_price_no.toFixed(2)}</p>
          </div>
          <div className="rounded bg-muted/50 p-2">
            <p className="text-xs text-muted-foreground">目标</p>
            <p className="font-bold text-green-500">${opportunity.target_price.toFixed(2)}</p>
          </div>
          <div className="rounded bg-muted/50 p-2">
            <p className="text-xs text-muted-foreground">预期收益</p>
            <p className="font-bold text-green-500">+{opportunity.expected_return.toFixed(1)}%</p>
          </div>
        </div>

        <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
          <span>信号强度: {(opportunity.signal_strength * 100).toFixed(0)}%</span>
          <span>{new Date(opportunity.created_at).toLocaleDateString()}</span>
        </div>
      </CardContent>
    </Card>
  );
}

function TradeCard({ trade }: { trade: Trade }) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Badge variant={trade.side === "yes" ? "default" : "destructive"}>
                {trade.side.toUpperCase()}
              </Badge>
              <Badge variant="outline">{trade.status}</Badge>
            </div>
            <p className="text-sm mt-1 truncate max-w-[200px]">{trade.market_slug || trade.market_id}</p>
          </div>
          <div className="text-right">
            <p className={`font-bold ${trade.pnl >= 0 ? "text-green-500" : "text-red-500"}`}>
              {trade.pnl >= 0 ? "+" : ""}{trade.pnl.toFixed(6)} BTC
            </p>
            <p className="text-xs text-muted-foreground">
              ({trade.pnl >= 0 ? "+" : ""}{trade.pnl_percent.toFixed(2)}%)
            </p>
          </div>
        </div>
        <div className="mt-2 flex justify-between text-xs text-muted-foreground">
          <span>仓位: {trade.amount_btc.toFixed(6)} BTC</span>
          <span>开仓价: ${trade.entry_price.toFixed(2)}</span>
        </div>
      </CardContent>
    </Card>
  );
}

function WalletCard({ wallet }: { wallet: Wallet }) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-orange-500/10 flex items-center justify-center">
              <Wallet className="h-5 w-5 text-orange-500" />
            </div>
            <div>
              <p className="font-medium">{wallet.wallet_name}</p>
              <p className="text-xs text-muted-foreground truncate max-w-[150px]">
                {wallet.address}
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="font-bold text-lg">{wallet.balance_btc.toFixed(6)} BTC</p>
            <p className="text-xs text-muted-foreground">${wallet.balance_usd.toFixed(2)} USD</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function ClawdBotPage() {
  const [activeTab, setActiveTab] = useState("opportunities");

  const { data: opportunitiesData, isLoading: loadingOpp, refetch: refetchOpp } = useQuery({
    queryKey: ["clawdbot-opportunities"],
    queryFn: async () => {
      const res = await clawdbotAPI.getOpportunities({ page: 1, page_size: 10 });
      return res.data;
    },
  });

  const { data: tradesData, isLoading: loadingTrades } = useQuery({
    queryKey: ["clawdbot-trades"],
    queryFn: async () => {
      const res = await clawdbotAPI.getTrades({ page: 1, page_size: 10 });
      return res.data;
    },
  });

  const { data: walletsData, isLoading: loadingWallets } = useQuery({
    queryKey: ["clawdbot-wallets"],
    queryFn: async () => {
      const res = await clawdbotAPI.getWallets();
      return res.data;
    },
  });

  const { data: configData } = useQuery({
    queryKey: ["clawdbot-config"],
    queryFn: async () => {
      const res = await clawdbotAPI.getConfig();
      return res.data;
    },
  });

  const scanMutation = useMutation({
    mutationFn: () => clawdbotAPI.scanOpportunities(),
    onSuccess: () => {
      refetchOpp();
    },
  });

  const summary = tradesData?.summary || { total_pnl: 0, win_rate: 0, total_trades: 0 };

  return (
    <div>
      <Header title="ClawdBot 自动交易" />

      <div className="mx-auto max-w-lg space-y-4 p-4">
        <Link href="/profile" className="inline-flex items-center gap-1 text-sm text-muted-foreground">
          <ArrowLeft className="h-4 w-4" /> 返回个人中心
        </Link>

        {/* Summary Cards */}
        <div className="grid grid-cols-3 gap-2">
          <Card>
            <CardContent className="p-3 text-center">
              <Activity className="mx-auto h-4 w-4 text-green-500 mb-1" />
              <p className="text-lg font-bold">{summary.total_trades}</p>
              <p className="text-xs text-muted-foreground">交易次数</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-3 text-center">
              <DollarSign className={`mx-auto h-4 w-4 mb-1 ${summary.total_pnl >= 0 ? "text-green-500" : "text-red-500"}`} />
              <p className="text-lg font-bold">{summary.total_pnl.toFixed(4)}</p>
              <p className="text-xs text-muted-foreground">总盈亏 BTC</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-3 text-center">
              <TrendingUp className="mx-auto h-4 w-4 text-blue-500 mb-1" />
              <p className="text-lg font-bold">{(summary.win_rate * 100).toFixed(0)}%</p>
              <p className="text-xs text-muted-foreground">胜率</p>
            </CardContent>
          </Card>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid grid-cols-4 w-full">
            <TabsTrigger value="opportunities">机会</TabsTrigger>
            <TabsTrigger value="trades">交易</TabsTrigger>
            <TabsTrigger value="wallets">钱包</TabsTrigger>
            <TabsTrigger value="settings">设置</TabsTrigger>
          </TabsList>

          <TabsContent value="opportunities" className="space-y-3 mt-3">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-medium">交易机会</h3>
              <Button
                variant="outline"
                size="sm"
                onClick={() => scanMutation.mutate()}
                disabled={scanMutation.isPending}
              >
                <RefreshCw className={`mr-2 h-3 w-3 ${scanMutation.isPending ? "animate-spin" : ""}`} />
                {scanMutation.isPending ? "扫描中..." : "扫描市场"}
              </Button>
            </div>

            {loadingOpp ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <Card key={i}>
                    <CardContent className="p-4">
                      <div className="h-4 w-3/4 bg-muted animate-pulse rounded mb-2" />
                      <div className="h-4 w-1/2 bg-muted animate-pulse rounded" />
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : opportunitiesData?.opportunities?.length === 0 ? (
              <Card>
                <CardContent className="p-6 text-center text-sm text-muted-foreground">
                  <Zap className="mx-auto h-8 w-8 mb-2 opacity-50" />
                  <p>暂无交易机会</p>
                  <p className="text-xs mt-1">点击「扫描市场」发现新机会</p>
                </CardContent>
              </Card>
            ) : (
              opportunitiesData?.opportunities?.map((opp: Opportunity) => (
                <OpportunityCard key={opp.id} opportunity={opp} />
              ))
            )}
          </TabsContent>

          <TabsContent value="trades" className="space-y-3 mt-3">
            <h3 className="text-sm font-medium">交易历史</h3>

            {loadingTrades ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <Card key={i}>
                    <CardContent className="p-4">
                      <div className="h-4 w-1/2 bg-muted animate-pulse rounded" />
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : tradesData?.trades?.length === 0 ? (
              <Card>
                <CardContent className="p-6 text-center text-sm text-muted-foreground">
                  <TrendingUp className="mx-auto h-8 w-8 mb-2 opacity-50" />
                  <p>暂无交易记录</p>
                </CardContent>
              </Card>
            ) : (
              tradesData?.trades?.map((trade: Trade) => (
                <TradeCard key={trade.id} trade={trade} />
              ))
            )}
          </TabsContent>

          <TabsContent value="wallets" className="space-y-3 mt-3">
            <h3 className="text-sm font-medium">Bitcoin 钱包</h3>

            {loadingWallets ? (
              <div className="space-y-3">
                {[1, 2].map((i) => (
                  <Card key={i}>
                    <CardContent className="p-4">
                      <div className="h-4 w-1/3 bg-muted animate-pulse rounded" />
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : walletsData?.wallets?.length === 0 ? (
              <Card>
                <CardContent className="p-6 text-center text-sm text-muted-foreground">
                  <Wallet className="mx-auto h-8 w-8 mb-2 opacity-50" />
                  <p>暂无钱包</p>
                  <Button className="mt-2" size="sm">
                    添加钱包
                  </Button>
                </CardContent>
              </Card>
            ) : (
              walletsData?.wallets?.map((wallet: Wallet) => (
                <WalletCard key={wallet.id} wallet={wallet} />
              ))
            )}
          </TabsContent>

          <TabsContent value="settings" className="space-y-3 mt-3">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Settings className="h-4 w-4" />
                  交易设置
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm">启用 ClawdBot</span>
                  <Button
                    variant={configData?.is_enabled ? "default" : "outline"}
                    size="sm"
                  >
                    {configData?.is_enabled ? "已启用" : "已禁用"}
                  </Button>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">自动交易</span>
                  <Button
                    variant={configData?.auto_trade ? "default" : "outline"}
                    size="sm"
                  >
                    {configData?.auto_trade ? "已启用" : "已禁用"}
                  </Button>
                </div>
                <div className="pt-2 border-t">
                  <p className="text-xs text-muted-foreground mb-2">最低置信度阈值: {(configData?.min_opportunity_confidence || 0.7) * 100}%</p>
                  <p className="text-xs text-muted-foreground mb-2">最大仓位: {configData?.max_position_size_btc || 0.01} BTC</p>
                  <p className="text-xs text-muted-foreground">最大日亏损: {configData?.max_daily_loss_btc || 0.05} BTC</p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
