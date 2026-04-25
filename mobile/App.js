import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { Provider as PaperProvider, DefaultTheme } from 'react-native-paper';
import { AuthProvider } from './src/context/AuthContext';
import { CartProvider } from './src/context/CartContext';
import AppNavigator from './src/navigation/AppNavigator';

const theme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    primary: '#1565C0',
    accent: '#FF6F00',
    background: '#F5F5F5',
    surface: '#FFFFFF',
    text: '#212121',
    placeholder: '#9E9E9E',
  },
};

export default function App() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <PaperProvider theme={theme}>
        <AuthProvider>
          <CartProvider>
            <StatusBar style="light" backgroundColor="#1565C0" />
            <AppNavigator />
          </CartProvider>
        </AuthProvider>
      </PaperProvider>
    </GestureHandlerRootView>
  );
}
