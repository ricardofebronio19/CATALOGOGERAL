import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';

export default function EmptyState({ icon = 'alert-circle-outline', title, message }) {
  return (
    <View style={styles.container}>
      <MaterialCommunityIcons name={icon} size={72} color="#BDBDBD" />
      <Text style={styles.title}>{title}</Text>
      {message ? <Text style={styles.message}>{message}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
    gap: 12,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#757575',
    textAlign: 'center',
  },
  message: {
    fontSize: 14,
    color: '#9E9E9E',
    textAlign: 'center',
    lineHeight: 20,
  },
});
