import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, FlatList, StyleSheet,
  TouchableOpacity, TextInput, Alert, Linking, ActivityIndicator,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { contactsAPI } from '../api/contacts';
import EmptyState from '../components/EmptyState';
import { formatWhatsApp, formatPhone } from '../utils/formatters';

export default function ContactsScreen({ navigation }) {
  const [contatos, setContatos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [onlyFavoritos, setOnlyFavoritos] = useState(false);

  const loadContatos = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (query.trim()) params.q = query.trim();
      if (onlyFavoritos) params.favoritos = true;
      const data = await contactsAPI.list(params);
      setContatos(data.contatos || []);
    } catch (e) {
      Alert.alert('Erro', 'Não foi possível carregar os contatos.');
    } finally {
      setLoading(false);
    }
  }, [query, onlyFavoritos]);

  useEffect(() => {
    const unsubscribe = navigation.addListener('focus', loadContatos);
    return unsubscribe;
  }, [navigation, loadContatos]);

  useEffect(() => {
    loadContatos();
  }, [onlyFavoritos]);

  function handleWhatsApp(numero) {
    const formatted = formatWhatsApp(numero);
    if (!formatted) return;
    Linking.openURL(`whatsapp://send?phone=${formatted}`).catch(() => {
      Alert.alert('Erro', 'Não foi possível abrir o WhatsApp.');
    });
  }

  function handleDelete(contato) {
    Alert.alert(
      'Excluir contato',
      `Excluir "${contato.nome}"?`,
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Excluir', style: 'destructive', onPress: async () => {
            try {
              await contactsAPI.delete(contato.id);
              loadContatos();
            } catch (e) {
              Alert.alert('Erro', e.message);
            }
          }
        },
      ]
    );
  }

  async function handleToggleFavorito(contato) {
    try {
      await contactsAPI.toggleFavorito(contato.id, !contato.favorito);
      loadContatos();
    } catch (e) {
      Alert.alert('Erro', e.message);
    }
  }

  const renderItem = ({ item }) => (
    <View style={styles.contactCard}>
      <View style={styles.avatar}>
        <Text style={styles.avatarText}>{(item.nome || '?')[0].toUpperCase()}</Text>
      </View>

      <View style={styles.contactInfo}>
        <Text style={styles.contactName}>{item.nome}</Text>
        {item.empresa ? <Text style={styles.contactCompany}>{item.empresa}</Text> : null}
        {item.telefone ? <Text style={styles.contactDetail}>{formatPhone(item.telefone)}</Text> : null}
      </View>

      <View style={styles.contactActions}>
        {item.whatsapp && (
          <TouchableOpacity onPress={() => handleWhatsApp(item.whatsapp)} style={styles.actionBtn}>
            <MaterialCommunityIcons name="whatsapp" size={22} color="#25D366" />
          </TouchableOpacity>
        )}
        <TouchableOpacity onPress={() => handleToggleFavorito(item)} style={styles.actionBtn}>
          <MaterialCommunityIcons
            name={item.favorito ? 'star' : 'star-outline'}
            size={22}
            color={item.favorito ? '#FF6F00' : '#9E9E9E'}
          />
        </TouchableOpacity>
        <TouchableOpacity
          onPress={() => navigation.navigate('ContactForm', { contato: item })}
          style={styles.actionBtn}
        >
          <MaterialCommunityIcons name="pencil" size={20} color="#1565C0" />
        </TouchableOpacity>
        <TouchableOpacity onPress={() => handleDelete(item)} style={styles.actionBtn}>
          <MaterialCommunityIcons name="trash-can-outline" size={20} color="#EF5350" />
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Barra de filtros */}
      <View style={styles.filterBar}>
        <View style={styles.searchBox}>
          <MaterialCommunityIcons name="magnify" size={18} color="#757575" />
          <TextInput
            style={styles.searchInput}
            value={query}
            onChangeText={setQuery}
            placeholder="Buscar contatos..."
            placeholderTextColor="#9E9E9E"
            returnKeyType="search"
            onSubmitEditing={loadContatos}
          />
        </View>
        <TouchableOpacity
          style={[styles.favBtn, onlyFavoritos && styles.favBtnActive]}
          onPress={() => setOnlyFavoritos(!onlyFavoritos)}
        >
          <MaterialCommunityIcons
            name="star"
            size={18}
            color={onlyFavoritos ? '#FF6F00' : '#9E9E9E'}
          />
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.addBtn}
          onPress={() => navigation.navigate('ContactForm', {})}
        >
          <MaterialCommunityIcons name="plus" size={20} color="#fff" />
        </TouchableOpacity>
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#1565C0" />
        </View>
      ) : contatos.length === 0 ? (
        <EmptyState
          icon="account-group-outline"
          title="Nenhum contato"
          message="Toque em + para adicionar seu primeiro contato."
        />
      ) : (
        <FlatList
          data={contatos}
          keyExtractor={(item) => String(item.id)}
          renderItem={renderItem}
          contentContainerStyle={styles.list}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F5' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  filterBar: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
    gap: 8,
  },
  searchBox: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F5F5F5',
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 6,
    gap: 6,
  },
  searchInput: { flex: 1, fontSize: 14, color: '#212121' },
  favBtn: {
    padding: 8,
    backgroundColor: '#F5F5F5',
    borderRadius: 8,
  },
  favBtnActive: { backgroundColor: '#FFF3E0' },
  addBtn: {
    backgroundColor: '#1565C0',
    borderRadius: 8,
    padding: 8,
  },
  list: { padding: 12 },
  contactCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 14,
    marginBottom: 8,
    flexDirection: 'row',
    alignItems: 'center',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#1565C0',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  avatarText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  contactInfo: { flex: 1 },
  contactName: { fontSize: 15, fontWeight: '600', color: '#212121' },
  contactCompany: { fontSize: 12, color: '#757575', marginTop: 1 },
  contactDetail: { fontSize: 12, color: '#9E9E9E', marginTop: 2 },
  contactActions: { flexDirection: 'row', gap: 2 },
  actionBtn: { padding: 6 },
});
