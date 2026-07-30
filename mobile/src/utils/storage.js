/**
 * Módulo de armazenamento do URL do servidor.
 * Mantém o baseURL em memória para ser usado pelo cliente axios.
 */

let _serverUrl = 'http://192.168.1.100:8000';

export function setServerUrl(url) {
  _serverUrl = url.trim().replace(/\/$/, '');
}

export function getServerUrl() {
  return _serverUrl;
}
