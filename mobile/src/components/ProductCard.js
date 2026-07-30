import React, { useContext } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Image } from 'expo-image';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { AuthContext } from '../context/AuthContext';
import { truncate } from '../utils/formatters';

export default function ProductCard({ produto, onPress }) {
  const { serverUrl } = useContext(AuthContext);
  const primeiraImagem = produto.imagens?.[0]
    ? `${serverUrl}/uploads/${produto.imagens[0].filename}`
    : null;

  const primeiraApp = produto.aplicacoes?.[0];

  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.75}>
      {/* Thumb da imagem */}
      <View style={styles.thumb}>
        {primeiraImagem ? (
          <Image
            source={{ uri: primeiraImagem }}
            style={styles.image}
            contentFit="contain"
            transition={200}
            cachePolicy="memory-disk"
          />
        ) : (
          <MaterialCommunityIcons name="car-cog" size={36} color="#BDBDBD" />
        )}
      </View>

      {/* Conteúdo */}
      <View style={styles.info}>
        <Text style={styles.codigo}>{produto.codigo}</Text>
        {produto.fornecedor ? (
          <Text style={styles.fornecedor}>{produto.fornecedor}</Text>
        ) : null}
        <Text style={styles.nome} numberOfLines={2}>{produto.nome}</Text>

        {/* Primeira aplicação como preview */}
        {primeiraApp && (
          <View style={styles.appBadge}>
            <MaterialCommunityIcons name="car" size={12} color="#1565C0" />
            <Text style={styles.appText} numberOfLines={1}>
              {truncate([primeiraApp.veiculo, primeiraApp.ano, primeiraApp.motor].filter(Boolean).join(' • '), 50)}
            </Text>
          </View>
        )}

        {produto.aplicacoes?.length > 1 && (
          <Text style={styles.moreApps}>+{produto.aplicacoes.length - 1} aplicações</Text>
        )}
      </View>

      <MaterialCommunityIcons name="chevron-right" size={20} color="#BDBDBD" />
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
    flexDirection: 'row',
    alignItems: 'center',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  thumb: {
    width: 60,
    height: 60,
    borderRadius: 8,
    backgroundColor: '#F5F5F5',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
    overflow: 'hidden',
  },
  image: { width: 60, height: 60 },
  info: { flex: 1 },
  codigo: { fontSize: 15, fontWeight: 'bold', color: '#1565C0' },
  fornecedor: { fontSize: 11, color: '#757575', marginTop: 1 },
  nome: { fontSize: 13, color: '#424242', marginTop: 2 },
  appBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 5,
    gap: 4,
    backgroundColor: '#E3F2FD',
    borderRadius: 6,
    paddingHorizontal: 6,
    paddingVertical: 2,
    alignSelf: 'flex-start',
  },
  appText: { fontSize: 11, color: '#1565C0', flexShrink: 1 },
  moreApps: { fontSize: 11, color: '#9E9E9E', marginTop: 2 },
});
