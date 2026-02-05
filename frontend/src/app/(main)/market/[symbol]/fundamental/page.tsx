"use client";

import { useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { useQuery, useMutation } from "@tanstack/react-query";
import Link from "next/link";
import { marketAPI, reportsAPI } from "@/lib/api-client";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Brain, Loader2, Info } from "lucide-react";
import { FundamentalData } from "@/types";

function MetricRow({ label, value, suffix = "" }: { label: string; value: number | null | undefined; suffix?: string }) {
  return (
    <div className="flex items-center justify-between py-2">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium tabular-nums">
        {value != null ? `${value.toFixed(2)}${suffix}` : "---"}
      </span>
    </div>
  );
}

function formatLargeNumber(num: number | null | undefined): string {
  if (num == null) return "---";
  if (Math.abs(num) >= 1e12) return `${(num / 1e12).toFixed(2)}万亿`;
  if (Math.abs(num) >= 1e8) return `${(num / 1e8).toFixed(2)}亿`;
  if (Math.abs(num) >= 1e4) return `${(num / 1e4).toFixed(2)}万`;
  return num.toFixed(2);
}

export default function FundamentalPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const symbol = decodeURIComponent(params.symbol as string);
  const market = searchParams.get("market") || "us";
  const [aiReport, setAiReport] = useState<string | null>(null);

  const { data: fundamentals, isLoading } = useQuery({
    queryKey: ["fundamentals", symbol, market],
    queryFn: async () => {
      const res = await marketAPI.getFundamentals(symbol, market);
      return res.data as FundamentalData;
    },
  });

  const reportMutation = useMutation({
    mutationFn: async () => {
      const res = await reportsAPI.generate({
        report_type: "fundamental",
        symbol,
        market,
      });
      return res.data;
    },
    onSuccess: (data) => {
      setAiReport(data.content);
    },
  });

  return (
    <div>
      <Header title={`${symbol} 基本面`} />
      <div className="mx-auto max-w-lg space-y-4 p-4">
        <Link href={`/market/${encodeURIComponent(symbol)}?market=${market}`} className="inline-flex items-center gap-1 text-sm text-muted-foreground">
          <ArrowLeft className="h-4 w-4" /> 返回
        </Link>

        {isLoading ? (
          <div className="flex h-40 items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : fundamentals ? (
          <>
            {/* Estimation Warning */}
            {fundamentals.is_estimated && (
              <div className="rounded-lg border border-yellow-500/20 bg-yellow-500/10 p-3">
                <div className="flex items-start gap-2">
                  <Info className="h-4 w-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                  <div className="text-sm">
                    <p className="font-medium text-yellow-500">基于行情数据估算</p>
                    <p className="text-muted-foreground mt-1">
                      {fundamentals.estimation_note || "当前数据基于股票行情数据估算得出，仅供参考"}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Valuation */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">估值指标</CardTitle>
              </CardHeader>
              <CardContent className="space-y-0 divide-y">
                <MetricRow label="市盈率 (PE)" value={fundamentals.pe_ratio} suffix="x" />
                <MetricRow label="市净率 (PB)" value={fundamentals.pb_ratio} suffix="x" />
                <MetricRow label="每股收益 (EPS)" value={fundamentals.eps} />
                <MetricRow label="股息率" value={fundamentals.dividend_yield} suffix="%" />
                <div className="flex items-center justify-between py-2">
                  <span className="text-sm text-muted-foreground">总市值</span>
                  <span className="text-sm font-medium">{formatLargeNumber(fundamentals.market_cap)}</span>
                </div>
              </CardContent>
            </Card>

            {/* Profitability */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">盈利能力</CardTitle>
              </CardHeader>
              <CardContent className="space-y-0 divide-y">
                <MetricRow label="净资产收益率 (ROE)" value={fundamentals.roe} suffix="%" />
                <MetricRow label="净利润率" value={fundamentals.net_profit_margin} suffix="%" />
                <MetricRow label="营收增长率" value={fundamentals.revenue_growth} suffix="%" />
                <div className="flex items-center justify-between py-2">
                  <span className="text-sm text-muted-foreground">营业收入</span>
                  <span className="text-sm font-medium">{formatLargeNumber(fundamentals.revenue)}</span>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="text-sm text-muted-foreground">净利润</span>
                  <span className="text-sm font-medium">{formatLargeNumber(fundamentals.net_income)}</span>
                </div>
              </CardContent>
            </Card>

            {/* Financial Health */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">财务健康</CardTitle>
              </CardHeader>
              <CardContent className="space-y-0 divide-y">
                <MetricRow label="负债率" value={fundamentals.debt_ratio} suffix="%" />
                <div className="flex items-center justify-between py-2">
                  <span className="text-sm text-muted-foreground">总负债</span>
                  <span className="text-sm font-medium">{formatLargeNumber(fundamentals.total_debt)}</span>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="text-sm text-muted-foreground">现金及等价物</span>
                  <span className="text-sm font-medium">{formatLargeNumber(fundamentals.total_cash)}</span>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="text-sm text-muted-foreground">经营现金流</span>
                  <span className="text-sm font-medium">{formatLargeNumber(fundamentals.operating_cash_flow)}</span>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="text-sm text-muted-foreground">自由现金流</span>
                  <span className="text-sm font-medium">{formatLargeNumber(fundamentals.free_cash_flow)}</span>
                </div>
              </CardContent>
            </Card>

            {/* Technical Indicators (when estimated) */}
            {fundamentals.is_estimated && (fundamentals.price_ma20 || fundamentals.volatility || fundamentals.return_60d) && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">技术指标</CardTitle>
                </CardHeader>
                <CardContent className="space-y-0 divide-y">
                  <MetricRow label="20日均线" value={fundamentals.price_ma20} />
                  <MetricRow label="60日均线" value={fundamentals.price_ma60} />
                  <MetricRow label="60日涨跌幅" value={fundamentals.return_60d} suffix="%" />
                  <MetricRow label="波动率（年化）" value={fundamentals.volatility} suffix="%" />
                </CardContent>
              </Card>
            )}
          </>
        ) : (
          <div className="flex h-40 items-center justify-center text-sm text-muted-foreground">
            暂无基本面数据
          </div>
        )}

        {/* AI Report Button */}
        <Button
          className="w-full"
          onClick={() => reportMutation.mutate()}
          disabled={reportMutation.isPending}
        >
          {reportMutation.isPending ? (
            <><Loader2 className="mr-2 h-4 w-4 animate-spin" />AI分析生成中...</>
          ) : (
            <><Brain className="mr-2 h-4 w-4" />AI 基本面分析报告 (5积分)</>
          )}
        </Button>

        {/* AI Report Content */}
        {aiReport && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Brain className="h-4 w-4" /> AI分析报告
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm prose-invert max-w-none whitespace-pre-wrap text-sm">
                {aiReport}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
