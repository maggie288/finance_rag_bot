"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { newsAPI } from "@/lib/api-client";
import { Header } from "@/components/layout/Header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Globe, Twitter, Youtube, FileText, TrendingUp, TrendingDown, Minus, RefreshCw } from "lucide-react";
import { NewsArticle } from "@/types";

const SOURCE_ICONS: Record<string, React.ReactNode> = {
  twitter: <Twitter className="h-3 w-3" />,
  youtube: <Youtube className="h-3 w-3" />,
  report: <FileText className="h-3 w-3" />,
  fed: <Globe className="h-3 w-3" />,
};

// 分类Tab配置
const CATEGORY_TABS = [
  { key: null, name: "全部" },
  { key: "a_stock", name: "A股" },
  { key: "hk_stock", name: "港股" },
  { key: "us_stock", name: "美股" },
  { key: "commodity", name: "大宗商品" },
  { key: "crypto", name: "加密货币" },
  { key: "policy", name: "国家政策" },
];

function SentimentIcon({ label }: { label: string | null }) {
  if (label === "bullish") return <TrendingUp className="h-3 w-3 text-green-500" />;
  if (label === "bearish") return <TrendingDown className="h-3 w-3 text-red-500" />;
  return <Minus className="h-3 w-3 text-muted-foreground" />;
}

function NewsCard({ article }: { article: NewsArticle }) {
  return (
    <Card className="cursor-pointer transition-colors hover:bg-accent/50">
      <CardContent className="p-3">
        <div className="flex items-start gap-3">
          <div className="flex-1 space-y-1">
            <p className="text-sm font-medium leading-tight line-clamp-2">
              {article.title || "Untitled"}
            </p>
            {article.content && (
              <p className="text-xs text-muted-foreground line-clamp-2">
                {article.content}
              </p>
            )}
            <div className="flex items-center gap-2 pt-1">
              <Badge variant="outline" className="h-5 text-[10px] flex items-center gap-1">
                {SOURCE_ICONS[article.source] || <Globe className="h-3 w-3" />}
                {article.source}
              </Badge>
              {article.sentiment_label && (
                <Badge
                  variant="secondary"
                  className={`h-5 text-[10px] flex items-center gap-1 ${
                    article.sentiment_label === "bullish"
                      ? "bg-green-500/10 text-green-500"
                      : article.sentiment_label === "bearish"
                      ? "bg-red-500/10 text-red-500"
                      : ""
                  }`}
                >
                  <SentimentIcon label={article.sentiment_label} />
                  {article.sentiment_label === "bullish" ? "看多" : article.sentiment_label === "bearish" ? "看空" : "中性"}
                </Badge>
              )}
              {article.symbols?.length > 0 && (
                <span className="text-[10px] text-muted-foreground">
                  {article.symbols.join(", ")}
                </span>
              )}
              {article.published_at && (
                <span className="text-[10px] text-muted-foreground ml-auto">
                  {new Date(article.published_at).toLocaleDateString("zh-CN")}
                </span>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function NewsPage() {
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["news", activeCategory],
    queryFn: async () => {
      const res = await newsAPI.getNewsFeed({
        page_size: 30,
        category: activeCategory || undefined,
      });
      return res.data;
    },
  });

  const fetchNewsMutation = useMutation({
    mutationFn: async () => {
      const res = await newsAPI.fetchNews({ max_articles: 30 });
      return res.data;
    },
    onSuccess: () => {
      // 延迟刷新，等待后台任务处理
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ["news"] });
      }, 2000);
    },
  });

  const articles: NewsArticle[] = data?.articles || [];

  const handleRefresh = () => {
    fetchNewsMutation.mutate();
  };

  return (
    <div>
      <Header title="资讯舆情" />
      <div className="mx-auto max-w-lg p-4 space-y-3">
        {/* 分类Tab */}
        <div className="flex gap-1 overflow-x-auto pb-2 scrollbar-hide">
          {CATEGORY_TABS.map((tab) => (
            <Button
              key={tab.key ?? "all"}
              variant={activeCategory === tab.key ? "default" : "ghost"}
              size="sm"
              className="shrink-0 text-xs h-7 px-2.5"
              onClick={() => setActiveCategory(tab.key)}
            >
              {tab.name}
            </Button>
          ))}
        </div>

        {/* 刷新按钮 */}
        <div className="flex justify-end">
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-xs gap-1"
            onClick={handleRefresh}
            disabled={fetchNewsMutation.isPending || isFetching}
          >
            <RefreshCw className={`h-3 w-3 ${(fetchNewsMutation.isPending || isFetching) ? "animate-spin" : ""}`} />
            {fetchNewsMutation.isPending ? "采集中..." : "获取最新资讯"}
          </Button>
        </div>

        {/* 新闻列表 */}
        {isLoading ? (
          <div className="flex h-40 items-center justify-center">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        ) : articles.length > 0 ? (
          articles.map((article) => (
            <NewsCard key={article.id} article={article} />
          ))
        ) : (
          <div className="flex h-40 flex-col items-center justify-center text-sm text-muted-foreground">
            <Globe className="h-8 w-8 mb-2 opacity-50" />
            <p>暂无资讯数据</p>
            <p className="text-xs mt-1">点击「获取最新资讯」按钮采集新闻</p>
          </div>
        )}
      </div>
    </div>
  );
}
