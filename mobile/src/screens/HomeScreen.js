import React, { useState, useCallback } from 'react';
import {
  View, FlatList, StyleSheet, Text,
  TextInput, TouchableOpacity, ActivityIndicator,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { productsAPI } from '../api/products';
import ProductCard from '../components/ProductCard';
import EmptyState from '../components/EmptyState';

export default function HomeScreen({ navigation }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);

  const doSearch = useCallback(async (termo = query, page = 1) => {
    const trimmed = termo.trim();
    if (!trimmed) return;
    setLoading(true);
    setSearched(true);
    try {
      const data = await productsAPI.search({ q: trimmed, page, per_page: 20 });
      if (page === 1) {
        setResults(data.produtos || []);
      } else {
        setResults((prev) => [...prev, ...(data.produtos || [])]);
      }
      setPagination(data.pagination);
      setCurrentPage(page);
    } catch (e) {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [query]);

  const loadMore = useCallback(() => {
    if (pagination?.has_next && !loading) {
      doSearch(query, currentPage + 1);
    }
  }, [pagination, loading, query, currentPage, doSearch]);

  const renderItem = useCallback(({ item }) => (
    <ProductCard
      produto={item}
      onPress={() => navigation.navigate('ProductDetail', { id: item.id })}
    />
  ), [navigation]);

  const renderFooter = () => {
    if (!pagination?.has_next) return null;
    return (
      <TouchableOpacity style={styles.loadMoreBtn} onPress={loadMore} disabled={loading}>
        {loading
          ? <ActivityIndicator color="#1565C0" />
          : <Text style={styles.loadMoreText}>Carregar mais</Text>
        }
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      {/* Barra de busca */}
      <View style={styles.searchBar}>
        <MaterialCommunityIcons name="magnify" size={22} color="#757575" style={styles.searchIcon} />
        <TextInput
          style={styles.searchInput}
          value={query}
          onChangeText={setQuery}
          placeholder="Código, nome, veículo, montadora..."
          placeholderTextColor="#9E9E9E"
          returnKeyType="search"
          onSubmitEditing={() => doSearch(query, 1)}
          autoCorrect={false}
          autoCapitalize="none"
        />
        {query.length > 0 && (
          <TouchableOpacity onPress={() => { setQuery(''); setResults([]); setSearched(false); }}>
            <MaterialCommunityIcons name="close-circle" size={20} color="#9E9E9E" />
          </TouchableOpacity>
        )}
        <TouchableOpacity style={styles.searchBtn} onPress={() => doSearch(query, 1)}>
          <Text style={styles.searchBtnText}>Buscar</Text>
        </TouchableOpacity>
      </View>

      {/* Contador de resultados */}
      {searched && !loading && pagination && (
        <Text style={styles.resultCount}>
          {pagination.total} resultado{pagination.total !== 1 ? 's' : ''} encontrado{pagination.total !== 1 ? 's' : ''}
        </Text>
      )}

      {/* Lista de resultados */}
      {loading && results.length === 0 ? (
        <View style={styles.centerState}>
          <ActivityIndicator size="large" color="#1565C0" />
          <Text style={styles.loadingText}>Buscando...</Text>
        </View>
      ) : searched && results.length === 0 ? (
        <EmptyState
          icon="car-search"
          title="Nenhuma peça encontrada"
          message="Tente termos diferentes ou verifique o código da peça."
        />
      ) : !searched ? (
        <EmptyState
          icon="magnify"
          title="Busque uma peça"
          message="Digite o código, nome, veículo ou montadora para encontrar peças."
        />
      ) : (
        <FlatList
          data={results}
          keyExtractor={(item) => String(item.id)}
          renderItem={renderItem}
          contentContainerStyle={styles.list}
          ListFooterComponent={renderFooter}
          onEndReachedThreshold={0.3}
          onEndReached={loadMore}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F5' },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    margin: 12,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 6,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.15,
    shadowRadius: 3,
  },
  searchIcon: { marginRight: 6 },
  searchInput: { flex: 1, fontSize: 15, color: '#212121', paddingVertical: 6 },
  searchBtn: {
    backgroundColor: '#1565C0',
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 7,
    marginLeft: 8,
  },
  searchBtnText: { color: '#fff', fontWeight: '600', fontSize: 13 },
  resultCount: { paddingHorizontal: 16, fontSize: 12, color: '#757575', marginBottom: 4 },
  list: { paddingHorizontal: 12, paddingBottom: 16 },
  centerState: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: 12 },
  loadingText: { color: '#757575', fontSize: 15 },
  loadMoreBtn: { alignItems: 'center', padding: 16 },
  loadMoreText: { color: '#1565C0', fontWeight: '600' },
});
