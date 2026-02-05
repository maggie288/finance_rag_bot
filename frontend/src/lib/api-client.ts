import axios, { AxiosInstance, InternalAxiosRequestConfig } from "axios";

function getApiBase(): string {
  const envUrl = process.env.NEXT_PUBLIC_API_URL;

  // 如果没有环境变量配置，使用默认值
  if (!envUrl) {
    return "http://localhost:8000";
  }

  // 如果是本机访问，使用 localhost
  if (typeof window !== "undefined") {
    const hostname = window.location.hostname;
    if (hostname === "localhost" || hostname === "127.0.0.1") {
      return "http://localhost:8000";
    }
    // 远程访问时，使用环境变量配置的地址
    return envUrl;
  }

  return envUrl;
}

const API_BASE = getApiBase();

const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

// Request interceptor: attach token
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Response interceptor: handle 401 & token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshToken = localStorage.getItem("refresh_token");
        if (refreshToken) {
          const res = await axios.post(`${API_BASE}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          });
          const { access_token, refresh_token } = res.data;
          localStorage.setItem("access_token", access_token);
          localStorage.setItem("refresh_token", refresh_token);
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return apiClient(originalRequest);
        }
      } catch {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;

// Auth API
export const authAPI = {
  register: (data: { email: string; password: string; display_name?: string }) =>
    apiClient.post("/auth/register", data),
  login: (data: { email: string; password: string }) =>
    apiClient.post("/auth/login", data),
  forgotPassword: (email: string) =>
    apiClient.post("/auth/forgot-password", { email }),
  resetPassword: (token: string, new_password: string) =>
    apiClient.post("/auth/reset-password", { token, new_password }),
};

// User API
export const userAPI = {
  getMe: () => apiClient.get("/users/me"),
  updateMe: (data: { display_name?: string; preferred_llm?: string; language?: string }) =>
    apiClient.patch("/users/me", data),
};

// Credits API
export const creditsAPI = {
  getBalance: () => apiClient.get("/credits/balance"),
  getHistory: (page = 1, pageSize = 20, type?: string) =>
    apiClient.get("/credits/history", { params: { page, page_size: pageSize, type } }),
  mockRecharge: (amount: number) =>
    apiClient.post("/credits/mock-recharge", { amount }),
};

// Market API
export const marketAPI = {
  getQuote: (symbol: string, market?: string) =>
    apiClient.get("/market/quote", { params: { symbol, market } }),
  batchQuote: (items: Array<{ symbol: string; market?: string }>) =>
    apiClient.post("/market/batch-quote", { items }),
  getKline: (symbol: string, market?: string, interval = "1day", outputsize = 100) =>
    apiClient.get("/market/kline", { params: { symbol, market, interval, outputsize } }),
  search: (query: string, market?: string) =>
    apiClient.get("/market/search", { params: { query, market } }),
  getFundamentals: (symbol: string, market?: string) =>
    apiClient.get("/market/fundamentals", { params: { symbol, market } }),
  refreshData: (market: string) =>
    apiClient.post("/market/refresh", null, { params: { market } }),
};

// AI API
export const aiAPI = {
  getModels: () => apiClient.get("/ai/models"),
  chat: (data: { query: string; symbol?: string; market?: string; model?: string; use_rag?: boolean }) =>
    apiClient.post("/ai/chat", data),
  chatStream: (data: { query: string; model?: string }) =>
    fetch(`${API_BASE}/api/v1/ai/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${typeof window !== "undefined" ? localStorage.getItem("access_token") : ""}`,
      },
      body: JSON.stringify(data),
    }),
};

// Prediction API
export const predictionAPI = {
  markov: (data: { symbol: string; market: string; prediction_type: string }) =>
    apiClient.post("/prediction/markov", data),
};

// Reports API
export const reportsAPI = {
  generate: (data: {
    report_type: string;
    symbol?: string;
    market?: string;
    query?: string;
    llm_model?: string;
  }) => apiClient.post("/reports/generate", data),
  list: (page = 1, pageSize = 20, reportType?: string) =>
    apiClient.get("/reports/list", { params: { page, page_size: pageSize, report_type: reportType } }),
  get: (id: string) => apiClient.get(`/reports/${id}`),
  listPredictions: (params?: { page?: number; page_size?: number; symbol?: string; prediction_type?: string }) =>
    apiClient.get("/reports/predictions/list", { params }),
  getPrediction: (id: string) => apiClient.get(`/reports/predictions/${id}`),
};

// News API
export const newsAPI = {
  getNewsFeed: (params?: { symbol?: string; source?: string; category?: string; page?: number; page_size?: number }) =>
    apiClient.get("/news/feed", { params }),
  fetchNews: (data: { symbol?: string; max_articles?: number }) =>
    apiClient.post("/news/fetch", null, { params: data }),
  getCategories: () => apiClient.get("/news/categories"),
};

// Watchlist API
export const watchlistAPI = {
  get: () => apiClient.get("/watchlist/"),
  add: (data: { symbol: string; market: string; name?: string }) =>
    apiClient.post("/watchlist/", data),
  remove: (id: string) => apiClient.delete(`/watchlist/${id}`),
  refreshNames: () => apiClient.post("/watchlist/refresh-names"),
};

// Trading API
export const tradingAPI = {
  getAgents: () => apiClient.get("/trading/agents"),
  // Create simulation (pending status, needs manual start)
  createSimulation: (data: {
    symbol: string;
    market: string;
    agent_name: string;
    config?: Record<string, unknown>;
  }) => apiClient.post("/trading/simulations", data),
  // Start a pending simulation
  startSimulation: (id: string) => apiClient.post(`/trading/simulations/${id}/start`),
  // Pause a running simulation
  pauseSimulation: (id: string) => apiClient.post(`/trading/simulations/${id}/pause`),
  // Resume a paused simulation
  resumeSimulation: (id: string) => apiClient.post(`/trading/simulations/${id}/resume`),
  // Stop a simulation permanently
  stopSimulation: (id: string) => apiClient.post(`/trading/simulations/${id}/stop`),
  // List simulations
  getSimulations: (params?: { symbol?: string; status?: string; page?: number; page_size?: number }) =>
    apiClient.get("/trading/simulations", { params }),
  getSimulation: (id: string) => apiClient.get(`/trading/simulations/${id}`),
  deleteSimulation: (id: string) => apiClient.delete(`/trading/simulations/${id}`),
  getSimulationTrades: (id: string) => apiClient.get(`/trading/simulations/${id}/trades`),
};

// ClawdBot API
export const clawdbotAPI = {
  getMarkets: (params?: { category?: string; limit?: number }) =>
    apiClient.get("/clawdbot/markets", { params }),
  getTrendingMarkets: (limit?: number) =>
    apiClient.get("/clawdbot/markets/trending", { params: { limit } }),
  getOpportunities: (params?: { status?: string; page?: number; page_size?: number }) =>
    apiClient.get("/clawdbot/opportunities", { params }),
  scanOpportunities: () => apiClient.post("/clawdbot/scan"),
  getTrades: (params?: { status?: string; page?: number; page_size?: number }) =>
    apiClient.get("/clawdbot/trades", { params }),
  addWallet: (data: { wallet_type: string; wallet_name: string; address: string }) =>
    apiClient.post("/clawdbot/wallets", data),
  getWallets: () => apiClient.get("/clawdbot/wallets"),
  getConfig: () => apiClient.get("/clawdbot/config"),
  updateConfig: (data: {
    is_enabled?: boolean;
    auto_trade?: boolean;
    min_opportunity_confidence?: number;
    max_position_size_btc?: number;
    max_daily_loss_btc?: number;
  }) => apiClient.post("/clawdbot/config", data),
};
