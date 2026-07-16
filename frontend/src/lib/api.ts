import axios, { AxiosInstance, AxiosResponse } from 'axios';

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

export interface APIResponse<T = any> {
  success: boolean;
  message: string | null;
  data: T;
  timestamp: string;
  request_id: string;
}

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const requestId = `req-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;
  if (config.headers) {
    config.headers['X-Request-ID'] = requestId;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error) => {
    console.error('API Client Error:', error.response?.data || error.message);
    return Promise.reject(error.response?.data || error);
  }
);

export const api = {
  get: async <T>(url: string, params?: any): Promise<T> => {
    const res = await apiClient.get<APIResponse<T> | T>(url, { params });
    if (res.data && typeof res.data === 'object' && 'data' in res.data && 'success' in res.data) {
      return (res.data as APIResponse<T>).data;
    }
    return res.data as T;
  },
  post: async <T>(url: string, body?: any): Promise<T> => {
    const res = await apiClient.post<APIResponse<T> | T>(url, body);
    if (res.data && typeof res.data === 'object' && 'data' in res.data && 'success' in res.data) {
      return (res.data as APIResponse<T>).data;
    }
    return res.data as T;
  },
  put: async <T>(url: string, body?: any): Promise<T> => {
    const res = await apiClient.put<APIResponse<T> | T>(url, body);
    if (res.data && typeof res.data === 'object' && 'data' in res.data && 'success' in res.data) {
      return (res.data as APIResponse<T>).data;
    }
    return res.data as T;
  },
  delete: async <T>(url: string, params?: any): Promise<T> => {
    const res = await apiClient.delete<APIResponse<T> | T>(url, { params });
    if (res.data && typeof res.data === 'object' && 'data' in res.data && 'success' in res.data) {
      return (res.data as APIResponse<T>).data;
    }
    return res.data as T;
  },
};
