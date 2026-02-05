"use client";

import { useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { newsAPI } from "@/lib/api-client";
import { Header } from "@/components/layout/Header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  ArrowLeft,
  ExternalLink,
  TrendingUp,
  TrendingDown,
  Minus,
  RefreshCw,
  Loader2,
} from "lucide-react";
import { useToast } from "@/components/ui/use-toast";

interface NewsArticle {
  id: string;
  source: string;
  title: string;
  content: string | null;
  url: string | null;
  author: string | null;
  symbols: string[];
  sentiment_score: number | null;
  sentiment_label: string | null;
  published_at: string | null;
}

export default function NewsPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const { toast } = useToast();
  const symbol = decodeURIComponent(params.symbol as string);
  const market = searchParams.get("market") || "us";
  const [fetching, setFetching] = useState(false);

  // Fetch news articles for this symbol
  const { data: newsData, refetch, isLoading } = useQuery({
    queryKey: ["news", symbol],
    queryFn: async () => {
      const res = await newsAPI.getNewsFeed({ symbol, page_size: 30 });
      return res.data;
    },
  });

  const articles = newsData?.articles as NewsArticle[] || [];

  const handleFetchNews = async () => {
    setFetching(true);
    try {
      await newsAPI.fetchNews({ symbol, max_articles: 20 });
      toast({
        title: "新闻采集已启动",
        description: "正在从多个数据源采集新闻，请稍后刷新查看...",
      });
      // Refetch after 10 seconds
      setTimeout(() => {
        refetch();
      }, 10000);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      toast({
        title: "采集失败",
        description: error?.response?.data?.detail || "请稍后重试",
        variant: "destructive",
      });
    } finally {
      setFetching(false);
    }
  };

  const getSentimentBadge = (label: string | null, score: number | null) => {
    if (!label) return null;

    const variants: Record<string, { color: string; icon: JSX.Element }> = {
      positive: { color: "bg-green-500/10 text-green-500", icon: <TrendingUp className="h-3 w-3" /> },
      negative: { color: "bg-red-500/10 text-red-500", icon: <TrendingDown className="h-3 w-3" /> },
      neutral: { color: "bg-gray-500/10 text-gray-500", icon: <Minus className="h-3 w-3" /> },
    };

    const variant = variants[label] || variants.neutral;

    return (
      <Badge variant="secondary" className={`${variant.color} flex items-center gap-1`}>
        {variant.icon}
        {label === "positive" && "看涨"}
        {label === "negative" && "看跌"}
        {label === "neutral" && "中性"}
        {score !== null && ` (${(score * 100).toFixed(0)})`}
      </Badge>
    );
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "未知时间";
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins}分钟前`;
    if (diffHours < 24) return `${diffHours}小时前`;
    if (diffDays < 7) return `${diffDays}天前`;
    return date.toLocaleDateString("zh-CN");
  };

  return (
    <div>
      <Header title="新闻资讯" />
      <div className="mx-auto max-w-lg space-y-4 p-4">
        {/* Back button */}
        <div className="flex items-center justify-between">
          <Link href={`/market/${encodeURIComponent(symbol)}?market=${market}`} className="inline-flex items-center gap-1 text-sm text-muted-foreground">
            <ArrowLeft className="h-4 w-4" /> 返回股票详情
          </Link>
          <Button
            onClick={handleFetchNews}
            disabled={fetching}
            size="sm"
            variant="outline"
          >
            {fetching ? (
              <>
                <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                采集中
              </>
            ) : (
              <>
                <RefreshCw className="mr-1 h-3 w-3" />
                获取新闻
              </>
            )}
          </Button>
        </div>

        {/* Symbol Info */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold">{symbol}</h2>
                <p className="text-xs text-muted-foreground">
                  {market === "us" && "美股"}
                  {market === "hk" && "港股"}
                  {market === "cn" && "A股"}
                  {market === "commodity" && "大宗商品"}
                </p>
              </div>
              <Badge variant="secondary">{articles.length} 条新闻</Badge>
            </div>
          </CardContent>
        </Card>

        {/* Loading State */}
        {isLoading && (
          <div className="flex h-[50vh] items-center justify-center">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        )}

        {/* Empty State */}
        {!isLoading && articles.length === 0 && (
          <Card>
            <CardContent className="flex flex-col items-center justify-center p-12">
              <p className="text-sm text-muted-foreground mb-4">暂无新闻数据</p>
              <Button onClick={handleFetchNews} disabled={fetching}>
                {fetching ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    采集中...
                  </>
                ) : (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4" />
                    立即获取新闻
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        )}

        {/* News List */}
        {!isLoading && articles.length > 0 && (
          <div className="space-y-3">
            {articles.map((article) => (
              <Card key={article.id} className="overflow-hidden">
                <CardContent className="p-4">
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="text-sm font-medium line-clamp-2 flex-1">
                        {article.title}
                      </h3>
                      {article.sentiment_label && getSentimentBadge(article.sentiment_label, article.sentiment_score)}
                    </div>

                    {article.content && (
                      <p className="text-xs text-muted-foreground line-clamp-2">
                        {article.content}
                      </p>
                    )}

                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{article.source}</span>
                        {article.author && <span>· {article.author}</span>}
                        <span>· {formatDate(article.published_at)}</span>
                      </div>
                      {article.url && (
                        <a
                          href={article.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-primary hover:underline"
                        >
                          阅读
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
