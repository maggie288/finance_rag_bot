"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { reportsAPI } from "@/lib/api-client";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, FileText, RefreshCw, Search } from "lucide-react";
import { PredictionResult } from "@/types";

interface PredictionWithName extends PredictionResult {
  stock_name?: string;
}

const predictionTypeLabels: Record<string, string> = {
  "3day": "3天",
  "1week": "1周",
  "1month": "1个月",
};

function formatDate(date: string | Date): string {
  const d = new Date(date);
  return d.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function PredictionCard({ prediction }: { prediction: PredictionWithName }) {
  return (
    <Link href={`/market/${encodeURIComponent(prediction.symbol)}/prediction?market=${prediction.market}&from=report&id=${prediction.id}`}>
      <Card className="cursor-pointer transition-all hover:shadow-md hover:border-primary/30">
        <CardContent className="p-4">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg">{prediction.symbol}</span>
                <Badge variant="outline" className="text-xs">
                  {predictionTypeLabels[prediction.prediction_type] || prediction.prediction_type}
                </Badge>
              </div>
              {prediction.stock_name && (
                <p className="text-sm text-muted-foreground">{prediction.stock_name}</p>
              )}
            </div>
            <div className="text-right text-sm">
              <p className="text-muted-foreground">预测时间</p>
              <p className="font-medium">{formatDate(prediction.created_at)}</p>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-3 gap-2 text-center">
            <div className="rounded bg-red-500/10 p-2">
              <p className="text-xs text-muted-foreground">低位</p>
              <p className="font-bold text-red-500">{prediction.predicted_range.low.toFixed(2)}</p>
            </div>
            <div className="rounded bg-blue-500/10 p-2">
              <p className="text-xs text-muted-foreground">中位</p>
              <p className="font-bold text-blue-500">{prediction.predicted_range.mid.toFixed(2)}</p>
            </div>
            <div className="rounded bg-green-500/10 p-2">
              <p className="text-xs text-muted-foreground">高位</p>
              <p className="font-bold text-green-500">{prediction.predicted_range.high.toFixed(2)}</p>
            </div>
          </div>

          <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
            <span>当前: {prediction.current_price.toFixed(2)}</span>
            <span>置信度: {(prediction.confidence * 100).toFixed(1)}%</span>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

function PredictionSkeleton() {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="h-6 w-20 bg-muted rounded animate-pulse" />
            <div className="h-5 w-12 bg-muted rounded animate-pulse" />
          </div>
          <div className="h-4 w-32 bg-muted rounded animate-pulse" />
          <div className="grid grid-cols-3 gap-2">
            <div className="h-12 bg-muted rounded animate-pulse" />
            <div className="h-12 bg-muted rounded animate-pulse" />
            <div className="h-12 bg-muted rounded animate-pulse" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function PredictionReportsPage() {
  const [page, setPage] = useState(1);
  const [searchSymbol, setSearchSymbol] = useState("");
  const [filterType, setFilterType] = useState("");

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["prediction-reports", page, searchSymbol, filterType],
    queryFn: async () => {
      const res = await reportsAPI.listPredictions({
        page,
        page_size: 10,
        symbol: searchSymbol || undefined,
        prediction_type: filterType || undefined,
      });
      return res.data;
    },
  });

  return (
    <div>
      <Header title="价格预测报告" />

      <div className="mx-auto max-w-lg space-y-4 p-4">
        <Link href="/profile" className="inline-flex items-center gap-1 text-sm text-muted-foreground">
          <ArrowLeft className="h-4 w-4" /> 返回个人中心
        </Link>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <FileText className="h-4 w-4" />
              预测报告列表
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="搜索股票代码..."
                  value={searchSymbol}
                  onChange={(e) => setSearchSymbol(e.target.value)}
                  className="w-full rounded-md border border-input bg-background py-2 pl-8 pr-3 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="">全部周期</option>
                <option value="3day">3天</option>
                <option value="1week">1周</option>
                <option value="1month">1个月</option>
              </select>
            </div>

            <Button variant="outline" size="sm" className="w-full" onClick={() => refetch()}>
              <RefreshCw className="mr-2 h-3 w-3" />
              刷新
            </Button>
          </CardContent>
        </Card>

        {error && (
          <Card className="border-destructive">
            <CardContent className="p-4 text-sm text-destructive">
              加载失败: {(error as Error)?.message || "请稍后重试"}
            </CardContent>
          </Card>
        )}

        <div className="space-y-3">
          {isLoading ? (
            Array.from({ length: 3 }).map((_, i) => <PredictionSkeleton key={i} />)
          ) : data?.predictions?.length === 0 ? (
            <Card>
              <CardContent className="p-6 text-center text-sm text-muted-foreground">
                <FileText className="mx-auto h-8 w-8 mb-2 opacity-50" />
                <p>暂无预测报告</p>
                <p className="text-xs mt-1">前往股票详情页进行价格预测并保存</p>
              </CardContent>
            </Card>
          ) : (
            data?.predictions?.map((prediction: PredictionWithName) => (
              <PredictionCard key={prediction.id} prediction={prediction} />
            ))
          )}
        </div>

        {data && data.predictions?.length > 0 && (
          <div className="flex items-center justify-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              上一页
            </Button>
            <span className="text-sm text-muted-foreground">
              第 {page} 页
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => p + 1)}
              disabled={!data?.predictions || data.predictions.length < 10}
            >
              下一页
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
