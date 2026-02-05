"use client";

import { useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { predictionAPI, reportsAPI } from "@/lib/api-client";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Brain, Loader2, TrendingUp, TrendingDown, Minus, ExternalLink } from "lucide-react";
import { PredictionResult, ComputationStep } from "@/types";

function StepCard({ step }: { step: ComputationStep }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border-l-2 border-primary/30 pl-4 pb-4">
      <div
        className="cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="text-xs h-5 w-5 p-0 flex items-center justify-center rounded-full">
            {step.step}
          </Badge>
          <span className="text-sm font-medium">{step.title}</span>
        </div>
        <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
          {step.description}
        </p>
      </div>
      {expanded && step.data && (
        <div className="mt-2 rounded bg-muted/50 p-3">
          <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
            {JSON.stringify(step.data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

function ProbBar({ label, value }: { label: string; value: number }) {
  const percent = (value * 100).toFixed(1);
  const isPositive = label.includes("上涨");
  const isNegative = label.includes("下跌");

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span>{label}</span>
        <span className="tabular-nums">{percent}%</span>
      </div>
      <div className="h-2 rounded-full bg-muted overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${
            isPositive ? "bg-green-500" : isNegative ? "bg-red-500" : "bg-blue-500"
          }`}
          style={{ width: `${Math.max(Number(percent), 2)}%` }}
        />
      </div>
    </div>
  );
}

export default function PredictionPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const symbol = decodeURIComponent(params.symbol as string);
  const market = searchParams.get("market") || "us";
  const predictionId = searchParams.get("id");
  const [predictionType, setPredictionType] = useState("1week");
  const [result, setResult] = useState<PredictionResult | null>(null);

  const mutation = useMutation({
    mutationFn: async () => {
      const res = await predictionAPI.markov({
        symbol,
        market,
        prediction_type: predictionType,
      });
      return res.data as PredictionResult;
    },
    onSuccess: (data) => setResult(data),
  });

  useQuery({
    queryKey: ["prediction-detail", predictionId],
    queryFn: async () => {
      if (!predictionId) return null;
      const res = await reportsAPI.getPrediction(predictionId);
      setResult(res.data);
      return res.data;
    },
    enabled: !!predictionId,
  });

  const horizonLabel: Record<string, string> = {
    "3day": "3天",
    "1week": "1周",
    "1month": "1个月",
  };

  return (
    <div>
      <Header title={`${symbol} 价格预测`} />
      <div className="mx-auto max-w-lg space-y-4 p-4">
        <Link href={`/market/${encodeURIComponent(symbol)}?market=${market}`} className="inline-flex items-center gap-1 text-sm text-muted-foreground">
          <ArrowLeft className="h-4 w-4" /> 返回
        </Link>

        {/* Prediction Controls */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">马尔可夫链价格预测</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-xs text-muted-foreground">
              基于历史价格数据构建状态转移矩阵，通过矩阵幂运算预测未来价格概率分布。
            </p>
            <div className="flex gap-2">
              {(["3day", "1week", "1month"] as const).map((type) => (
                <Button
                  key={type}
                  variant={predictionType === type ? "default" : "outline"}
                  size="sm"
                  className="flex-1"
                  onClick={() => setPredictionType(type)}
                >
                  {horizonLabel[type]}
                </Button>
              ))}
            </div>
            <Button
              className="w-full"
              onClick={() => mutation.mutate()}
              disabled={mutation.isPending}
            >
              {mutation.isPending ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />计算中...</>
              ) : (
                <><Brain className="mr-2 h-4 w-4" />开始预测 (1积分)</>
              )}
            </Button>
          </CardContent>
        </Card>

        {mutation.isError && (
          <Card className="border-destructive">
            <CardContent className="p-4 text-sm text-destructive">
              预测失败: {(mutation.error as Error)?.message || "请稍后重试"}
            </CardContent>
          </Card>
        )}

        {/* Results */}
        {result && (
          <>
            {/* Price Range */}
            <Card>
              <CardHeader className="pb-2 flex flex-row items-center justify-between">
                <CardTitle className="text-sm">预测结果 ({horizonLabel[result.prediction_type]})</CardTitle>
                {result && (
                  <Link
                    href={`/profile/prediction?id=${result.id}`}
                    className="text-xs text-muted-foreground hover:text-primary flex items-center gap-1"
                  >
                    <ExternalLink className="h-3 w-3" />
                    查看已保存
                  </Link>
                )}
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div className="rounded-lg bg-red-500/10 p-3">
                    <TrendingDown className="mx-auto h-4 w-4 text-red-500 mb-1" />
                    <p className="text-xs text-muted-foreground">低位</p>
                    <p className="text-sm font-bold tabular-nums text-red-500">
                      {result.predicted_range.low.toFixed(2)}
                    </p>
                  </div>
                  <div className="rounded-lg bg-blue-500/10 p-3">
                    <Minus className="mx-auto h-4 w-4 text-blue-500 mb-1" />
                    <p className="text-xs text-muted-foreground">中位</p>
                    <p className="text-sm font-bold tabular-nums text-blue-500">
                      {result.predicted_range.mid.toFixed(2)}
                    </p>
                  </div>
                  <div className="rounded-lg bg-green-500/10 p-3">
                    <TrendingUp className="mx-auto h-4 w-4 text-green-500 mb-1" />
                    <p className="text-xs text-muted-foreground">高位</p>
                    <p className="text-sm font-bold tabular-nums text-green-500">
                      {result.predicted_range.high.toFixed(2)}
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs">
                  <span>当前价格: <strong className="tabular-nums">{result.current_price.toFixed(2)}</strong></span>
                  <span>当前状态: <Badge variant="secondary" className="text-xs">{result.current_state}</Badge></span>
                </div>
                <div className="text-xs text-muted-foreground">
                  置信度: {(result.confidence * 100).toFixed(1)}%
                </div>
              </CardContent>
            </Card>

            {/* State Probabilities */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">状态概率分布</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {Object.entries(result.predicted_state_probs).map(([label, prob]) => (
                  <ProbBar key={label} label={label} value={prob} />
                ))}
              </CardContent>
            </Card>

            {/* Transition Matrix */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">转移概率矩阵</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr>
                        <th className="p-1 text-left text-muted-foreground">From \ To</th>
                        {result.state_labels.map((l) => (
                          <th key={l} className="p-1 text-center text-muted-foreground whitespace-nowrap">
                            {l.substring(0, 4)}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {result.transition_matrix.map((row, i) => (
                        <tr key={i}>
                          <td className="p-1 font-medium whitespace-nowrap">{result.state_labels[i]}</td>
                          {row.map((val, j) => (
                            <td
                              key={j}
                              className="p-1 text-center tabular-nums"
                              style={{
                                backgroundColor: `rgba(59, 130, 246, ${val * 0.5})`,
                              }}
                            >
                              {(val * 100).toFixed(0)}%
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

            {/* Computation Steps */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">计算过程 (点击展开详情)</CardTitle>
              </CardHeader>
              <CardContent className="space-y-0">
                {result.computation_steps.map((step) => (
                  <StepCard key={step.step} step={step} />
                ))}
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}
