"use client";

import { useState, useRef, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { aiAPI } from "@/lib/api-client";
import { Header } from "@/components/layout/Header";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Send, Bot, User, Loader2, Sparkles } from "lucide-react";
import { LLMModel } from "@/types";

interface Message {
  role: "user" | "assistant";
  content: string;
  model?: string;
  tokens?: number;
  sources?: Array<{ text: string; metadata: Record<string, string> }>;
}

const MODEL_LABELS: Record<string, string> = {
  deepseek: "DeepSeek",
  minimax: "MiniMax",
  claude: "Claude",
  openai: "GPT-4o",
};

const QUICK_PROMPTS = [
  "分析TSLA最新财报",
  "美联储最新货币政策",
  "比较NVDA和AMD基本面",
  "A股市场今日走势分析",
];

export default function AIChatPage() {
  const searchParams = useSearchParams();
  const symbolParam = searchParams.get("symbol");
  const marketParam = searchParams.get("market");

  const user = useAuthStore((s) => s.user);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState(symbolParam ? `分析 ${symbolParam} 的最新情况` : "");
  const [model, setModel] = useState<LLMModel>((user?.preferred_llm as LLMModel) || "deepseek");
  const [useRag, setUseRag] = useState(true);
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = { role: "user", content: input.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await aiAPI.chat({
        query: userMessage.content,
        symbol: symbolParam || undefined,
        market: marketParam || undefined,
        model,
        use_rag: useRag,
      });

      const assistantMessage: Message = {
        role: "assistant",
        content: res.data.answer,
        model: res.data.model_used,
        tokens: res.data.tokens_used,
        sources: res.data.sources,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${detail || "请求失败，请稍后重试"}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col">
      <Header title="AI 智能分析" />

      {/* Model Selector */}
      <div className="mx-auto flex w-full max-w-lg items-center gap-2 border-b px-4 py-2">
        <Select value={model} onValueChange={(v) => setModel(v as LLMModel)}>
          <SelectTrigger className="h-8 w-32 text-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {Object.entries(MODEL_LABELS).map(([key, label]) => (
              <SelectItem key={key} value={key} className="text-xs">
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button
          variant={useRag ? "default" : "outline"}
          size="sm"
          className="h-8 text-xs"
          onClick={() => setUseRag(!useRag)}
        >
          <Sparkles className="mr-1 h-3 w-3" />
          RAG {useRag ? "开" : "关"}
        </Button>
        {symbolParam && (
          <Badge variant="secondary" className="text-xs">
            {symbolParam}
          </Badge>
        )}
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-lg space-y-4 p-4">
          {messages.length === 0 && (
            <div className="space-y-4 pt-8">
              <div className="text-center">
                <Bot className="mx-auto h-12 w-12 text-muted-foreground/50 mb-3" />
                <p className="text-sm text-muted-foreground">
                  我是你的金融分析AI助手，可以帮你分析股票、解读财报、预测趋势。
                </p>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {QUICK_PROMPTS.map((prompt) => (
                  <Button
                    key={prompt}
                    variant="outline"
                    size="sm"
                    className="h-auto whitespace-normal text-left text-xs p-2"
                    onClick={() => setInput(prompt)}
                  >
                    {prompt}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}>
              {msg.role === "assistant" && (
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10">
                  <Bot className="h-4 w-4 text-primary" />
                </div>
              )}
              <div
                className={`max-w-[85%] rounded-lg p-3 text-sm ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted"
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.content}</div>
                {msg.role === "assistant" && msg.model && (
                  <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
                    <Badge variant="outline" className="text-[10px] h-4">
                      {MODEL_LABELS[msg.model] || msg.model}
                    </Badge>
                    {msg.tokens && <span>{msg.tokens} tokens</span>}
                  </div>
                )}
              </div>
              {msg.role === "user" && (
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary">
                  <User className="h-4 w-4 text-primary-foreground" />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex gap-3">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10">
                <Bot className="h-4 w-4 text-primary" />
              </div>
              <div className="rounded-lg bg-muted p-3">
                <Loader2 className="h-4 w-4 animate-spin" />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Input */}
      <div className="border-t bg-background">
        <div className="mx-auto flex max-w-lg items-end gap-2 p-4">
          <Textarea
            placeholder="输入你的问题..."
            className="min-h-[40px] max-h-[120px] resize-none text-sm"
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
          />
          <Button size="icon" onClick={handleSend} disabled={loading || !input.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
