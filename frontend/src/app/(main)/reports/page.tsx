"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { reportsAPI } from "@/lib/api-client";
import { Header } from "@/components/layout/Header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, ArrowLeft, Brain } from "lucide-react";

const TYPE_LABELS: Record<string, string> = {
  fundamental: "基本面分析",
  sentiment: "舆情分析",
  prediction: "价格预测",
  custom: "自定义研究",
  macro: "宏观分析",
};

export default function ReportsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["reports"],
    queryFn: async () => {
      const res = await reportsAPI.list(1, 50);
      return res.data;
    },
  });

  const reports = data?.reports || [];

  return (
    <div>
      <Header title="我的报告" />
      <div className="mx-auto max-w-lg space-y-3 p-4">
        <Link href="/profile" className="inline-flex items-center gap-1 text-sm text-muted-foreground">
          <ArrowLeft className="h-4 w-4" /> 返回
        </Link>

        {isLoading ? (
          <div className="flex h-40 items-center justify-center">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        ) : reports.length > 0 ? (
          reports.map((report: Record<string, unknown>) => (
            <Card key={String(report.id)} className="cursor-pointer transition-colors hover:bg-accent/50">
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                    <Brain className="h-4 w-4 text-primary" />
                  </div>
                  <div className="flex-1 space-y-1">
                    <p className="text-sm font-medium line-clamp-1">
                      {String(report.title || "Untitled Report")}
                    </p>
                    <p className="text-xs text-muted-foreground line-clamp-2">
                      {String(report.summary || "")}
                    </p>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="text-[10px]">
                        {TYPE_LABELS[String(report.report_type)] || String(report.report_type)}
                      </Badge>
                      {Boolean(report.symbol) && (
                        <Badge variant="outline" className="text-[10px]">
                          {String(report.symbol)}
                        </Badge>
                      )}
                      <span className="text-[10px] text-muted-foreground ml-auto">
                        {new Date(String(report.created_at)).toLocaleDateString("zh-CN")}
                      </span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        ) : (
          <div className="flex h-40 flex-col items-center justify-center text-sm text-muted-foreground">
            <FileText className="h-8 w-8 mb-2 opacity-50" />
            <p>暂无报告</p>
            <p className="text-xs mt-1">使用AI分析功能后，报告将出现在这里</p>
          </div>
        )}
      </div>
    </div>
  );
}
