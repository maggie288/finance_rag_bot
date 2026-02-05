"use client";

import { useEffect, useRef, useState } from "react";
import { createChart, IChartApi, CandlestickSeries, HistogramSeries } from "lightweight-charts";
import { KlinePoint } from "@/types";

interface CandlestickChartProps {
  data: KlinePoint[];
  height?: number;
}

export function CandlestickChart({ data, height = 300 }: CandlestickChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!containerRef.current || data.length === 0) {
      setError(null);
      return;
    }

    setError(null);

    try {
      // Clean up previous chart
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }

      const chart = createChart(containerRef.current, {
        width: containerRef.current.clientWidth,
        height,
        layout: {
          background: { color: "transparent" },
          textColor: "#9ca3af",
          fontSize: 11,
        },
        grid: {
          vertLines: { color: "rgba(255,255,255,0.04)" },
          horzLines: { color: "rgba(255,255,255,0.04)" },
        },
        crosshair: {
          mode: 0,
        },
        rightPriceScale: {
          borderColor: "rgba(255,255,255,0.1)",
        },
        timeScale: {
          borderColor: "rgba(255,255,255,0.1)",
          timeVisible: true,
        },
      });

      chartRef.current = chart;

      // Detect if data is intraday (has time portion in datetime)
      const isIntraday = data.some((d) => {
        if (!d.datetime) return false;
        const timeMatch = d.datetime.match(/[T\s](\d{2}):(\d{2}):(\d{2})/);
        if (!timeMatch) return false;
        // Check if time is not midnight (00:00:00)
        return timeMatch[1] !== "00" || timeMatch[2] !== "00" || timeMatch[3] !== "00";
      });

      const toTime = (datetime: string) => {
        if (isIntraday) {
          return Math.floor(new Date(datetime.replace(" ", "T")).getTime() / 1000) as never;
        }
        // Extract date part (yyyy-mm-dd) from either ISO format or space-separated format
        return datetime.split(/[T\s]/)[0] as never;
      };

      // Candlestick series
      const candleSeries = chart.addSeries(CandlestickSeries, {
        upColor: "#22c55e",
        downColor: "#ef4444",
        borderUpColor: "#22c55e",
        borderDownColor: "#ef4444",
        wickUpColor: "#22c55e",
        wickDownColor: "#ef4444",
      });

      const candleData = data
        .filter((point) => point.datetime)
        .map((point) => ({
          time: toTime(point.datetime),
          open: point.open,
          high: point.high,
          low: point.low,
          close: point.close,
        }))
        .sort((a, b) => {
          // Handle both numeric timestamps and string dates
          if (typeof a.time === 'number' && typeof b.time === 'number') {
            return a.time - b.time;
          }
          return String(a.time).localeCompare(String(b.time));
        });

      candleSeries.setData(candleData as never);

      // Volume series
      if (data.some((d) => d.volume != null)) {
        const volumeSeries = chart.addSeries(HistogramSeries, {
          priceFormat: { type: "volume" },
          priceScaleId: "volume",
        });

        chart.priceScale("volume").applyOptions({
          scaleMargins: { top: 0.8, bottom: 0 },
        });

        const volumeData = data
          .filter((point) => point.datetime)
          .map((point) => ({
            time: toTime(point.datetime),
            value: point.volume || 0,
            color: point.close >= point.open ? "rgba(34,197,94,0.3)" : "rgba(239,68,68,0.3)",
          }))
          .sort((a, b) => {
            // Handle both numeric timestamps and string dates
            if (typeof a.time === 'number' && typeof b.time === 'number') {
              return a.time - b.time;
            }
            return String(a.time).localeCompare(String(b.time));
          });

        volumeSeries.setData(volumeData as never);
      }

      chart.timeScale().fitContent();

      // Resize handler
      const handleResize = () => {
        if (containerRef.current) {
          chart.applyOptions({ width: containerRef.current.clientWidth });
        }
      };
      window.addEventListener("resize", handleResize);

      return () => {
        window.removeEventListener("resize", handleResize);
        chart.remove();
        chartRef.current = null;
      };
    } catch (err) {
      console.error("Chart creation error:", err);
      setError("图表加载失败");
    }
  }, [data, height]);

  if (error) {
    return (
      <div className="flex h-[300px] items-center justify-center text-sm text-muted-foreground">
        {error}
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="flex h-[300px] items-center justify-center text-sm text-muted-foreground">
        暂无数据
      </div>
    );
  }

  return <div ref={containerRef} className="w-full" />;
}
