import React, { useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';

import api, { API_BASE_URL } from '../services/api';
import { colors } from '../constants/theme';

export default function LoginScreen({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleLogin() {
    setError('');
    setLoading(true);

    try {
      const response = await api.post('/auth/login', { username, password });
      await AsyncStorage.setItem('token', response.data.access_token);
      onLogin();
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Check your API and credentials.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      style={styles.container}
    >
      <View style={styles.brand}>
        <View style={styles.logo}>
          <Ionicons name="speedometer" size={34} color={colors.orange} />
        </View>
        <Text style={styles.title}>Well Analytics</Text>
        <Text style={styles.subtitle}>Performance Prediction & Optimization</Text>
      </View>

      <View style={styles.form}>
        <Text style={styles.label}>Username</Text>
        <TextInput
          value={username}
          onChangeText={setUsername}
          autoCapitalize="none"
          placeholder="Enter username"
          placeholderTextColor={colors.muted}
          style={styles.input}
        />

        <Text style={styles.label}>Password</Text>
        <TextInput
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          placeholder="Enter password"
          placeholderTextColor={colors.muted}
          style={styles.input}
        />

        {error ? <Text style={styles.error}>{error}</Text> : null}

        <Pressable
          onPress={handleLogin}
          disabled={loading || !username || !password}
          style={({ pressed }) => [
            styles.button,
            (pressed || loading || !username || !password) && styles.buttonPressed,
          ]}
        >
          {loading ? (
            <ActivityIndicator color={colors.navy} />
          ) : (
            <>
              <Ionicons name="log-in" size={20} color={colors.navy} />
              <Text style={styles.buttonText}>Login</Text>
            </>
          )}
        </Pressable>

        <Text style={styles.apiText}>API: {API_BASE_URL}</Text>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    padding: 24,
    backgroundColor: colors.background,
  },
  brand: {
    alignItems: 'center',
    marginBottom: 32,
  },
  logo: {
    width: 70,
    height: 70,
    borderRadius: 35,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.navy,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: 16,
  },
  title: {
    color: colors.white,
    fontSize: 30,
    fontWeight: '800',
  },
  subtitle: {
    color: colors.muted,
    marginTop: 8,
    textAlign: 'center',
  },
  form: {
    backgroundColor: colors.card,
    borderRadius: 8,
    padding: 18,
    borderWidth: 1,
    borderColor: colors.border,
  },
  label: {
    color: colors.white,
    fontWeight: '700',
    marginBottom: 8,
  },
  input: {
    height: 48,
    backgroundColor: colors.navy,
    borderRadius: 8,
    paddingHorizontal: 14,
    color: colors.white,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: 16,
  },
  error: {
    color: colors.red,
    marginBottom: 12,
    fontWeight: '700',
  },
  button: {
    height: 50,
    borderRadius: 8,
    backgroundColor: colors.orange,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 8,
  },
  buttonPressed: {
    opacity: 0.72,
  },
  buttonText: {
    color: colors.navy,
    fontWeight: '800',
    fontSize: 16,
  },
  apiText: {
    color: colors.muted,
    fontSize: 11,
    marginTop: 14,
    textAlign: 'center',
  },
});
