"use client";

import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "@/stores/auth-store";
import { marketAPI } from "@/lib/api-client";
import { useWatchlistStore } from "@/stores/watchlist-store";
import { Header } from "@/components/layout/Header";
import { Card, CardContent } from "@/components/ui/card";
import Link from "next/link";
import {
  TrendingUp,
  BarChart3,
  MessageSquare,
  Brain,
  Globe,
  Coins,
} from "lucide-react";
import { StockQuote } from "@/types";

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const { items, loaded, fetchWatchlist } = useWatchlistStore();

  useEffect(() => {
    if (!loaded) fetchWatchlist();
  }, [loaded, fetchWatchlist]);

  // Take first 7 watchlist items for the quick quotes section
  const quickItems = items.slice(0, 7);

  // Single batch request for dashboard quotes
  const { data: quotes } = useQuery({
    queryKey: ["dashboard-batch-quote", quickItems.map((s) => s.symbol).join(",")],
    queryFn: async () => {
      if (quickItems.length === 0) return {};
      const res = await marketAPI.batchQuote(
        quickItems.map((s) => ({ symbol: s.symbol, market: s.market }))
      );
      const map: Record<string, StockQuote> = {};
      for (const q of res.data.quotes) {
        map[q.symbol] = q;
      }
      return map;
    },
    enabled: quickItems.length > 0,
    refetchInterval: 30000,
  });

  return (
    <div>
      <Header title="Finance RAG Bot" />
      <div className="mx-auto max-w-lg space-y-4 p-4">
        {/* Welcome */}
        <div>
          <h2 className="text-lg font-semibold">
            {user?.display_name || user?.email?.split("@")[0]}，你好
          </h2>
          <p className="text-sm text-muted-foreground">AI驱动的金融量化分析助手</p>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-4 gap-2">
          <Link href="/market" className="flex flex-col items-center gap-1 rounded-lg bg-card p-3 text-center">
            <BarChart3 className="h-5 w-5 text-blue-500" />
            <span className="text-xs">行情</span>
          </Link>
          <Link href="/ai-chat" className="flex flex-col items-center gap-1 rounded-lg bg-card p-3 text-center">
            <MessageSquare className="h-5 w-5 text-green-500" />
            <span className="text-xs">AI分析</span>
          </Link>
          <Link href="/news" className="flex flex-col items-center gap-1 rounded-lg bg-card p-3 text-center">
            <Globe className="h-5 w-5 text-purple-500" />
            <span className="text-xs">资讯</span>
          </Link>
          <Link href="/profile/credits" className="flex flex-col items-center gap-1 rounded-lg bg-card p-3 text-center">
            <Coins className="h-5 w-5 text-yellow-500" />
            <span className="text-xs">积分</span>
          </Link>
        </div>

        {/* Quick Quotes */}
        <div>
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-medium">我的自选</h3>
            <Link href="/profile/watchlist" className="text-xs text-primary">
              管理自选
            </Link>
          </div>
          {quickItems.length > 0 ? (
            <div className="grid grid-cols-2 gap-2">
              {quickItems.map((item) => {
                const quote = quotes?.[item.symbol];
                const isUp = quote?.change_percent != null && quote.change_percent >= 0;
                return (
                  <Link key={item.symbol} href={`/market/${encodeURIComponent(item.symbol)}?market=${item.market}`}>
                    <Card className="cursor-pointer transition-colors hover:bg-accent/50">
                      <CardContent className="p-3">
                        <div className="flex items-center justify-between">
                          <div className="min-w-0 flex-1">
                            <p className="truncate text-sm font-medium">{item.name || item.symbol}</p>
                            <p className="truncate text-xs text-muted-foreground">{item.symbol}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-sm font-semibold">
                              {quote ? quote.price.toFixed(2) : "---"}
                            </p>
                            {quote?.change_percent != null && (
                              <p className={`text-xs ${isUp ? "price-up" : "price-down"}`}>
                                {isUp ? "+" : ""}
                                {quote.change_percent.toFixed(2)}%
                              </p>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                );
              })}
            </div>
          ) : (
            <Card>
              <CardContent className="flex h-20 items-center justify-center p-3">
                <Link href="/profile/watchlist" className="text-sm text-muted-foreground">
                  添加自选股以在此展示行情
                </Link>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Feature Cards */}
        <div className="space-y-2">
          <h3 className="text-sm font-medium">功能入口</h3>

          <Link href="/ai-chat">
            <Card className="cursor-pointer transition-colors hover:bg-accent/50">
              <CardContent className="flex items-center gap-3 p-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/10">
                  <Brain className="h-5 w-5 text-blue-500" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">RAG 智能问答</p>
                  <p className="text-xs text-muted-foreground">
                    查询股票新闻、财报分析、舆情总结
                  </p>
                </div>
              </CardContent>
            </Card>
          </Link>

          <Link href="/market">
            <Card className="cursor-pointer transition-colors hover:bg-accent/50">
              <CardContent className="flex items-center gap-3 p-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-500/10">
                  <TrendingUp className="h-5 w-5 text-green-500" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">多市场行情</p>
                  <p className="text-xs text-muted-foreground">
                    美股、港股、A股、大宗商品实时数据
                  </p>
                </div>
              </CardContent>
            </Card>
          </Link>
        </div>
      </div>
    </div>
  );
}
