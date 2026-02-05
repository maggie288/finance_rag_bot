"use client";

import { create } from "zustand";
import { StockQuote, MarketType } from "@/types";

interface MarketState {
  activeMarket: MarketType;
  setActiveMarket: (market: MarketType) => void;
  selectedSymbol: string | null;
  setSelectedSymbol: (symbol: string | null) => void;
  realtimePrices: Record<string, StockQuote>;
  updatePrice: (symbol: string, quote: StockQuote) => void;
}

export const useMarketStore = create<MarketState>((set) => ({
  activeMarket: "us",
  setActiveMarket: (market) => set({ activeMarket: market }),
  selectedSymbol: null,
  setSelectedSymbol: (symbol) => set({ selectedSymbol: symbol }),
  realtimePrices: {},
  updatePrice: (symbol, quote) =>
    set((state) => ({
      realtimePrices: { ...state.realtimePrices, [symbol]: quote },
    })),
}));
