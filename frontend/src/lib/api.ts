import axios, { AxiosInstance, AxiosResponse } from 'axios';

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

async function apiFetch(url: string, options: RequestInit = {}, timeoutMs = 30000, retries = 2) {
  for (let attempt = 0; attempt <= retries; attempt++) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const res = await fetch(url, { ...options, signal: controller.signal });
      return res;
    } catch (err) {
      if (attempt < retries) {
        await new Promise((r) => setTimeout(r, 1000 * Math.pow(2, attempt)));
        continue;
      }
      throw new Error(`Failed to connect to ${url} — ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      clearTimeout(timeout);
    }
  }
  throw new Error(`Failed to connect to ${url} — max retries exceeded`);
}

export interface APIResponse<T = unknown> {
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
    const token = localStorage.getItem('vyron_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
  }
  return config;
});

apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error) => {
    const msg = error.response?.data?.error?.message || error.response?.data?.detail || error.response?.data?.message || error.message || 'Unknown error';
    const status = error.response?.status ? `[${error.response.status}]` : '';
    console.error(`API Client Error ${status}:`, msg, error.response?.data || '');
    return Promise.reject(new Error(`${status} ${msg}`.trim()));
  }
);

export async function uploadFile(
  file: File,
  category: string = 'upload',
  autoIndex: boolean = true,
  onProgress?: (percent: number) => void
): Promise<{ file_id: string; document_id?: string; filename: string; extracted_text_preview?: string }> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('category', category);
  formData.append('auto_index', String(autoIndex));

  const token = localStorage.getItem('vyron_token');
  const response = await apiFetch(`${API_BASE_URL}/upload/file`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.error?.message || err.detail || err.message || `Upload failed with status ${response.status}`);
  }

  const json = await response.json();
  return json.data as { file_id: string; document_id?: string; filename: string; extracted_text_preview?: string };
}

export async function deleteFile(fileId: string): Promise<void> {
  await api.delete(`/upload/${fileId}`);
}

export const api = {
  get: async <T>(url: string, params?: Record<string, unknown>): Promise<T> => {
    const res = await apiClient.get<APIResponse<T> | T>(url, { params });
    if (res.data && typeof res.data === 'object' && 'data' in res.data && 'success' in res.data) {
      return (res.data as APIResponse<T>).data;
    }
    return res.data as T;
  },
  post: async <T>(url: string, body?: unknown): Promise<T> => {
    const res = await apiClient.post<APIResponse<T> | T>(url, body);
    if (res.data && typeof res.data === 'object' && 'data' in res.data && 'success' in res.data) {
      return (res.data as APIResponse<T>).data;
    }
    return res.data as T;
  },
  put: async <T>(url: string, body?: unknown): Promise<T> => {
    const res = await apiClient.put<APIResponse<T> | T>(url, body);
    if (res.data && typeof res.data === 'object' && 'data' in res.data && 'success' in res.data) {
      return (res.data as APIResponse<T>).data;
    }
    return res.data as T;
  },
  delete: async <T>(url: string, params?: Record<string, unknown>): Promise<T> => {
    const res = await apiClient.delete<APIResponse<T> | T>(url, { params });
    if (res.data && typeof res.data === 'object' && 'data' in res.data && 'success' in res.data) {
      return (res.data as APIResponse<T>).data;
    }
    return res.data as T;
  },
};
