import React, { useState, useEffect, useContext, useCallback } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity,
  Alert, ActivityIndicator, Linking,
} from 'react-native';
import { Image } from 'expo-image';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { productsAPI } from '../api/products';
import { CartContext } from '../context/CartContext';
import { AuthContext } from '../context/AuthContext';
import ImageCarousel from '../components/ImageCarousel';
import ApplicationsList from '../components/ApplicationsList';
import { formatCodigo } from '../utils/formatters';

export default function ProductDetailScreen({ route, navigation }) {
  const { id } = route.params;
  const { serverUrl } = useContext(AuthContext);
  const { addItem } = useContext(CartContext);
  const [produto, setProduto] = useState(null);
  const [loading, setLoading] = useState(true);
  const [addingToCart, setAddingToCart] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const data = await productsAPI.getById(id);
        setProduto(data.produto);
        navigation.setOptions({ title: data.produto?.codigo || 'Detalhes' });
      } catch (e) {
        Alert.alert('Erro', 'Não foi possível carregar a peça.');
        navigation.goBack();
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  const handleAddToCart = useCallback(async () => {
    setAddingToCart(true);
    try {
      await addItem(produto.id, 1);
      Alert.alert('Adicionado!', `${produto.codigo} foi adicionado ao carrinho.`);
    } catch (e) {
      Alert.alert('Erro', e.message || 'Não foi possível adicionar ao carrinho.');
    } finally {
      setAddingToCart(false);
    }
  }, [produto, addItem]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#1565C0" />
      </View>
    );
  }

  if (!produto) return null;

  const imageUrls = (produto.imagens || []).map((img) => `${serverUrl}/uploads/${img.filename}`);

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Galeria de imagens */}
      {imageUrls.length > 0 && <ImageCarousel urls={imageUrls} />}

      {/* Cabeçalho da peça */}
      <View style={styles.card}>
        <Text style={styles.codigo}>{formatCodigo(produto.codigo, produto.fornecedor)}</Text>
        <Text style={styles.nome}>{produto.nome}</Text>
        {produto.grupo ? <Text style={styles.tag}>{produto.grupo}</Text> : null}
      </View>

      {/* Detalhes */}
      {(produto.medidas || produto.conversoes || produto.observacoes) && (
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Informações</Text>
          <InfoRow label="Medidas" value={produto.medidas} />
          <InfoRow label="Conversões" value={produto.conversoes} />
          <InfoRow label="Observações" value={produto.observacoes} />
        </View>
      )}

      {/* Aplicações */}
      {produto.aplicacoes?.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>
            Aplicações ({produto.aplicacoes.length})
          </Text>
          <ApplicationsList aplicacoes={produto.aplicacoes} />
        </View>
      )}

      {/* Similares */}
      {produto.similares_ids?.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Similares</Text>
          {produto.similares_ids.map((simId) => (
            <TouchableOpacity
              key={simId}
              style={styles.similarItem}
              onPress={() => navigation.push('ProductDetail', { id: simId })}
            >
              <MaterialCommunityIcons name="link-variant" size={16} color="#1565C0" />
              <Text style={styles.similarText}>Ver peça #{simId}</Text>
              <MaterialCommunityIcons name="chevron-right" size={16} color="#9E9E9E" />
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* Botão carrinho */}
      <TouchableOpacity
        style={[styles.cartBtn, addingToCart && styles.cartBtnDisabled]}
        onPress={handleAddToCart}
        disabled={addingToCart}
      >
        {addingToCart
          ? <ActivityIndicator color="#fff" size="small" />
          : (
            <>
              <MaterialCommunityIcons name="cart-plus" size={22} color="#fff" />
              <Text style={styles.cartBtnText}>Adicionar ao Carrinho</Text>
            </>
          )
        }
      </TouchableOpacity>
    </ScrollView>
  );
}

function InfoRow({ label, value }) {
  if (!value) return null;
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={styles.infoValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F5' },
  content: { padding: 12, paddingBottom: 32 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  codigo: { fontSize: 20, fontWeight: 'bold', color: '#1565C0' },
  nome: { fontSize: 16, color: '#212121', marginTop: 4 },
  tag: {
    alignSelf: 'flex-start',
    backgroundColor: '#E3F2FD',
    color: '#1565C0',
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: 12,
    fontSize: 12,
    fontWeight: '600',
    marginTop: 8,
  },
  sectionTitle: { fontSize: 15, fontWeight: '700', color: '#424242', marginBottom: 10 },
  infoRow: { flexDirection: 'row', marginBottom: 6 },
  infoLabel: { width: 90, fontSize: 13, color: '#757575', fontWeight: '600' },
  infoValue: { flex: 1, fontSize: 13, color: '#212121' },
  similarItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    gap: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F5F5F5',
  },
  similarText: { flex: 1, color: '#1565C0', fontSize: 14 },
  cartBtn: {
    backgroundColor: '#FF6F00',
    borderRadius: 12,
    paddingVertical: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    marginTop: 4,
    elevation: 3,
  },
  cartBtnDisabled: { opacity: 0.7 },
  cartBtnText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
});
