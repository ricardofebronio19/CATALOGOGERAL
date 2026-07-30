import React, { useState, useContext } from 'react';
import {
  View, Text, TextInput, TouchableOpacity,
  StyleSheet, KeyboardAvoidingView, Platform,
  ScrollView, Alert,
} from 'react-native';
import { ActivityIndicator } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { AuthContext } from '../context/AuthContext';

export default function LoginScreen() {
  const { login, serverUrl, updateServerUrl } = useContext(AuthContext);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [server, setServer] = useState(serverUrl);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showServerField, setShowServerField] = useState(false);

  async function handleLogin() {
    if (!username.trim() || !password) {
      Alert.alert('Atenção', 'Informe usuário e senha.');
      return;
    }
    if (server !== serverUrl) {
      await updateServerUrl(server);
    }
    setLoading(true);
    try {
      await login(username.trim(), password);
    } catch (e) {
      Alert.alert('Erro de autenticação', e.message || 'Usuário ou senha inválidos.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.wrapper}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        <View style={styles.logoContainer}>
          <MaterialCommunityIcons name="car-cog" size={72} color="#fff" />
          <Text style={styles.title}>Catálogo de Peças</Text>
          <Text style={styles.subtitle}>CGI</Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.label}>Usuário</Text>
          <TextInput
            style={styles.input}
            value={username}
            onChangeText={setUsername}
            autoCapitalize="none"
            autoCorrect={false}
            placeholder="seu_usuario"
            placeholderTextColor="#BDBDBD"
            returnKeyType="next"
          />

          <Text style={styles.label}>Senha</Text>
          <View style={styles.passwordRow}>
            <TextInput
              style={[styles.input, { flex: 1 }]}
              value={password}
              onChangeText={setPassword}
              secureTextEntry={!showPassword}
              placeholder="••••••••"
              placeholderTextColor="#BDBDBD"
              returnKeyType="done"
              onSubmitEditing={handleLogin}
            />
            <TouchableOpacity onPress={() => setShowPassword(!showPassword)} style={styles.eyeBtn}>
              <MaterialCommunityIcons
                name={showPassword ? 'eye-off' : 'eye'}
                size={22}
                color="#757575"
              />
            </TouchableOpacity>
          </View>

          <TouchableOpacity style={styles.loginBtn} onPress={handleLogin} disabled={loading}>
            {loading
              ? <ActivityIndicator color="#fff" size="small" />
              : <Text style={styles.loginBtnText}>Entrar</Text>
            }
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.serverToggle}
            onPress={() => setShowServerField(!showServerField)}
          >
            <MaterialCommunityIcons name="server" size={16} color="#757575" />
            <Text style={styles.serverToggleText}>
              {showServerField ? 'Ocultar endereço do servidor' : 'Configurar endereço do servidor'}
            </Text>
          </TouchableOpacity>

          {showServerField && (
            <View style={styles.serverBox}>
              <Text style={styles.label}>Endereço do servidor</Text>
              <TextInput
                style={styles.input}
                value={server}
                onChangeText={setServer}
                autoCapitalize="none"
                autoCorrect={false}
                placeholder="http://192.168.1.100:8000"
                placeholderTextColor="#BDBDBD"
                keyboardType="url"
              />
              <Text style={styles.hint}>
                Endereço IP do computador onde o servidor Flask está rodando na rede local.
              </Text>
            </View>
          )}
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  wrapper: { flex: 1, backgroundColor: '#1565C0' },
  container: { flexGrow: 1, justifyContent: 'center', padding: 24 },
  logoContainer: { alignItems: 'center', marginBottom: 32 },
  title: { fontSize: 26, fontWeight: 'bold', color: '#fff', marginTop: 12 },
  subtitle: { fontSize: 16, color: '#BBDEFB', marginTop: 4 },
  card: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 24,
    elevation: 6,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
  },
  label: { fontSize: 13, fontWeight: '600', color: '#424242', marginBottom: 4, marginTop: 12 },
  input: {
    borderWidth: 1,
    borderColor: '#E0E0E0',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: Platform.OS === 'ios' ? 12 : 8,
    fontSize: 15,
    color: '#212121',
    backgroundColor: '#FAFAFA',
  },
  passwordRow: { flexDirection: 'row', alignItems: 'center' },
  eyeBtn: { padding: 8, marginLeft: 4 },
  loginBtn: {
    backgroundColor: '#1565C0',
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 20,
  },
  loginBtnText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  serverToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 16,
    gap: 6,
  },
  serverToggleText: { color: '#757575', fontSize: 13 },
  serverBox: { marginTop: 12 },
  hint: { fontSize: 11, color: '#9E9E9E', marginTop: 4 },
});
