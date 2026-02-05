"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useWatchlistStore, DEFAULT_STOCKS } from "@/stores/watchlist-store";
import { Header } from "@/components/layout/Header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ArrowLeft, Plus, Trash2, RotateCcw, RefreshCw } from "lucide-react";
import { MarketType, WatchlistItem } from "@/types";

const MARKET_LABELS: Record<string, string> = {
  us: "美股",
  hk: "港股",
  cn: "A股",
  commodity: "商品",
};

export default function WatchlistManagePage() {
  const { items, loaded, fetchWatchlist, addStock, removeStock, initDefaults, refreshMarketData, refreshing, refreshNames } = useWatchlistStore();
  const [activeTab, setActiveTab] = useState<MarketType>("us");
  const [symbol, setSymbol] = useState("");
  const [name, setName] = useState("");
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState("");
  const [resetting, setResetting] = useState(false);

  useEffect(() => {
    if (!loaded) fetchWatchlist();
  }, [loaded, fetchWatchlist]);

  const marketItems = items.filter((i) => i.market === activeTab);

  const handleAdd = async () => {
    if (!symbol.trim()) return;
    setAdding(true);
    setError("");
    try {
      await addStock(symbol.trim().toUpperCase(), activeTab, name.trim() || undefined);
      setSymbol("");
      setName("");
    } catch (err: unknown) {
      setError((err as Error).message || "添加失败");
    } finally {
      setAdding(false);
    }
  };

  const handleRemove = async (item: WatchlistItem) => {
    await removeStock(item.id);
  };

  const handleReset = async () => {
    setResetting(true);
    await initDefaults();
    setResetting(false);
  };

  const handleAddDefault = async (stock: { symbol: string; market: string; name: string }) => {
    try {
      await addStock(stock.symbol, stock.market, stock.name);
    } catch {
      // skip if already exists
    }
  };

  // Find default stocks not yet in watchlist for current market
  const defaults = DEFAULT_STOCKS[activeTab] || [];
  const existingSymbols = new Set(marketItems.map((i) => i.symbol));
  const missingDefaults = defaults.filter((d) => !existingSymbols.has(d.symbol));

  return (
    <div>
      <Header title="自选股管理" />
      <div className="mx-auto max-w-lg space-y-3 p-4">
        <div className="flex items-center justify-between">
          <Link href="/profile" className="inline-flex items-center gap-1 text-sm text-muted-foreground">
            <ArrowLeft className="h-4 w-4" /> 返回
          </Link>
          <Button
            variant="ghost"
            size="sm"
            className="text-xs"
            onClick={handleReset}
            disabled={resetting}
          >
            <RotateCcw className="mr-1 h-3 w-3" />
            {resetting ? "重置中..." : "恢复默认"}
          </Button>
        </div>

        <p className="text-xs text-muted-foreground">
          管理您关注的股票列表，行情页面和仪表盘将展示这些股票的实时数据。
        </p>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as MarketType)}>
          <TabsList className="w-full">
            {(["us", "hk", "cn", "commodity"] as MarketType[]).map((m) => (
              <TabsTrigger key={m} value={m} className="flex-1">
                {MARKET_LABELS[m]}
                {items.filter((i) => i.market === m).length > 0 && (
                  <Badge variant="secondary" className="ml-1 px-1 text-[10px]">
                    {items.filter((i) => i.market === m).length}
                  </Badge>
                )}
              </TabsTrigger>
            ))}
          </TabsList>

          {(["us", "hk", "cn", "commodity"] as MarketType[]).map((market) => (
            <TabsContent key={market} value={market} className="mt-3 space-y-3">
              {/* Add Stock Form */}
              <Card>
                <CardContent className="p-3">
                  <div className="flex gap-2">
                    <Input
                      placeholder="股票代码"
                      value={symbol}
                      onChange={(e) => setSymbol(e.target.value)}
                      className="flex-1"
                      onKeyDown={(e) => e.key === "Enter" && handleAdd()}
                    />
                    <Input
                      placeholder="名称(可选)"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="flex-1"
                      onKeyDown={(e) => e.key === "Enter" && handleAdd()}
                    />
                    <Button size="sm" onClick={handleAdd} disabled={adding || !symbol.trim()}>
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                  {error && <p className="mt-1 text-xs text-destructive">{error}</p>}
                  {market === "cn" && (
                    <p className="mt-1 text-[10px] text-muted-foreground">A股代码格式: 600519.SH / 000858.SZ</p>
                  )}
                  {market === "hk" && (
                    <p className="mt-1 text-[10px] text-muted-foreground">港股代码格式: 0700.HK / 9988.HK</p>
                  )}
                  {market === "commodity" && (
                    <p className="mt-1 text-[10px] text-muted-foreground">商品代码: XAU/USD, XAG/USD, CL, NG</p>
                  )}
                </CardContent>
              </Card>

              {/* Refresh Button */}
              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => refreshNames()}
                  disabled={refreshing}
                >
                  <RefreshCw className={`mr-1 h-3 w-3 ${refreshing ? "animate-spin" : ""}`} />
                  {refreshing ? "刷新中..." : "刷新名称"}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => refreshMarketData(market as MarketType)}
                  disabled={refreshing}
                >
                  <RefreshCw className={`mr-1 h-3 w-3 ${refreshing ? "animate-spin" : ""}`} />
                  {refreshing ? "刷新中..." : "刷新数据"}
                </Button>
              </div>

              {/* Quick Add Missing Defaults */}
              {missingDefaults.length > 0 && market === activeTab && (
                <div className="flex flex-wrap gap-1">
                  <span className="text-[10px] text-muted-foreground leading-6">快速添加:</span>
                  {missingDefaults.map((stock) => (
                    <Button
                      key={stock.symbol}
                      variant="outline"
                      size="sm"
                      className="h-6 text-[10px] px-2"
                      onClick={() => handleAddDefault(stock)}
                    >
                      <Plus className="mr-0.5 h-3 w-3" />
                      {stock.symbol}
                    </Button>
                  ))}
                </div>
              )}

              {/* Stock List */}
              {items.filter((i) => i.market === market).length > 0 ? (
                <Card>
                  <CardContent className="p-0">
                    {items
                      .filter((i) => i.market === market)
                      .map((item, idx, arr) => (
                        <div
                          key={item.id}
                          className={`flex items-center justify-between p-3 ${idx < arr.length - 1 ? "border-b" : ""}`}
                        >
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium truncate">{item.name || item.symbol}</p>
                            <p className="text-xs text-muted-foreground truncate">{item.symbol}</p>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0 text-muted-foreground hover:text-destructive flex-shrink-0"
                            onClick={() => handleRemove(item)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                  </CardContent>
                </Card>
              ) : (
                <div className="flex h-24 items-center justify-center text-sm text-muted-foreground">
                  暂无{MARKET_LABELS[market]}自选股
                </div>
              )}
            </TabsContent>
          ))}
        </Tabs>
      </div>
    </div>
  );
}
