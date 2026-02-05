"use client";

import { useState } from "react";
import Link from "next/link";
import { useAuthStore } from "@/stores/auth-store";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { ArrowLeft, Save, Loader2 } from "lucide-react";
import { LLMModel } from "@/types";

export default function SettingsPage() {
  const { user, updateUser } = useAuthStore();
  const [displayName, setDisplayName] = useState(user?.display_name || "");
  const [preferredLlm, setPreferredLlm] = useState<LLMModel>(
    (user?.preferred_llm as LLMModel) || "deepseek"
  );
  const [saving, setSaving] = useState(false);
  const { toast } = useToast();

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateUser({
        display_name: displayName,
        preferred_llm: preferredLlm,
      });
      toast({ title: "保存成功" });
    } catch {
      toast({ title: "保存失败", variant: "destructive" });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <Header title="设置" showCredits={false} />
      <div className="mx-auto max-w-lg space-y-4 p-4">
        <Link href="/profile" className="inline-flex items-center gap-1 text-sm text-muted-foreground">
          <ArrowLeft className="h-4 w-4" /> 返回
        </Link>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">个人信息</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label className="text-xs">邮箱</Label>
              <Input value={user?.email || ""} disabled className="text-sm" />
            </div>
            <div className="space-y-2">
              <Label className="text-xs">昵称</Label>
              <Input
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="text-sm"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">AI 模型设置</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label className="text-xs">默认大语言模型</Label>
              <Select value={preferredLlm} onValueChange={(v) => setPreferredLlm(v as LLMModel)}>
                <SelectTrigger className="text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="deepseek">DeepSeek (经济实惠)</SelectItem>
                  <SelectItem value="minimax">MiniMax (中文优化)</SelectItem>
                  <SelectItem value="claude">Claude (推理能力强)</SelectItem>
                  <SelectItem value="openai">GPT-4o (综合能力强)</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                不同模型消耗不同积分: DeepSeek/MiniMax 0.5积分/次, Claude/GPT-4o 2积分/次
              </p>
            </div>
          </CardContent>
        </Card>

        <Button className="w-full" onClick={handleSave} disabled={saving}>
          {saving ? (
            <><Loader2 className="mr-2 h-4 w-4 animate-spin" />保存中...</>
          ) : (
            <><Save className="mr-2 h-4 w-4" />保存设置</>
          )}
        </Button>
      </div>
    </div>
  );
}
