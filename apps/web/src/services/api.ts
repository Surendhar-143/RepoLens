import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '../stores/auth.ts';

// Create default axios instance pointing to the API route prefix
export const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to inject Authorization header if token exists
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().token;
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to format structured errors
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // Standardize error responses to match Backend structure
    const defaultError = {
      success: false,
      error: {
        code: 'NETWORK_ERROR',
        message: 'Could not connect to the server.',
      },
    };

    if (error.response) {
      const data = error.response.data as any;
      if (data && data.error) {
        return Promise.reject(data);
      }
      
      return Promise.reject({
        success: false,
        error: {
          code: `HTTP_${error.response.status}`,
          message: error.message || 'An error occurred on the server.',
        },
      });
    }

    return Promise.reject(defaultError);
  }
);
