/**
 * Cliente axios base.
 * O baseURL é lido dinamicamente do módulo storage para refletir
 * eventuais mudanças de servidor sem reiniciar o app.
 */
import axios from 'axios';
import { getServerUrl } from '../utils/storage';

const apiClient = axios.create({
  timeout: 15000,
  withCredentials: true,           // Mantém cookie de sessão Flask
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Interceptor de request: injeta baseURL dinâmico
apiClient.interceptors.request.use((config) => {
  config.baseURL = getServerUrl();
  return config;
});

// Interceptor de response: extrai o campo `data` da resposta padronizada da API
apiClient.interceptors.response.use(
  (response) => {
    // A API retorna { status, data, message, ... }
    if (response.data && response.data.data !== undefined) {
      return response.data.data;
    }
    return response.data;
  },
  (error) => {
    const msg =
      error.response?.data?.error ||
      error.response?.data?.message ||
      error.message ||
      'Erro desconhecido';
    return Promise.reject(new Error(msg));
  }
);

export default apiClient;
