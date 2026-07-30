import React, { createContext, useState, useEffect, useCallback } from 'react';
import * as SecureStore from 'expo-secure-store';
import { authAPI } from '../api/auth';
import { setServerUrl, getServerUrl } from '../utils/storage';

export const AuthContext = createContext(null);

const USER_KEY = 'catalogo_user';
const SERVER_KEY = 'catalogo_server_url';
const DEFAULT_SERVER = 'http://192.168.1.100:8000';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [serverUrl, setServerUrlState] = useState(DEFAULT_SERVER);
  const [isLoading, setIsLoading] = useState(true);

  // Carrega dados persistidos ao inicializar
  useEffect(() => {
    async function bootstrap() {
      try {
        const savedServer = await SecureStore.getItemAsync(SERVER_KEY);
        const savedUser = await SecureStore.getItemAsync(USER_KEY);

        if (savedServer) {
          setServerUrlState(savedServer);
          setServerUrl(savedServer);
        }

        if (savedUser) {
          const parsedUser = JSON.parse(savedUser);
          // Verifica se a sessão ainda é válida
          try {
            const me = await authAPI.me();
            setUser(me.user);
          } catch {
            // Sessão expirada, limpa dados
            await SecureStore.deleteItemAsync(USER_KEY);
          }
        }
      } catch (e) {
        console.warn('Erro ao carregar dados de sessão:', e);
      } finally {
        setIsLoading(false);
      }
    }
    bootstrap();
  }, []);

  const login = useCallback(async (username, password) => {
    const data = await authAPI.login(username, password);
    setUser(data.user);
    await SecureStore.setItemAsync(USER_KEY, JSON.stringify(data.user));
    return data.user;
  }, []);

  const logout = useCallback(async () => {
    try {
      await authAPI.logout();
    } catch (_) {}
    setUser(null);
    await SecureStore.deleteItemAsync(USER_KEY);
  }, []);

  const updateServerUrl = useCallback(async (url) => {
    const trimmed = url.trim().replace(/\/$/, '');
    setServerUrlState(trimmed);
    setServerUrl(trimmed);
    await SecureStore.setItemAsync(SERVER_KEY, trimmed);
    // Limpa sessão ao trocar servidor
    setUser(null);
    await SecureStore.deleteItemAsync(USER_KEY);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, serverUrl, updateServerUrl }}>
      {children}
    </AuthContext.Provider>
  );
}
