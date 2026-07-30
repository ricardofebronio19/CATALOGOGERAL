import apiClient from './client';

export const authAPI = {
  login: (username, password) =>
    apiClient.post('/api/v1/auth/login', { username, password }),

  logout: () => apiClient.post('/api/v1/auth/logout'),

  me: () => apiClient.get('/api/v1/auth/me'),
};
