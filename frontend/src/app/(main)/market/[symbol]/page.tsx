"use client";

import { useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import dynamic from "next/dynamic";
import { marketAPI } from "@/lib/api-client";
import { Header } from "@/components/layout/Header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  BarChart3,
  FileText,
  Brain,
  ArrowLeft,
  Zap,
  Newspaper,
} from "lucide-react";
import { StockQuote, KlinePoint } from "@/types";

const CandlestickChart = dynamic(
  () => import("@/components/charts/CandlestickChart").then((mod) => mod.CandlestickChart),
  { ssr: false, loading: () => <ChartLoadingPlaceholder /> }
);

function ChartLoadingPlaceholder() {
  return (
    <div className="flex h-[300px] items-center justify-center">
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
    </div>
  );
}

const INTERVALS = [
  { value: "5min", label: "分时" },
  { value: "1day", label: "日K" },
  { value: "1week", label: "周K" },
  { value: "1month", label: "月K" },
];

export default function StockDetailPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const symbol = decodeURIComponent(params.symbol as string);
  const market = searchParams.get("market") || "us";
  const [interval, setInterval] = useState("1day");

  // Fetch quote
  const { data: quote } = useQuery({
    queryKey: ["quote", symbol, market],
    queryFn: async () => {
      const res = await marketAPI.getQuote(symbol, market);
      return res.data as StockQuote;
    },
    refetchInterval: 10000,
  });

  // Fetch kline
  const { data: klineData, isLoading: klineLoading } = useQuery({
    queryKey: ["kline", symbol, market, interval],
    queryFn: async () => {
      const outputsize = interval === "5min" ? 78 : interval === "1day" ? 120 : 60;
      const res = await marketAPI.getKline(symbol, market, interval, outputsize);
      return res.data.data as KlinePoint[];
    },
  });

  const isUp = quote?.change_percent != null && quote.change_percent >= 0;

  return (
    <div>
      <Header title={symbol} />
      <div className="mx-auto max-w-lg">
        {/* Back button */}
        <div className="px-4 pt-2">
          <Link href="/market" className="inline-flex items-center gap-1 text-sm text-muted-foreground">
            <ArrowLeft className="h-4 w-4" /> 返回行情
          </Link>
        </div>

        {/* Price Header */}
        <div className="px-4 py-3">
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold tabular-nums">
              {quote ? quote.price.toFixed(2) : "---"}
            </span>
            {quote?.change_percent != null && (
              <span className={`text-sm font-medium ${isUp ? "price-up" : "price-down"}`}>
                {isUp ? "+" : ""}{quote.change?.toFixed(2)} ({isUp ? "+" : ""}{quote.change_percent.toFixed(2)}%)
              </span>
            )}
          </div>
          <div className="mt-1 flex gap-4 text-xs text-muted-foreground">
            {quote?.high != null && <span>高: {quote.high.toFixed(2)}</span>}
            {quote?.low != null && <span>低: {quote.low.toFixed(2)}</span>}
            {quote?.volume != null && <span>量: {(quote.volume / 10000).toFixed(0)}万</span>}
          </div>
        </div>

        {/* Chart Period Selector */}
        <div className="flex gap-1 px-4 pb-2">
          {INTERVALS.map((item) => (
            <Button
              key={item.value}
              variant={interval === item.value ? "default" : "ghost"}
              size="sm"
              className="h-7 text-xs"
              onClick={() => setInterval(item.value)}
            >
              {item.label}
            </Button>
          ))}
        </div>

        {/* Chart */}
        <div className="px-2">
          {klineLoading ? (
            <div className="flex h-[300px] items-center justify-center">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            </div>
          ) : klineData && klineData.length > 0 ? (
            <CandlestickChart data={klineData} height={300} />
          ) : (
            <div className="flex h-[300px] items-center justify-center text-sm text-muted-foreground">
              暂无数据
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="grid grid-cols-2 gap-2 px-4 py-4">
          <Link href={`/market/${encodeURIComponent(symbol)}/news?market=${market}`}>
            <Button variant="outline" className="w-full h-auto flex-col gap-1 py-3">
              <Newspaper className="h-4 w-4" />
              <span className="text-xs">新闻资讯</span>
            </Button>
          </Link>
          <Link href={`/market/${encodeURIComponent(symbol)}/fundamental?market=${market}`}>
            <Button variant="outline" className="w-full h-auto flex-col gap-1 py-3">
              <FileText className="h-4 w-4" />
              <span className="text-xs">基本面分析</span>
            </Button>
          </Link>
          <Link href={`/market/${encodeURIComponent(symbol)}/prediction?market=${market}`}>
            <Button variant="outline" className="w-full h-auto flex-col gap-1 py-3">
              <Brain className="h-4 w-4" />
              <span className="text-xs">价格预测</span>
            </Button>
          </Link>
          <Link href={`/market/${encodeURIComponent(symbol)}/ai-trading?market=${market}`}>
            <Button variant="outline" className="w-full h-auto flex-col gap-1 py-3">
              <Zap className="h-4 w-4" />
              <span className="text-xs">AI交易代理</span>
            </Button>
          </Link>
          <Link href={`/ai-chat?symbol=${encodeURIComponent(symbol)}&market=${market}`}>
            <Button variant="outline" className="w-full h-auto flex-col gap-1 py-3">
              <BarChart3 className="h-4 w-4" />
              <span className="text-xs">AI分析</span>
            </Button>
          </Link>
        </div>

        {/* Quote Details */}
        {quote && (
          <Card className="mx-4 mb-4">
            <CardContent className="grid grid-cols-2 gap-3 p-4 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">开盘</span>
                <span className="tabular-nums">{quote.open?.toFixed(2) || "---"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">昨收</span>
                <span className="tabular-nums">{quote.prev_close?.toFixed(2) || "---"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">最高</span>
                <span className="tabular-nums">{quote.high?.toFixed(2) || "---"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">最低</span>
                <span className="tabular-nums">{quote.low?.toFixed(2) || "---"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">成交量</span>
                <span className="tabular-nums">
                  {quote.volume ? `${(quote.volume / 10000).toFixed(0)}万` : "---"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">市场</span>
                <Badge variant="secondary" className="text-xs">
                  {market === "us" ? "美股" : market === "hk" ? "港股" : market === "cn" ? "A股" : "商品"}
                </Badge>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
