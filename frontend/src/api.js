import axios from 'axios';

const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const api = axios.create({ baseURL: BASE });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const authApi = {
  register: (email, password, username) =>
    api.post('/auth/register', { email, password, username }),
  login: (email, password) =>
    api.post('/auth/login', { email, password }),
};

export const sessionApi = {
  start: () => api.post('/sessions'),
  get: (id) => api.get(`/sessions/${id}`),
  message: (id, content) => api.post(`/sessions/${id}/message`, { content }),
  submitCode: (id, code, language) =>
    api.post(`/sessions/${id}/submit-code`, { code, language }),
  end: (id) => api.post(`/sessions/${id}/end`),
  review: (id) => api.get(`/sessions/${id}/review`),
};

export const progressApi = {
  getProgress: () => api.get('/users/me/progress'),
  getPatterns: () => api.get('/users/me/patterns'),
  getLearningPath: () => api.get('/users/me/learning-path'),
};
