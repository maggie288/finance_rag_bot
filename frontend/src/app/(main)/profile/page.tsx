"use client";

import { useAuthStore } from "@/stores/auth-store";
import { useRouter } from "next/navigation";
import { Header } from "@/components/layout/Header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import Link from "next/link";
import {
  Coins,
  Settings,
  FileText,
  LogOut,
  ChevronRight,
  Brain,
  ListChecks,
  Bot,
  TrendingUp,
  Zap,
} from "lucide-react";

export default function ProfilePage() {
  const { user, logout } = useAuthStore();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const MODEL_LABELS: Record<string, string> = {
    deepseek: "DeepSeek",
    minimax: "MiniMax",
    claude: "Claude",
    openai: "GPT-4o",
  };

  return (
    <div>
      <Header title="个人中心" showCredits={false} />
      <div className="mx-auto max-w-lg space-y-4 p-4">
        {/* User Info */}
        <Card>
          <CardContent className="flex items-center gap-4 p-4">
            <Avatar className="h-14 w-14">
              <AvatarFallback className="bg-primary/10 text-primary text-lg">
                {user?.display_name?.[0] || user?.email?.[0]?.toUpperCase() || "U"}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1">
              <p className="font-medium">{user?.display_name || "User"}</p>
              <p className="text-xs text-muted-foreground">{user?.email}</p>
              <div className="mt-1 flex items-center gap-2">
                <Badge variant="secondary" className="text-xs">
                  <Coins className="mr-1 h-3 w-3" />
                  {Number(user?.credits_balance || 0).toFixed(1)} 积分
                </Badge>
                <Badge variant="outline" className="text-xs">
                  <Brain className="mr-1 h-3 w-3" />
                  {MODEL_LABELS[user?.preferred_llm || "deepseek"]}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Menu Items */}
        <Card>
          <CardContent className="p-0">
            <Link href="/profile/watchlist" className="flex items-center justify-between p-4 transition-colors hover:bg-accent/50">
              <div className="flex items-center gap-3">
                <ListChecks className="h-5 w-5 text-orange-500" />
                <div>
                  <span className="text-sm">自选股管理</span>
                  <p className="text-[10px] text-muted-foreground">管理行情页和仪表盘展示的股票</p>
                </div>
              </div>
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            </Link>
            <Separator />
            <Link href="/profile/trading" className="flex items-center justify-between p-4 transition-colors hover:bg-accent/50">
              <div className="flex items-center gap-3">
                <Bot className="h-5 w-5 text-purple-500" />
                <div>
                  <span className="text-sm">AI 交易代理</span>
                  <p className="text-[10px] text-muted-foreground">查看和管理AI自动交易代理执行状态</p>
                </div>
              </div>
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            </Link>
            <Separator />
            <Link href="/profile/clawdbot" className="flex items-center justify-between p-4 transition-colors hover:bg-accent/50">
              <div className="flex items-center gap-3">
                <Zap className="h-5 w-5 text-orange-500" />
                <div>
                  <span className="text-sm">ClawdBot 自动交易</span>
                  <p className="text-[10px] text-muted-foreground">Polymarket 预测市场自动交易</p>
                </div>
              </div>
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            </Link>
            <Separator />
            <Link href="/profile/prediction" className="flex items-center justify-between p-4 transition-colors hover:bg-accent/50">
              <div className="flex items-center gap-3">
                <TrendingUp className="h-5 w-5 text-green-500" />
                <div>
                  <span className="text-sm">价格预测报告</span>
                  <p className="text-[10px] text-muted-foreground">查看历史价格预测报告</p>
                </div>
              </div>
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            </Link>
            <Separator />
            <Link href="/profile/credits" className="flex items-center justify-between p-4 transition-colors hover:bg-accent/50">
              <div className="flex items-center gap-3">
                <Coins className="h-5 w-5 text-yellow-500" />
                <span className="text-sm">积分管理</span>
              </div>
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            </Link>
            <Separator />
            <Link href="/reports" className="flex items-center justify-between p-4 transition-colors hover:bg-accent/50">
              <div className="flex items-center gap-3">
                <FileText className="h-5 w-5 text-blue-500" />
                <span className="text-sm">我的报告</span>
              </div>
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            </Link>
            <Separator />
            <Link href="/profile/settings" className="flex items-center justify-between p-4 transition-colors hover:bg-accent/50">
              <div className="flex items-center gap-3">
                <Settings className="h-5 w-5 text-muted-foreground" />
                <span className="text-sm">设置</span>
              </div>
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            </Link>
          </CardContent>
        </Card>

        <Button variant="outline" className="w-full text-destructive" onClick={handleLogout}>
          <LogOut className="mr-2 h-4 w-4" />
          退出登录
        </Button>
      </div>
    </div>
  );
}
