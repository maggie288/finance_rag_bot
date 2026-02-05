"use client";

import { useAuthStore } from "@/stores/auth-store";
import { Badge } from "@/components/ui/badge";
import { Coins } from "lucide-react";
import Link from "next/link";

interface HeaderProps {
  title?: string;
  showCredits?: boolean;
}

export function Header({ title = "Finance Bot", showCredits = true }: HeaderProps) {
  const user = useAuthStore((s) => s.user);

  return (
    <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 safe-area-top">
      <div className="mx-auto flex h-12 max-w-lg items-center justify-between px-4">
        <h1 className="text-base font-semibold">{title}</h1>
        {showCredits && user && (
          <Link href="/profile/credits" className="flex items-center gap-1">
            <Badge variant="secondary" className="flex items-center gap-1 text-xs">
              <Coins className="h-3 w-3" />
              {Number(user.credits_balance).toFixed(1)}
            </Badge>
          </Link>
        )}
      </div>
    </header>
  );
}
