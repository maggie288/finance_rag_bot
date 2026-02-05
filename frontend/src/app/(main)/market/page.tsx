"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { marketAPI } from "@/lib/api-client";
import { useWatchlistStore } from "@/stores/watchlist-store";
import { Header } from "@/components/layout/Header";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Search, Settings2 } from "lucide-react";
import { MarketType, StockQuote, WatchlistItem } from "@/types";
import Link from "next/link";

function StockRow({
  symbol,
  name,
  market,
  quote,
}: {
  symbol: string;
  name: string;
  market: string;
  quote?: StockQuote;
}) {
  const router = useRouter();
  const isUp = quote?.change_percent != null && quote.change_percent >= 0;

  return (
    <div
      className="flex cursor-pointer items-center justify-between border-b p-3 transition-colors last:border-0 hover:bg-accent/50"
      onClick={() => router.push(`/market/${encodeURIComponent(symbol)}?market=${market}`)}
    >
      <div className="flex-1">
        <p className="text-sm font-medium">{symbol}</p>
        <p className="text-xs text-muted-foreground">{name}</p>
      </div>
      <div className="text-right">
        <p className="text-sm font-semibold tabular-nums">
          {quote ? quote.price.toFixed(2) : "---"}
        </p>
      </div>
      <div className="ml-3 w-20 text-right">
        {quote?.change_percent != null ? (
          <Badge
            variant="secondary"
            className={`text-xs tabular-nums ${isUp ? "bg-green-500/10 text-green-500" : "bg-red-500/10 text-red-500"}`}
          >
            {isUp ? "+" : ""}
            {quote.change_percent.toFixed(2)}%
          </Badge>
        ) : (
          <span className="text-xs text-muted-foreground">---</span>
        )}
      </div>
    </div>
  );
}

function SearchStockRow({ symbol, name, market }: { symbol: string; name: string; market: string }) {
  const { data } = useQuery({
    queryKey: ["quote", symbol],
    queryFn: async () => {
      const res = await marketAPI.getQuote(symbol, market);
      return res.data as StockQuote;
    },
  });

  return <StockRow symbol={symbol} name={name} market={market} quote={data} />;
}

function MarketTabContent({ market, stocks }: { market: string; stocks: WatchlistItem[] }) {
  // Single batch request for all stocks in this tab
  const { data: quotes } = useQuery({
    queryKey: ["batch-quote", market, stocks.map((s) => s.symbol).join(",")],
    queryFn: async () => {
      if (stocks.length === 0) return {};
      const res = await marketAPI.batchQuote(
        stocks.map((s) => ({ symbol: s.symbol, market: s.market }))
      );
      const map: Record<string, StockQuote> = {};
      for (const q of res.data.quotes) {
        map[q.symbol] = q;
      }
      return map;
    },
    enabled: stocks.length > 0,
    refetchInterval: 30000,
  });

  if (stocks.length === 0) {
    return (
      <div className="mx-4 flex h-32 flex-col items-center justify-center text-sm text-muted-foreground">
        <p>暂无自选股</p>
        <Link href="/profile/watchlist" className="mt-1 text-xs text-primary">
          去添加自选股
        </Link>
      </div>
    );
  }

  return (
    <Card className="mx-4">
      <CardContent className="p-0">
        {stocks.map((stock) => (
          <StockRow
            key={stock.symbol}
            symbol={stock.symbol}
            name={stock.name || stock.symbol}
            market={market}
            quote={quotes?.[stock.symbol]}
          />
        ))}
      </CardContent>
    </Card>
  );
}

export default function MarketPage() {
  const [activeTab, setActiveTab] = useState<MarketType>("us");
  const [searchQuery, setSearchQuery] = useState("");
  const { items, loaded, fetchWatchlist } = useWatchlistStore();

  useEffect(() => {
    if (!loaded) fetchWatchlist();
  }, [loaded, fetchWatchlist]);

  const { data: searchResults } = useQuery({
    queryKey: ["search", searchQuery],
    queryFn: async () => {
      if (searchQuery.length < 1) return [];
      const res = await marketAPI.search(searchQuery);
      return res.data;
    },
    enabled: searchQuery.length >= 1,
  });

  return (
    <div>
      <Header title="市场行情" />
      <div className="mx-auto max-w-lg">
        {/* Search */}
        <div className="flex items-center gap-2 p-4 pb-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="搜索股票代码或名称..."
              className="pl-9"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <Link href="/profile/watchlist">
            <Settings2 className="h-5 w-5 text-muted-foreground" />
          </Link>
        </div>

        {/* Search Results */}
        {searchQuery && searchResults && searchResults.length > 0 && (
          <Card className="mx-4 mb-2">
            <CardContent className="p-0">
              {searchResults.slice(0, 5).map((item: Record<string, string>, i: number) => (
                <SearchStockRow
                  key={i}
                  symbol={item.symbol}
                  name={item.name}
                  market={item.country === "China" ? "cn" : item.exchange?.includes("HK") ? "hk" : "us"}
                />
              ))}
            </CardContent>
          </Card>
        )}

        {/* Market Tabs */}
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as MarketType)}>
          <div className="px-4">
            <TabsList className="w-full">
              <TabsTrigger value="us" className="flex-1">美股</TabsTrigger>
              <TabsTrigger value="hk" className="flex-1">港股</TabsTrigger>
              <TabsTrigger value="cn" className="flex-1">A股</TabsTrigger>
              <TabsTrigger value="commodity" className="flex-1">商品</TabsTrigger>
            </TabsList>
          </div>

          {(["us", "hk", "cn", "commodity"] as MarketType[]).map((market) => (
            <TabsContent key={market} value={market} className="mt-2">
              <MarketTabContent
                market={market}
                stocks={items.filter((i) => i.market === market)}
              />
            </TabsContent>
          ))}
        </Tabs>
      </div>
    </div>
  );
}
