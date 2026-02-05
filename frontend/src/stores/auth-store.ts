"use client";

import { create } from "zustand";
import { User } from "@/types";
import { authAPI, userAPI } from "@/lib/api-client";

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName?: string) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  updateUser: (data: { display_name?: string; preferred_llm?: string }) => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,

  login: async (email, password) => {
    const res = await authAPI.login({ email, password });
    localStorage.setItem("access_token", res.data.access_token);
    localStorage.setItem("refresh_token", res.data.refresh_token);
    const userRes = await userAPI.getMe();
    set({ user: userRes.data, isAuthenticated: true, isLoading: false });
  },

  register: async (email, password, displayName) => {
    const res = await authAPI.register({ email, password, display_name: displayName });
    localStorage.setItem("access_token", res.data.access_token);
    localStorage.setItem("refresh_token", res.data.refresh_token);
    const userRes = await userAPI.getMe();
    set({ user: userRes.data, isAuthenticated: true, isLoading: false });
  },

  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    set({ user: null, isAuthenticated: false });
  },

  fetchUser: async () => {
    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        set({ isLoading: false });
        return;
      }
      const res = await userAPI.getMe();
      set({ user: res.data, isAuthenticated: true, isLoading: false });
    } catch {
      set({ isLoading: false, isAuthenticated: false, user: null });
    }
  },

  updateUser: async (data) => {
    const res = await userAPI.updateMe(data);
    set({ user: res.data });
  },
}));
