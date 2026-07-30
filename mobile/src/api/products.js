import apiClient from './client';

export const productsAPI = {
  /**
   * Busca produtos com filtros opcionais.
   * @param {object} params - { q, codigo, montadora, aplicacao, grupo, medidas, page, per_page }
   */
  search: (params = {}) =>
    apiClient.get('/api/v1/buscar', { params }),

  list: (params = {}) =>
    apiClient.get('/api/v1/produtos', { params }),

  getById: (id) =>
    apiClient.get(`/api/v1/produtos/${id}`),

  stats: () =>
    apiClient.get('/api/v1/stats'),
};
