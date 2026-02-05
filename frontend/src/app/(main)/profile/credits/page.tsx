"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { creditsAPI } from "@/lib/api-client";
import { useAuthStore } from "@/stores/auth-store";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { ArrowLeft, Coins, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { CreditTransaction } from "@/types";

const RECHARGE_AMOUNTS = [10, 50, 100, 500];

export default function CreditsPage() {
  const user = useAuthStore((s) => s.user);
  const fetchUser = useAuthStore((s) => s.fetchUser);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: historyData } = useQuery({
    queryKey: ["creditHistory"],
    queryFn: async () => {
      const res = await creditsAPI.getHistory(1, 50);
      return res.data;
    },
  });

  const rechargeMutation = useMutation({
    mutationFn: async (amount: number) => {
      const res = await creditsAPI.mockRecharge(amount);
      return res.data;
    },
    onSuccess: (_, amount) => {
      toast({ title: "充值成功", description: `已充值 ${amount} 积分` });
      fetchUser();
      queryClient.invalidateQueries({ queryKey: ["creditHistory"] });
    },
    onError: () => {
      toast({ title: "充值失败", variant: "destructive" });
    },
  });

  const transactions: CreditTransaction[] = historyData?.transactions || [];

  return (
    <div>
      <Header title="积分管理" showCredits={false} />
      <div className="mx-auto max-w-lg space-y-4 p-4">
        <Link href="/profile" className="inline-flex items-center gap-1 text-sm text-muted-foreground">
          <ArrowLeft className="h-4 w-4" /> 返回
        </Link>

        {/* Balance */}
        <Card className="bg-gradient-to-br from-primary/10 to-primary/5">
          <CardContent className="p-6 text-center">
            <p className="text-sm text-muted-foreground">当前积分</p>
            <p className="mt-1 text-3xl font-bold tabular-nums">
              {Number(user?.credits_balance || 0).toFixed(1)}
            </p>
          </CardContent>
        </Card>

        {/* Recharge */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">充值积分 (模拟)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-2">
              {RECHARGE_AMOUNTS.map((amount) => (
                <Button
                  key={amount}
                  variant="outline"
                  className="h-auto flex-col py-3"
                  onClick={() => rechargeMutation.mutate(amount)}
                  disabled={rechargeMutation.isPending}
                >
                  <Coins className="h-4 w-4 text-yellow-500 mb-1" />
                  <span className="text-sm font-medium">{amount}</span>
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* History */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">交易记录</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {transactions.length === 0 ? (
              <div className="p-6 text-center text-sm text-muted-foreground">
                暂无交易记录
              </div>
            ) : (
              <div className="divide-y">
                {transactions.map((tx) => (
                  <div key={tx.id} className="flex items-center justify-between p-3">
                    <div className="flex items-center gap-3">
                      <div className={`flex h-8 w-8 items-center justify-center rounded-full ${
                        tx.type === "recharge" ? "bg-green-500/10" : "bg-red-500/10"
                      }`}>
                        {tx.type === "recharge" ? (
                          <ArrowDownRight className="h-4 w-4 text-green-500" />
                        ) : (
                          <ArrowUpRight className="h-4 w-4 text-red-500" />
                        )}
                      </div>
                      <div>
                        <p className="text-sm">{tx.description || tx.type}</p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(tx.created_at).toLocaleString("zh-CN")}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`text-sm font-medium tabular-nums ${
                        Number(tx.amount) > 0 ? "text-green-500" : "text-red-500"
                      }`}>
                        {Number(tx.amount) > 0 ? "+" : ""}{Number(tx.amount).toFixed(1)}
                      </p>
                      <p className="text-xs text-muted-foreground tabular-nums">
                        余: {Number(tx.balance_after).toFixed(1)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
