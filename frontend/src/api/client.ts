/**
 * API Client — Axios instance with auth interceptors
 */
import axios, { AxiosError } from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export const api = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ── Request interceptor: attach JWT ─────────────────────
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Response interceptor: handle 401, refresh token ─────
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as (typeof error.config & { _retry?: boolean });

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        // No refresh token — force logout
        localStorage.clear();
        window.location.href = '/login';
        return Promise.reject(error);
      }

      try {
        const response = await axios.post(`${BASE_URL}/api/v1/auth/refresh`, {
          refresh_token: refreshToken,
        });
        const { access_token } = response.data;
        localStorage.setItem('access_token', access_token);
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch {
        localStorage.clear();
        window.location.href = '/login';
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  }
);

// ── Auth API ─────────────────────────────────────────────
export const authApi = {
  login: async (email: string, password: string) => {
    const form = new URLSearchParams();
    form.append('username', email);
    form.append('password', password);
    const response = await api.post('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return response.data;
  },
  signup: async (data: object) => {
    const response = await api.post('/auth/signup', data);
    return response.data;
  },
  logout: async () => {
    await api.post('/auth/logout');
    localStorage.clear();
  },
  me: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
  forgotPassword: async (email: string) => {
    const response = await api.post('/auth/forgot-password', { email });
    return response.data;
  },
};

// ── Sessions API ─────────────────────────────────────────
export const sessionsApi = {
  getActive: async () => {
    const response = await api.get('/sessions/active');
    return response.data;
  },
  start: async (data?: object) => {
    const response = await api.post('/sessions/start', data || {});
    return response.data;
  },
  end: async () => {
    const response = await api.post('/sessions/end');
    return response.data;
  },
  list: async (page = 1, pageSize = 20) => {
    const response = await api.get('/sessions/', { params: { page, page_size: pageSize } });
    return response.data;
  },
};

// ── Analytics API ────────────────────────────────────────
export const analyticsApi = {
  getSummary: async () => {
    const response = await api.get('/analytics/summary');
    return response.data;
  },
  getDaily: async (date?: string) => {
    const response = await api.get('/analytics/daily', { params: date ? { target_date: date } : {} });
    return response.data;
  },
  getWeekly: async () => {
    const response = await api.get('/analytics/weekly');
    return response.data;
  },
  getHeatmap: async (days = 30) => {
    const response = await api.get('/analytics/heatmap', { params: { days } });
    return response.data;
  },
};

// ── Predictions API ──────────────────────────────────────
export const predictionsApi = {
  getLatest: async () => {
    const response = await api.get('/predictions/latest');
    return response.data;
  },
  getHistory: async (page = 1, pageSize = 50, sessionId?: string) => {
    const response = await api.get('/predictions/history', {
      params: { page, page_size: pageSize, ...(sessionId ? { session_id: sessionId } : {}) },
    });
    return response.data;
  },
};

// ── Recommendations API ──────────────────────────────────
export const recommendationsApi = {
  getActive: async () => {
    const response = await api.get('/recommendations/');
    return response.data;
  },
  dismiss: async (id: string) => {
    const response = await api.post(`/recommendations/${id}/dismiss`);
    return response.data;
  },
  complete: async (id: string) => {
    const response = await api.post(`/recommendations/${id}/complete`);
    return response.data;
  },
};

// ── Notifications API ────────────────────────────────────
export const notificationsApi = {
  getAll: async (unreadOnly = false) => {
    const response = await api.get('/notifications/', { params: { unread_only: unreadOnly } });
    return response.data;
  },
  markRead: async (id: string) => {
    const response = await api.post(`/notifications/${id}/read`);
    return response.data;
  },
  markAllRead: async () => {
    const response = await api.post('/notifications/read-all');
    return response.data;
  },
};

// ── Admin API ─────────────────────────────────────────────
export const adminApi = {
  getUsers: async (page = 1, pageSize = 50) => {
    const response = await api.get('/admin/users', { params: { page, page_size: pageSize } });
    return response.data;
  },
  getHighRisk: async (threshold = 0.75) => {
    const response = await api.get('/admin/high-risk', { params: { threshold } });
    return response.data;
  },
  getStats: async () => {
    const response = await api.get('/admin/stats');
    return response.data;
  },
  exportCsv: async () => {
    const response = await api.get('/admin/export/csv', { responseType: 'blob' });
    return response.data;
  },
  exportPdf: async () => {
    const response = await api.get('/admin/export/pdf', { responseType: 'blob' });
    return response.data;
  },
};
