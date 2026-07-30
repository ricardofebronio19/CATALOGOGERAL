import apiClient from './client';

export const contactsAPI = {
  list: (params = {}) =>
    apiClient.get('/api/v1/contatos', { params }),

  getById: (id) =>
    apiClient.get(`/api/v1/contatos/${id}`),

  create: (data) =>
    apiClient.post('/api/v1/contatos', data),

  update: (id, data) =>
    apiClient.put(`/api/v1/contatos/${id}`, data),

  delete: (id) =>
    apiClient.delete(`/api/v1/contatos/${id}`),

  toggleFavorito: (id, favorito) =>
    apiClient.put(`/api/v1/contatos/${id}`, { favorito }),
};
