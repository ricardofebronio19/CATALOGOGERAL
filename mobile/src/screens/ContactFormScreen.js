import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity,
  StyleSheet, ScrollView, Alert, ActivityIndicator,
  KeyboardAvoidingView, Platform,
} from 'react-native';
import { contactsAPI } from '../api/contacts';

export default function ContactFormScreen({ route, navigation }) {
  const existing = route.params?.contato;

  const [form, setForm] = useState({
    nome: existing?.nome || '',
    empresa: existing?.empresa || '',
    telefone: existing?.telefone || '',
    whatsapp: existing?.whatsapp || '',
    email: existing?.email || '',
    cargo: existing?.cargo || '',
    endereco: existing?.endereco || '',
    observacoes: existing?.observacoes || '',
  });
  const [loading, setLoading] = useState(false);

  function set(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSave() {
    if (!form.nome.trim()) {
      Alert.alert('Atenção', 'O nome é obrigatório.');
      return;
    }
    setLoading(true);
    try {
      if (existing) {
        await contactsAPI.update(existing.id, form);
        Alert.alert('Sucesso', 'Contato atualizado com sucesso.');
      } else {
        await contactsAPI.create(form);
        Alert.alert('Sucesso', 'Contato criado com sucesso.');
      }
      navigation.goBack();
    } catch (e) {
      Alert.alert('Erro', e.message || 'Não foi possível salvar o contato.');
    } finally {
      setLoading(false);
    }
  }

  const fields = [
    { key: 'nome', label: 'Nome *', placeholder: 'Nome completo', required: true },
    { key: 'empresa', label: 'Empresa', placeholder: 'Nome da empresa' },
    { key: 'telefone', label: 'Telefone', placeholder: '(11) 99999-9999', keyboardType: 'phone-pad' },
    { key: 'whatsapp', label: 'WhatsApp', placeholder: '(11) 99999-9999', keyboardType: 'phone-pad' },
    { key: 'email', label: 'E-mail', placeholder: 'email@exemplo.com', keyboardType: 'email-address', autoCapitalize: 'none' },
    { key: 'cargo', label: 'Cargo', placeholder: 'Ex: Gerente de compras' },
    { key: 'endereco', label: 'Endereço', placeholder: 'Endereço completo', multiline: true },
    { key: 'observacoes', label: 'Observações', placeholder: 'Notas adicionais', multiline: true },
  ];

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView style={styles.container} contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        {fields.map((f) => (
          <View key={f.key} style={styles.field}>
            <Text style={styles.label}>{f.label}</Text>
            <TextInput
              style={[styles.input, f.multiline && styles.inputMulti]}
              value={form[f.key]}
              onChangeText={(v) => set(f.key, v)}
              placeholder={f.placeholder}
              placeholderTextColor="#BDBDBD"
              keyboardType={f.keyboardType || 'default'}
              autoCapitalize={f.autoCapitalize || 'sentences'}
              multiline={f.multiline}
              numberOfLines={f.multiline ? 3 : 1}
            />
          </View>
        ))}

        <TouchableOpacity
          style={[styles.saveBtn, loading && styles.saveBtnDisabled]}
          onPress={handleSave}
          disabled={loading}
        >
          {loading
            ? <ActivityIndicator color="#fff" size="small" />
            : <Text style={styles.saveBtnText}>{existing ? 'Atualizar Contato' : 'Criar Contato'}</Text>
          }
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F5' },
  content: { padding: 16, paddingBottom: 32 },
  field: { marginBottom: 12 },
  label: { fontSize: 13, fontWeight: '600', color: '#424242', marginBottom: 4 },
  input: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#E0E0E0',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: Platform.OS === 'ios' ? 12 : 8,
    fontSize: 15,
    color: '#212121',
  },
  inputMulti: { minHeight: 80, textAlignVertical: 'top' },
  saveBtn: {
    backgroundColor: '#1565C0',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 8,
    elevation: 3,
  },
  saveBtnDisabled: { opacity: 0.7 },
  saveBtnText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
});
