import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { t } from '@/lib/i18n';
import { theme } from '@/lib/theme';
import { useAuth } from '@/lib/useAuth';

type Mode = 'login' | 'register';

export default function LoginScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { loading, error, login, register } = useAuth();

  const [mode, setMode] = useState<Mode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const isLogin = mode === 'login';

  async function handleSubmit() {
    if (loading) return;
    const ok = isLogin
      ? await login(email, password)
      : await register(email, password);
    if (ok) router.replace('/');
  }

  return (
    <View
      style={[
        styles.container,
        { paddingTop: insets.top + theme.spacing.xl },
      ]}
    >
      <Text style={styles.title}>{t('app.name')}</Text>
      <Text style={styles.subtitle}>
        {isLogin ? t('auth.loginTitle') : t('auth.registerTitle')}
      </Text>

      <View style={styles.field}>
        <Text style={styles.label}>{t('auth.emailLabel')}</Text>
        <TextInput
          style={styles.input}
          value={email}
          onChangeText={setEmail}
          placeholder={t('auth.emailPlaceholder')}
          placeholderTextColor={theme.colors.textSecondary}
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="email-address"
          textContentType="emailAddress"
        />
      </View>

      <View style={styles.field}>
        <Text style={styles.label}>{t('auth.passwordLabel')}</Text>
        <TextInput
          style={styles.input}
          value={password}
          onChangeText={setPassword}
          placeholder={t('auth.passwordPlaceholder')}
          placeholderTextColor={theme.colors.textSecondary}
          autoCapitalize="none"
          autoCorrect={false}
          secureTextEntry
          textContentType="password"
        />
      </View>

      {error && (
        <View style={styles.errorBox}>
          <Ionicons name="alert-circle" size={18} color={theme.colors.danger} />
          <Text style={styles.errorText}>{t(error)}</Text>
        </View>
      )}

      <Pressable
        accessibilityRole="button"
        accessibilityState={{ disabled: loading }}
        disabled={loading}
        onPress={handleSubmit}
        style={({ pressed }) => [
          styles.submit,
          loading && styles.submitDisabled,
          pressed && styles.pressed,
        ]}
      >
        {loading ? (
          <ActivityIndicator color={theme.colors.background} />
        ) : (
          <Text style={styles.submitText}>
            {isLogin ? t('auth.loginSubmit') : t('auth.registerSubmit')}
          </Text>
        )}
      </Pressable>

      <Pressable
        accessibilityRole="button"
        onPress={() => setMode(isLogin ? 'register' : 'login')}
        style={({ pressed }) => [styles.toggle, pressed && styles.pressed]}
      >
        <Text style={styles.toggleText}>
          {isLogin ? t('auth.toRegister') : t('auth.toLogin')}
        </Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
    paddingHorizontal: theme.spacing.lg,
  },
  title: {
    fontFamily: theme.fonts.heading,
    fontSize: 32,
    fontWeight: '700',
    color: theme.colors.textPrimary,
  },
  subtitle: {
    fontFamily: theme.fonts.body,
    fontSize: 16,
    color: theme.colors.textSecondary,
    marginTop: theme.spacing.xs,
    marginBottom: theme.spacing.xl,
  },
  field: {
    marginBottom: theme.spacing.lg,
  },
  label: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.sm,
  },
  input: {
    minHeight: theme.touchTarget,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    paddingHorizontal: theme.spacing.lg,
    fontFamily: theme.fonts.body,
    fontSize: 16,
    color: theme.colors.textPrimary,
  },
  errorBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    marginBottom: theme.spacing.lg,
  },
  errorText: {
    flex: 1,
    fontFamily: theme.fonts.body,
    fontSize: 14,
    color: theme.colors.danger,
  },
  submit: {
    minHeight: theme.touchTarget,
    backgroundColor: theme.colors.accent,
    borderRadius: theme.radius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  submitDisabled: {
    opacity: 0.5,
  },
  submitText: {
    fontFamily: theme.fonts.heading,
    fontSize: 18,
    fontWeight: '700',
    color: theme.colors.background,
  },
  toggle: {
    minHeight: theme.touchTarget,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: theme.spacing.sm,
  },
  toggleText: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.accent,
  },
  pressed: {
    opacity: 0.85,
  },
});
