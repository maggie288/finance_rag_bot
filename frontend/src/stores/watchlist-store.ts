"use client";

import { create } from "zustand";
import { WatchlistItem, MarketType } from "@/types";
import { watchlistAPI, marketAPI } from "@/lib/api-client";

const DEFAULT_STOCKS: Record<string, Array<{ symbol: string; market: string; name: string }>> = {
  us: [
    { symbol: "TSLA", market: "us", name: "Tesla" },
    { symbol: "AAPL", market: "us", name: "Apple" },
    { symbol: "NVDA", market: "us", name: "NVIDIA" },
    { symbol: "MSFT", market: "us", name: "Microsoft" },
  ],
  hk: [
    { symbol: "0700.HK", market: "hk", name: "腾讯控股" },
    { symbol: "9988.HK", market: "hk", name: "阿里巴巴" },
  ],
  cn: [
    { symbol: "600519.SH", market: "cn", name: "贵州茅台" },
    { symbol: "000858.SZ", market: "cn", name: "五粮液" },
  ],
  commodity: [
    { symbol: "XAU/USD", market: "commodity", name: "黄金" },
    { symbol: "XAG/USD", market: "commodity", name: "白银" },
  ],
};

interface WatchlistState {
  items: WatchlistItem[];
  loaded: boolean;
  loading: boolean;
  refreshing: boolean;
  fetchWatchlist: () => Promise<void>;
  addStock: (symbol: string, market: string, name?: string) => Promise<void>;
  removeStock: (id: string) => Promise<void>;
  initDefaults: () => Promise<void>;
  getByMarket: (market: MarketType) => WatchlistItem[];
  refreshMarketData: (market: MarketType) => Promise<void>;
  refreshNames: () => Promise<void>;
}

export const useWatchlistStore = create<WatchlistState>((set, get) => ({
  items: [],
  loaded: false,
  loading: false,
  refreshing: false,

  fetchWatchlist: async () => {
    if (get().loading) return;
    set({ loading: true });
    try {
      const res = await watchlistAPI.get();
      set({ items: res.data.items, loaded: true });
    } catch {
      set({ loaded: true });
    } finally {
      set({ loading: false });
    }
  },

  addStock: async (symbol, market, name) => {
    try {
      await watchlistAPI.add({ symbol, market, name });
      await get().fetchWatchlist();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      throw new Error(msg || "添加失败");
    }
  },

  removeStock: async (id) => {
    try {
      await watchlistAPI.remove(id);
      set((state) => ({ items: state.items.filter((i) => i.id !== id) }));
    } catch {
      // ignore
    }
  },

  initDefaults: async () => {
    const all = Object.values(DEFAULT_STOCKS).flat();
    for (const stock of all) {
      try {
        await watchlistAPI.add({ symbol: stock.symbol, market: stock.market, name: stock.name });
      } catch {
        // skip duplicates
      }
    }
    await get().fetchWatchlist();
  },

  getByMarket: (market) => {
    return get().items.filter((i) => i.market === market);
  },

  refreshMarketData: async (market) => {
    if (get().refreshing) return;
    set({ refreshing: true });
    try {
      await marketAPI.refreshData(market);
    } catch {
    } finally {
      set({ refreshing: false });
    }
  },

  refreshNames: async () => {
    if (get().refreshing) return;
    set({ refreshing: true });
    try {
      console.log("[Watchlist] 开始刷新股票名称...");
      const res = await watchlistAPI.refreshNames();
      console.log("[Watchlist] 刷新API返回:", res.data);
      await get().fetchWatchlist();
      console.log("[Watchlist] 刷新后的数据:", get().items);
    } catch (err) {
      console.error("[Watchlist] 刷新失败:", err);
    } finally {
      set({ refreshing: false });
    }
  },
}));

export { DEFAULT_STOCKS };
