import apiClient from './client';

export const cartAPI = {
  getCart: () => apiClient.get('/api/v1/carrinho'),

  addItem: (produtoId, quantidade = 1) =>
    apiClient.post('/api/v1/carrinho/adicionar', { produto_id: produtoId, quantidade }),

  removeItem: (produtoId) =>
    apiClient.post('/api/v1/carrinho/remover', { produto_id: produtoId }),

  updateItem: (produtoId, quantidade) =>
    apiClient.post('/api/v1/carrinho/atualizar', { produto_id: produtoId, quantidade }),

  clearCart: () => apiClient.post('/api/v1/carrinho/limpar'),
};
