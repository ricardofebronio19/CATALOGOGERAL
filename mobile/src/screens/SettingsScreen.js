import React, { useState, useContext } from 'react';
import {
  View, Text, TextInput, TouchableOpacity,
  StyleSheet, ScrollView, Alert, Linking,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { AuthContext } from '../context/AuthContext';

export default function SettingsScreen() {
  const { user, logout, serverUrl, updateServerUrl } = useContext(AuthContext);
  const [newUrl, setNewUrl] = useState(serverUrl);
  const [saved, setSaved] = useState(false);

  async function handleSaveUrl() {
    if (!newUrl.trim()) {
      Alert.alert('Atenção', 'Informe um endereço válido.');
      return;
    }
    await updateServerUrl(newUrl);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
    Alert.alert('Servidor atualizado', 'Faça login novamente com o novo endereço.');
  }

  function handleLogout() {
    Alert.alert(
      'Sair',
      'Tem certeza que deseja sair da conta?',
      [
        { text: 'Cancelar', style: 'cancel' },
        { text: 'Sair', style: 'destructive', onPress: logout },
      ]
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Usuário atual */}
      <View style={styles.userCard}>
        <View style={styles.userAvatar}>
          <MaterialCommunityIcons name="account" size={36} color="#1565C0" />
        </View>
        <View>
          <Text style={styles.userName}>{user?.username || '—'}</Text>
          <Text style={styles.userRole}>{user?.is_admin ? 'Administrador' : 'Usuário'}</Text>
        </View>
      </View>

      {/* Configuração do servidor */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Servidor Flask</Text>
        <Text style={styles.sectionHint}>
          Endereço IP do PC onde o servidor está rodando na rede Wi-Fi local.
        </Text>

        <Text style={styles.label}>Endereço</Text>
        <TextInput
          style={styles.input}
          value={newUrl}
          onChangeText={setNewUrl}
          placeholder="http://192.168.1.100:8000"
          placeholderTextColor="#BDBDBD"
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="url"
        />

        <TouchableOpacity style={styles.saveBtn} onPress={handleSaveUrl}>
          <MaterialCommunityIcons name={saved ? 'check' : 'content-save'} size={18} color="#fff" />
          <Text style={styles.saveBtnText}>{saved ? 'Salvo!' : 'Salvar Endereço'}</Text>
        </TouchableOpacity>
      </View>

      {/* Informações */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Informações</Text>
        <InfoRow icon="server-network" label="Servidor atual" value={serverUrl} />
        <InfoRow icon="api" label="API" value={`${serverUrl}/api/v1/`} />
      </View>

      {/* Logout */}
      <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
        <MaterialCommunityIcons name="logout" size={20} color="#EF5350" />
        <Text style={styles.logoutText}>Sair da conta</Text>
      </TouchableOpacity>

      <Text style={styles.version}>Catálogo de Peças CGI • v1.0.0</Text>
    </ScrollView>
  );
}

function InfoRow({ icon, label, value }) {
  return (
    <View style={styles.infoRow}>
      <MaterialCommunityIcons name={icon} size={18} color="#757575" style={{ marginRight: 8 }} />
      <View style={{ flex: 1 }}>
        <Text style={styles.infoLabel}>{label}</Text>
        <Text style={styles.infoValue} numberOfLines={1}>{value}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F5' },
  content: { padding: 16, paddingBottom: 40 },
  userCard: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 20,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
    marginBottom: 16,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  userAvatar: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#E3F2FD',
    justifyContent: 'center',
    alignItems: 'center',
  },
  userName: { fontSize: 18, fontWeight: 'bold', color: '#212121' },
  userRole: { fontSize: 13, color: '#757575', marginTop: 2 },
  section: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    elevation: 1,
  },
  sectionTitle: { fontSize: 15, fontWeight: '700', color: '#424242', marginBottom: 6 },
  sectionHint: { fontSize: 12, color: '#9E9E9E', marginBottom: 12 },
  label: { fontSize: 13, fontWeight: '600', color: '#616161', marginBottom: 4 },
  input: {
    borderWidth: 1,
    borderColor: '#E0E0E0',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    color: '#212121',
    backgroundColor: '#FAFAFA',
  },
  saveBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1565C0',
    borderRadius: 8,
    paddingVertical: 11,
    marginTop: 10,
    gap: 8,
  },
  saveBtnText: { color: '#fff', fontWeight: '600', fontSize: 14 },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F5F5F5',
  },
  infoLabel: { fontSize: 12, color: '#757575' },
  infoValue: { fontSize: 13, color: '#212121', marginTop: 1 },
  logoutBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    paddingVertical: 16,
    gap: 10,
    marginBottom: 16,
    elevation: 1,
    borderWidth: 1,
    borderColor: '#FFEBEE',
  },
  logoutText: { color: '#EF5350', fontSize: 16, fontWeight: '600' },
  version: { textAlign: 'center', fontSize: 12, color: '#BDBDBD' },
});
