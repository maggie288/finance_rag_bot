"use client";

import { useState } from "react";
import Link from "next/link";
import { authAPI } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { ArrowLeft } from "lucide-react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await authAPI.forgotPassword(email);
      setSent(true);
      toast({ title: "邮件已发送", description: "请检查您的邮箱" });
    } catch {
      toast({ title: "发送失败", description: "请稍后重试", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <Link href="/login" className="mb-2 flex items-center gap-1 text-sm text-muted-foreground">
            <ArrowLeft className="h-4 w-4" /> 返回登录
          </Link>
          <CardTitle className="text-xl">忘记密码</CardTitle>
          <CardDescription>输入注册邮箱，我们将发送重置链接</CardDescription>
        </CardHeader>
        <CardContent>
          {sent ? (
            <div className="text-center">
              <p className="text-sm text-muted-foreground">
                如果该邮箱已注册，我们已发送重置密码的链接到您的邮箱。
              </p>
              <Button variant="outline" className="mt-4" onClick={() => setSent(false)}>
                重新发送
              </Button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">邮箱</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="your@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "发送中..." : "发送重置链接"}
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
