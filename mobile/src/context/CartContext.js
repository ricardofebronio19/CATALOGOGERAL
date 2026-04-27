import React, { createContext, useState, useCallback, useContext } from 'react';
import { cartAPI } from '../api/cart';

export const CartContext = createContext(null);

export function CartProvider({ children }) {
  const [cartItems, setCartItems] = useState([]);
  const [cartCount, setCartCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  const refreshCart = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await cartAPI.getCart();
      setCartItems(data.items || []);
      setCartCount(data.total_items || 0);
    } catch (e) {
      console.warn('Erro ao carregar carrinho:', e);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const addItem = useCallback(async (produtoId, quantidade = 1) => {
    const data = await cartAPI.addItem(produtoId, quantidade);
    setCartItems(data.items || []);
    setCartCount(data.total_items || 0);
    return data;
  }, []);

  const removeItem = useCallback(async (produtoId) => {
    const data = await cartAPI.removeItem(produtoId);
    setCartItems(data.items || []);
    setCartCount(data.total_items || 0);
    return data;
  }, []);

  const updateItem = useCallback(async (produtoId, quantidade) => {
    const data = await cartAPI.updateItem(produtoId, quantidade);
    setCartItems(data.items || []);
    setCartCount(data.total_items || 0);
    return data;
  }, []);

  const clearCart = useCallback(async () => {
    const data = await cartAPI.clearCart();
    setCartItems([]);
    setCartCount(0);
    return data;
  }, []);

  return (
    <CartContext.Provider value={{
      cartItems,
      cartCount,
      isLoading,
      refreshCart,
      addItem,
      removeItem,
      updateItem,
      clearCart,
    }}>
      {children}
    </CartContext.Provider>
  );
}
