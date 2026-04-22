import React, { useContext, useEffect } from 'react';
import {
  View, Text, FlatList, StyleSheet,
  TouchableOpacity, Alert, Linking, ActivityIndicator,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { CartContext } from '../context/CartContext';
import { AuthContext } from '../context/AuthContext';
import EmptyState from '../components/EmptyState';
import { formatWhatsApp } from '../utils/formatters';

export default function CartScreen({ navigation }) {
  const { cartItems, cartCount, isLoading, refreshCart, removeItem, updateItem, clearCart } = useContext(CartContext);
  const { serverUrl } = useContext(AuthContext);

  useEffect(() => {
    const unsubscribe = navigation.addListener('focus', refreshCart);
    return unsubscribe;
  }, [navigation, refreshCart]);

  function handleClear() {
    Alert.alert(
      'Limpar carrinho',
      'Tem certeza que deseja remover todos os itens?',
      [
        { text: 'Cancelar', style: 'cancel' },
        { text: 'Limpar', style: 'destructive', onPress: clearCart },
      ]
    );
  }

  function handleRemove(item) {
    Alert.alert(
      'Remover item',
      `Remover "${item.nome || item.codigo}" do carrinho?`,
      [
        { text: 'Cancelar', style: 'cancel' },
        { text: 'Remover', style: 'destructive', onPress: () => removeItem(item.produto_id) },
      ]
    );
  }

  async function handleShareWhatsApp() {
    const lines = cartItems.map(
      (i) => `• ${i.codigo || 'Peça'} - ${i.nome || ''} (qtd: ${i.quantidade})`
    );
    const msg = `Pedido - Catálogo de Peças CGI\n\n${lines.join('\n')}`;
    const encoded = encodeURIComponent(msg);
    const url = `whatsapp://send?text=${encoded}`;
    const canOpen = await Linking.canOpenURL(url);
    if (canOpen) {
      Linking.openURL(url);
    } else {
      Alert.alert('WhatsApp não encontrado', 'Instale o WhatsApp para compartilhar o pedido.');
    }
  }

  if (isLoading && cartItems.length === 0) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#1565C0" />
      </View>
    );
  }

  if (cartItems.length === 0) {
    return (
      <EmptyState
        icon="cart-outline"
        title="Carrinho vazio"
        message="Adicione peças pelo catálogo para montar seu pedido."
      />
    );
  }

  const renderItem = ({ item }) => (
    <View style={styles.itemCard}>
      <View style={styles.itemInfo}>
        <Text style={styles.itemCodigo}>{item.codigo || `Peça #${item.produto_id}`}</Text>
        <Text style={styles.itemNome} numberOfLines={2}>{item.nome || '—'}</Text>
      </View>

      <View style={styles.qtyRow}>
        <TouchableOpacity
          style={styles.qtyBtn}
          onPress={() => item.quantidade > 1
            ? updateItem(item.produto_id, item.quantidade - 1)
            : handleRemove(item)
          }
        >
          <MaterialCommunityIcons name="minus" size={18} color="#1565C0" />
        </TouchableOpacity>
        <Text style={styles.qty}>{item.quantidade}</Text>
        <TouchableOpacity
          style={styles.qtyBtn}
          onPress={() => updateItem(item.produto_id, item.quantidade + 1)}
        >
          <MaterialCommunityIcons name="plus" size={18} color="#1565C0" />
        </TouchableOpacity>
      </View>

      <TouchableOpacity onPress={() => handleRemove(item)} style={styles.removeBtn}>
        <MaterialCommunityIcons name="trash-can-outline" size={22} color="#EF5350" />
      </TouchableOpacity>
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerText}>{cartCount} ite{cartCount !== 1 ? 'ns' : 'm'} no carrinho</Text>
        <TouchableOpacity onPress={handleClear}>
          <Text style={styles.clearText}>Limpar tudo</Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={cartItems}
        keyExtractor={(item) => String(item.produto_id)}
        renderItem={renderItem}
        contentContainerStyle={styles.list}
      />

      <View style={styles.footer}>
        <TouchableOpacity style={styles.whatsappBtn} onPress={handleShareWhatsApp}>
          <MaterialCommunityIcons name="whatsapp" size={22} color="#fff" />
          <Text style={styles.whatsappBtnText}>Enviar por WhatsApp</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F5' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  headerText: { fontSize: 15, fontWeight: '600', color: '#424242' },
  clearText: { fontSize: 13, color: '#EF5350', fontWeight: '600' },
  list: { padding: 12 },
  itemCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    flexDirection: 'row',
    alignItems: 'center',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  itemInfo: { flex: 1, marginRight: 8 },
  itemCodigo: { fontSize: 15, fontWeight: 'bold', color: '#1565C0' },
  itemNome: { fontSize: 13, color: '#616161', marginTop: 2 },
  qtyRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  qtyBtn: {
    backgroundColor: '#E3F2FD',
    borderRadius: 20,
    width: 32,
    height: 32,
    justifyContent: 'center',
    alignItems: 'center',
  },
  qty: { fontSize: 16, fontWeight: 'bold', color: '#212121', minWidth: 24, textAlign: 'center' },
  removeBtn: { padding: 6, marginLeft: 6 },
  footer: { padding: 16, backgroundColor: '#fff', borderTopWidth: 1, borderTopColor: '#E0E0E0' },
  whatsappBtn: {
    backgroundColor: '#25D366',
    borderRadius: 12,
    paddingVertical: 15,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 10,
    elevation: 2,
  },
  whatsappBtnText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
});
