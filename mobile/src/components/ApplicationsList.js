import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { formatAplicacao } from '../utils/formatters';

const MAX_VISIBLE = 5;

export default function ApplicationsList({ aplicacoes }) {
  const [expanded, setExpanded] = useState(false);

  if (!aplicacoes || aplicacoes.length === 0) return null;

  const visible = expanded ? aplicacoes : aplicacoes.slice(0, MAX_VISIBLE);
  const hasMore = aplicacoes.length > MAX_VISIBLE;

  // Agrupa por montadora para melhor legibilidade
  const grouped = visible.reduce((acc, app) => {
    const key = app.montadora || 'Outros';
    if (!acc[key]) acc[key] = [];
    acc[key].push(app);
    return acc;
  }, {});

  return (
    <View>
      {Object.entries(grouped).map(([montadora, apps]) => (
        <View key={montadora} style={styles.group}>
          <Text style={styles.montadora}>{montadora}</Text>
          {apps.map((app) => (
            <View key={app.id} style={styles.appRow}>
              <MaterialCommunityIcons name="car-side" size={14} color="#757575" style={{ marginRight: 6, marginTop: 1 }} />
              <Text style={styles.appText}>{formatAplicacao(app)}</Text>
            </View>
          ))}
        </View>
      ))}

      {hasMore && (
        <TouchableOpacity style={styles.toggleBtn} onPress={() => setExpanded(!expanded)}>
          <MaterialCommunityIcons
            name={expanded ? 'chevron-up' : 'chevron-down'}
            size={16}
            color="#1565C0"
          />
          <Text style={styles.toggleText}>
            {expanded
              ? 'Mostrar menos'
              : `Ver mais ${aplicacoes.length - MAX_VISIBLE} aplicações`
            }
          </Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  group: { marginBottom: 10 },
  montadora: {
    fontSize: 12,
    fontWeight: '700',
    color: '#1565C0',
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  appRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingVertical: 3,
    borderBottomWidth: 1,
    borderBottomColor: '#F5F5F5',
  },
  appText: { flex: 1, fontSize: 13, color: '#424242', lineHeight: 18 },
  toggleBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    gap: 4,
  },
  toggleText: { color: '#1565C0', fontSize: 13, fontWeight: '600' },
});
